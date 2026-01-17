"""
Audit API Routes

Endpoints for audit log access and verification.
"""

from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.audit import AuditLedger, ChainVerifier, VerificationResult
from app.core.audit.ledger import create_decision_receipt


router = APIRouter()

# Global audit ledger instance
_ledger: AuditLedger | None = None


def get_ledger() -> AuditLedger:
    """Get or create the audit ledger"""
    global _ledger
    if _ledger is None:
        _ledger = AuditLedger()
    return _ledger


# === Request/Response Models ===

class LogEventRequest(BaseModel):
    action: str = Field(..., description="Type of action")
    actor: str = Field("system", description="Who caused the event (system/user/agent)")
    actor_id: str | None = Field(None, description="Specific actor identifier")
    payload: dict = Field(default_factory=dict, description="Event data")
    data_ref: str | None = Field(None, description="Reference to related artifact")


class LogDecisionRequest(BaseModel):
    operator_id: str = Field(..., description="Who made the decision")
    action_type: str = Field(..., description="act, escalate, or defer")
    action_description: str = Field(..., description="What was decided")
    rationale: str = Field(..., description="Why this decision was made")
    incident_id: str | None = Field(None, description="Related incident ID")


class CreateReceiptRequest(BaseModel):
    operator_id: str = Field(..., description="Who made the decision")
    action_type: str = Field(..., description="act, escalate, or defer")
    action_description: str = Field(..., description="What was decided")
    rationale: str = Field(..., description="Why this decision was made")
    uncertainty_snapshot: dict = Field(default_factory=dict, description="Trust state at decision time")
    active_contradictions: list[str] = Field(default_factory=list, description="Active contradiction IDs")
    evidence_refs: list[str] = Field(default_factory=list, description="Evidence references")


class VerifyResponse(BaseModel):
    status: str
    is_valid: bool
    message: str
    events_checked: int
    events_passed: int
    genesis_hash: str
    latest_hash: str
    verified_at: str


# === Endpoints ===

@router.get("/verify", response_model=VerifyResponse, summary="Verify audit chain")
async def verify_chain():
    """
    Verify the integrity of the hash-chained audit log.
    
    Iterates through all events, recomputing hashes and checking
    continuity to detect any tampering.
    
    Returns "Chain Verified: PASS" for a valid chain.
    """
    ledger = get_ledger()
    events = ledger.get_events()
    
    verifier = ChainVerifier()
    result = verifier.verify_chain(events)
    
    # Log the verification
    await ledger.log_chain_verified(
        is_valid=result.is_valid,
        events_checked=result.events_checked,
        error_message=result.error_message,
    )
    
    message = "Chain Verified: PASS" if result.is_valid else f"Chain Verified: FAIL - {result.error_message}"
    
    return VerifyResponse(
        status=result.status.value,
        is_valid=result.is_valid,
        message=message,
        events_checked=result.events_checked,
        events_passed=result.events_passed,
        genesis_hash=result.genesis_hash,
        latest_hash=result.latest_hash,
        verified_at=result.verified_at.isoformat(),
    )


@router.get("/log", summary="Get audit events")
async def get_log(
    start: int = Query(0, ge=0, description="Start index"),
    limit: int = Query(50, ge=1, le=500, description="Maximum events to return"),
    action: str | None = Query(None, description="Filter by action type"),
):
    """
    Get audit log events.
    
    Events are returned in chronological order with hash chain information.
    """
    ledger = get_ledger()
    events = ledger.get_events(start_idx=start, limit=limit, action_filter=action)
    
    return {
        "events": [e.model_dump(mode="json") for e in events],
        "total": ledger.event_count,
        "start": start,
        "limit": limit,
    }


@router.get("/log/{event_id}", summary="Get single audit event")
async def get_event(event_id: str):
    """Get a specific audit event by ID"""
    ledger = get_ledger()
    event = ledger.get_event_by_id(event_id)
    
    if event is None:
        raise HTTPException(status_code=404, detail=f"Event not found: {event_id}")
    
    return event.model_dump(mode="json")


@router.get("/chain", summary="Get chain info")
async def get_chain_info():
    """Get audit chain metadata"""
    ledger = get_ledger()
    return ledger.get_chain_info()


@router.post("/log", summary="Log a new event")
async def log_event(request: LogEventRequest):
    """
    Log a new event to the audit ledger.
    
    The event is automatically hash-chained with the previous event.
    """
    ledger = get_ledger()
    
    if request.actor not in ("system", "user", "agent"):
        raise HTTPException(status_code=400, detail="Actor must be system, user, or agent")
    
    event = await ledger.log_event(
        action=request.action,
        actor=request.actor,
        payload=request.payload,
        actor_id=request.actor_id,
        data_ref=request.data_ref,
    )
    
    return {
        "event_id": event.event_id,
        "current_hash": event.current_hash,
        "logged": True,
    }


@router.post("/decision", summary="Log operator decision")
async def log_decision(request: LogDecisionRequest):
    """
    Log an operator action/decision.
    
    This creates an audit event for the decision with the operator's
    rationale captured.
    """
    ledger = get_ledger()
    
    event = await ledger.log_operator_action(
        operator_id=request.operator_id,
        action_type=request.action_type,
        action_description=request.action_description,
        rationale=request.rationale,
        incident_id=request.incident_id,
    )
    
    return {
        "event_id": event.event_id,
        "current_hash": event.current_hash,
        "anchor_tx_sig": event.anchor_tx_sig,
        "logged": True,
    }


@router.post("/receipt", summary="Create decision receipt")
async def create_receipt(request: CreateReceiptRequest):
    """
    Create an immutable decision receipt.
    
    This is the defensible record generated when an action is taken,
    capturing the complete context at decision time.
    """
    ledger = get_ledger()
    
    receipt = create_decision_receipt(
        operator_id=request.operator_id,
        action_type=request.action_type,
        action_description=request.action_description,
        rationale=request.rationale,
        uncertainty_snapshot=request.uncertainty_snapshot,
        active_contradictions=request.active_contradictions,
        evidence_refs=request.evidence_refs,
    )
    
    # Log the receipt
    event = await ledger.log_decision_receipt(receipt)
    
    return {
        "receipt_id": receipt.receipt_id,
        "content_hash": receipt.content_hash,
        "audit_event_id": event.event_id,
        "anchor_tx_sig": event.anchor_tx_sig,
        "receipt": receipt.model_dump(mode="json"),
    }


@router.get("/export", summary="Export full chain")
async def export_chain():
    """
    Export the complete audit chain.
    
    Returns all events with full hash chain for archival or verification.
    """
    ledger = get_ledger()
    chain = ledger.export_chain()
    return chain.model_dump(mode="json")
