"""
Transit Feed Ingestor.
Ingests real-time transit status, route delays, crowding, and service disruptions across city lines.
"""

import random
import time
from typing import List, Dict, Any
from backend.app.models.schemas import FeedType, CivicEvent, SeverityLevel
from backend.app.ingestion.base import BaseIngestor
from backend.app.ingestion.normalizer import FeedNormalizer
from backend.app.config import CITY_ZONES


class TransitIngestor(BaseIngestor):
    def __init__(self):
        super().__init__(FeedType.TRANSIT)
        self.routes = [
            {"route_id": "M1-Red", "name": "Line 1 Metro (North-South Express)", "zone_id": "downtown", "type": "Subway"},
            {"route_id": "M2-Blue", "name": "Line 2 Metro (Waterfront Crosstown)", "zone_id": "waterfront", "type": "Subway"},
            {"route_id": "B12-City", "name": "Bus 12 (Downtown Arterial Loop)", "zone_id": "downtown", "type": "Bus"},
            {"route_id": "B45-Hill", "name": "Bus 45 (North Hills Shuttle)", "zone_id": "north_hills", "type": "Bus"},
            {"route_id": "B88-Tech", "name": "Bus 88 (Tech Campus Express)", "zone_id": "tech_corridor", "type": "Bus"},
            {"route_id": "T1-East", "name": "Light Rail 1 (Suburban Corridor)", "zone_id": "east_suburbs", "type": "Light Rail"},
            {"route_id": "F1-Ferry", "name": "Harbor Ferry Service", "zone_id": "waterfront", "type": "Ferry"},
        ]
        self._delay_overrides: Dict[str, float] = {}

    async def fetch_raw_data(self) -> List[Dict[str, Any]]:
        start_time = time.time()
        now_epoch_ms = int(time.time() * 1000)  # Tests epoch millisecond format normalization
        raw_items: List[Dict[str, Any]] = []

        for r in self.routes:
            rid = r["route_id"]
            # Base delay plus any injected delay override
            override = self._delay_overrides.get(rid)
            if override is not None:
                delay_mins = override
            else:
                # Stochastic transit fluctuations
                p = random.random()
                if p < 0.10:
                    delay_mins = round(random.uniform(15.0, 35.0), 1)
                elif p < 0.30:
                    delay_mins = round(random.uniform(5.0, 14.0), 1)
                else:
                    delay_mins = round(random.uniform(0.5, 4.0), 1)

            zone = CITY_ZONES[r["zone_id"]]
            status = "NORMAL"
            if delay_mins >= 25.0:
                status = "MAJOR_DISRUPTION"
            elif delay_mins >= 12.0:
                status = "DELAYED"
            elif delay_mins >= 6.0:
                status = "MINOR_DELAY"

            raw_items.append({
                "feed_name": "Metropolitan Transit Authority (MTA-GTFS-RT)",
                "epoch_timestamp_ms": now_epoch_ms,
                "route_id": rid,
                "route_name": r["name"],
                "transit_mode": r["type"],
                "zone_id": r["zone_id"],
                "delay_minutes": delay_mins,
                "service_status": status,
                "crowd_capacity_pct": min(100, int(40 + delay_mins * 2.5)),
                "latitude": zone.center_lat + random.uniform(-0.003, 0.003),
                "longitude": zone.center_lng + random.uniform(-0.003, 0.003),
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

            timestamp = FeedNormalizer.parse_timestamp(item.get("epoch_timestamp_ms"))
            delay_mins = float(item.get("delay_minutes", 0.0))
            route_name = item.get("route_name", "Transit Line")
            crowd_pct = item.get("crowd_capacity_pct", 50)

            if delay_mins >= 25.0:
                severity = SeverityLevel.CRITICAL
                headline = f"Major Transit Stoppage: {route_name} halted ({int(delay_mins)}m delay, {crowd_pct}% crowding)"
            elif delay_mins >= 15.0:
                severity = SeverityLevel.HIGH
                headline = f"Significant Transit Delay: {route_name} delayed by {int(delay_mins)}m in {zname}"
            elif delay_mins >= 7.0:
                severity = SeverityLevel.MODERATE
                headline = f"Transit Advisory: {route_name} experiencing {int(delay_mins)}m delays"
            else:
                severity = SeverityLevel.NORMAL
                headline = f"{route_name} operating on schedule ({int(delay_mins)}m normal window)"

            impact = FeedNormalizer.calculate_impact_score(
                FeedType.TRANSIT, "delay_minutes", delay_mins, severity
            )

            events.append(CivicEvent(
                feed_type=FeedType.TRANSIT,
                timestamp=timestamp,
                zone_id=zid,
                zone_name=zname,
                location=loc,
                severity=severity,
                metric_name="delay_minutes",
                metric_value=delay_mins,
                metric_unit="minutes",
                summary_headline=headline,
                civic_impact_score=impact,
                raw_payload=item,
                feed_source=item.get("feed_name", "Transit Authority Feed"),
            ))
        return events

    def inject_transit_delay(self, route_id: str, delay_minutes: float):
        """Injected delay modifier for demonstration and replay."""
        self._delay_overrides[route_id] = delay_minutes

    def reset_overrides(self):
        self._delay_overrides.clear()
