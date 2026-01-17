"""
Telemetry Data Models

Models for sensor telemetry points and configuration.
"""

from datetime import datetime
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class QualityFlag(str, Enum):
    """Quality flag for telemetry readings"""
    GOOD = "GOOD"
    BAD = "BAD"
    UNCERTAIN = "UNCERTAIN"


class TrustState(str, Enum):
    """Trust state for sensors based on trust score"""
    TRUSTED = "trusted"           # Reliable enough for normal operation
    DEGRADED = "degraded"         # Usable but risky; verification required
    CONFLICTING = "conflicting"   # Sensors that should agree are in disagreement
    UNTRUSTED = "untrusted"       # Reading is likely wrong
    QUARANTINED = "quarantined"   # Severe fault or suspected tampering
    RECOVERING = "recovering"     # Improving but needs more time


class TelemetryPoint(BaseModel):
    """
    A single timestamped telemetry reading from a sensor.
    
    This is the fundamental data unit flowing through the system.
    """
    tag_id: str = Field(..., description="Unique identifier for the sensor/tag")
    timestamp: datetime = Field(..., description="ISO8601 timestamp of the reading")
    value: float | None = Field(None, description="Sensor value (None if missing)")
    quality: QualityFlag = Field(default=QualityFlag.GOOD, description="Quality flag from source")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SensorConfig(BaseModel):
    """
    Configuration for a sensor/tag in the system.
    
    Defines physical limits, redundancy groups, and expected behavior.
    """
    tag_id: str = Field(..., description="Unique identifier for the sensor")
    name: str = Field(..., description="Human-readable name")
    unit: str = Field(default="", description="Unit of measurement (e.g., 'PSI', 'GPM')")
    
    # Physical limits for Range Violation detection (RC05)
    min_value: float = Field(..., description="Minimum plausible physical value")
    max_value: float = Field(..., description="Maximum plausible physical value")
    
    # Rate of change limits for ROC Violation detection (RC06)
    max_roc: float = Field(..., description="Maximum plausible rate of change per second")
    
    # Redundancy group for conflict detection (RC10)
    redundancy_group: str | None = Field(None, description="Group ID for redundant sensors")
    
    # Expected update interval for Stale Stream detection (RC02)
    expected_interval_sec: float = Field(default=1.0, description="Expected update interval in seconds")
    
    # Flatline detection parameters (RC07)
    flatline_epsilon: float = Field(default=0.001, description="Variance threshold for flatline detection")
    flatline_duration_sec: float = Field(default=30.0, description="Duration to trigger flatline")
    
    # Context for time-of-day expectations (RC12)
    context_bands: dict[str, tuple[float, float]] = Field(
        default_factory=dict, 
        description="Expected value bands by context (e.g., 'day': (90, 110))"
    )


class SensorState(BaseModel):
    """
    Current state of a sensor including trust information.
    
    This is the "belief state" about a sensor at a point in time.
    """
    tag_id: str = Field(..., description="Sensor identifier")
    timestamp: datetime = Field(..., description="When this state was computed")
    
    # Current value
    current_value: float | None = Field(None, description="Last known value")
    quality: QualityFlag = Field(default=QualityFlag.GOOD, description="Quality flag")
    
    # Trust information
    trust_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Trust score 0-1")
    trust_state: TrustState = Field(default=TrustState.TRUSTED, description="Trust state category")
    active_reason_codes: list[str] = Field(default_factory=list, description="Active reason codes")
    
    # Time tracking
    last_update: datetime | None = Field(None, description="When value was last updated")
    seconds_since_update: float = Field(default=0.0, description="Seconds since last update")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
