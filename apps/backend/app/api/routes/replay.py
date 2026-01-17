"""
Replay API Routes - Endpoints for temporal state reconstruction.

Provides:
- GET /state-at: Get complete system state at any timestamp
- GET /markers: Get timeline markers (with clustering support)
- GET /confidence-band: Get confidence ribbon data
- GET /incident/{id}: Get full incident timeline
"""

from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException

from app.models.temporal import (
    AtTimeState,
    TimelineMarker,
    MarkerCluster,
    ConfidencePoint,
    IncidentTimeline,
)
from app.core.replay_engine import replay_engine


router = APIRouter()


# =============================================================================
# State at Time t
# =============================================================================

@router.get("/state-at", response_model=AtTimeState)
async def get_state_at(
    t: str = Query(..., description="ISO timestamp (e.g., 2026-01-14T10:01:00)"),
):
    """
    Get complete system state at timestamp t.
    
    Returns ONLY information that was available at time t.
    Future evidence is NOT included (core promise).
    
    Response includes:
    - claim: One sentence describing active belief
    - confirmation_status: confirmed/unconfirmed/conflicting
    - confidence: high/medium/low
    - trust_snapshot: Per-sensor trust states
    - contradictions: Active contradictions (not resolved)
    - posture: monitor/verify/escalate/contain/defer
    - operator_history: Actions taken up to time t
    - receipt_status: Receipt creation status
    """
    try:
        timestamp = datetime.fromisoformat(t)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid timestamp format: {t}")
    
    # Ensure data is loaded
    if not replay_engine._events:
        replay_engine.load_all()
    
    return replay_engine.get_state_at(timestamp)


# =============================================================================
# Timeline Markers
# =============================================================================

@router.get("/markers", response_model=List[TimelineMarker])
async def get_markers(
    start: Optional[str] = Query(None, description="Start time (ISO)"),
    end: Optional[str] = Query(None, description="End time (ISO)"),
    zoom: int = Query(1, ge=1, le=3, description="Zoom level: 1=full, 2=minutes, 3=seconds"),
):
    """
    Get timeline markers for display.
    
    Markers include:
    - Alarms
    - Trust state changes
    - Contradiction appearances
    - Operator actions
    - Receipt creations
    - Mode changes
    """
    start_dt = datetime.fromisoformat(start) if start else None
    end_dt = datetime.fromisoformat(end) if end else None
    
    return replay_engine.get_markers(start_dt, end_dt, zoom)


@router.get("/markers/clustered", response_model=List[MarkerCluster])
async def get_clustered_markers(
    start: str = Query(..., description="Start time (ISO)"),
    end: str = Query(..., description="End time (ISO)"),
    max_clusters: int = Query(10, ge=3, le=50, description="Max clusters"),
):
    """
    Get clustered markers for zoomed-out view.
    
    When zoomed out, markers are grouped into clusters like:
    "6 Trust Updates" or "3 Contradictions"
    """
    try:
        start_dt = datetime.fromisoformat(start)
        end_dt = datetime.fromisoformat(end)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid timestamp: {e}")
    
    return replay_engine.get_clustered_markers(start_dt, end_dt, max_clusters)


# =============================================================================
# Confidence Ribbon
# =============================================================================

@router.get("/confidence-band", response_model=List[ConfidencePoint])
async def get_confidence_band(
    start: Optional[str] = Query(None, description="Start time (ISO)"),
    end: Optional[str] = Query(None, description="End time (ISO)"),
    resolution: int = Query(20, ge=5, le=100, description="Number of points"),
):
    """
    Get confidence ribbon data for timeline background.
    
    Returns evenly spaced points showing confidence level (high/medium/low)
    over time, used to visualize "why the operator hesitated."
    """
    start_dt = datetime.fromisoformat(start) if start else None
    end_dt = datetime.fromisoformat(end) if end else None
    
    return replay_engine.get_confidence_band(start_dt, end_dt, resolution)


# =============================================================================
# Full Incident Timeline
# =============================================================================

@router.get("/incident/{incident_id}", response_model=IncidentTimeline)
async def get_incident_timeline(incident_id: str):
    """
    Get full incident timeline.
    
    Returns complete timeline with:
    - All markers
    - Confidence band
    - Summary statistics
    """
    return replay_engine.get_incident_timeline(incident_id)


# =============================================================================
# Data Management
# =============================================================================

@router.post("/reload")
async def reload_data():
    """Reload all data from CSV/JSON files."""
    replay_engine.load_all()
    return {
        "status": "ok",
        "events": len(replay_engine._events),
        "contradictions": len(replay_engine._contradictions),
        "receipts": len(replay_engine._receipts),
    }


@router.get("/bounds")
async def get_incident_bounds():
    """Get incident time bounds."""
    if not replay_engine._events:
        replay_engine.load_all()
    
    return {
        "start": replay_engine._incident_start.isoformat() if replay_engine._incident_start else None,
        "end": replay_engine._incident_end.isoformat() if replay_engine._incident_end else None,
        "duration_sec": (
            (replay_engine._incident_end - replay_engine._incident_start).total_seconds()
            if replay_engine._incident_start and replay_engine._incident_end
            else 0
        ),
    }
