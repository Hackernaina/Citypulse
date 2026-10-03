"""
Tests for Threshold Alerting & Notification Manager (Point 6).
"""

from backend.app.models.schemas import ZonePulse
from backend.app.alerting.alert_manager import AlertManager


def test_alert_manager_threshold_triggers():
    manager = AlertManager()

    zones_pulse = {
        "east_suburbs": ZonePulse(
            zone_id="east_suburbs",
            zone_name="East Suburbs & Industrial Park",
            health_score=52.0,
            status_label="Elevated Stress",
            status_color="amber",
            weather_summary="Dry",
            transit_status="Normal",
            incident_count=1,
            aqi_index=165.0,  # Exceeds default threshold 120.0
            sentiment_score=0.1,
        )
    }

    # Evaluate with overall health below 65 (e.g. 58)
    alerts = manager.evaluate(
        overall_health=58.0,
        zones_pulse=zones_pulse,
        anomalies=[],
        correlations=[],
    )

    assert len(alerts) >= 2
    # Verify health alert and aqi alert
    rule_ids = [a["rule_id"] for a in alerts]
    assert "rule_health_drop" in rule_ids
    assert "rule_aqi_spike" in rule_ids

    # Verify webhook dispatch log was populated
    assert len(manager.webhook_dispatch_log) >= 2


def test_alert_acknowledgement_and_clearing():
    manager = AlertManager()
    manager.active_alerts.append({
        "alert_id": "test-alert-1",
        "title": "Test Alert",
        "message": "Testing",
        "acknowledged": False,
    })

    # Acknowledge
    assert manager.acknowledge_alert("test-alert-1") is True
    assert manager.active_alerts[0]["acknowledged"] is True

    # Clear
    assert manager.clear_alert("test-alert-1") is True
    assert len(manager.active_alerts) == 0
