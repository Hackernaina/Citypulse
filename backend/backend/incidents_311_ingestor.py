"""
311 Incident & Municipal Complaint Ingestor.
Ingests citizen service requests, emergency dispatch logs, and public works complaints.
"""

import random
import time
from typing import List, Dict, Any
from backend.app.models.schemas import FeedType, CivicEvent, SeverityLevel
from backend.app.ingestion.base import BaseIngestor
from backend.app.ingestion.normalizer import FeedNormalizer
from backend.app.config import CITY_ZONES


INCIDENT_CATEGORIES = [
    {"type": "STREET_FLOODING", "desc": "Street waterlogging & storm drain overflow", "base_sev": SeverityLevel.HIGH},
    {"type": "POWER_OUTAGE", "desc": "Local electrical grid outage / transformer failure", "base_sev": SeverityLevel.HIGH},
    {"type": "TRAFFIC_SIGNAL_OUT", "desc": "Traffic signals malfunctioning or dark", "base_sev": SeverityLevel.MODERATE},
    {"type": "FALLEN_TREE", "desc": "Fallen tree blocking roadway / wires down", "base_sev": SeverityLevel.MODERATE},
    {"type": "WATER_MAIN_BREAK", "desc": "Water main break / pavement buckling", "base_sev": SeverityLevel.HIGH},
    {"type": "ODOR_COMPLAINT", "desc": "Strong chemical odor / gas smell reported", "base_sev": SeverityLevel.HIGH},
    {"type": "NOISE_DISTURBANCE", "desc": "Late-night commercial noise violation", "base_sev": SeverityLevel.LOW},
    {"type": "POTHOLE_HAZARD", "desc": "Deep road pothole / lane hazard", "base_sev": SeverityLevel.LOW},
]


class Incidents311Ingestor(BaseIngestor):
    def __init__(self):
        super().__init__(FeedType.INCIDENTS_311)
        self._injected_incidents: List[Dict[str, Any]] = []

    async def fetch_raw_data(self) -> List[Dict[str, Any]]:
        start_time = time.time()
        raw_items: List[Dict[str, Any]] = []

        # Include injected scenario incidents
        if self._injected_incidents:
            raw_items.extend(self._injected_incidents)

        # Baseline stochastic citizen 311 calls
        for zone_id, zone in CITY_ZONES.items():
            if random.random() < 0.35:
                cat = random.choice(INCIDENT_CATEGORIES)
                iso_timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                raw_items.append({
                    "portal": "Open311 Municipal Gateway",
                    "ticket_id": f"311-{random.randint(100000, 999999)}",
                    "created_date_iso": iso_timestamp,
                    "category": cat["type"],
                    "description": cat["desc"],
                    "zone_id": zone_id,
                    "address": f"{random.randint(10, 890)} {zone.name.split()[0]} Ave",
                    "latitude": zone.center_lat + random.uniform(-0.005, 0.005),
                    "longitude": zone.center_lng + random.uniform(-0.005, 0.005),
                    "reported_urgency": "Standard",
                })

        self.last_latency_ms = round((time.time() - start_time) * 1000, 2)
        return raw_items

    def parse_and_normalize(self, raw_items: List[Dict[str, Any]]) -> List[CivicEvent]:
        events: List[CivicEvent] = []
        for item in raw_items:
            zone_id = item.get("zone_id", "downtown")
            zid, zname, loc = FeedNormalizer.resolve_zone(
                lat=item.get("latitude"),
                lng=item.get("longitude"),
                zone_id=zone_id
            )
            loc.address = item.get("address")

            raw_time = item.get("created_date_iso") or item.get("timestamp")
            timestamp = FeedNormalizer.parse_timestamp(raw_time)
            cat_type = item.get("category", "GENERAL_COMPLAINT")
            desc = item.get("description", "Citizen complaint logged")

            # Determine severity
            if cat_type in ("STREET_FLOODING", "POWER_OUTAGE", "WATER_MAIN_BREAK", "ODOR_COMPLAINT"):
                severity = SeverityLevel.HIGH
            elif cat_type in ("TRAFFIC_SIGNAL_OUT", "FALLEN_TREE"):
                severity = SeverityLevel.MODERATE
            else:
                severity = SeverityLevel.LOW

            headline = f"311 Alert: {desc} near {loc.address or zname}"

            impact = FeedNormalizer.calculate_impact_score(
                FeedType.INCIDENTS_311, "incident_reports", 1.0, severity
            )

            events.append(CivicEvent(
                feed_type=FeedType.INCIDENTS_311,
                timestamp=timestamp,
                zone_id=zid,
                zone_name=zname,
                location=loc,
                severity=severity,
                metric_name="incident_count",
                metric_value=1.0,
                metric_unit="report",
                summary_headline=headline,
                civic_impact_score=impact,
                raw_payload=item,
                feed_source="City 311 Citizen Services",
            ))
        return events

    def inject_incident(self, zone_id: str, category: str, description: str, address: str = ""):
        """Inject specific incident for test scenarios and historical replay."""
        zone = CITY_ZONES.get(zone_id, CITY_ZONES["downtown"])
        self._injected_incidents.append({
            "portal": "Open311 Municipal Gateway",
            "ticket_id": f"311-{random.randint(100000, 999999)}",
            "created_date_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "category": category,
            "description": description,
            "zone_id": zone_id,
            "address": address or f"{random.randint(10, 890)} {zone.name.split()[0]} St",
            "latitude": zone.center_lat + random.uniform(-0.002, 0.002),
            "longitude": zone.center_lng + random.uniform(-0.002, 0.002),
            "reported_urgency": "Emergency Escalation",
        })

    def clear_injected(self):
        self._injected_incidents.clear()
