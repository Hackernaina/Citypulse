"""
Civic Sentiment & Hyperlocal Chatter Ingestor.
Ingests aggregated, anonymized social sentiment and volume spike ratios across city districts.
Adheres strictly to Privacy Constraint: No PII, fully aggregated civic sentiment telemetry.
"""

import random
import time
from typing import List, Dict, Any
from backend.app.models.schemas import FeedType, CivicEvent, SeverityLevel
from backend.app.ingestion.base import BaseIngestor
from backend.app.ingestion.normalizer import FeedNormalizer
from backend.app.config import CITY_ZONES


SAMPLE_CIVIC_KEYWORDS = {
    "positive": ["smooth commute", "sunny day", "farmers market open", "clean park", "on time train"],
    "concern": ["traffic slowing down", "storm clouds rolling in", "pothole on 5th", "crowded bus", "bus skipped stop"],
    "distress": ["underpass flooded cars stuck", "lights out completely", "smoke smell burning", "subway suspended emergency", "huge siren parade"],
}


class SentimentIngestor(BaseIngestor):
    def __init__(self):
        super().__init__(FeedType.SOCIAL_SENTIMENT)
        self._zone_sentiment_state = {
            zid: {"sentiment": 0.55, "volume_multiplier": 1.0, "top_phrases": ["pleasant morning", "traffic moving"]}
            for zid in CITY_ZONES
        }

    async def fetch_raw_data(self) -> List[Dict[str, Any]]:
        start_time = time.time()
        raw_items: List[Dict[str, Any]] = []

        for zone_id, zone in CITY_ZONES.items():
            curr = self._zone_sentiment_state[zone_id]
            # Baseline minor fluctuation
            curr["sentiment"] = round(max(-1.0, min(1.0, curr["sentiment"] + random.uniform(-0.05, 0.05))), 2)

            raw_items.append({
                "stream": "Aggregated Hyperlocal Public Pulse (Anonymized)",
                "zone_id": zone_id,
                "timestamp": "now",
                "sentiment_polarity": curr["sentiment"],  # -1.0 to +1.0
                "chatter_volume_multiplier": curr["volume_multiplier"],
                "sample_trending_phrases": curr["top_phrases"],
                "sample_count": int(150 * curr["volume_multiplier"]),
                "privacy_audit": "COMPLIANT_ANONYMIZED_ONLY",
                "center_point": {"lat": zone.center_lat, "lng": zone.center_lng},
            })

        self.last_latency_ms = round((time.time() - start_time) * 1000, 2)
        return raw_items

    def parse_and_normalize(self, raw_items: List[Dict[str, Any]]) -> List[CivicEvent]:
        events: List[CivicEvent] = []
        for item in raw_items:
            zone_id = item.get("zone_id", "downtown")
            zid, zname, loc = FeedNormalizer.resolve_zone(
                lat=item.get("center_point", {}).get("lat"),
                lng=item.get("center_point", {}).get("lng"),
                zone_id=zone_id
            )

            timestamp = FeedNormalizer.parse_timestamp(item.get("timestamp"))
            polarity = float(item.get("sentiment_polarity", 0.0))
            vol_mult = float(item.get("chatter_volume_multiplier", 1.0))
            phrases = item.get("sample_trending_phrases", [])
            phrase_str = f" ('{phrases[0]}')" if phrases else ""

            if polarity <= -0.6 or vol_mult >= 3.5:
                severity = SeverityLevel.HIGH
                headline = f"Social Sentiment Alert: Sharp resident distress in {zname}{phrase_str} ({vol_mult:.1f}x chatter spike)"
            elif polarity <= -0.2:
                severity = SeverityLevel.MODERATE
                headline = f"Civic Chatter Advisory: Elevated resident frustration in {zname}{phrase_str}"
            else:
                severity = SeverityLevel.NORMAL
                headline = f"Community sentiment stable in {zname} (Index: {polarity:+.2f})"

            impact = FeedNormalizer.calculate_impact_score(
                FeedType.SOCIAL_SENTIMENT, "sentiment_score", polarity, severity
            )

            events.append(CivicEvent(
                feed_type=FeedType.SOCIAL_SENTIMENT,
                timestamp=timestamp,
                zone_id=zid,
                zone_name=zname,
                location=loc,
                severity=severity,
                metric_name="sentiment_score",
                metric_value=polarity,
                metric_unit="polarity",
                summary_headline=headline,
                civic_impact_score=impact,
                raw_payload=item,
                feed_source="Aggregated Civic Social Sentiment",
            ))
        return events

    def inject_sentiment_drop(self, zone_id: str, polarity: float, volume_multiplier: float, phrases: List[str]):
        """Inject negative sentiment spike during crisis."""
        if zone_id in self._zone_sentiment_state:
            self._zone_sentiment_state[zone_id]["sentiment"] = polarity
            self._zone_sentiment_state[zone_id]["volume_multiplier"] = volume_multiplier
            self._zone_sentiment_state[zone_id]["top_phrases"] = phrases

    def reset_state(self):
        for zid in self._zone_sentiment_state:
            self._zone_sentiment_state[zid]["sentiment"] = 0.55
            self._zone_sentiment_state[zid]["volume_multiplier"] = 1.0
            self._zone_sentiment_state[zid]["top_phrases"] = ["pleasant morning", "traffic moving"]
