"""
Configuration for CityPulse: The Live Civic Health Dashboard
"""

from typing import Dict, Any, List
from pydantic import BaseModel


class ZoneConfig(BaseModel):
    id: str
    name: str
    description: str
    center_lat: float
    center_lng: float
    bounds: List[List[float]]  # Polygon coordinates [[lat, lng], ...]
    baseline_complaint_rate: float = 2.0  # expected complaints per 30 mins
    baseline_transit_delay: float = 3.0     # minutes average


# Defined metropolitan districts with realistic coordinates
CITY_ZONES: Dict[str, ZoneConfig] = {
    "downtown": ZoneConfig(
        id="downtown",
        name="Downtown & Financial Core",
        description="High-density commercial center, major transit hubs, low-lying underpasses.",
        center_lat=40.7128,
        center_lng=-74.0060,
        bounds=[
            [40.7180, -74.0150],
            [40.7190, -73.9980],
            [40.7070, -73.9970],
            [40.7060, -74.0140],
        ],
        baseline_complaint_rate=4.0,
        baseline_transit_delay=5.0,
    ),
    "waterfront": ZoneConfig(
        id="waterfront",
        name="Harbor & Waterfront District",
        description="Coastal residential and ferry docks, vulnerable to tidal surges and drainage backup.",
        center_lat=40.7020,
        center_lng=-74.0150,
        bounds=[
            [40.7070, -74.0200],
            [40.7080, -74.0100],
            [40.6970, -74.0090],
            [40.6960, -74.0190],
        ],
        baseline_complaint_rate=2.0,
        baseline_transit_delay=3.0,
    ),
    "north_hills": ZoneConfig(
        id="north_hills",
        name="North Hills & Uptown",
        description="Residential neighborhood with steep topography and mature tree canopy.",
        center_lat=40.7300,
        center_lng=-73.9950,
        bounds=[
            [40.7380, -74.0050],
            [40.7390, -73.9850],
            [40.7220, -73.9840],
            [40.7210, -74.0040],
        ],
        baseline_complaint_rate=2.5,
        baseline_transit_delay=3.5,
    ),
    "tech_corridor": ZoneConfig(
        id="tech_corridor",
        name="Tech & Innovation Corridor",
        description="Mixed-use innovation district, university campus, high pedestrian and cyclist traffic.",
        center_lat=40.7200,
        center_lng=-73.9850,
        bounds=[
            [40.7250, -73.9920],
            [40.7260, -73.9780],
            [40.7140, -73.9770],
            [40.7130, -73.9910],
        ],
        baseline_complaint_rate=3.0,
        baseline_transit_delay=4.0,
    ),
    "east_suburbs": ZoneConfig(
        id="east_suburbs",
        name="East Suburbs & Industrial Park",
        description="Light manufacturing, highway arteries, logistics terminals, and air sensor network.",
        center_lat=40.7150,
        center_lng=-73.9650,
        bounds=[
            [40.7220, -73.9750],
            [40.7230, -73.9550],
            [40.7070, -73.9540],
            [40.7060, -73.9740],
        ],
        baseline_complaint_rate=2.0,
        baseline_transit_delay=3.0,
    ),
}

DEFAULT_SETTINGS: Dict[str, Any] = {
    "city_name": "Metropolis Central",
    "simulation_speed": 1.0,
    "feed_polling_interval_seconds": 4,
    "rolling_window_minutes": 30,
    "anomaly_z_score_threshold": 2.0,
    "alert_thresholds": {
        "civic_health_min": 65.0,  # Alert if health drops below this
        "aqi_max": 120.0,
        "transit_delay_max": 18.0,
        "complaint_surge_multiplier": 2.5,
    },
}
