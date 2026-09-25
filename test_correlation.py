"""
Tests for Anomaly Detection and Cross-Feed Correlation (Point 3).
"""

from datetime import datetime, timezone
from backend.app.models.schemas import CivicEvent, FeedType, SeverityLevel, GeoPoint
from backend.app.analytics.anomaly_detector import AnomalyDetector
from backend.app.analytics.correlation_engine import CorrelationEngine


def test_anomaly_detection_complaint_spike():
    """Verify statistical anomaly triggers on 311 complaint density surge."""
    detector = AnomalyDetector(z_threshold=2.0, rolling_minutes=30)
    now = datetime.now(timezone.utc)

    # Normal events
    events = [
        CivicEvent(
            feed_type=FeedType.INCIDENTS_311,
            timestamp=now,
            zone_id="downtown",
            zone_name="Downtown & Financial Core",
            location=GeoPoint(lat=40.7128, lng=-74.0060),
            severity=SeverityLevel.HIGH,
            metric_name="incident_count",
            metric_value=1.0,
            metric_unit="report",
            summary_headline=f"311 Complaint #{i}",
            civic_impact_score=50.0,
        )
        for i in range(12)  # 12 complaints far exceeds baseline of 4.0
    ]

    anomalies = detector.detect_anomalies(events)
    assert len(anomalies) >= 1
    a = anomalies[0]
    assert a.feed_type == FeedType.INCIDENTS_311
    assert a.z_score >= 2.0
    assert a.zone_id == "downtown"


def test_cross_feed_correlation_storm_cascade():
    """
    Verify cross-feed spatio-temporal correlation detects compound crisis:
    Torrential Rain + Flooding 311 Calls + Transit Stoppage.
    """
    detector = AnomalyDetector(z_threshold=2.0, rolling_minutes=30)
    engine = CorrelationEngine(time_window_minutes=30)
    now = datetime.now(timezone.utc)

    # 1. Weather event: torrential rain in Downtown
    e_weather = CivicEvent(
        feed_type=FeedType.WEATHER,
        timestamp=now,
        zone_id="downtown",
        zone_name="Downtown & Financial Core",
        location=GeoPoint(lat=40.7128, lng=-74.0060),
        severity=SeverityLevel.CRITICAL,
        metric_name="precipitation_mm_hr",
        metric_value=32.0,
        metric_unit="mm/hr",
        summary_headline="Severe cloudburst: 32 mm/hr rain over Downtown",
        civic_impact_score=90.0,
    )

    # 2. 311 incident: underpass flooding
    e_incident = CivicEvent(
        feed_type=FeedType.INCIDENTS_311,
        timestamp=now,
        zone_id="downtown",
        zone_name="Downtown & Financial Core",
        location=GeoPoint(lat=40.7128, lng=-74.0060),
        severity=SeverityLevel.HIGH,
        metric_name="incident_count",
        metric_value=1.0,
        metric_unit="report",
        summary_headline="311 Alert: Roadway flooding and catch-basin overflow",
        civic_impact_score=75.0,
    )

    # 3. Transit delay: Bus halted due to water
    e_transit = CivicEvent(
        feed_type=FeedType.TRANSIT,
        timestamp=now,
        zone_id="downtown",
        zone_name="Downtown & Financial Core",
        location=GeoPoint(lat=40.7128, lng=-74.0060),
        severity=SeverityLevel.CRITICAL,
        metric_name="delay_minutes",
        metric_value=28.0,
        metric_unit="minutes",
        summary_headline="Bus 12 delayed by 28 mins due to high water on roadway",
        civic_impact_score=85.0,
    )

    events = [e_weather, e_incident, e_transit]
    anomalies = detector.detect_anomalies(events)
    correlations = engine.correlate(events, anomalies)

    assert len(correlations) >= 1
    c = correlations[0]
    assert c.pattern_type == "STORM_TRANSIT_CASCADE"
    assert c.zone_id == "downtown"
    assert FeedType.WEATHER in c.feeds_involved
    assert FeedType.INCIDENTS_311 in c.feeds_involved
    assert FeedType.TRANSIT in c.feeds_involved
    assert c.confidence_score >= 0.70

    # Constraint 7 check: Epistemic honesty disclaimer present
    assert "Probable link" in c.epistemic_disclaimer or "not confirmed direct causation" in c.epistemic_disclaimer
