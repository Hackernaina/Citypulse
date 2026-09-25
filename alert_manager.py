"""
Threshold Alerting & Notification Manager for CityPulse.
Evaluates customizable civic thresholds, surfaces alerts, and manages notification lifecycles.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import uuid
from backend.app.models.schemas import CivicEvent, Anomaly, Correlation, SeverityLevel


class AlertRule:
    def __init__(
        self,
        rule_id: str,
        name: str,
        metric: str,
        threshold: float,
        operator: str,  # "gt", "lt"
        severity: SeverityLevel,
        channel: str = "IN_APP",
        enabled: bool = True,
    ):
        self.rule_id = rule_id
        self.name = name
        self.metric = metric
        self.threshold = threshold
        self.operator = operator
        self.severity = severity
        self.channel = channel
        self.enabled = enabled


class AlertManager:
    def __init__(self):
        self.rules: Dict[str, AlertRule] = {
            "rule_health_drop": AlertRule(
                rule_id="rule_health_drop",
                name="Civic Stress Threshold",
                metric="civic_health",
                threshold=65.0,
                operator="lt",
                severity=SeverityLevel.HIGH,
            ),
            "rule_aqi_spike": AlertRule(
                rule_id="rule_aqi_spike",
                name="Unhealthy Air Quality Threshold",
                metric="aqi",
                threshold=120.0,
                operator="gt",
                severity=SeverityLevel.HIGH,
            ),
            "rule_transit_delay": AlertRule(
                rule_id="rule_transit_delay",
                name="Severe Transit Delay Threshold",
                metric="transit_delay",
                threshold=18.0,
                operator="gt",
                severity=SeverityLevel.MODERATE,
            ),
            "rule_flood_warning": AlertRule(
                rule_id="rule_flood_warning",
                name="Flash Flood / Heavy Rain Threshold",
                metric="precipitation_mm_hr",
                threshold=15.0,
                operator="gt",
                severity=SeverityLevel.HIGH,
            ),
        }
        self.active_alerts: List[Dict[str, Any]] = []
        self.notification_history: List[Dict[str, Any]] = []
        self.webhook_dispatch_log: List[Dict[str, Any]] = []

    def evaluate(
        self,
        overall_health: float,
        zones_pulse: Dict[str, Any],
        anomalies: List[Anomaly],
        correlations: List[Correlation],
    ) -> List[Dict[str, Any]]:
        """
        Evaluates active rules against current city telemetry and raises alerts.
        """
        now = datetime.now(timezone.utc)
        current_alerts: List[Dict[str, Any]] = []

        # 1. Evaluate Overall Health Rule
        r_health = self.rules.get("rule_health_drop")
        if r_health and r_health.enabled and overall_health < r_health.threshold:
            current_alerts.append({
                "alert_id": f"alert-health-{int(now.timestamp())}",
                "rule_id": r_health.rule_id,
                "title": f"Civic Health Dropped to {overall_health:.1f}%",
                "message": f"Metropolis Central health index dropped below threshold ({r_health.threshold}%). Civic stress is elevated.",
                "severity": r_health.severity.value,
                "timestamp": now.isoformat(),
                "zone_id": "citywide",
                "zone_name": "Citywide",
                "acknowledged": False,
            })

        # 2. Evaluate Zone-Specific Rules
        for zid, zp in zones_pulse.items():
            # AQI Rule
            r_aqi = self.rules.get("rule_aqi_spike")
            if r_aqi and r_aqi.enabled and zp.aqi_index > r_aqi.threshold:
                current_alerts.append({
                    "alert_id": f"alert-aqi-{zid}-{int(now.timestamp())}",
                    "rule_id": r_aqi.rule_id,
                    "title": f"Air Quality Alert: {zp.zone_name}",
                    "message": f"AQI reached {int(zp.aqi_index)} (threshold: {r_aqi.threshold}). Sensitive groups should take precautions.",
                    "severity": r_aqi.severity.value,
                    "timestamp": now.isoformat(),
                    "zone_id": zid,
                    "zone_name": zp.zone_name,
                    "acknowledged": False,
                })

        # 3. Raise Alerts for Compound Correlations
        for c in correlations:
            current_alerts.append({
                "alert_id": f"alert-corr-{c.correlation_id}",
                "rule_id": "correlation_cascade",
                "title": f"Compound Incident: {c.title}",
                "message": c.hypothesis,
                "severity": SeverityLevel.CRITICAL.value if c.confidence_score >= 0.85 else SeverityLevel.HIGH.value,
                "timestamp": now.isoformat(),
                "zone_id": c.zone_id,
                "zone_name": c.zone_name,
                "acknowledged": False,
                "confidence": c.confidence_score,
            })

        # Deduplicate & record history
        for a in current_alerts:
            if not any(x["alert_id"] == a["alert_id"] for x in self.active_alerts):
                self.active_alerts.append(a)
                self.notification_history.append(a)
                # Dispatch simulated webhook / notification
                self.webhook_dispatch_log.append({
                    "dispatched_at": now.isoformat(),
                    "destination": "Resident Notification Push / Municipal Webhook",
                    "payload": a,
                })

        # Keep history within reasonable limit
        self.notification_history = self.notification_history[-50:]
        self.webhook_dispatch_log = self.webhook_dispatch_log[-30:]

        return self.active_alerts

    def acknowledge_alert(self, alert_id: str) -> bool:
        for a in self.active_alerts:
            if a["alert_id"] == alert_id:
                a["acknowledged"] = True
                return True
        return False

    def clear_alert(self, alert_id: str) -> bool:
        self.active_alerts = [a for a in self.active_alerts if a["alert_id"] != alert_id]
        return True

    def update_threshold(self, rule_id: str, new_threshold: float) -> bool:
        if rule_id in self.rules:
            self.rules[rule_id].threshold = new_threshold
            return True
        return False

    def get_rules(self) -> List[Dict[str, Any]]:
        return [
            {
                "rule_id": r.rule_id,
                "name": r.name,
                "metric": r.metric,
                "threshold": r.threshold,
                "operator": r.operator,
                "severity": r.severity.value,
                "enabled": r.enabled,
            }
            for r in self.rules.values()
        ]
