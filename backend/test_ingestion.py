"""
Tests for Data Ingestion, Normalization, and Graceful Degradation (Points 1 & 2).
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from backend.app.models.schemas import FeedType, SeverityLevel, FeedStatus
from backend.app.ingestion.normalizer import FeedNormalizer
from backend.app.ingestion.weather_ingestor import WeatherIngestor
from backend.app.ingestion.transit_ingestor import TransitIngestor
from backend.app.ingestion.incidents_311_ingestor import Incidents311Ingestor
from backend.app.ingestion.air_quality_ingestor import AirQualityIngestor
from backend.app.ingestion.sentiment_ingestor import SentimentIngestor
from backend.app.ingestion.feed_manager import FeedManager


def test_feed_normalizer_mismatched_timestamps():
    """Verify normalizer handles epoch ms, epoch sec, ISO strings, and relative strings."""
    # 1. ISO string with Z
    dt1 = FeedNormalizer.parse_timestamp("2026-09-25T12:00:00Z")
    assert dt1.year == 2026 and dt1.month == 9

    # 2. Epoch milliseconds
    dt2 = FeedNormalizer.parse_timestamp(1727265600000)
    assert isinstance(dt2, datetime)

    # 3. Epoch seconds
    dt3 = FeedNormalizer.parse_timestamp(1727265600)
    assert isinstance(dt3, datetime)

    # 4. Relative time string
    dt4 = FeedNormalizer.parse_timestamp("5 mins ago")
    now = datetime.now(timezone.utc)
    diff = abs((now - dt4).total_seconds())
    assert 280 <= diff <= 320  # ~300 seconds


def test_feed_normalizer_impact_score():
    """Verify standard 0-100 civic impact scoring."""
    # Normal calm weather
    score_calm = FeedNormalizer.calculate_impact_score(FeedType.WEATHER, "precipitation_mm_hr", 0.0, SeverityLevel.NORMAL)
    assert 0.0 <= score_calm <= 15.0

    # Severe downpour
    score_storm = FeedNormalizer.calculate_impact_score(FeedType.WEATHER, "precipitation_mm_hr", 35.0, SeverityLevel.CRITICAL)
    assert score_storm >= 80.0

    # Unhealthy AQI
    score_aqi = FeedNormalizer.calculate_impact_score(FeedType.AIR_QUALITY, "aqi", 185.0, SeverityLevel.HIGH)
    assert score_aqi >= 70.0


def test_all_five_distinct_ingestors():
    """Verify ingestion and normalization across 5 distinct civic feeds (Point 1)."""
    async def _run():
        weather = WeatherIngestor(use_live_api=False)
        transit = TransitIngestor()
        incidents = Incidents311Ingestor()
        aq = AirQualityIngestor(use_live_api=False)
        sentiment = SentimentIngestor()

        raw_w = await weather.fetch_raw_data()
        events_w = weather.parse_and_normalize(raw_w)
        assert len(events_w) > 0
        assert events_w[0].feed_type == FeedType.WEATHER

        raw_t = await transit.fetch_raw_data()
        events_t = transit.parse_and_normalize(raw_t)
        assert len(events_t) > 0
        assert events_t[0].feed_type == FeedType.TRANSIT

        incidents.inject_incident("downtown", "STREET_FLOODING", "Test drain clog")
        raw_i = await incidents.fetch_raw_data()
        events_i = incidents.parse_and_normalize(raw_i)
        assert len(events_i) > 0
        assert any(e.feed_type == FeedType.INCIDENTS_311 for e in events_i)

        raw_aq = await aq.fetch_raw_data()
        events_aq = aq.parse_and_normalize(raw_aq)
        assert len(events_aq) > 0
        assert events_aq[0].feed_type == FeedType.AIR_QUALITY

        raw_s = await sentiment.fetch_raw_data()
        events_s = sentiment.parse_and_normalize(raw_s)
        assert len(events_s) > 0
        assert events_s[0].feed_type == FeedType.SOCIAL_SENTIMENT

    asyncio.run(_run())


def test_feed_manager_and_graceful_degradation():
    """Verify FeedManager concurrent ingestion and graceful degradation when a feed drops."""
    async def _run():
        manager = FeedManager(use_live_apis=False)
        events = await manager.ingest_all()
        assert len(events) > 0

        # Simulate dropping the weather feed
        success = manager.toggle_feed("WEATHER", False)
        assert success is True
        health = manager.get_feed_health_map()
        assert health["WEATHER"].status == FeedStatus.OFFLINE

        # Ingest again; should not raise exception or crash
        events_degraded = await manager.ingest_all()
        assert not any(e.feed_type == FeedType.WEATHER for e in events_degraded)
        assert any(e.feed_type == FeedType.TRANSIT for e in events_degraded)

        # Re-enable feed
        manager.toggle_feed("WEATHER", True)
        events_recovered = await manager.ingest_all()
        assert any(e.feed_type == FeedType.WEATHER for e in events_recovered)

    asyncio.run(_run())
