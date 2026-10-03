"""
Historical Replay Controller for CityPulse.
Enables step-by-step time scrubbing, scenario switching, and live vs replay state transitions.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from backend.app.models.schemas import CivicEvent, GeoPoint
from backend.app.ingestion.normalizer import FeedNormalizer
from backend.app.config import CITY_ZONES
from backend.app.replay.scenarios import generate_replay_scenarios


class ReplayController:
    def __init__(self):
        self.scenarios = generate_replay_scenarios()
        self.is_active = False
        self.current_scenario_id = "flash_flood"
        self.current_step_index = 0
        self.is_playing = False
        self.playback_speed = 1.0

    def get_available_scenarios(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": s["id"],
                "title": s["title"],
                "description": s["description"],
                "total_steps": s["total_steps"],
            }
            for s in self.scenarios.values()
        ]

    def load_scenario(self, scenario_id: str):
        if scenario_id in self.scenarios:
            self.current_scenario_id = scenario_id
            self.current_step_index = 0
            self.is_active = True
            return True
        return False

    def exit_replay(self):
        self.is_active = False
        self.is_playing = False
        self.current_step_index = 0

    def step_forward(self) -> int:
        scenario = self.scenarios.get(self.current_scenario_id)
        if scenario and self.current_step_index < scenario["total_steps"] - 1:
            self.current_step_index += 1
        return self.current_step_index

    def step_back(self) -> int:
        if self.current_step_index > 0:
            self.current_step_index -= 1
        return self.current_step_index

    def seek_step(self, step: int) -> int:
        scenario = self.scenarios.get(self.current_scenario_id)
        if scenario:
            self.current_step_index = max(0, min(scenario["total_steps"] - 1, step))
        return self.current_step_index

    def get_events_for_current_step(self) -> List[CivicEvent]:
        """
        Gathers cumulative events up to the current step of the active scenario,
        generating realistic normalized CivicEvents.
        """
        scenario = self.scenarios.get(self.current_scenario_id)
        if not scenario:
            return []

        now = datetime.now(timezone.utc)
        events: List[CivicEvent] = []

        # Gather events from all frames up to current_step_index
        # Recent frames are within the 30-min window
        for frame in scenario["frames"][: self.current_step_index + 1]:
            # Calculate mock timestamp: current step is 'now', earlier frames are delta minutes back
            min_back = (scenario["frames"][self.current_step_index]["time_offset_min"] - frame["time_offset_min"])
            frame_time = now - timedelta(minutes=min_back)

            for raw in frame["events"]:
                zid = raw["zone_id"]
                zone = CITY_ZONES.get(zid, CITY_ZONES["downtown"])
                zid, zname, loc = FeedNormalizer.resolve_zone(
                    lat=zone.center_lat,
                    lng=zone.center_lng,
                    zone_id=zid
                )

                events.append(CivicEvent(
                    feed_type=raw["feed_type"],
                    timestamp=frame_time,
                    zone_id=zid,
                    zone_name=zname,
                    location=loc,
                    severity=raw["severity"],
                    metric_name=raw["metric_name"],
                    metric_value=raw["metric_value"],
                    metric_unit="std",
                    summary_headline=raw["headline"],
                    civic_impact_score=raw["impact"],
                    feed_source=f"Historical Replay ({scenario['title']})",
                ))

        return events

    def get_current_frame_meta(self) -> Dict[str, Any]:
        scenario = self.scenarios.get(self.current_scenario_id)
        if not scenario:
            return {}
        frame = scenario["frames"][self.current_step_index]
        return {
            "scenario_id": self.current_scenario_id,
            "scenario_title": scenario["title"],
            "step_index": self.current_step_index,
            "total_steps": scenario["total_steps"],
            "frame_label": frame["label"],
            "is_playing": self.is_playing,
            "playback_speed": self.playback_speed,
        }
