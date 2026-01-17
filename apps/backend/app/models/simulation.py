"""
Simulation Data Models

Models for scenario specification and failure mode injection.
"""

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class FailureModeType(str, Enum):
    """Types of failure modes that can be injected"""
    MISSING_BURSTS = "missing_bursts"     # RC01 - data gaps
    STALE_STREAM = "stale_stream"         # RC02 - no updates
    RANGE_VIOLATION = "range_violation"   # RC05 - outside limits
    ROC_VIOLATION = "roc_violation"       # RC06 - rate of change
    FLATLINE = "flatline"                 # RC07 - stuck value
    DRIFT = "drift"                       # RC09 - gradual divergence
    REDUNDANCY_CONFLICT = "redundancy_conflict"  # RC10 - sensor mismatch
    PHYSICS_CONTRADICTION = "physics_contradiction"  # RC11 - impossible state


class FailureMode(BaseModel):
    """
    Specification for a single failure mode.
    
    Defines how a sensor should fail during simulation.
    """
    type: FailureModeType = Field(..., description="Type of failure")
    tag_id: str = Field(..., description="Which sensor to affect")
    
    # Timing
    start_time_sec: float = Field(..., description="When to start failure (seconds from scenario start)")
    duration_sec: float | None = Field(None, description="How long failure lasts (None = permanent)")
    
    # Parameters (vary by failure type)
    params: dict = Field(default_factory=dict, description="Failure-specific parameters")
    
    # Severity
    severity: float = Field(default=1.0, ge=0.0, le=1.0, description="Severity multiplier")


class FailureInjection(BaseModel):
    """
    A request to inject a failure during live simulation.
    """
    failure_type: FailureModeType = Field(..., description="Type of failure to inject")
    tag_id: str = Field(..., description="Which sensor to affect")
    params: dict = Field(default_factory=dict, description="Failure-specific parameters")
    
    # Optional timing override
    duration_sec: float | None = Field(None, description="How long failure should last")


class SensorSpec(BaseModel):
    """
    Specification for a sensor in a scenario.
    """
    tag_id: str = Field(..., description="Unique sensor identifier")
    name: str = Field(..., description="Human-readable name")
    unit: str = Field(..., description="Unit of measurement")
    
    # Physical properties
    baseline_value: float = Field(..., description="Normal operating value")
    noise_std: float = Field(default=0.05, description="Standard deviation of noise")
    min_value: float = Field(..., description="Minimum physical value")
    max_value: float = Field(..., description="Maximum physical value")
    max_roc: float = Field(..., description="Maximum rate of change per second")
    
    # Signal characteristics
    trend_rate: float = Field(default=0.0, description="Linear trend per second")
    oscillation_amplitude: float = Field(default=0.0, description="Sine wave amplitude")
    oscillation_period_sec: float = Field(default=60.0, description="Sine wave period")
    
    # Grouping
    redundancy_group: str | None = Field(None, description="Redundancy group ID")


class ScenarioSpec(BaseModel):
    """
    Complete specification for a simulation scenario.
    
    Defines sensors, their behaviors, and planned failure injections.
    """
    scenario_id: str = Field(..., description="Unique scenario identifier")
    name: str = Field(..., description="Human-readable scenario name")
    description: str = Field(default="", description="Scenario description")
    
    # Timing
    duration_sec: float = Field(..., description="Total scenario duration in seconds")
    sample_rate: float = Field(default=1.0, description="Samples per second")
    
    # Sensors
    sensors: list[SensorSpec] = Field(..., description="Sensors in this scenario")
    
    # Planned failures
    failures: list[FailureMode] = Field(
        default_factory=list, 
        description="Scheduled failure injections"
    )
    
    # Seed for reproducibility
    seed: int = Field(default=42, description="Random seed for determinism")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    tags: list[str] = Field(default_factory=list, description="Categorization tags")


class ScenarioState(BaseModel):
    """
    Current state of a running scenario.
    """
    scenario_id: str = Field(..., description="Active scenario ID")
    started_at: datetime = Field(..., description="When scenario started")
    current_time_sec: float = Field(default=0.0, description="Current simulation time")
    
    # Status
    is_running: bool = Field(default=True, description="Whether scenario is active")
    is_paused: bool = Field(default=False, description="Whether scenario is paused")
    
    # Injected failures
    active_failures: list[str] = Field(
        default_factory=list, 
        description="Currently active failure IDs"
    )
    completed_failures: list[str] = Field(
        default_factory=list,
        description="Failures that have ended"
    )
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
