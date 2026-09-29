"""
Anomaly Detection Engine for CityPulse.
Detects statistical baseline deviations and threshold spikes across all normalized civic streams.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
import math
from backend.app.models.schemas import CivicEvent, Anomaly, FeedType, SeverityLevel
from backend.app.config import CITY_ZONES


class AnomalyDetector:
    def __init__(self, z_threshold: float = 2.0, rolling_minutes: int = 30):
        self.z_threshold = z_threshold
        self.rolling_minutes = rolling_minutes

    def detect_anomalies(self, recent_events: List[CivicEvent]) -> List[Anomaly]:
        """
        Analyzes recent events within the rolling window and surfaces anomalies.
        """
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(minutes=self.rolling_minutes)
        window_events = [e for e in recent_events if e.timestamp >= cutoff]

        anomalies: List[Anomaly] = []

        # 1. Group events by zone_id and metric_name
        grouped: Dict[str, Dict[str, List[CivicEvent]]] = {zid: {} for zid in CITY_ZONES}
        for e in window_events:
            if e.zone_id in grouped:
                metric_key = f"{e.feed_type.value}:{e.metric_name}"
                grouped[e.zone_id].setdefault(metric_key, []).append(e)

        for zone_id, zone_config in CITY_ZONES.items():
            metrics = grouped[zone_id]

            # A. 311 Complaint Density Anomaly
            complaint_events = metrics.get(f"{FeedType.INCIDENTS_311.value}:incident_count", [])
            complaint_count = len(complaint_events)
            baseline_complaints = zone_config.baseline_complaint_rate
            # Poisson/Gaussian variance approximation
            complaint_std = max(1.0, math.sqrt(baseline_complaints))
            z_complaints = (complaint_count - baseline_complaints) / complaint_std

            if z_complaints >= self.z_threshold and complaint_count >= 3:
                sev = SeverityLevel.CRITICAL if z_complaints >= 3.5 else SeverityLevel.HIGH
                anomalies.append(Anomaly(
                    feed_type=FeedType.INCIDENTS_311,
                    zone_id=zone_id,
                    zone_name=zone_config.name,
                    metric_name="incident_count",
                    current_value=float(complaint_count),
                    baseline_value=float(baseline_complaints),
                    z_score=round(z_complaints, 2),
                    description=(
                        f"Spike in 311 incident reports ({complaint_count} reports vs {baseline_complaints:.1f} baseline, "
                        f"Z-score {z_complaints:.2f}) in {zone_config.name}."
                    ),
                    severity=sev,
                ))

            # B. Transit Delay Anomaly
            transit_events = metrics.get(f"{FeedType.TRANSIT.value}:delay_minutes", [])
            if transit_events:
                avg_delay = sum(e.metric_value for e in transit_events) / len(transit_events)
                baseline_delay = zone_config.baseline_transit_delay
                delay_std = 3.5
                z_delay = (avg_delay - baseline_delay) / delay_std

                if z_delay >= self.z_threshold or avg_delay >= 18.0:
                    sev = SeverityLevel.CRITICAL if avg_delay >= 25.0 else SeverityLevel.HIGH
                    anomalies.append(Anomaly(
                        feed_type=FeedType.TRANSIT,
                        zone_id=zone_id,
                        zone_name=zone_config.name,
                        metric_name="delay_minutes",
                        current_value=round(avg_delay, 1),
                        baseline_value=round(baseline_delay, 1),
                        z_score=round(z_delay, 2),
                        description=(
                            f"Transit congestion surge: {avg_delay:.1f} min avg delay "
                            f"(expected {baseline_delay:.1f} min) across lines serving {zone_config.name}."
                        ),
                        severity=sev,
                    ))

            # C. Weather Precipitation Anomaly
            weather_events = metrics.get(f"{FeedType.WEATHER.value}:precipitation_mm_hr", [])
            if weather_events:
                max_rain = max(e.metric_value for e in weather_events)
                if max_rain >= 15.0:
                    z_rain = (max_rain - 0.5) / 4.0
                    sev = SeverityLevel.CRITICAL if max_rain >= 25.0 else SeverityLevel.HIGH
                    anomalies.append(Anomaly(
                        feed_type=FeedType.WEATHER,
                        zone_id=zone_id,
                        zone_name=zone_config.name,
                        metric_name="precipitation_mm_hr",
                        current_value=round(max_rain, 1),
                        baseline_value=0.5,
                        z_score=round(z_rain, 2),
                        description=f"Intense precipitation event ({max_rain} mm/hr) over {zone_config.name}.",
                        severity=sev,
                    ))

            # D. Air Quality Anomaly
            aqi_events = metrics.get(f"{FeedType.AIR_QUALITY.value}:aqi", [])
            if aqi_events:
                max_aqi = max(e.metric_value for e in aqi_events)
                if max_aqi >= 120.0:
                    z_aqi = (max_aqi - 50.0) / 25.0
                    sev = SeverityLevel.CRITICAL if max_aqi >= 180.0 else SeverityLevel.HIGH
                    anomalies.append(Anomaly(
                        feed_type=FeedType.AIR_QUALITY,
                        zone_id=zone_id,
                        zone_name=zone_config.name,
                        metric_name="aqi",
                        current_value=round(max_aqi, 1),
                        baseline_value=45.0,
                        z_score=round(z_aqi, 2),
                        description=f"Air Quality degradation spike: AQI reached {int(max_aqi)} in {zone_config.name}.",
                        severity=sev,
                    ))

            # E. Social Sentiment Anomaly
            sentiment_events = metrics.get(f"{FeedType.SOCIAL_SENTIMENT.value}:sentiment_score", [])
            if sentiment_events:
                min_sentiment = min(e.metric_value for e in sentiment_events)
                if min_sentiment <= -0.4:
                    z_sent = (0.5 - min_sentiment) / 0.3
                    sev = SeverityLevel.HIGH if min_sentiment <= -0.7 else SeverityLevel.MODERATE
                    anomalies.append(Anomaly(
                        feed_type=FeedType.SOCIAL_SENTIMENT,
                        zone_id=zone_id,
                        zone_name=zone_config.name,
                        metric_name="sentiment_score",
                        current_value=round(min_sentiment, 2),
                        baseline_value=0.55,
                        z_score=round(z_sent, 2),
                        description=f"Sharp negative social sentiment downturn ({min_sentiment:+.2f}) in {zone_config.name}.",
                        severity=sev,
                    ))

        return anomalies
