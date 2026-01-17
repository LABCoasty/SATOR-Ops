"""
Agent Tools API Routes

Endpoints for the SATOR agent command interface.
These are the tools exposed via LeanMCP for agent interaction.
"""

from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.replay import ReplayEngine
from app.core.audit import AuditLedger, ChainVerifier
from app.models.mcp import SATOR_MCP_TOOLS, get_tools_as_json


router = APIRouter()


# === Shared instances ===

def get_replay_engine():
    from .replay import get_replay_engine as _get
    return _get()


def get_ledger():
    from .audit import get_ledger as _get
    return _get()


# === Response Models ===

class ContradictionResponse(BaseModel):
    contradiction_id: str
    timestamp: str
    primary_tag_id: str
    secondary_tag_ids: list[str]
    reason_code: str
    description: str
    values: dict[str, float | None]


class TrustExplanation(BaseModel):
    tag_id: str
    timestamp: str
    trust_score: float
    trust_state: str
    reason_codes: list[str]
    explanations: list[str]


class VerifyAuditResponse(BaseModel):
    status: str
    is_valid: bool
    events_checked: int
    root_hash: str


class StateSnapshot(BaseModel):
    timestamp: str
    telemetry: dict[str, float | None]
    trust_scores: dict[str, float]
    active_reason_codes: dict[str, list[str]]
    unresolved_contradictions: list[str]
    operational_mode: str


# === Endpoints (Agent Tools) ===

@router.get("/tools", summary="List available MCP tools")
async def list_tools():
    """
    List all available MCP tools.
    
    Returns the tool schemas for LeanMCP registration.
    """
    return {"tools": get_tools_as_json()}


@router.get("/contradictions", summary="List contradictions at time t")
async def list_contradictions(
    timestamp: str = Query(..., description="ISO8601 timestamp to query")
):
    """
    List active sensor contradictions at a given timestamp.
    
    Returns conflicts where sensors that should agree are in disagreement.
    This is a core agent tool for understanding evidence conflicts.
    """
    engine = get_replay_engine()
    
    try:
        state = await engine.get_state_at_t(timestamp)
        contradiction_ids = state.get("unresolved_contradictions", [])
        
        # In a full implementation, we'd fetch full contradiction details
        # For now, return the IDs
        return {
            "timestamp": timestamp,
            "contradictions": [
                {"contradiction_id": cid}
                for cid in contradiction_ids
            ],
            "count": len(contradiction_ids),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid timestamp: {e}")


@router.get("/explain-trust", response_model=TrustExplanation, summary="Explain trust score")
async def explain_trust_score(
    tag_id: str = Query(..., description="Sensor/tag identifier"),
    timestamp: str | None = Query(None, description="Timestamp (defaults to current)"),
):
    """
    Explain the trust score and active reason codes for a sensor.
    
    Provides a detailed breakdown of why the sensor is trusted, degraded,
    or quarantined. This is the agent's primary tool for understanding
    sensor reliability.
    """
    engine = get_replay_engine()
    
    query_time = timestamp or datetime.utcnow().isoformat()
    
    try:
        state = await engine.get_state_at_t(query_time)
        
        trust_score = state.get("trust_scores", {}).get(tag_id, 1.0)
        reason_codes = state.get("active_reason_codes", {}).get(tag_id, [])
        
        # Determine trust state from score
        from config import config
        if trust_score >= config.trust_degraded_threshold:
            trust_state = "trusted"
        elif trust_score >= config.trust_untrusted_threshold:
            trust_state = "degraded"
        elif trust_score >= config.trust_quarantine_threshold:
            trust_state = "untrusted"
        else:
            trust_state = "quarantined"
        
        # Generate human-readable explanations for each reason code
        explanations = []
        reason_code_explanations = {
            "RC01": "Data gaps detected - missing bursts of readings",
            "RC02": "Stale stream - no updates received recently",
            "RC05": "Range violation - values outside physical limits",
            "RC06": "Rate of change violation - sudden implausible spike",
            "RC07": "Flatline detected - sensor stuck at constant value",
            "RC09": "Drift detected - diverging from peer sensors",
            "RC10": "Redundancy conflict - disagrees with related sensors",
            "RC11": "Physics contradiction - violates physical invariants",
        }
        
        for rc in reason_codes:
            if rc in reason_code_explanations:
                explanations.append(f"{rc}: {reason_code_explanations[rc]}")
            else:
                explanations.append(f"{rc}: Unknown reason code")
        
        if not explanations:
            explanations.append("No active issues - sensor is fully trusted")
        
        return TrustExplanation(
            tag_id=tag_id,
            timestamp=query_time,
            trust_score=trust_score,
            trust_state=trust_state,
            reason_codes=reason_codes,
            explanations=explanations,
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid timestamp: {e}")


@router.get("/verify-audit", response_model=VerifyAuditResponse, summary="Verify audit chain")
async def verify_audit(
    start_event_id: str | None = Query(None, description="Starting event ID"),
    end_event_id: str | None = Query(None, description="Ending event ID"),
):
    """
    Verify the integrity of the hash-chained audit log.
    
    Returns verification status and any detected tampering.
    This is the agent's tool for confirming the audit trail is intact.
    """
    ledger = get_ledger()
    events = ledger.get_events()
    
    # Filter by event IDs if specified
    if start_event_id or end_event_id:
        start_idx = 0
        end_idx = len(events)
        
        for i, event in enumerate(events):
            if start_event_id and event.event_id == start_event_id:
                start_idx = i
            if end_event_id and event.event_id == end_event_id:
                end_idx = i + 1
        
        events = events[start_idx:end_idx]
    
    verifier = ChainVerifier()
    result = verifier.verify_chain(events)
    
    return VerifyAuditResponse(
        status="PASS" if result.is_valid else "FAIL",
        is_valid=result.is_valid,
        events_checked=result.events_checked,
        root_hash=result.genesis_hash,
    )


@router.get("/state-at-t", response_model=StateSnapshot, summary="Get state at timestamp")
async def get_state_at_t(
    timestamp: str = Query(..., description="ISO8601 timestamp to reconstruct")
):
    """
    Reconstruct the complete system belief state at a specific timestamp.
    
    Returns telemetry values, trust scores, active contradictions,
    and operational mode. This is the agent's primary tool for
    historical queries ("What happened at 2:00 PM?").
    """
    engine = get_replay_engine()
    
    try:
        state = await engine.get_state_at_t(timestamp)
        return StateSnapshot(**state)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid timestamp: {e}")


@router.get("/incident/{incident_id}/summary", summary="Get incident summary")
async def get_incident_summary(incident_id: str):
    """
    Get a summary of an incident including timeline of events
    and key contradictions.
    
    This helps the agent quickly understand an incident's context.
    """
    ledger = get_ledger()
    
    # Find events related to this incident
    all_events = ledger.get_events()
    incident_events = [
        e for e in all_events
        if e.data_ref == incident_id or 
           e.payload.get("incident_id") == incident_id
    ]
    
    if not incident_events:
        raise HTTPException(status_code=404, detail=f"Incident not found: {incident_id}")
    
    # Build summary
    timeline = []
    contradictions = []
    
    for event in incident_events:
        timeline.append({
            "timestamp": event.timestamp.isoformat(),
            "action": event.action,
            "actor": event.actor,
            "summary": event.payload.get("description", event.action),
        })
        
        if event.action == "contradiction_detected":
            contradictions.append(event.payload)
    
    return {
        "incident_id": incident_id,
        "event_count": len(incident_events),
        "timeline": timeline,
        "top_contradictions": contradictions[:5],
        "first_event": incident_events[0].timestamp.isoformat() if incident_events else None,
        "last_event": incident_events[-1].timestamp.isoformat() if incident_events else None,
    }


@router.get("/decision-receipt/{receipt_id}", summary="Get decision receipt")
async def get_decision_receipt(receipt_id: str):
    """
    Retrieve a decision receipt by ID.
    
    Returns the complete defensible record of a decision.
    """
    ledger = get_ledger()
    
    # Find the audit event for this receipt
    all_events = ledger.get_events(action_filter="decision_receipt")
    
    for event in all_events:
        if event.payload.get("receipt_id") == receipt_id:
            return {
                "receipt_id": receipt_id,
                "audit_event_id": event.event_id,
                "timestamp": event.timestamp.isoformat(),
                "content_hash": event.payload.get("content_hash"),
                "operator_id": event.payload.get("operator_id"),
                "action_type": event.payload.get("action_type"),
                "current_hash": event.current_hash,
            }
    
    raise HTTPException(status_code=404, detail=f"Receipt not found: {receipt_id}")
