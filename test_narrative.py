"""
Tests for Plain-Language Summary Engine (Point 5 - Focus Requirement).
"""

from datetime import datetime, timezone
from backend.app.models.schemas import (
    CivicEvent, Correlation, ZonePulse, FeedType, SeverityLevel, GeoPoint
)
from backend.app.narrative.summary_engine import PlainLanguageSummaryEngine


def test_plain_language_summary_calm_conditions():
    """Verify narrative synthesis during normal calm baseline."""
    engine = PlainLanguageSummaryEngine()
    now = datetime.now(timezone.utc)

    zones_pulse = {
        "downtown": ZonePulse(
            zone_id="downtown",
            zone_name="Downtown & Financial Core",
            health_score=94.0,
            status_label="Calm & Stable",
            status_color="emerald",
            weather_summary="Clear, 22°C",
            transit_status="On Schedule",
            incident_count=1,
            aqi_index=35.0,
            sentiment_score=0.65,
        )
    }

    summary = engine.generate_summary(
        overall_health=94.0,
        overall_status="City Pulse Healthy",
        events=[],
        anomalies=[],
        correlations=[],
        zones_pulse=zones_pulse,
    )

    assert "normal" in summary.ten_second_headline.lower() or "calm" in summary.ten_second_headline.lower()
    assert len(summary.what_is_happening) >= 1
    assert len(summary.why_it_matters) >= 1
    assert len(summary.actionable_advice) >= 1
    assert "Grounding Guarantee" in summary.epistemic_note


def test_plain_language_summary_crisis_cascade():
    """Verify narrative translates technical compound crisis into non-technical resident guidance."""
    engine = PlainLanguageSummaryEngine()
    now = datetime.now(timezone.utc)

    corr = Correlation(
        title="Storm-Induced Drainage & Transit Cascade in Downtown",
        zone_id="downtown",
        zone_name="Downtown & Financial Core",
        feeds_involved=[FeedType.WEATHER, FeedType.INCIDENTS_311, FeedType.TRANSIT],
        event_ids=["e1", "e2"],
        confidence_score=0.91,
        pattern_type="STORM_TRANSIT_CASCADE",
        hypothesis="Heavy rainfall (32 mm/hr) coincided with flood reports and transit delays.",
        impact_rationale="Surface runoff overwhelmed catch-basins.",
    )

    zones_pulse = {
        "downtown": ZonePulse(
            zone_id="downtown",
            zone_name="Downtown & Financial Core",
            health_score=42.0,
            status_label="High Disruption",
            status_color="orange",
            weather_summary="Severe Cloudburst",
            transit_status="Bus Delays",
            incident_count=5,
            aqi_index=40.0,
            sentiment_score=-0.65,
        )
    }

    summary = engine.generate_summary(
        overall_health=48.0,
        overall_status="Severe Disruption Active",
        events=[],
        anomalies=[],
        correlations=[corr],
        zones_pulse=zones_pulse,
    )

    # 1. 10-second headline indicates disruption
    assert "disrupt" in summary.ten_second_headline.lower() or "alert" in summary.ten_second_headline.lower()

    # 2. What's happening explicitly mentions water/drainage
    assert any("drainage" in text.lower() or "rainfall" in text.lower() for text in summary.what_is_happening)

    # 3. Why it matters informs resident about commute/daily impact
    assert any("commute" in text.lower() or "minutes" in text.lower() or "underpass" in text.lower() for text in summary.why_it_matters)

    # 4. Actionable advice gives clear guidance (avoid underpass / take rail)
    assert any("underpass" in text.lower() or "rail" in text.lower() for text in summary.actionable_advice)
