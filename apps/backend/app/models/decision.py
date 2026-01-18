"""
Decision models for SATOR Ops.

Defines decision modes, action types, and decision-related data structures.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class DecisionMode(str, Enum):
    """Operational mode of the decision system."""
    OBSERVE = "observe"      # Passive monitoring mode
    DECISION = "decision"    # Active decision-making mode
    REPLAY = "replay"        # Forensic review mode


class ActionType(str, Enum):
    """Types of actions an operator can take."""
    ACT = "act"              # Proceed with control action
    ESCALATE = "escalate"    # Transfer to higher authority
    DEFER = "defer"          # Delay decision and request more info


class Decision(BaseModel):
    """
    A decision record in the system.
    
    This represents a decision context that has been created,
    though DecisionCard is more commonly used for active decision cards.
    """
    decision_id: str
    mode: DecisionMode
    created_at: datetime
    evidence_ids: list[str]
    allowed_actions: list[str]
    uncertainty_score: float
    resolved: bool = False
    action_taken: Optional[ActionType] = None
    action_taken_at: Optional[datetime] = None
    operator_id: Optional[str] = None
