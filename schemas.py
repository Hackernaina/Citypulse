"""
Data models and schemas for CityPulse: The Live Civic Health Dashboard
Normalized Common Data Model for all civic feeds.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
import uuid


class FeedType(str, Enum):
    WEATHER = "WEATHER"
    TRANSIT = "TRANSIT"
    INCIDENTS_311 = "INCIDENTS_311"
    AIR_QUALITY = "AIR_QUALITY"
    SOCIAL_SENTIMENT = "SOCIAL_SENTIMENT"


class SeverityLevel(str, Enum):
    NORMAL = "NORMAL"
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class FeedStatus(str, Enum):
    LIVE = "LIVE"
    DEGRADED = "DEGRADED"
    OFFLINE = "OFFLINE"


class GeoPoint(BaseModel):
    lat: float
    lng: float
    address: Optional[str] = None
    landmark: Optional[str] = None


class CivicEvent(BaseModel):
    """
    Common Normalized Data Model:
    Converts heterogeneous feeds (weather, transit, 311, AQI, sentiment)
    into a unified temporal & spatial event structure.
    """
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    feed_type: FeedType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    zone_id: str
    zone_name: str
    location: GeoPoint
    severity: SeverityLevel = SeverityLevel.NORMAL
    metric_name: str
    metric_value: float
    metric_unit: str
    summary_headline: str
    civic_impact_score: float = Field(
        ..., ge=0.0, le=100.0,
        description="Standardized civic disruption weight from 0 (none) to 100 (catastrophic)"
    )
    raw_payload: Dict[str, Any] = Field(default_factory=dict)
    feed_source: str = "Synthetic Stream / Sensor Fusion"


class Anomaly(BaseModel):
    """
    Represents a statistical or threshold anomaly detected in a civic feed.
    """
    anomaly_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    feed_type: FeedType
    zone_id: str
    zone_name: str
    metric_name: str
    current_value: float
    baseline_value: float
    z_score: float
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    description: str
    severity: SeverityLevel


class Correlation(BaseModel):
    """
    Represents a cross-feed spatial-temporal correlation.
    Strictly upholds Epistemic Honesty: framed as probable link, not confirmed causation.
    """
    correlation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    zone_id: str
    zone_name: str
    feeds_involved: List[FeedType]
    event_ids: List[str]
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    discovered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    pattern_type: str  # e.g. "STORM_TRANSIT_CASCADE", "GRID_OVERHEAT", "ENVIRONMENTAL_DISTRESS"
    hypothesis: str
    impact_rationale: str
    epistemic_disclaimer: str = (
        "Probable link based on spatial and temporal co-occurrence. "
        "Presented as an emerging pattern, not confirmed direct causation."
    )


class PlainLanguageSummary(BaseModel):
    """
    Point 5: Plain-Language Summary
    Designed for non-technical residents: what is happening right now, why it matters, and what to do.
    """
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ten_second_headline: str
    what_is_happening: List[str]
    why_it_matters: List[str]
    actionable_advice: List[str]
    affected_neighborhoods: List[str]
    overall_sentiment: str  # e.g. "Calm", "Elevated Caution", "Severe Disruption"
    epistemic_note: str = (
        "Grounding: Synthesized directly from current normalized sensor readings and cross-feed correlations."
    )


class ZonePulse(BaseModel):
    zone_id: str
    zone_name: str
    health_score: float = Field(..., ge=0.0, le=100.0, description="100 is pristine calm, 0 is total breakdown")
    status_label: str  # "Calm", "Moderate Activity", "Elevated Stress", "Critical Disruption"
    status_color: str  # "emerald", "amber", "orange", "rose"
    weather_summary: str
    transit_status: str
    incident_count: int
    aqi_index: float
    sentiment_score: float
    active_anomalies: List[Anomaly] = Field(default_factory=list)
    active_correlations: List[Correlation] = Field(default_factory=list)
    recent_events: List[CivicEvent] = Field(default_factory=list)


class FeedHealth(BaseModel):
    feed_type: FeedType
    status: FeedStatus
    last_ingested_at: Optional[datetime] = None
    event_count_last_hour: int = 0
    latency_ms: float = 0.0


class CityPulseState(BaseModel):
    """
    Complete real-time state of the city's civic pulse.
    """
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    city_name: str = "Metropolis Central"
    overall_health_score: float = Field(..., ge=0.0, le=100.0)
    overall_status_label: str
    pulse_rate_bpm: int = Field(..., description="Metaphorical pulse rate: 65 is calm, 120 is racing/crisis")
    zones: Dict[str, ZonePulse]
    feeds_health: Dict[str, FeedHealth]
    active_anomalies: List[Anomaly]
    active_correlations: List[Correlation]
    plain_language_summary: PlainLanguageSummary
    active_alerts: List[Dict[str, Any]] = Field(default_factory=list)
    is_replay_mode: bool = False
    replay_current_step: Optional[int] = None
    replay_total_steps: Optional[int] = None
