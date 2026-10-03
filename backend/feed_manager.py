"""
Feed Manager for CityPulse.
Orchestrates multi-feed ingestion, rolling event buffers, and graceful feed degradation.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from backend.app.models.schemas import FeedType, CivicEvent, FeedStatus, FeedHealth
from backend.app.ingestion.base import BaseIngestor
from backend.app.ingestion.weather_ingestor import WeatherIngestor
from backend.app.ingestion.transit_ingestor import TransitIngestor
from backend.app.ingestion.incidents_311_ingestor import Incidents311Ingestor
from backend.app.ingestion.air_quality_ingestor import AirQualityIngestor
from backend.app.ingestion.sentiment_ingestor import SentimentIngestor


class FeedManager:
    def __init__(self, use_live_apis: bool = False):
        self.weather = WeatherIngestor(use_live_api=use_live_apis)
        self.transit = TransitIngestor()
        self.incidents_311 = Incidents311Ingestor()
        self.air_quality = AirQualityIngestor(use_live_api=use_live_apis)
        self.sentiment = SentimentIngestor()

        self.ingestors: Dict[FeedType, BaseIngestor] = {
            FeedType.WEATHER: self.weather,
            FeedType.TRANSIT: self.transit,
            FeedType.INCIDENTS_311: self.incidents_311,
            FeedType.AIR_QUALITY: self.air_quality,
            FeedType.SOCIAL_SENTIMENT: self.sentiment,
        }

        # Rolling storage
        self.event_buffer: List[CivicEvent] = []
        self.max_buffer_size: int = 600
        self.feed_stats: Dict[FeedType, Dict[str, Any]] = {
            ft: {"count_last_hour": 0, "last_ingested": None, "latency_ms": 0.0}
            for ft in FeedType
        }

    async def ingest_all(self) -> List[CivicEvent]:
        """
        Polls and normalizes all active feeds concurrently.
        Gracefully skips offline feeds.
        """
        new_events: List[CivicEvent] = []
        tasks = []
        active_feeds: List[FeedType] = []

        for ft, ingestor in self.ingestors.items():
            if ingestor.is_enabled and ingestor.status != FeedStatus.OFFLINE:
                tasks.append(ingestor.fetch_raw_data())
                active_feeds.append(ft)

        if not tasks:
            return []

        results = await asyncio.gather(*tasks, return_exceptions=True)

        now = datetime.now(timezone.utc)
        for ft, res in zip(active_feeds, results):
            ingestor = self.ingestors[ft]
            if isinstance(res, Exception):
                # Feed encountered error -> mark degraded gracefully
                ingestor.status = FeedStatus.DEGRADED
                continue

            try:
                events = ingestor.parse_and_normalize(res)
                new_events.extend(events)
                self.feed_stats[ft]["count_last_hour"] += len(events)
                self.feed_stats[ft]["last_ingested"] = now
                self.feed_stats[ft]["latency_ms"] = ingestor.last_latency_ms
                if ingestor.status == FeedStatus.DEGRADED:
                    ingestor.status = FeedStatus.LIVE
            except Exception:
                ingestor.status = FeedStatus.DEGRADED

        # Append to buffer and prune old events (> 90 minutes)
        cutoff = now - timedelta(minutes=90)
        self.event_buffer.extend(new_events)
        self.event_buffer = [e for e in self.event_buffer if e.timestamp >= cutoff][-self.max_buffer_size:]

        return new_events

    def get_feed_health_map(self) -> Dict[str, FeedHealth]:
        """Returns diagnostic health summary of all 5 civic data feeds."""
        health_map: Dict[str, FeedHealth] = {}
        for ft, ing in self.ingestors.items():
            stats = self.feed_stats[ft]
            health_map[ft.value] = FeedHealth(
                feed_type=ft,
                status=ing.status if ing.is_enabled else FeedStatus.OFFLINE,
                last_ingested_at=stats["last_ingested"],
                event_count_last_hour=stats["count_last_hour"],
                latency_ms=stats["latency_ms"],
            )
        return health_map

    def toggle_feed(self, feed_type_str: str, enable: bool):
        """Allows toggling feeds ON/OFF for resilience and graceful degradation testing."""
        for ft, ing in self.ingestors.items():
            if ft.value.lower() == feed_type_str.lower() or ft.value == feed_type_str:
                ing.is_enabled = enable
                ing.status = FeedStatus.LIVE if enable else FeedStatus.OFFLINE
                return True
        return False

    def clear_buffer(self):
        self.event_buffer.clear()
        self.incidents_311.clear_injected()
        self.transit.reset_overrides()
        self.sentiment.reset_state()
