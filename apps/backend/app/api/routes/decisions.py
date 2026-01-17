from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
from enum import Enum
import uuid

from ...data.seed_data import generate_timeline_events, TRUST_BREAKDOWN


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
    trust_score: float
    timebox_expires_at: Optional[datetime]
    action_taken: Optional[ActionType] = None
    action_details: Optional[str] = None
    status: str = "pending"


class TimelineEvent(BaseModel):
    time: str
    timestamp: int
    label: str
    trust_score: float
    has_contradiction: bool
    description: str


class DecisionContext(BaseModel):
    current_assessment: str
    trust_score: float
    evidence_count: int
    contradictions_count: int
    known_unknowns: List[str]


# In-memory storage for demo
_decisions_store: List[dict] = []


def _generate_decision_id() -> str:
    return f"dec_{uuid.uuid4().hex[:12]}"


@router.get("/", response_model=List[DecisionResponse])
async def list_decisions(
    mode: Optional[DecisionMode] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    """List all decisions with optional filtering."""
    decisions = _decisions_store.copy()
    
    if mode:
        decisions = [d for d in decisions if d["mode"] == mode.value]
    if status:
        decisions = [d for d in decisions if d["status"] == status]
    
    decisions = decisions[offset:offset + limit]
    
    return [
        DecisionResponse(
            id=d["id"],
            mode=DecisionMode(d["mode"]),
            created_at=datetime.fromisoformat(d["created_at"]),
            evidence_ids=d["evidence_ids"],
            allowed_actions=d["allowed_actions"],
            uncertainty_score=d["uncertainty_score"],
            trust_score=d["trust_score"],
            timebox_expires_at=datetime.fromisoformat(d["timebox_expires_at"]) if d.get("timebox_expires_at") else None,
            action_taken=ActionType(d["action_taken"]) if d.get("action_taken") else None,
            action_details=d.get("action_details"),
            status=d["status"],
        )
        for d in decisions
    ]


@router.post("/", response_model=DecisionResponse)
async def create_decision(decision: DecisionCreate):
    """Create a new decision context."""
    now = datetime.utcnow()
    decision_id = _generate_decision_id()
    
    # Calculate trust score from uncertainty (inverse relationship)
    trust_score = max(0.0, min(1.0, 1.0 - decision.uncertainty_score + 0.3))
    
    decision_data = {
        "id": decision_id,
        "mode": decision.mode.value,
        "created_at": now.isoformat(),
        "evidence_ids": decision.evidence_ids,
        "allowed_actions": decision.allowed_actions,
        "uncertainty_score": decision.uncertainty_score,
        "trust_score": trust_score,
        "timebox_expires_at": (now + timedelta(seconds=decision.timebox_seconds)).isoformat() if decision.timebox_seconds else None,
        "action_taken": None,
        "action_details": None,
        "status": "pending",
    }
    
    _decisions_store.append(decision_data)
    
    return DecisionResponse(
        id=decision_id,
        mode=decision.mode,
        created_at=now,
        evidence_ids=decision.evidence_ids,
        allowed_actions=decision.allowed_actions,
        uncertainty_score=decision.uncertainty_score,
        trust_score=trust_score,
        timebox_expires_at=datetime.fromisoformat(decision_data["timebox_expires_at"]) if decision_data["timebox_expires_at"] else None,
        status="pending",
    )


@router.get("/timeline", response_model=List[TimelineEvent])
async def get_timeline():
    """Get the event timeline for the current assessment window."""
    events = generate_timeline_events()
    return [
        TimelineEvent(
            time=e["time"],
            timestamp=e["timestamp"],
            label=e["label"],
            trust_score=e["trust_score"],
            has_contradiction=e["has_contradiction"],
            description=e["description"],
        )
        for e in events
    ]


@router.get("/context", response_model=DecisionContext)
async def get_context():
    """Get current decision context with assessment summary."""
    return DecisionContext(
        current_assessment="System Operating Within Normal Parameters",
        trust_score=TRUST_BREAKDOWN["composite_score"],
        evidence_count=5,
        contradictions_count=2,
        known_unknowns=[
            "Remote Station C offline — cannot verify external conditions",
            "Legacy System Link degraded — historical comparison limited",
        ],
    )


@router.get("/trust-breakdown")
async def get_trust_breakdown():
    """Get detailed trust score breakdown."""
    return TRUST_BREAKDOWN


@router.get("/{decision_id}", response_model=DecisionResponse)
async def get_decision(decision_id: str):
    """Get a specific decision by ID."""
    for d in _decisions_store:
        if d["id"] == decision_id:
            return DecisionResponse(
                id=d["id"],
                mode=DecisionMode(d["mode"]),
                created_at=datetime.fromisoformat(d["created_at"]),
                evidence_ids=d["evidence_ids"],
                allowed_actions=d["allowed_actions"],
                uncertainty_score=d["uncertainty_score"],
                trust_score=d["trust_score"],
                timebox_expires_at=datetime.fromisoformat(d["timebox_expires_at"]) if d.get("timebox_expires_at") else None,
                action_taken=ActionType(d["action_taken"]) if d.get("action_taken") else None,
                action_details=d.get("action_details"),
                status=d["status"],
            )
    
    raise HTTPException(status_code=404, detail="Decision not found")


@router.post("/{decision_id}/action", response_model=DecisionResponse)
async def record_action(decision_id: str, action: DecisionAction):
    """Record an action taken for a decision."""
    for d in _decisions_store:
        if d["id"] == decision_id:
            d["action_taken"] = action.action_type.value
            d["action_details"] = action.action_details
            d["status"] = "completed"
            
            return DecisionResponse(
                id=d["id"],
                mode=DecisionMode(d["mode"]),
                created_at=datetime.fromisoformat(d["created_at"]),
                evidence_ids=d["evidence_ids"],
                allowed_actions=d["allowed_actions"],
                uncertainty_score=d["uncertainty_score"],
                trust_score=d["trust_score"],
                timebox_expires_at=datetime.fromisoformat(d["timebox_expires_at"]) if d.get("timebox_expires_at") else None,
                action_taken=ActionType(d["action_taken"]),
                action_details=d["action_details"],
                status="completed",
            )
    
    raise HTTPException(status_code=404, detail="Decision not found")


@router.get("/{decision_id}/receipt")
async def get_decision_receipt(decision_id: str):
    """Get the receipt for a completed decision."""
    for d in _decisions_store:
        if d["id"] == decision_id:
            if d["status"] != "completed":
                raise HTTPException(status_code=400, detail="Decision not yet completed")
            
            return {
                "id": f"rcpt_{decision_id[4:]}",
                "decision_id": decision_id,
                "created_at": datetime.utcnow().isoformat(),
                "outcome": "continue_operations" if d["action_taken"] == "act" else d["action_taken"],
                "trust_score": d["trust_score"],
                "evidence_count": len(d["evidence_ids"]),
                "hash": f"0x{uuid.uuid4().hex[:8]}...{uuid.uuid4().hex[-4:]}",
                "verified": True,
            }
    
    raise HTTPException(status_code=404, detail="Decision not found")
