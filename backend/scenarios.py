"""
Historical Incident Scenarios for Pattern-Detection Replay.
Provides rich multi-step datasets demonstrating how anomalies emerge,
cross-feed correlations form, and plain-language summaries guide residents over time.
"""

from typing import List, Dict, Any
from datetime import datetime, timezone, timedelta
from backend.app.models.schemas import FeedType, SeverityLevel, GeoPoint, CivicEvent


def generate_replay_scenarios() -> Dict[str, Dict[str, Any]]:
    now = datetime.now(timezone.utc)

    # =========================================================================
    # SCENARIO 1: The Flash Flood & Evening Rush Hour Cascade
    # =========================================================================
    flood_frames: List[Dict[str, Any]] = [
        {
            "step": 0,
            "time_offset_min": 0,
            "label": "16:30 - Pre-Storm Normal Flow",
            "events": [
                {
                    "feed_type": FeedType.WEATHER,
                    "zone_id": "downtown",
                    "severity": SeverityLevel.NORMAL,
                    "metric_name": "precipitation_mm_hr",
                    "metric_value": 0.0,
                    "headline": "Overcast clouds, 22°C, normal humidity in Downtown",
                    "impact": 5.0,
                },
                {
                    "feed_type": FeedType.TRANSIT,
                    "zone_id": "downtown",
                    "severity": SeverityLevel.NORMAL,
                    "metric_name": "delay_minutes",
                    "metric_value": 2.5,
                    "headline": "Line 1 Metro & Bus 12 operating on schedule",
                    "impact": 8.0,
                },
                {
                    "feed_type": FeedType.SOCIAL_SENTIMENT,
                    "zone_id": "downtown",
                    "severity": SeverityLevel.NORMAL,
                    "metric_name": "sentiment_score",
                    "metric_value": 0.65,
                    "headline": "Positive civic chatter: smooth afternoon commute",
                    "impact": 5.0,
                },
            ],
        },
        {
            "step": 1,
            "time_offset_min": 15,
            "label": "16:45 - Cloudburst Begins",
            "events": [
                {
                    "feed_type": FeedType.WEATHER,
                    "zone_id": "downtown",
                    "severity": SeverityLevel.MODERATE,
                    "metric_name": "precipitation_mm_hr",
                    "metric_value": 14.5,
                    "headline": "Heavy rain squall beginning over Downtown core (14.5 mm/hr)",
                    "impact": 42.0,
                },
                {
                    "feed_type": FeedType.TRANSIT,
                    "zone_id": "downtown",
                    "severity": SeverityLevel.NORMAL,
                    "metric_name": "delay_minutes",
                    "metric_value": 4.0,
                    "headline": "Line 1 Metro operating on schedule, light road spray",
                    "impact": 12.0,
                },
            ],
        },
        {
            "step": 2,
            "time_offset_min": 30,
            "label": "17:00 - Torrential Downpour & Catch-Basin Backlog",
            "events": [
                {
                    "feed_type": FeedType.WEATHER,
                    "zone_id": "downtown",
                    "severity": SeverityLevel.CRITICAL,
                    "metric_name": "precipitation_mm_hr",
                    "metric_value": 32.0,
                    "headline": "Flash Flood Warning: Torrential 32 mm/hr rainfall over Downtown",
                    "impact": 92.0,
                },
                {
                    "feed_type": FeedType.INCIDENTS_311,
                    "zone_id": "downtown",
                    "severity": SeverityLevel.HIGH,
                    "metric_name": "incident_count",
                    "metric_value": 1.0,
                    "headline": "311 Alert: Catch-basin overflow & street pooling near 4th & Market St",
                    "impact": 70.0,
                },
                {
                    "feed_type": FeedType.TRANSIT,
                    "zone_id": "downtown",
                    "severity": SeverityLevel.MODERATE,
                    "metric_name": "delay_minutes",
                    "metric_value": 11.0,
                    "headline": "Bus 12 delayed 11m due to standing water on 4th Ave",
                    "impact": 45.0,
                },
            ],
        },
        {
            "step": 3,
            "time_offset_min": 45,
            "label": "17:15 - Underpass Flooded & Transit Paralyzed",
            "events": [
                {
                    "feed_type": FeedType.WEATHER,
                    "zone_id": "downtown",
                    "severity": SeverityLevel.CRITICAL,
                    "metric_name": "precipitation_mm_hr",
                    "metric_value": 29.0,
                    "headline": "Continuous heavy deluge (29 mm/hr) over Downtown",
                    "impact": 88.0,
                },
                {
                    "feed_type": FeedType.INCIDENTS_311,
                    "zone_id": "downtown",
                    "severity": SeverityLevel.CRITICAL,
                    "metric_name": "incident_count",
                    "metric_value": 3.0,
                    "headline": "311 Urgent: 4th Ave Underpass submerged; 2 vehicles stalled in water",
                    "impact": 95.0,
                },
                {
                    "feed_type": FeedType.TRANSIT,
                    "zone_id": "downtown",
                    "severity": SeverityLevel.CRITICAL,
                    "metric_name": "delay_minutes",
                    "metric_value": 28.5,
                    "headline": "Line 1 Metro halted due to track drainage backup; Bus 12 rerouted (28m delay)",
                    "impact": 92.0,
                },
                {
                    "feed_type": FeedType.SOCIAL_SENTIMENT,
                    "zone_id": "downtown",
                    "severity": SeverityLevel.HIGH,
                    "metric_name": "sentiment_score",
                    "metric_value": -0.68,
                    "headline": "Resident frustration spike: '#DowntownFlood cars stranded underpass'",
                    "impact": 78.0,
                },
            ],
        },
        {
            "step": 4,
            "time_offset_min": 60,
            "label": "17:30 - Peak Compound Disruption (Correlation Triggered)",
            "events": [
                {
                    "feed_type": FeedType.WEATHER,
                    "zone_id": "downtown",
                    "severity": SeverityLevel.HIGH,
                    "metric_name": "precipitation_mm_hr",
                    "metric_value": 18.0,
                    "headline": "Rain easing slightly to 18 mm/hr, sustained standing water",
                    "impact": 65.0,
                },
                {
                    "feed_type": FeedType.INCIDENTS_311,
                    "zone_id": "downtown",
                    "severity": SeverityLevel.HIGH,
                    "metric_name": "incident_count",
                    "metric_value": 5.0,
                    "headline": "311 Surge: 5 basement flooding reports along commercial strip",
                    "impact": 85.0,
                },
                {
                    "feed_type": FeedType.TRANSIT,
                    "zone_id": "downtown",
                    "severity": SeverityLevel.CRITICAL,
                    "metric_name": "delay_minutes",
                    "metric_value": 32.0,
                    "headline": "Severe transit gridlock: surface buses halted across 6 blocks",
                    "impact": 96.0,
                },
                {
                    "feed_type": FeedType.SOCIAL_SENTIMENT,
                    "zone_id": "downtown",
                    "severity": SeverityLevel.HIGH,
                    "metric_name": "sentiment_score",
                    "metric_value": -0.75,
                    "headline": "Social outcry: commuters stranded, high emergency chatter",
                    "impact": 85.0,
                },
            ],
        },
        {
            "step": 5,
            "time_offset_min": 75,
            "label": "17:45 - Emergency Pumping & Initial Receding",
            "events": [
                {
                    "feed_type": FeedType.WEATHER,
                    "zone_id": "downtown",
                    "severity": SeverityLevel.MODERATE,
                    "metric_name": "precipitation_mm_hr",
                    "metric_value": 4.0,
                    "headline": "Rain tapering off to light drizzle (4 mm/hr)",
                    "impact": 25.0,
                },
                {
                    "feed_type": FeedType.INCIDENTS_311,
                    "zone_id": "downtown",
                    "severity": SeverityLevel.MODERATE,
                    "metric_name": "incident_count",
                    "metric_value": 2.0,
                    "headline": "Public Works deployed mobile suction pumps on 4th Ave",
                    "impact": 40.0,
                },
                {
                    "feed_type": FeedType.TRANSIT,
                    "zone_id": "downtown",
                    "severity": SeverityLevel.MODERATE,
                    "metric_name": "delay_minutes",
                    "metric_value": 16.0,
                    "headline": "Line 1 subway single-tracking resumed, delays dropping to 16m",
                    "impact": 52.0,
                },
            ],
        },
        {
            "step": 6,
            "time_offset_min": 90,
            "label": "18:00 - Roadway Reopened & Normalizing",
            "events": [
                {
                    "feed_type": FeedType.WEATHER,
                    "zone_id": "downtown",
                    "severity": SeverityLevel.NORMAL,
                    "metric_name": "precipitation_mm_hr",
                    "metric_value": 0.0,
                    "headline": "Rain has stopped completely, skies clearing",
                    "impact": 5.0,
                },
                {
                    "feed_type": FeedType.TRANSIT,
                    "zone_id": "downtown",
                    "severity": SeverityLevel.LOW,
                    "metric_name": "delay_minutes",
                    "metric_value": 6.0,
                    "headline": "Transit clearing: Line 1 delays under 6m, buses back on route",
                    "impact": 20.0,
                },
                {
                    "feed_type": FeedType.SOCIAL_SENTIMENT,
                    "zone_id": "downtown",
                    "severity": SeverityLevel.NORMAL,
                    "metric_name": "sentiment_score",
                    "metric_value": 0.40,
                    "headline": "Community sentiment rebounding as roads reopen",
                    "impact": 15.0,
                },
            ],
        },
    ]

    # =========================================================================
    # SCENARIO 2: Summer Heatwave & Substation Transformer Fire
    # =========================================================================
    heatwave_frames: List[Dict[str, Any]] = [
        {
            "step": 0,
            "time_offset_min": 0,
            "label": "13:00 - High Heat Baseline",
            "events": [
                {"feed_type": FeedType.WEATHER, "zone_id": "tech_corridor", "severity": SeverityLevel.MODERATE, "metric_name": "temperature_c", "metric_value": 36.5, "headline": "Extreme Heat Advisory: 36.5°C in Tech Corridor", "impact": 45.0},
                {"feed_type": FeedType.AIR_QUALITY, "zone_id": "tech_corridor", "severity": SeverityLevel.MODERATE, "metric_name": "aqi", "metric_value": 85.0, "headline": "Moderate Ozone ground layer forming (AQI 85)", "impact": 35.0},
            ]
        },
        {
            "step": 1,
            "time_offset_min": 20,
            "label": "13:20 - Substation Trip & Blackout",
            "events": [
                {"feed_type": FeedType.INCIDENTS_311, "zone_id": "tech_corridor", "severity": SeverityLevel.CRITICAL, "metric_name": "incident_count", "metric_value": 4.0, "headline": "311 Alert: Electrical transformer failure, 12 blocks without power", "impact": 90.0},
                {"feed_type": FeedType.TRANSIT, "zone_id": "tech_corridor", "severity": SeverityLevel.HIGH, "metric_name": "delay_minutes", "metric_value": 22.0, "headline": "Traffic signals dark at 3 intersections; Bus 88 gridlocked", "impact": 75.0},
                {"feed_type": FeedType.SOCIAL_SENTIMENT, "zone_id": "tech_corridor", "severity": SeverityLevel.HIGH, "metric_name": "sentiment_score", "metric_value": -0.62, "headline": "Sentiment drop: AC units down during heatwave", "impact": 72.0},
            ]
        },
        {
            "step": 2,
            "time_offset_min": 45,
            "label": "13:45 - Grid Restoration & Traffic Control",
            "events": [
                {"feed_type": FeedType.INCIDENTS_311, "zone_id": "tech_corridor", "severity": SeverityLevel.MODERATE, "metric_name": "incident_count", "metric_value": 1.0, "headline": "Utility crews rerouting power through auxiliary substation", "impact": 35.0},
                {"feed_type": FeedType.TRANSIT, "zone_id": "tech_corridor", "severity": SeverityLevel.LOW, "metric_name": "delay_minutes", "metric_value": 7.0, "headline": "Traffic police directing intersections; delays easing", "impact": 22.0},
            ]
        }
    ]

    # =========================================================================
    # SCENARIO 3: Industrial Corridor Air Quality Smoke Incident
    # =========================================================================
    smoke_frames: List[Dict[str, Any]] = [
        {
            "step": 0,
            "time_offset_min": 0,
            "label": "09:00 - Morning Industrial Baseline",
            "events": [
                {"feed_type": FeedType.AIR_QUALITY, "zone_id": "east_suburbs", "severity": SeverityLevel.NORMAL, "metric_name": "aqi", "metric_value": 65.0, "headline": "Air quality moderate (AQI 65) in East Suburbs", "impact": 20.0},
            ]
        },
        {
            "step": 1,
            "time_offset_min": 15,
            "label": "09:15 - Sudden Particulate Surge",
            "events": [
                {"feed_type": FeedType.AIR_QUALITY, "zone_id": "east_suburbs", "severity": SeverityLevel.CRITICAL, "metric_name": "aqi", "metric_value": 215.0, "headline": "Hazardous Air Alert: AQI spiked to 215 (PM2.5 130 µg/m³)", "impact": 94.0},
                {"feed_type": FeedType.INCIDENTS_311, "zone_id": "east_suburbs", "severity": SeverityLevel.HIGH, "metric_name": "incident_count", "metric_value": 3.0, "headline": "311 Calls: Pungent chemical odor & smoke plume reported", "impact": 80.0},
                {"feed_type": FeedType.SOCIAL_SENTIMENT, "zone_id": "east_suburbs", "severity": SeverityLevel.HIGH, "metric_name": "sentiment_score", "metric_value": -0.70, "headline": "Resident alarm: '#EastSuburbsSmoke irritation in eyes and throat'", "impact": 82.0},
            ]
        },
        {
            "step": 2,
            "time_offset_min": 40,
            "label": "09:40 - Wind Dispersion & Containment",
            "events": [
                {"feed_type": FeedType.AIR_QUALITY, "zone_id": "east_suburbs", "severity": SeverityLevel.MODERATE, "metric_name": "aqi", "metric_value": 95.0, "headline": "Air quality recovering (AQI 95) as winds disperse plume", "impact": 35.0},
            ]
        }
    ]

    return {
        "flash_flood": {
            "id": "flash_flood",
            "title": "The Flash Flood & Evening Rush Hour Cascade",
            "description": "Demonstrates multi-feed fusion: torrential rain -> street drainage failure -> 311 flood calls -> transit stoppage -> correlation detection -> resident advisory.",
            "total_steps": len(flood_frames),
            "frames": flood_frames,
        },
        "heatwave_grid": {
            "id": "heatwave_grid",
            "title": "Summer Heatwave & Substation Transformer Fire",
            "description": "High temperature stress triggers electrical transformer failure, traffic signals cut off, and resident distress surge.",
            "total_steps": len(heatwave_frames),
            "frames": heatwave_frames,
        },
        "air_smoke": {
            "id": "air_smoke",
            "title": "Industrial Corridor Chemical & Smoke Incident",
            "description": "Sudden PM2.5 AQI spike to 215 coincides with citizen odor reports and negative sentiment.",
            "total_steps": len(smoke_frames),
            "frames": smoke_frames,
        },
    }
