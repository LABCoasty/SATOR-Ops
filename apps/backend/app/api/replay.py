"""
Replay API Routes

Endpoints for state reconstruction and timeline access.
"""

from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.replay import ReplayEngine
from app.core.replay.timeline import TimelineEventType, EventSeverity


router = APIRouter()

# Global replay engine instance
_replay_engine: ReplayEngine | None = None


def get_replay_engine() -> ReplayEngine:
    """Get or create the replay engine"""
    global _replay_engine
    if _replay_engine is None:
        _replay_engine = ReplayEngine()
    return _replay_engine


# === Request/Response Models ===

class StateAtTimeRequest(BaseModel):
    timestamp: str = Field(..., description="ISO8601 timestamp to reconstruct")


class StateAtTimeResponse(BaseModel):
    timestamp: str
    telemetry: dict[str, float | None]
    trust_scores: dict[str, float]
    active_reason_codes: dict[str, list[str]]
    unresolved_contradictions: list[str]
    operational_mode: str
    decision_clock_started: str | None = None


class TimelineEventResponse(BaseModel):
    event_id: str
    timestamp: str
    event_type: str
    severity: str
    summary: str
    details: dict
    related_tags: list[str]


# === Endpoints ===

@router.get("/state-at-t", response_model=StateAtTimeResponse, summary="Get state at timestamp")
async def get_state_at_time(
    timestamp: str = Query(..., description="ISO8601 timestamp to reconstruct")
):
    """
    Reconstruct the system belief state at a specific timestamp.
    
    Returns the exact state that would have been seen by an operator
    at that time, including:
    - Last known telemetry values for all tags
    - Trust scores and active reason codes
    - Unresolved contradictions
    - Operational mode (Observe/Decision)
    """
    engine = get_replay_engine()
    
    try:
        state = await engine.get_state_at_t(timestamp)
        return StateAtTimeResponse(**state)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid timestamp: {e}")


@router.get("/timeline/events", summary="Get timeline events")
async def get_timeline_events(
    start: str | None = Query(None, description="Start timestamp (ISO8601)"),
    end: str | None = Query(None, description="End timestamp (ISO8601)"),
    event_types: str | None = Query(None, description="Comma-separated event types"),
    severity: str | None = Query(None, description="Filter by severity"),
    tag_id: str | None = Query(None, description="Filter by related tag"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum events to return"),
):
    """
    Get timeline events with optional filtering.
    
    Events include alarms, trust drops, contradictions, and operator actions.
    """
    engine = get_replay_engine()
    
    type_list = None
    if event_types:
        type_list = [t.strip() for t in event_types.split(",")]
    
    events = await engine.get_timeline_events(
        start_iso=start,
        end_iso=end,
        event_types=type_list,
    )
    
    # Apply additional filters
    if severity:
        events = [e for e in events if e.get("severity") == severity]
    
    if tag_id:
        events = [e for e in events if tag_id in e.get("related_tags", [])]
    
    return {"events": events[:limit]}


@router.get("/timeline/markers", summary="Get timeline markers")
async def get_timeline_markers(
    start: str | None = Query(None, description="Start timestamp (ISO8601)"),
    end: str | None = Query(None, description="End timestamp (ISO8601)"),
):
    """
    Get simplified event markers for the timeline scrubber.
    
    Returns minimal data for rendering markers on the UI timeline.
    """
    engine = get_replay_engine()
    markers = engine.timeline_indexer.get_event_markers(start, end)
    return {"markers": markers}


@router.get("/timeline/event/{event_id}", summary="Get single event")
async def get_event(event_id: str):
    """Get a specific timeline event by ID"""
    engine = get_replay_engine()
    event = engine.timeline_indexer.get_event_by_id(event_id)
    
    if event is None:
        raise HTTPException(status_code=404, detail=f"Event not found: {event_id}")
    
    return event


@router.get("/timeline/stats", summary="Get timeline statistics")
async def get_timeline_stats():
    """Get statistics about timeline events"""
    engine = get_replay_engine()
    return engine.timeline_indexer.get_stats()


@router.post("/timeline/index", summary="Index a new event")
async def index_event(
    event_type: str = Query(..., description="Type of event"),
    severity: str = Query("info", description="Event severity"),
    summary: str = Query(..., description="Event summary"),
    tag_id: str | None = Query(None, description="Related tag ID"),
    details: dict = None,
):
    """
    Index a new event on the timeline.
    
    This is typically called internally when events occur, but can be
    used manually for testing.
    """
    engine = get_replay_engine()
    
    event_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "severity": severity,
        "summary": summary,
        "details": details or {},
        "related_tags": [tag_id] if tag_id else [],
    }
    
    event_id = engine.index_event(event_data)
    return {"event_id": event_id, "indexed": True}


@router.get("/snapshot", summary="Get reconstruction snapshot")
async def get_reconstruction_snapshot():
    """Get a debugging snapshot of the state reconstructor"""
    engine = get_replay_engine()
    return engine.state_reconstructor.get_state_snapshot()


@router.post("/clear", summary="Clear replay state")
async def clear_state():
    """Clear all cached state (for testing)"""
    engine = get_replay_engine()
    engine.state_reconstructor.clear()
    engine.timeline_indexer.clear()
    return {"cleared": True}
