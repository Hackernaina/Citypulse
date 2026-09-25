"""
Plain-Language Summary Engine for CityPulse.
Great focus on Point 5: "Generate a plain-language summary -- what's happening right now and why it matters."
Produces clear, empathetic, non-jargon narratives tailored for non-technical residents in under 10 seconds.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from backend.app.models.schemas import (
    CivicEvent, Anomaly, Correlation, PlainLanguageSummary, FeedType, SeverityLevel
)
from backend.app.config import CITY_ZONES


class PlainLanguageSummaryEngine:
    def __init__(self):
        pass

    def generate_summary(
        self,
        overall_health: float,
        overall_status: str,
        events: List[CivicEvent],
        anomalies: List[Anomaly],
        correlations: List[Correlation],
        zones_pulse: Dict[str, Any],
    ) -> PlainLanguageSummary:
        """
        Synthesizes raw civic events, anomalies, and correlations into
        an intuitive, glanceable, plain-language narrative.
        """
        now = datetime.now(timezone.utc)

        # 1. Identify active critical areas and patterns
        distressed_zones = [
            zp for zp in zones_pulse.values() if zp.health_score < 75.0
        ]
        distressed_zones.sort(key=lambda z: z.health_score)

        # Gather distinct phenomena
        weather_events = [e for e in events if e.feed_type == FeedType.WEATHER and e.severity in (SeverityLevel.HIGH, SeverityLevel.CRITICAL)]
        transit_events = [e for e in events if e.feed_type == FeedType.TRANSIT and e.severity in (SeverityLevel.HIGH, SeverityLevel.CRITICAL)]
        incident_events = [e for e in events if e.feed_type == FeedType.INCIDENTS_311 and e.severity in (SeverityLevel.HIGH, SeverityLevel.CRITICAL)]
        aqi_events = [e for e in events if e.feed_type == FeedType.AIR_QUALITY and e.metric_value >= 120.0]

        # 2. Formulate the "10-Second Executive Headline"
        if overall_health >= 85.0:
            ten_sec = (
                "All districts are operating normally. Weather is clear, public transit is running on time, "
                "and no civic disruptions have been detected."
            )
            overall_sentiment = "Calm & Stable"
        elif overall_health >= 70.0:
            top_zone = distressed_zones[0].zone_name if distressed_zones else "select areas"
            ten_sec = (
                f"Minor civic activity detected in {top_zone}, but citywide systems remain stable and accessible."
            )
            overall_sentiment = "Normal Activity"
        elif overall_health >= 50.0:
            affected_names = ", ".join([z.zone_name for z in distressed_zones[:2]])
            ten_sec = (
                f"Noticeable disruptions are affecting {affected_names}. Expect travel delays and check localized neighborhood guidance."
            )
            overall_sentiment = "Elevated Caution"
        else:
            affected_names = ", ".join([z.zone_name for z in distressed_zones[:3]])
            ten_sec = (
                f"CRITICAL CIVIC ALERT: Major multi-system disruptions underway in {affected_names}. "
                f"Emergency teams responding; residents advised to limit non-essential travel."
            )
            overall_sentiment = "Severe Disruption"

        # 3. Formulate "What Is Happening Right Now"
        what_is_happening: List[str] = []

        if correlations:
            for c in correlations:
                if c.pattern_type == "STORM_TRANSIT_CASCADE":
                    what_is_happening.append(
                        f"In {c.zone_name}, heavy rainfall has overwhelmed street drainage, causing water to pool along roadway underpasses and stalling transit routes."
                    )
                elif c.pattern_type == "GRID_OVERHEAT":
                    what_is_happening.append(
                        f"In {c.zone_name}, elevated summer temperatures coincide with electrical power outages and non-functional traffic signals at major intersections."
                    )
                elif c.pattern_type == "ENVIRONMENTAL_DISTRESS":
                    what_is_happening.append(
                        f"In {c.zone_name}, air sensors report unhealthy particulate spikes while residents have reported strong smoke and chemical odors."
                    )
                elif c.pattern_type == "TRANSIT_BOTTLENECK":
                    what_is_happening.append(
                        f"In {c.zone_name}, transit delays have reached over 20 minutes, leading to severe platform crowding and passenger bottlenecks."
                    )
                else:
                    what_is_happening.append(f"{c.title}: {c.hypothesis}")

        # Add specific active events if no correlations yet
        if not what_is_happening:
            if weather_events:
                what_is_happening.append(
                    f"Inclement weather is sweeping through: {weather_events[0].summary_headline}."
                )
            if transit_events:
                what_is_happening.append(
                    f"Public transit disruptions: {transit_events[0].summary_headline}."
                )
            if incident_events:
                what_is_happening.append(
                    f"Municipal emergency reports: {incident_events[0].summary_headline}."
                )
            if aqi_events:
                what_is_happening.append(
                    f"Environmental sensors: {aqi_events[0].summary_headline}."
                )

        if not what_is_happening:
            what_is_happening.append(
                "City operations, traffic flows, and neighborhood services are functioning within standard calm baselines."
            )

        # 4. Formulate "Why It Matters To You" (Resident Impact)
        why_it_matters: List[str] = []

        if correlations:
            for c in correlations:
                if c.pattern_type == "STORM_TRANSIT_CASCADE":
                    why_it_matters.append(
                        f"Commute Impact: Roadway flooding will add 20 to 35 minutes to surface trips through {c.zone_name}. "
                        "Low cars risk stall damage in standing underpass water."
                    )
                elif c.pattern_type == "GRID_OVERHEAT":
                    why_it_matters.append(
                        f"Safety & Daily Living: Traffic lights are dark in {c.zone_name}—treat all affected intersections as 4-way stops. "
                        "Air conditioning units may experience intermittent brownouts."
                    )
                elif c.pattern_type == "ENVIRONMENTAL_DISTRESS":
                    why_it_matters.append(
                        f"Health Precaution: Air Quality in {c.zone_name} is unhealthy for children, the elderly, and anyone with asthma. "
                        "Prolonged outdoor exposure may cause coughing or eye irritation."
                    )
                elif c.pattern_type == "TRANSIT_BOTTLENECK":
                    why_it_matters.append(
                        f"Transit Travel Time: Station crowding may require waiting 2-3 train cycles before boarding in {c.zone_name}."
                    )
        elif distressed_zones:
            top = distressed_zones[0]
            why_it_matters.append(
                f"Conditions in {top.zone_name} are experiencing elevated strain (Health Index {top.health_score:.0f}/100), "
                "which may cause minor delays in local municipal services and transit."
            )
        else:
            why_it_matters.append(
                "No daily disruptions to commutes, water, electricity, or outdoor air quality. A great time for outdoor errands and travel."
            )

        # 5. Formulate "Actionable Advice"
        actionable_advice: List[str] = []
        if any(c.pattern_type == "STORM_TRANSIT_CASCADE" for c in correlations):
            actionable_advice.append("Avoid low-lying underpasses and switch from surface buses to elevated/underground rail lines.")
        if any(c.pattern_type == "GRID_OVERHEAT" for c in correlations):
            actionable_advice.append("Drive with extreme caution at unpowered signals, conserve heavy home appliance power, and check on elderly neighbors.")
        if any(c.pattern_type == "ENVIRONMENTAL_DISTRESS" for c in correlations):
            actionable_advice.append("Keep residential windows closed, turn AC to recirculate indoor air, and wear an N95 mask if outdoors.")
        if any(c.pattern_type == "TRANSIT_BOTTLENECK" for c in correlations):
            actionable_advice.append("Consider delaying your commute by 30 minutes or using micro-mobility/walking for short hops.")
        
        if not actionable_advice:
            actionable_advice.append("Normal daily routines can proceed as planned.")

        affected_neighborhoods = [z.zone_name for z in distressed_zones] if distressed_zones else ["Citywide Calm"]

        return PlainLanguageSummary(
            generated_at=now,
            ten_second_headline=ten_sec,
            what_is_happening=what_is_happening,
            why_it_matters=why_it_matters,
            actionable_advice=actionable_advice,
            affected_neighborhoods=affected_neighborhoods,
            overall_sentiment=overall_sentiment,
            epistemic_note=(
                "Grounding Guarantee: Synthesized directly from current normalized sensor readings and cross-feed correlations. "
                "Multi-feed co-occurrences reflect probable compound events, not verified single-source causation."
            )
        )
