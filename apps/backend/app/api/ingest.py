"""
Ingest API – Overshoot.ai JSON → CSV for video disaster scenario.

Accept structured JSON from Overshoot RealtimeVision (outputSchema) and append
to video_disaster_telemetry.csv and video_disaster_events.csv. Optionally
start the video_disaster run on first ingest.

Frontend: use Overshoot SDK (https://docs.overshoot.ai/) with outputSchema
matching the schema at GET /ingest/overshoot/schema, then POST each result
to /ingest/overshoot.
"""

from fastapi import APIRouter, Body, HTTPException

from app.api.simulation import get_engine

router = APIRouter()


# OutputSchema for Overshoot RealtimeVision – use as outputSchema in JS
OVERSHOOT_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "timestamp_ms": {"type": "integer", "description": "Window timestamp (epoch ms)"},
        "person_count": {"type": "integer", "minimum": 0, "default": 0},
        "water_level": {"type": "number", "minimum": 0, "maximum": 100, "default": 0},
        "fire_detected": {"type": "boolean", "default": False},
        "smoke_level": {"type": "string", "enum": ["none", "light", "medium", "dense"], "default": "none"},
        "structural_damage": {"type": "string", "enum": ["none", "moderate", "severe"], "default": "none"},
        "injured_detected": {"type": "boolean", "default": False},
        "disaster_type": {"type": "string"},
        "location_id": {"type": "string"},
        "objects": {"type": "array", "items": {"type": "object", "properties": {"label": {}, "confidence": {}}}},
        "notes": {"type": "string"},
    },
    "required": ["timestamp_ms", "person_count", "fire_detected"],
}


@router.post("/overshoot", summary="Ingest Overshoot JSON")
async def ingest_overshoot(body: dict | list[dict] = Body(..., description="One or more Overshoot disaster records")):
    """
    Ingest Overshoot.ai RealtimeVision JSON. Converts to telemetry and events
    CSV rows and appends to the video_disaster run. If the run is not started,
    it is started on first ingest. Start explicitly via POST /simulation/start
    with scenario_id=video_disaster to reset/begin a new run.
    """
    engine = get_engine()
    vm = engine.video_manager
    if not vm._running:
        vm.start()
    try:
        out = vm.ingest(body)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return out


@router.get("/overshoot/schema", summary="Overshoot outputSchema")
async def get_overshoot_schema():
    """Return the JSON outputSchema to use with Overshoot RealtimeVision."""
    return {"outputSchema": OVERSHOOT_OUTPUT_SCHEMA}


@router.get("/video/status", summary="Video disaster run status")
async def get_video_status():
    """Status of the current video disaster run."""
    engine = get_engine()
    vm = engine.video_manager
    state = vm.get_current_state()
    if state is None:
        return {"running": False, "time_sec": 0.0, "has_data": False}
    return {
        "running": state.get("is_running", False),
        "time_sec": state.get("current_time_sec", 0.0),
        "has_data": vm._current_time_sec > 0,
    }
