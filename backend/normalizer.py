"""
Data Normalization Engine for CityPulse.
Normalizes mismatched feeds into a single consistent Common Civic Event Schema.
"""

from datetime import datetime, timezone, timedelta
import re
from typing import Any, Dict, Optional, Tuple
from backend.app.models.schemas import CivicEvent, FeedType, SeverityLevel, GeoPoint
from backend.app.config import CITY_ZONES


class FeedNormalizer:
    @staticmethod
    def parse_timestamp(raw_time: Any) -> datetime:
        """
        Parses mismatched timestamp formats:
        - ISO-8601 strings (with or without 'Z', with offsets)
        - Epoch unix integers/floats (seconds or milliseconds)
        - Relative strings ("3 mins ago", "10 seconds ago", "now")
        """
        if raw_time is None:
            return datetime.now(timezone.utc)

        if isinstance(raw_time, datetime):
            if raw_time.tzinfo is None:
                return raw_time.replace(tzinfo=timezone.utc)
            return raw_time.astimezone(timezone.utc)

        if isinstance(raw_time, (int, float)):
            # If greater than 1e11, it's milliseconds
            if raw_time > 1e11:
                return datetime.fromtimestamp(raw_time / 1000.0, tz=timezone.utc)
            return datetime.fromtimestamp(raw_time, tz=timezone.utc)

        if isinstance(raw_time, str):
            clean = raw_time.strip()
            # Relative time matching
            now = datetime.now(timezone.utc)
            if clean.lower() in ("now", "just now"):
                return now
            match = re.match(r"^(\d+)\s*(min|minute|sec|second|hour)s?\s*ago$", clean, re.IGNORECASE)
            if match:
                val = int(match.group(1))
                unit = match.group(2).lower()
                if "sec" in unit:
                    return now - timedelta(seconds=val)
                elif "min" in unit:
                    return now - timedelta(minutes=val)
                elif "hour" in unit:
                    return now - timedelta(hours=val)

            # Try standard ISO-8601
            try:
                # Replace trailing 'Z' if present
                iso_str = clean.replace("Z", "+00:00")
                return datetime.fromisoformat(iso_str).astimezone(timezone.utc)
            except Exception:
                pass

            # Try common datetime patterns
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S", "%d-%m-%Y %H:%M:%S"):
                try:
                    dt = datetime.strptime(clean, fmt)
                    return dt.replace(tzinfo=timezone.utc)
                except ValueError:
                    continue

        return datetime.now(timezone.utc)

    @staticmethod
    def resolve_zone(lat: Optional[float] = None, lng: Optional[float] = None, zone_id: Optional[str] = None) -> Tuple[str, str, GeoPoint]:
        """
        Resolves zone_id, zone_name and location.
        Falls back to nearest district center if coordinates are provided without zone_id.
        """
        if zone_id and zone_id in CITY_ZONES:
            zone = CITY_ZONES[zone_id]
            point_lat = lat if lat is not None else zone.center_lat
            point_lng = lng if lng is not None else zone.center_lng
            return zone.id, zone.name, GeoPoint(lat=point_lat, lng=point_lng)

        if lat is not None and lng is not None:
            # Find closest zone center
            best_zone_id = "downtown"
            min_dist = float("inf")
            for zid, zone in CITY_ZONES.items():
                dist = (lat - zone.center_lat) ** 2 + (lng - zone.center_lng) ** 2
                if dist < min_dist:
                    min_dist = dist
                    best_zone_id = zid
            zone = CITY_ZONES[best_zone_id]
            return zone.id, zone.name, GeoPoint(lat=lat, lng=lng)

        # Default fallback
        zone = CITY_ZONES["downtown"]
        return zone.id, zone.name, GeoPoint(lat=zone.center_lat, lng=zone.center_lng)

    @staticmethod
    def calculate_impact_score(feed_type: FeedType, metric_name: str, metric_value: float, severity: SeverityLevel) -> float:
        """
        Standardizes raw metrics into a uniform 0 - 100 civic impact score:
        0 = Normal calm conditions
        100 = Catastrophic civic disruption
        """
        base_scores = {
            SeverityLevel.NORMAL: 5.0,
            SeverityLevel.LOW: 20.0,
            SeverityLevel.MODERATE: 45.0,
            SeverityLevel.HIGH: 75.0,
            SeverityLevel.CRITICAL: 95.0,
        }
        score = base_scores.get(severity, 10.0)

        # Specific metric weighting adjustments
        if feed_type == FeedType.WEATHER:
            if metric_name == "precipitation_mm_hr":
                # > 30 mm/h is torrential
                score = min(100.0, metric_value * 2.8)
            elif metric_name == "wind_gust_kmh":
                score = min(100.0, max(0.0, (metric_value - 20) * 1.5))
            elif metric_name == "temperature_c":
                if metric_value > 35:
                    score = min(100.0, 40 + (metric_value - 35) * 8)
                elif metric_value < -5:
                    score = min(100.0, 40 + abs(metric_value + 5) * 8)

        elif feed_type == FeedType.TRANSIT:
            if metric_name == "delay_minutes":
                # > 30 mins delay is severe impact
                score = min(100.0, metric_value * 3.2)

        elif feed_type == FeedType.INCIDENTS_311:
            if metric_name == "incident_reports":
                score = min(100.0, metric_value * 12.0)

        elif feed_type == FeedType.AIR_QUALITY:
            if metric_name == "aqi":
                # EPA AQI: 0-50 Good, 51-100 Mod, 101-150 Sensitive, 151-200 Unhealthy, 201-300 Very Unhealthy
                if metric_value <= 50:
                    score = 5.0
                elif metric_value <= 100:
                    score = 25.0
                elif metric_value <= 150:
                    score = 55.0
                elif metric_value <= 200:
                    score = 75.0
                else:
                    score = min(100.0, 80.0 + (metric_value - 200) * 0.2)

        elif feed_type == FeedType.SOCIAL_SENTIMENT:
            if metric_name == "sentiment_score":
                # Score from -1.0 (rage/panic) to +1.0 (positive)
                if metric_value < 0:
                    score = min(100.0, abs(metric_value) * 90.0)
                else:
                    score = max(0.0, (1.0 - metric_value) * 10.0)

        return round(max(0.0, min(100.0, score)), 1)
