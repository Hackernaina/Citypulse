"""
Civic Health & Pulse Calculator for CityPulse.
Aggregates normalized events, anomalies, and correlations into glanceable 0-100 scores and BPM pulse rates.
"""

from typing import List, Dict
from datetime import datetime, timezone, timedelta
from backend.app.models.schemas import (
    CivicEvent, Anomaly, Correlation, ZonePulse, FeedHealth, CityPulseState, FeedType
)
from backend.app.config import CITY_ZONES


class CivicHealthCalculator:
    def __init__(self, rolling_window_minutes: int = 30):
        self.rolling_window_minutes = rolling_window_minutes

    def calculate_state(
        self,
        events: List[CivicEvent],
        anomalies: List[Anomaly],
        correlations: List[Correlation],
        feeds_health: Dict[str, FeedHealth],
        is_replay: bool = False,
        replay_step: int = None,
        replay_total: int = None,
    ) -> Dict[str, Any]:
        """
        Calculates zone pulses, citywide health score, and pulse BPM.
        """
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(minutes=self.rolling_window_minutes)
        window_events = [e for e in events if e.timestamp >= cutoff]

        zones_pulse: Dict[str, ZonePulse] = {}
        total_city_stress = 0.0

        for zone_id, zone_config in CITY_ZONES.items():
            z_events = [e for e in window_events if e.zone_id == zone_id]
            z_anomalies = [a for a in anomalies if a.zone_id == zone_id]
            z_correlations = [c for c in correlations if c.zone_id == zone_id]

            # Calculate stress penalty (0 to 100)
            event_impact = sum(e.civic_impact_score for e in z_events)
            anomaly_impact = len(z_anomalies) * 15.0
            correlation_impact = len(z_correlations) * 25.0

            raw_stress = (event_impact * 0.35) + anomaly_impact + correlation_impact
            stress = min(100.0, raw_stress)
            health = round(max(0.0, 100.0 - stress), 1)
            total_city_stress += stress

            # Status designation
            if health >= 85.0:
                label = "Calm & Stable"
                color = "emerald"
            elif health >= 70.0:
                label = "Normal Activity"
                color = "teal"
            elif health >= 55.0:
                label = "Elevated Stress"
                color = "amber"
            elif health >= 40.0:
                label = "High Disruption"
                color = "orange"
            else:
                label = "Critical Disruption"
                color = "rose"

            # Summaries
            weather_evs = [e for e in z_events if e.feed_type == FeedType.WEATHER]
            transit_evs = [e for e in z_events if e.feed_type == FeedType.TRANSIT]
            aqi_evs = [e for e in z_events if e.feed_type == FeedType.AIR_QUALITY]
            sent_evs = [e for e in z_events if e.feed_type == FeedType.SOCIAL_SENTIMENT]

            weather_desc = weather_evs[-1].summary_headline if weather_evs else "Normal Conditions"
            transit_desc = transit_evs[-1].summary_headline if transit_evs else "On Schedule"
            aqi_val = aqi_evs[-1].metric_value if aqi_evs else 42.0
            sent_val = sent_evs[-1].metric_value if sent_evs else 0.55
            incident_count = len([e for e in z_events if e.feed_type == FeedType.INCIDENTS_311])

            zones_pulse[zone_id] = ZonePulse(
                zone_id=zone_id,
                zone_name=zone_config.name,
                health_score=health,
                status_label=label,
                status_color=color,
                weather_summary=weather_desc,
                transit_status=transit_desc,
                incident_count=incident_count,
                aqi_index=aqi_val,
                sentiment_score=sent_val,
                active_anomalies=z_anomalies,
                active_correlations=z_correlations,
                recent_events=z_events[-6:],
            )

        avg_city_stress = total_city_stress / max(1, len(CITY_ZONES))
        overall_health = round(max(0.0, 100.0 - avg_city_stress), 1)

        # Metaphorical BPM: 65 is relaxed resting heart rate; 130 is emergency tachycardia
        pulse_bpm = int(65 + (100.0 - overall_health) * 0.7)

        if overall_health >= 85.0:
            overall_status = "City Pulse Healthy"
        elif overall_health >= 70.0:
            overall_status = "City Pulse Active"
        elif overall_health >= 55.0:
            overall_status = "Elevated City Stress"
        else:
            overall_status = "Severe Disruption Active"

        return {
            "overall_health_score": overall_health,
            "overall_status_label": overall_status,
            "pulse_rate_bpm": pulse_bpm,
            "zones": zones_pulse,
            "window_events": window_events,
        }
