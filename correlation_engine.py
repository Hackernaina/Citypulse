"""
Cross-Feed Spatial-Temporal Correlation Engine for CityPulse.
Surfaces compound civic patterns across heterogeneous feeds while upholding Epistemic Honesty.
"""

from typing import List, Dict, Set
from datetime import datetime, timezone, timedelta
from backend.app.models.schemas import CivicEvent, Anomaly, Correlation, FeedType
from backend.app.config import CITY_ZONES


class CorrelationEngine:
    def __init__(self, time_window_minutes: int = 30):
        self.time_window_minutes = time_window_minutes

    def correlate(self, events: List[CivicEvent], anomalies: List[Anomaly]) -> List[Correlation]:
        """
        Evaluates co-occurring anomalies and high-severity events in spatial and temporal proximity.
        """
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(minutes=self.time_window_minutes)
        window_events = [e for e in events if e.timestamp >= cutoff]

        correlations: List[Correlation] = []

        # Group by zone
        zone_events: Dict[str, List[CivicEvent]] = {zid: [] for zid in CITY_ZONES}
        zone_anomalies: Dict[str, List[Anomaly]] = {zid: [] for zid in CITY_ZONES}

        for e in window_events:
            if e.zone_id in zone_events:
                zone_events[e.zone_id].append(e)

        for a in anomalies:
            if a.zone_id in zone_anomalies:
                zone_anomalies[a.zone_id].append(a)

        for zone_id, zone_config in CITY_ZONES.items():
            evs = zone_events[zone_id]
            anoms = zone_anomalies[zone_id]
            feed_types_present: Set[FeedType] = {e.feed_type for e in evs}

            # Gather metrics
            weather_evs = [e for e in evs if e.feed_type == FeedType.WEATHER]
            transit_evs = [e for e in evs if e.feed_type == FeedType.TRANSIT]
            incident_evs = [e for e in evs if e.feed_type == FeedType.INCIDENTS_311]
            aqi_evs = [e for e in evs if e.feed_type == FeedType.AIR_QUALITY]
            sentiment_evs = [e for e in evs if e.feed_type == FeedType.SOCIAL_SENTIMENT]

            max_rain = max([e.metric_value for e in weather_evs], default=0.0)
            max_delay = max([e.metric_value for e in transit_evs], default=0.0)
            flooding_complaints = [
                e for e in incident_evs
                if "flood" in e.summary_headline.lower() or "water" in e.summary_headline.lower()
            ]
            power_complaints = [
                e for e in incident_evs
                if "power" in e.summary_headline.lower() or "signal" in e.summary_headline.lower() or "dark" in e.summary_headline.lower()
            ]
            odor_complaints = [
                e for e in incident_evs
                if "odor" in e.summary_headline.lower() or "smoke" in e.summary_headline.lower() or "chemical" in e.summary_headline.lower()
            ]
            max_aqi = max([e.metric_value for e in aqi_evs], default=0.0)
            min_sentiment = min([e.metric_value for e in sentiment_evs], default=0.5)

            # PATTERN 1: Storm-Induced Drainage & Transit Cascade
            if max_rain >= 10.0 and (len(flooding_complaints) >= 1 or max_delay >= 15.0):
                feeds = [FeedType.WEATHER]
                if flooding_complaints:
                    feeds.append(FeedType.INCIDENTS_311)
                if max_delay >= 12.0:
                    feeds.append(FeedType.TRANSIT)

                conf = min(0.95, 0.65 + (max_rain / 50.0) * 0.2 + (0.1 if len(feeds) >= 3 else 0.0))
                correlations.append(Correlation(
                    title=f"Storm-Induced Drainage & Transit Cascade in {zone_config.name}",
                    zone_id=zone_id,
                    zone_name=zone_config.name,
                    feeds_involved=feeds,
                    event_ids=[e.event_id for e in evs if e.feed_type in feeds][:8],
                    confidence_score=round(conf, 2),
                    pattern_type="STORM_TRANSIT_CASCADE",
                    hypothesis=(
                        f"Heavy rainfall ({max_rain} mm/hr) coincided within {self.time_window_minutes} minutes "
                        f"of {len(flooding_complaints)} localized flood reports and transit delays reaching {max_delay:.0f} minutes."
                    ),
                    impact_rationale=(
                        "Surface runoff likely overwhelmed storm catch-basins, causing street water accumulation that slowed surface bus and arterial routes."
                    ),
                ))

            # PATTERN 2: Heatwave & Power Grid Strain Cascade
            weather_temp = max([e.raw_payload.get("temperature_c", 20.0) for e in weather_evs], default=20.0)
            if weather_temp >= 34.0 and (power_complaints or min_sentiment <= -0.3):
                feeds = [FeedType.WEATHER]
                if power_complaints:
                    feeds.append(FeedType.INCIDENTS_311)
                if min_sentiment <= -0.2:
                    feeds.append(FeedType.SOCIAL_SENTIMENT)

                conf = 0.84 if len(feeds) >= 3 else 0.72
                correlations.append(Correlation(
                    title=f"Extreme Heat Electrical Grid Strain in {zone_config.name}",
                    zone_id=zone_id,
                    zone_name=zone_config.name,
                    feeds_involved=feeds,
                    event_ids=[e.event_id for e in evs if e.feed_type in feeds][:8],
                    confidence_score=conf,
                    pattern_type="GRID_OVERHEAT",
                    hypothesis=(
                        f"Ambient heat of {weather_temp:.1f}°C aligns with {len(power_complaints)} power/signal "
                        f"outage complaints and a drop in neighborhood sentiment ({min_sentiment:+.2f})."
                    ),
                    impact_rationale=(
                        "Substation cooling stress and air conditioning loads correlate with localized feeder trips and unpowered traffic signals."
                    ),
                ))

            # PATTERN 3: Environmental Irritant & Community Distress
            if max_aqi >= 110.0 and (odor_complaints or min_sentiment <= -0.35):
                feeds = [FeedType.AIR_QUALITY]
                if odor_complaints:
                    feeds.append(FeedType.INCIDENTS_311)
                if min_sentiment <= -0.2:
                    feeds.append(FeedType.SOCIAL_SENTIMENT)

                conf = 0.88 if odor_complaints else 0.75
                correlations.append(Correlation(
                    title=f"Elevated Atmospheric Hazard & Citizen Reports in {zone_config.name}",
                    zone_id=zone_id,
                    zone_name=zone_config.name,
                    feeds_involved=feeds,
                    event_ids=[e.event_id for e in evs if e.feed_type in feeds][:8],
                    confidence_score=conf,
                    pattern_type="ENVIRONMENTAL_DISTRESS",
                    hypothesis=(
                        f"AQI spike to {int(max_aqi)} correlates spatially with {len(odor_complaints)} citizen odor/fume calls "
                        f"and negative sentiment ({min_sentiment:+.2f})."
                    ),
                    impact_rationale=(
                        "Particulate or emission plume is dispersing at ground level, triggering both sensor thresholds and immediate resident reports."
                    ),
                ))

            # PATTERN 4: Transit Bottleneck & Commuter Outcry
            if max_delay >= 20.0 and min_sentiment <= -0.5:
                feeds = [FeedType.TRANSIT, FeedType.SOCIAL_SENTIMENT]
                correlations.append(Correlation(
                    title=f"Transit Bottleneck & Commuter Dissatisfaction in {zone_config.name}",
                    zone_id=zone_id,
                    zone_name=zone_config.name,
                    feeds_involved=feeds,
                    event_ids=[e.event_id for e in evs if e.feed_type in feeds][:8],
                    confidence_score=0.86,
                    pattern_type="TRANSIT_BOTTLENECK",
                    hypothesis=(
                        f"Severe transit delays ({max_delay:.0f} mins) match a concurrent surge in frustrated civic chatter "
                        f"(sentiment index {min_sentiment:+.2f})."
                    ),
                    impact_rationale=(
                        "Station platforms are crowding, causing delayed journeys and immediate vocal social reporting from commuters."
                    ),
                ))

        return correlations
