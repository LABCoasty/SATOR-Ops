"""
Overshoot Vision Models - Pydantic models for Overshoot AI vision output.

Defines structured models for:
- Equipment states (valve positions, gauge readings, indicator lights)
- Operator actions (person location, interactions with equipment)
- Safety events (spills, leaks, smoke, unauthorized access)
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


# ============================================================================
# Enums
# ============================================================================

class EquipmentType(str, Enum):
    """Types of equipment that can be detected."""
    VALVE = "valve"
    GAUGE = "gauge"
    PUMP = "pump"
    INDICATOR_LIGHT = "indicator_light"
    PRESSURE_VESSEL = "pressure_vessel"
    PIPE = "pipe"
    CONTROL_PANEL = "control_panel"
    EMERGENCY_SHUTOFF = "emergency_shutoff"
    FLOW_METER = "flow_meter"
    TEMPERATURE_PROBE = "temperature_probe"
    UNKNOWN = "unknown"


class EquipmentStatus(str, Enum):
    """Status of equipment."""
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"
    OFFLINE = "offline"


class ValvePosition(str, Enum):
    """Visual valve position states."""
    OPEN = "open"
    CLOSED = "closed"
    PARTIAL = "partial"
    UNKNOWN = "unknown"


class IndicatorColor(str, Enum):
    """Indicator light colors."""
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"
    OFF = "off"
    BLINKING = "blinking"


class ActionType(str, Enum):
    """Types of operator actions detected."""
    WALKING = "walking"
    STANDING = "standing"
    OPERATING_EQUIPMENT = "operating_equipment"
    INSPECTING = "inspecting"
    POINTING = "pointing"
    CARRYING = "carrying"
    RUNNING = "running"
    FALLING = "falling"
    UNKNOWN = "unknown"


class SafetyEventType(str, Enum):
    """Types of safety events."""
    SPILL = "spill"
    LEAK = "leak"
    SMOKE = "smoke"
    FIRE = "fire"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    PPE_VIOLATION = "ppe_violation"
    FALL_HAZARD = "fall_hazard"
    CONFINED_SPACE = "confined_space"
    PRESSURE_RELEASE = "pressure_release"
    EQUIPMENT_DAMAGE = "equipment_damage"
    NONE = "none"


class Confidence(str, Enum):
    """Confidence level for detections."""
    HIGH = "high"      # > 0.9
    MEDIUM = "medium"  # 0.7 - 0.9
    LOW = "low"        # 0.5 - 0.7
    UNCERTAIN = "uncertain"  # < 0.5


# ============================================================================
# Bounding Box and Location
# ============================================================================

class BoundingBox(BaseModel):
    """Bounding box for detected objects."""
    x: float  # Top-left x (0-1 normalized)
    y: float  # Top-left y (0-1 normalized)
    width: float  # Width (0-1 normalized)
    height: float  # Height (0-1 normalized)
    
    def center(self) -> tuple[float, float]:
        """Get center point of bounding box."""
        return (self.x + self.width / 2, self.y + self.height / 2)


class Location(BaseModel):
    """Location in the scene."""
    zone: Optional[str] = None  # Named zone (e.g., "pump_room", "control_area")
    coordinates: Optional[BoundingBox] = None
    description: Optional[str] = None


# ============================================================================
# Equipment State
# ============================================================================

class GaugeReading(BaseModel):
    """Visual gauge reading."""
    value: Optional[float] = None
    unit: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    in_normal_range: bool = True
    confidence: float = 0.0


class EquipmentState(BaseModel):
    """
    State of a piece of equipment detected in the video.
    
    Captures visual observations of equipment including valve positions,
    gauge readings, and indicator lights.
    """
    equipment_id: str  # Unique ID for this equipment instance
    equipment_type: EquipmentType
    name: Optional[str] = None
    location: Optional[Location] = None
    bbox: Optional[BoundingBox] = None
    
    # Status
    status: EquipmentStatus = EquipmentStatus.NORMAL
    
    # Type-specific states
    valve_position: Optional[ValvePosition] = None
    gauge_reading: Optional[GaugeReading] = None
    indicator_color: Optional[IndicatorColor] = None
    
    # Raw visual data
    visual_description: Optional[str] = None
    
    # Confidence and metadata
    confidence: float = 0.0
    confidence_level: Confidence = Confidence.UNCERTAIN
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Mapping to telemetry
    mapped_tag_id: Optional[str] = None  # Maps to sensor tag_id
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return self.model_dump(mode="json")


# ============================================================================
# Operator Action
# ============================================================================

class Person(BaseModel):
    """A person detected in the video."""
    person_id: str
    bbox: Optional[BoundingBox] = None
    location: Optional[Location] = None
    wearing_ppe: bool = True
    ppe_items: List[str] = Field(default_factory=list)  # hard_hat, safety_vest, etc.


class OperatorAction(BaseModel):
    """
    Action performed by an operator detected in the video.
    
    Captures person movements, interactions with equipment, and activities.
    """
    action_id: str = Field(default_factory=lambda: str(__import__("uuid").uuid4()))
    person: Person
    action_type: ActionType
    
    # Interaction details
    interacting_with: Optional[str] = None  # equipment_id if interacting
    interaction_description: Optional[str] = None
    
    # Movement
    moving_direction: Optional[str] = None  # "towards_pump", "away_from_valve"
    speed: Optional[str] = None  # "stationary", "walking", "running"
    
    # Context
    visual_description: Optional[str] = None
    
    # Confidence and metadata
    confidence: float = 0.0
    confidence_level: Confidence = Confidence.UNCERTAIN
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    duration_seconds: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return self.model_dump(mode="json")


# ============================================================================
# Safety Event
# ============================================================================

class SafetyEvent(BaseModel):
    """
    Safety event detected in the video.
    
    Captures safety-critical observations like spills, leaks, smoke,
    unauthorized access, and PPE violations.
    """
    event_id: str = Field(default_factory=lambda: str(__import__("uuid").uuid4()))
    event_type: SafetyEventType
    severity: str = "warning"  # info, warning, critical, emergency
    
    # Location and extent
    location: Optional[Location] = None
    bbox: Optional[BoundingBox] = None
    affected_area: Optional[str] = None
    
    # Details
    description: str
    visual_evidence: Optional[str] = None  # Description of what was seen
    
    # Related entities
    related_equipment: List[str] = Field(default_factory=list)  # equipment_ids
    related_persons: List[str] = Field(default_factory=list)  # person_ids
    
    # Confidence and metadata
    confidence: float = 0.0
    confidence_level: Confidence = Confidence.UNCERTAIN
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Status
    acknowledged: bool = False
    resolved: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return self.model_dump(mode="json")


# ============================================================================
# Vision Frame and Analysis
# ============================================================================

class VisionFrame(BaseModel):
    """
    Single frame of vision analysis from Overshoot.
    
    Contains all detections for a single frame/moment in time.
    """
    frame_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    video_timestamp_ms: Optional[int] = None  # Position in video
    
    # Detections
    equipment_states: List[EquipmentState] = Field(default_factory=list)
    operator_actions: List[OperatorAction] = Field(default_factory=list)
    safety_events: List[SafetyEvent] = Field(default_factory=list)
    
    # Frame metadata
    frame_quality: float = 1.0  # 0-1, quality of the frame
    scene_description: Optional[str] = None
    
    def has_detections(self) -> bool:
        """Check if frame has any detections."""
        return bool(
            self.equipment_states or 
            self.operator_actions or 
            self.safety_events
        )
    
    def has_safety_events(self) -> bool:
        """Check if frame has safety events."""
        return bool(self.safety_events)
    
    def get_critical_events(self) -> List[SafetyEvent]:
        """Get critical severity safety events."""
        return [e for e in self.safety_events if e.severity in ["critical", "emergency"]]


class VisionAnalysis(BaseModel):
    """
    Aggregated vision analysis over a time window.
    
    Combines multiple frames to provide a summary of what's happening.
    """
    analysis_id: str = Field(default_factory=lambda: str(__import__("uuid").uuid4()))
    start_time: datetime
    end_time: datetime
    
    # Aggregated data
    frames_analyzed: int = 0
    total_equipment_detected: int = 0
    total_persons_detected: int = 0
    total_safety_events: int = 0
    
    # Current state (latest observations)
    current_equipment_states: List[EquipmentState] = Field(default_factory=list)
    current_operator_actions: List[OperatorAction] = Field(default_factory=list)
    active_safety_events: List[SafetyEvent] = Field(default_factory=list)
    
    # Trends and changes
    equipment_changes: List[Dict[str, Any]] = Field(default_factory=list)
    notable_actions: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Summary
    summary: Optional[str] = None
    recommendations: List[str] = Field(default_factory=list)
    
    # Confidence
    overall_confidence: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return self.model_dump(mode="json")


# ============================================================================
# Webhook Payload
# ============================================================================

class OvershootWebhookPayload(BaseModel):
    """
    Payload received from Overshoot webhook.
    
    This is the format expected from Overshoot's API when it sends
    real-time vision analysis updates.
    """
    event_type: str = "vision_update"  # vision_update, analysis_complete, error
    session_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Data (one of these will be populated based on event_type)
    frame: Optional[VisionFrame] = None
    analysis: Optional[VisionAnalysis] = None
    error: Optional[str] = None
    
    # Metadata
    video_source: Optional[str] = None
    processing_time_ms: Optional[int] = None
