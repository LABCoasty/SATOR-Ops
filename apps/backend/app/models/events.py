"""
Event Data Models

Models for system events: alarms, trust updates, contradictions, and operator actions.
"""

from datetime import datetime
from enum import Enum
from typing import Literal
from pydantic import BaseModel, Field


class AlarmSeverity(str, Enum):
    """Severity levels for alarms"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class OperationalMode(str, Enum):
    """Operational mode of the system"""
    OBSERVE = "observe"     # Passive baseline - standard situational awareness
    DECISION = "decision"   # Active decision mode - formal commitment required
    REPLAY = "replay"       # Forensic review mode


class ReasonCode(str, Enum):
    """
    Reason codes for trust score penalties.
    
    Each code provides explainability for why a sensor's trust was affected.
    """
    RC01 = "RC01"  # Missing Bursts - data gaps
    RC02 = "RC02"  # Stale Stream - time since last update exceeded
    RC03 = "RC03"  # Time Jitter - out-of-order packets
    RC04 = "RC04"  # Upstream BAD - source quality flags
    RC05 = "RC05"  # Range Violation - outside physical limits
    RC06 = "RC06"  # ROC Violation - rate of change exceeded
    RC07 = "RC07"  # Flatline - stuck reading
    RC08 = "RC08"  # Spike Density - high noise
    RC09 = "RC09"  # Drift vs Peers - diverging from redundancy group
    RC10 = "RC10"  # Redundancy Conflict - deviation from neighbors
    RC11 = "RC11"  # Physics Contradiction - impossible physical state
    RC12 = "RC12"  # Context Mismatch - unexpected for time/mode
    RC13 = "RC13"  # Clock Anomaly - timestamp issues
    RC14 = "RC14"  # Replay/Spoof - suspected tampering


class AlarmEvent(BaseModel):
    """
    A discrete alarm event in the system.
    """
    event_id: str = Field(..., description="Unique event identifier")
    timestamp: datetime = Field(..., description="When the alarm occurred")
    tag_id: str = Field(..., description="Related sensor ID")
    severity: AlarmSeverity = Field(..., description="Alarm severity")
    message: str = Field(..., description="Human-readable alarm message")
    reason_codes: list[ReasonCode] = Field(default_factory=list, description="Associated reason codes")
    acknowledged: bool = Field(default=False, description="Whether operator acknowledged")
    acknowledged_by: str | None = Field(None, description="Who acknowledged")
    acknowledged_at: datetime | None = Field(None, description="When acknowledged")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TrustUpdate(BaseModel):
    """
    A trust score update for a sensor.
    
    Records the reason codes and evidence that caused a trust change.
    """
    event_id: str = Field(..., description="Unique event identifier")
    tag_id: str = Field(..., description="Sensor identifier")
    timestamp: datetime = Field(..., description="When the update occurred")
    
    # Trust change
    previous_score: float = Field(..., ge=0.0, le=1.0, description="Previous trust score")
    new_score: float = Field(..., ge=0.0, le=1.0, description="New trust score")
    delta: float = Field(..., description="Change in trust score")
    
    # Explainability
    reason_codes: list[ReasonCode] = Field(..., description="Reason codes causing this update")
    evidence_refs: list[str] = Field(default_factory=list, description="IDs of evidence items")
    explanation: str = Field(default="", description="Human-readable explanation")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Contradiction(BaseModel):
    """
    A contradiction between sensors or physical state.
    
    Represents a situation where sensors that should agree are in disagreement,
    or where readings violate physical invariants.
    """
    contradiction_id: str = Field(..., description="Unique contradiction identifier")
    timestamp: datetime = Field(..., description="When contradiction was detected")
    
    # Sensors involved
    primary_tag_id: str = Field(..., description="Primary sensor in conflict")
    secondary_tag_ids: list[str] = Field(default_factory=list, description="Other sensors involved")
    
    # Contradiction details
    reason_code: ReasonCode = Field(..., description="Specific reason code (RC10 or RC11)")
    description: str = Field(..., description="Human-readable description")
    
    # Values at time of conflict
    values: dict[str, float | None] = Field(..., description="Tag ID to value mapping")
    expected_relationship: str = Field(..., description="What the relationship should be")
    
    # Resolution
    resolved: bool = Field(default=False, description="Whether contradiction is resolved")
    resolved_at: datetime | None = Field(None, description="When resolved")
    resolution_method: str | None = Field(None, description="How it was resolved")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class OperatorAction(BaseModel):
    """
    An operator action/decision in response to a situation.
    
    Records the decision, rationale, and context for accountability.
    """
    action_id: str = Field(..., description="Unique action identifier")
    timestamp: datetime = Field(..., description="When action was taken")
    operator_id: str = Field(..., description="Who took the action")
    
    # Action type
    action_type: Literal["act", "escalate", "defer"] = Field(
        ..., 
        description="Type of action taken"
    )
    
    # Context
    incident_id: str | None = Field(None, description="Related incident ID")
    triggered_by: str | None = Field(None, description="What triggered decision mode")
    
    # Decision details
    action_description: str = Field(..., description="What action was taken")
    rationale: str = Field(..., description="Why this action was chosen")
    
    # Evidence snapshot at decision time
    evidence_snapshot: dict = Field(
        default_factory=dict, 
        description="System state snapshot at decision time"
    )
    
    # For escalation
    escalated_to: str | None = Field(None, description="Who it was escalated to")
    
    # For deferral
    defer_until: datetime | None = Field(None, description="When to revisit")
    defer_reason: str | None = Field(None, description="Reason for deferral")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SystemState(BaseModel):
    """
    Complete system state at a point in time.
    
    This is what gets reconstructed during replay.
    """
    timestamp: datetime = Field(..., description="Timestamp of this state")
    
    # Telemetry
    telemetry: dict[str, float | None] = Field(
        default_factory=dict, 
        description="Tag ID to current value mapping"
    )
    
    # Trust
    trust_scores: dict[str, float] = Field(
        default_factory=dict, 
        description="Tag ID to trust score mapping"
    )
    active_reason_codes: dict[str, list[str]] = Field(
        default_factory=dict, 
        description="Tag ID to active reason codes"
    )
    
    # Contradictions
    unresolved_contradictions: list[str] = Field(
        default_factory=list, 
        description="IDs of unresolved contradictions"
    )
    
    # Mode
    operational_mode: OperationalMode = Field(
        default=OperationalMode.OBSERVE,
        description="Current operational mode"
    )
    decision_clock_started: datetime | None = Field(
        None, 
        description="When decision clock started (if in decision mode)"
    )
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
