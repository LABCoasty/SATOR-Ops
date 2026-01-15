from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
from enum import Enum


router = APIRouter()


class DecisionMode(str, Enum):
    OBSERVE = "observe"
    DECISION = "decision"
    REPLAY = "replay"


class ActionType(str, Enum):
    ACT = "act"
    ESCALATE = "escalate"
    DEFER = "defer"


class DecisionCreate(BaseModel):
    mode: DecisionMode
    evidence_ids: List[str]
    allowed_actions: List[str]
    uncertainty_score: float
    timebox_seconds: Optional[int] = 300


class DecisionAction(BaseModel):
    decision_id: str
    action_type: ActionType
    action_details: Optional[str] = None
    reason: Optional[str] = None


class DecisionResponse(BaseModel):
    id: str
    mode: DecisionMode
    created_at: datetime
    evidence_ids: List[str]
    allowed_actions: List[str]
    uncertainty_score: float
    timebox_expires_at: Optional[datetime]
    action_taken: Optional[ActionType] = None
    action_details: Optional[str] = None


@router.get("/", response_model=List[DecisionResponse])
async def list_decisions(
    mode: Optional[DecisionMode] = None,
    limit: int = 50,
    offset: int = 0,
):
    return []


@router.post("/", response_model=DecisionResponse)
async def create_decision(decision: DecisionCreate):
    return DecisionResponse(
        id="dec_placeholder",
        mode=decision.mode,
        created_at=datetime.utcnow(),
        evidence_ids=decision.evidence_ids,
        allowed_actions=decision.allowed_actions,
        uncertainty_score=decision.uncertainty_score,
        timebox_expires_at=datetime.utcnow(),
    )


@router.get("/{decision_id}", response_model=DecisionResponse)
async def get_decision(decision_id: str):
    raise HTTPException(status_code=404, detail="Decision not found")


@router.post("/{decision_id}/action", response_model=DecisionResponse)
async def record_action(decision_id: str, action: DecisionAction):
    raise HTTPException(status_code=404, detail="Decision not found")


@router.get("/{decision_id}/receipt")
async def get_decision_receipt(decision_id: str):
    raise HTTPException(status_code=404, detail="Decision not found")
