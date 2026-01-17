"""
Temporal Models - Data models for the SATOR Replay Engine.

Defines:
- AtTimeState: Complete system state at a specific timestamp
- TimelineMarker: Events shown on the timeline
- ConfidencePoint: Points for the confidence ribbon
- Supporting types for trust, contradictions, postures
"""

from datetime import datetime
from typing import Optional, Dict, List, Any
from enum import Enum
from pydantic import BaseModel, Field


# =============================================================================
# Enums
# =============================================================================

class ConfirmationStatus(str, Enum):
    """What the system believed about a claim at time t"""
    CONFIRMED = "confirmed"
    UNCONFIRMED = "unconfirmed"
    CONFLICTING = "conflicting"


class ConfidenceLevel(str, Enum):
    """Confidence bands for the ribbon"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Posture(str, Enum):
    """Recommended operator posture"""
    MONITOR = "monitor"
    VERIFY = "verify"
    ESCALATE = "escalate"
    CONTAIN = "contain"
    DEFER = "defer"


class ActionGating(str, Enum):
    """What actions are allowed at this posture"""
    ALLOWED = "allowed"
    RISKY = "risky"
    BLOCKED = "blocked"


class TrustState(str, Enum):
    """Per-sensor trust state"""
    TRUSTED = "trusted"
    DEGRADED = "degraded"
    UNTRUSTED = "untrusted"
    QUARANTINED = "quarantined"


class MarkerType(str, Enum):
    """Types of markers on the timeline"""
    ALARM = "alarm"
    TRUST_CHANGE = "trust_change"
    CONTRADICTION_APPEARED = "contradiction_appeared"
    CONTRADICTION_RESOLVED = "contradiction_resolved"
    OPERATOR_ACTION = "operator_action"
    RECEIPT_CREATED = "receipt_created"
    MODE_CHANGE = "mode_change"
    SCENARIO_START = "scenario_start"
    SCENARIO_END = "scenario_end"


class EventSeverity(str, Enum):
    """Event severity levels"""
    INFO = "info"
    WARNING = "warning"
    ALARM = "alarm"
    CRITICAL = "critical"


# =============================================================================
# Trust & Sensor Models
# =============================================================================

class SensorTrustSnapshot(BaseModel):
    """Trust state for a single sensor at time t"""
    tag_id: str
    trust_score: float = Field(ge=0.0, le=1.0)
    trust_state: TrustState
    reason_codes: List[str] = Field(default_factory=list)


class TrustSnapshot(BaseModel):
    """Aggregated trust snapshot at time t"""
    zone_trust_state: TrustState = TrustState.TRUSTED
    zone_confidence: ConfidenceLevel = ConfidenceLevel.HIGH
    sensors: Dict[str, SensorTrustSnapshot] = Field(default_factory=dict)


# =============================================================================
# Contradiction Models
# =============================================================================

class Contradiction(BaseModel):
    """A detected contradiction at time t"""
    contradiction_id: str
    timestamp: datetime
    primary_tag_id: str
    secondary_tag_ids: List[str] = Field(default_factory=list)
    reason_code: str
    description: str
    values: Dict[str, float] = Field(default_factory=dict)
    expected_relationship: str
    resolved: bool = False
    severity: EventSeverity = EventSeverity.WARNING


# =============================================================================
# Operator Action Models
# =============================================================================

class OperatorAction(BaseModel):
    """An action taken by an operator"""
    timestamp: datetime
    action_type: str  # defer, escalate, override, verify, acknowledge
    description: str
    operator_id: Optional[str] = None


class ReceiptStatus(BaseModel):
    """Status of decision receipt at time t"""
    exists: bool = False
    receipt_id: Optional[str] = None
    created_at: Optional[datetime] = None
    label: str = "No receipt yet"  # "No receipt yet" | "Receipt drafted" | "Receipt created at HH:MM:SS"


# =============================================================================
# Reason Code Models
# =============================================================================

class ReasonCode(BaseModel):
    """Reason code with dual language (plain + technical)"""
    code: str  # e.g., "RC10"
    plain_english: str  # e.g., "Sensors that should agree are in conflict"
    technical: str  # e.g., "Redundancy conflict detected"


# =============================================================================
# Timeline Marker Models
# =============================================================================

class TimelineMarker(BaseModel):
    """A marker event on the timeline"""
    id: str
    timestamp: datetime
    time_sec: float  # Seconds from incident start
    marker_type: MarkerType
    severity: EventSeverity
    label: str
    description: str
    tag_id: Optional[str] = None
    reason_code: Optional[str] = None
    has_contradiction: bool = False
    
    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class MarkerCluster(BaseModel):
    """Clustered markers when zoomed out"""
    start_time: datetime
    end_time: datetime
    count: int
    dominant_type: MarkerType
    label: str  # e.g., "6 Trust Updates"
    markers: List[TimelineMarker] = Field(default_factory=list)


# =============================================================================
# Confidence Ribbon
# =============================================================================

class ConfidencePoint(BaseModel):
    """A point on the confidence ribbon"""
    timestamp: datetime
    time_sec: float
    confidence_level: ConfidenceLevel
    trust_score: float = Field(ge=0.0, le=1.0)
    
    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


# =============================================================================
# At-Time State (Core Model per Spec §4)
# =============================================================================

class AtTimeState(BaseModel):
    """
    Complete system state at timestamp t.
    
    Per spec: "Replay shows what was known at the time, not what we know now."
    This model contains ONLY information that was available at time t.
    """
    timestamp: datetime
    time_sec: float  # Seconds from incident start
    
    # A. Claim at time t (one sentence)
    claim: str = "System operating normally"
    
    # B. Confirmation status
    confirmation_status: ConfirmationStatus = ConfirmationStatus.CONFIRMED
    
    # C. Confidence
    confidence: ConfidenceLevel = ConfidenceLevel.HIGH
    
    # D. Trust snapshot
    trust_snapshot: TrustSnapshot = Field(default_factory=TrustSnapshot)
    
    # E. Contradictions at time t (only active, not resolved)
    contradictions: List[Contradiction] = Field(default_factory=list)
    
    # F. Recommended posture
    posture: Posture = Posture.MONITOR
    posture_reason: str = "All sensors reporting normally"
    
    # G. Action gating
    action_gating: ActionGating = ActionGating.ALLOWED
    allowed_actions: List[str] = Field(default_factory=list)
    
    # H. Operator action history up to time t
    operator_history: List[OperatorAction] = Field(default_factory=list)
    
    # Receipt status
    receipt_status: ReceiptStatus = Field(default_factory=ReceiptStatus)
    
    # Top reason codes (for display)
    top_reason_codes: List[ReasonCode] = Field(default_factory=list)
    
    # Next recommended step
    next_step: str = "Continue monitoring"
    
    # Mode
    mode: str = "observe"  # observe | decision | replay
    
    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


# =============================================================================
# Timeline (Full Incident)
# =============================================================================

class IncidentTimeline(BaseModel):
    """Full timeline for an incident"""
    incident_id: str
    start_time: datetime
    end_time: datetime
    duration_sec: float
    
    # All markers
    markers: List[TimelineMarker] = Field(default_factory=list)
    
    # Confidence ribbon points
    confidence_band: List[ConfidencePoint] = Field(default_factory=list)
    
    # Summary
    total_events: int = 0
    total_contradictions: int = 0
    total_operator_actions: int = 0
    
    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
