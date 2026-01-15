from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field


class DecisionMode(str, Enum):
    OBSERVE = "observe"
    DECISION = "decision"
    REPLAY = "replay"


class ActionType(str, Enum):
    ACT = "act"
    ESCALATE = "escalate"
    DEFER = "defer"


class Decision(BaseModel):
    id: str
    mode: DecisionMode
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    evidence_ids: List[str] = Field(default_factory=list)
    allowed_actions: List[str] = Field(default_factory=list)
    uncertainty_score: float = 0.0

    timebox_seconds: int = 300
    timebox_expires_at: Optional[datetime] = None

    action_taken: Optional[ActionType] = None
    action_details: Optional[str] = None
    action_taken_at: Optional[datetime] = None

    operator_id: Optional[str] = None
    escalated_to: Optional[str] = None
    defer_reason: Optional[str] = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class DecisionTransition(BaseModel):
    decision_id: str
    from_mode: DecisionMode
    to_mode: DecisionMode
    triggered_by: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    reason: Optional[str] = None
