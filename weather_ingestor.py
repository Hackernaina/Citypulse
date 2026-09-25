"""
Weather Feed Ingestor.
Ingests live weather feeds from public APIs (Open-Meteo) or high-fidelity simulated meteorological stations.
"""

import random
import time
from typing import List, Dict, Any, Optional
import httpx
from backend.app.models.schemas import FeedType, CivicEvent, SeverityLevel, GeoPoint
from backend.app.ingestion.base import BaseIngestor
from backend.app.ingestion.normalizer import FeedNormalizer
from backend.app.config import CITY_ZONES


class WeatherIngestor(BaseIngestor):
    def __init__(self, use_live_api: bool = False):
        super().__init__(FeedType.WEATHER)
        self.use_live_api = use_live_api
        # Persistent state for smooth realistic simulation
        self._zone_weather_state = {
            zid: {
                "temp": 22.0,
                "rain_mm": 0.0,
                "wind_kmh": 12.0,
                "condition": "Partly Cloudy",
            }
            for zid in CITY_ZONES
        }

    async def fetch_raw_data(self) -> List[Dict[str, Any]]:
        start_time = time.time()
        raw_items: List[Dict[str, Any]] = []

        if self.use_live_api:
            # Query Open-Meteo for Downtown coordinates
            downtown = CITY_ZONES["downtown"]
            url = (
                f"https://api.open-meteo.com/v1/forecast"
                f"?latitude={downtown.center_lat}&longitude={downtown.center_lng}"
                f"&current=temperature_2m,relative_humidity_2m,precipitation,rain,wind_speed_10m"
            )
            try:
                async with httpx.AsyncClient(timeout=4.0) as client:
                    resp = await client.get(url)
                    if resp.status_code == 200:
                        data = resp.json()
                        current = data.get("current", {})
                        raw_items.append({
                            "source": "Open-Meteo Public API",
                            "zone_id": "downtown",
                            "timestamp": current.get("time"),
                            "temperature_c": current.get("temperature_2m", 20.0),
                            "precipitation_mm": current.get("precipitation", 0.0),
                            "wind_speed_kmh": current.get("wind_speed_10m", 10.0),
                            "condition": "Cloudy" if current.get("rain", 0) > 0 else "Clear",
                        })
            except Exception:
                # Graceful fallback to simulated stream if external API fails or times out
                pass

        # If live API was not used or returned empty, generate for each city zone
        if not raw_items:
            for zone_id, zone in CITY_ZONES.items():
                curr = self._zone_weather_state[zone_id]
                # Slight dynamic drift
                curr["temp"] = round(curr["temp"] + random.uniform(-0.4, 0.4), 1)
                curr["wind_kmh"] = round(max(2.0, curr["wind_kmh"] + random.uniform(-1.5, 1.5)), 1)
                
                # Check for rainfall fluctuation
                if random.random() < 0.15:
                    # Spurts of rain in vulnerable zones
                    curr["rain_mm"] = round(random.uniform(5.0, 28.0), 1)
                    curr["condition"] = "Heavy Rain" if curr["rain_mm"] > 15 else "Light Rain"
                else:
                    curr["rain_mm"] = round(max(0.0, curr["rain_mm"] * 0.7), 1)
                    if curr["rain_mm"] < 0.5:
                        curr["rain_mm"] = 0.0
                        curr["condition"] = "Partly Cloudy"

                raw_items.append({
                    "source": "CityPulse Meteorological Sensor Net",
                    "zone_id": zone_id,
                    "timestamp": "just now",  # Tests normalizer relative timestamp handling
                    "temperature_c": curr["temp"],
                    "precipitation_mm": curr["rain_mm"],
                    "wind_speed_kmh": curr["wind_kmh"],
                    "condition": curr["condition"],
                    "coordinates": {"lat": zone.center_lat, "lng": zone.center_lng},
                })

        self.last_latency_ms = round((time.time() - start_time) * 1000, 2)
        return raw_items

    def parse_and_normalize(self, raw_items: List[Dict[str, Any]]) -> List[CivicEvent]:
        events: List[CivicEvent] = []
        for item in raw_items:
            zone_id = item.get("zone_id", "downtown")
            coords = item.get("coordinates", {})
            lat = coords.get("lat")
            lng = coords.get("lng")
            zid, zname, loc = FeedNormalizer.resolve_zone(lat=lat, lng=lng, zone_id=zone_id)

            timestamp = FeedNormalizer.parse_timestamp(item.get("timestamp"))
            rain_mm = float(item.get("precipitation_mm", 0.0))
            wind_kmh = float(item.get("wind_speed_kmh", 0.0))
            temp_c = float(item.get("temperature_c", 20.0))
            condition = item.get("condition", "Clear")

            # Determine severity based on meteorological thresholds
            severity = SeverityLevel.NORMAL
            if rain_mm >= 25.0 or wind_kmh >= 65.0:
                severity = SeverityLevel.CRITICAL
                headline = f"Torrential Rain Warning: {rain_mm} mm/hr with {wind_kmh} km/h gusts in {zname}"
            elif rain_mm >= 12.0 or wind_kmh >= 45.0:
                severity = SeverityLevel.HIGH
                headline = f"Severe Weather Alert: Heavy rain ({rain_mm} mm/hr) in {zname}"
            elif rain_mm >= 4.0 or wind_kmh >= 30.0:
                severity = SeverityLevel.MODERATE
                headline = f"Moderate Rain & Wet Roads: {rain_mm} mm/hr in {zname}"
            else:
                headline = f"{condition}, {temp_c}°C, winds {wind_kmh} km/h in {zname}"

            impact = FeedNormalizer.calculate_impact_score(
                FeedType.WEATHER, "precipitation_mm_hr", rain_mm, severity
            )

            events.append(CivicEvent(
                feed_type=FeedType.WEATHER,
                timestamp=timestamp,
                zone_id=zid,
                zone_name=zname,
                location=loc,
                severity=severity,
                metric_name="precipitation_mm_hr",
                metric_value=rain_mm,
                metric_unit="mm/hr",
                summary_headline=headline,
                civic_impact_score=impact,
                raw_payload=item,
                feed_source=item.get("source", "Weather Ingestor"),
            ))
        return events

    def inject_weather_event(self, zone_id: str, rain_mm: float, wind_kmh: float, condition: str = "Severe Downpour"):
        """Injected scenario modifier for demonstration and replay."""
        if zone_id in self._zone_weather_state:
            self._zone_weather_state[zone_id]["rain_mm"] = rain_mm
            self._zone_weather_state[zone_id]["wind_kmh"] = wind_kmh
            self._zone_weather_state[zone_id]["condition"] = condition
