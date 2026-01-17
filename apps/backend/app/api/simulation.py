"""
Simulation API Routes

Endpoints for controlling the simulation engine.
"""

from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.simulation import SimulationEngine, GOLDEN_SCENARIOS, get_available_scenarios
from app.models.simulation import FailureModeType, FailureInjection


router = APIRouter()

# Global simulation engine instance
_engine: SimulationEngine | None = None


def get_engine() -> SimulationEngine:
    """Get or create the simulation engine"""
    global _engine
    if _engine is None:
        from config import config
        _engine = SimulationEngine(seed=config.simulation_seed)
    return _engine


# === Request/Response Models ===

class StartScenarioRequest(BaseModel):
    scenario_id: str = Field(..., description="ID of the scenario to start")


class StartScenarioResponse(BaseModel):
    scenario_id: str
    name: str
    description: str
    duration_sec: float
    sensors: list[str]
    scheduled_failures: int
    started_at: str


class InjectFailureRequest(BaseModel):
    failure_type: FailureModeType = Field(..., description="Type of failure to inject")
    tag_id: str = Field(..., description="Sensor to affect")
    duration_sec: float | None = Field(None, description="Failure duration (None = permanent)")
    params: dict = Field(default_factory=dict, description="Failure-specific parameters")


class InjectFailureResponse(BaseModel):
    failure_id: str
    type: str
    tag_id: str
    started_at: float
    ends_at: float | None


class TelemetryResponse(BaseModel):
    timestamp: str
    values: dict[str, float | None]
    quality: dict[str, str]


# === Endpoints ===

@router.get("/scenarios", summary="List available scenarios")
async def list_scenarios():
    """Get list of available golden scenarios"""
    return {
        "scenarios": get_available_scenarios()
    }


@router.post("/start", response_model=StartScenarioResponse, summary="Start a scenario")
async def start_scenario(request: StartScenarioRequest):
    """
    Start a golden scenario.
    
    This initializes the simulation with the scenario's sensors and
    schedules all planned failures.
    """
    engine = get_engine()
    
    if request.scenario_id not in GOLDEN_SCENARIOS:
        raise HTTPException(
            status_code=404,
            detail=f"Scenario not found: {request.scenario_id}. Available: {list(GOLDEN_SCENARIOS.keys())}"
        )
    
    result = engine.scenario_runner.start(request.scenario_id)
    return StartScenarioResponse(**result)


@router.post("/stop", summary="Stop the current scenario")
async def stop_scenario():
    """Stop the currently running scenario"""
    engine = get_engine()
    
    if not engine.scenario_runner._active_scenario:
        raise HTTPException(status_code=400, detail="No active scenario")
    
    result = engine.scenario_runner.stop()
    return result


@router.get("/status", summary="Get scenario status")
async def get_status():
    """Get current scenario status"""
    engine = get_engine()
    state = engine.scenario_runner.get_current_state()
    
    if state is None:
        return {"active": False}
    
    return {
        "active": state.is_running,
        "scenario_id": state.scenario_id,
        "current_time_sec": state.current_time_sec,
        "is_paused": state.is_paused,
        "active_failures": state.active_failures,
    }


@router.post("/inject_failure", response_model=InjectFailureResponse, summary="Inject a failure")
async def inject_failure(request: InjectFailureRequest):
    """
    Inject a failure during live simulation.
    
    This allows manually triggering failures during the demo to show
    the system's reaction in real-time.
    """
    engine = get_engine()
    
    state = engine.scenario_runner.get_current_state()
    if state is None or not state.is_running:
        raise HTTPException(status_code=400, detail="No active scenario")
    
    result = engine.injector.inject(
        failure_type=request.failure_type,
        tag_id=request.tag_id,
        current_time_sec=state.current_time_sec,
        duration_sec=request.duration_sec,
        **request.params
    )
    
    return InjectFailureResponse(**result)


@router.get("/telemetry", summary="Get current telemetry")
async def get_telemetry(
    time_sec: float | None = Query(None, description="Specific time to query (defaults to current)")
):
    """
    Get current telemetry values for all sensors.
    
    Returns the latest values with failure effects applied.
    """
    engine = get_engine()
    
    state = engine.scenario_runner.get_current_state()
    if state is None:
        raise HTTPException(status_code=400, detail="No active scenario")
    
    query_time = time_sec if time_sec is not None else state.current_time_sec
    points = engine.scenario_runner.get_telemetry_at(query_time)
    
    values = {}
    quality = {}
    
    for point in points:
        values[point.tag_id] = point.value
        quality[point.tag_id] = point.quality.value
    
    return TelemetryResponse(
        timestamp=datetime.utcnow().isoformat(),
        values=values,
        quality=quality,
    )


@router.get("/telemetry/range", summary="Get telemetry for time range")
async def get_telemetry_range(
    start_sec: float = Query(..., description="Start time in seconds"),
    end_sec: float = Query(..., description="End time in seconds"),
):
    """Get telemetry for a time range"""
    engine = get_engine()
    
    if engine.scenario_runner._active_scenario is None:
        raise HTTPException(status_code=400, detail="No active scenario")
    
    data = engine.scenario_runner.get_telemetry_range(start_sec, end_sec)
    
    # Convert to serializable format
    result = {}
    for tag_id, points in data.items():
        result[tag_id] = [
            {
                "timestamp": p.timestamp.isoformat(),
                "value": p.value,
                "quality": p.quality.value,
            }
            for p in points
        ]
    
    return {"data": result}


@router.post("/advance", summary="Advance simulation time")
async def advance_time(delta_sec: float = Query(1.0, description="Seconds to advance")):
    """Advance the simulation time by a specified amount"""
    engine = get_engine()
    
    state = engine.scenario_runner.get_current_state()
    if state is None or not state.is_running:
        raise HTTPException(status_code=400, detail="No active scenario")
    
    engine.scenario_runner.advance_time(delta_sec)
    
    new_state = engine.scenario_runner.get_current_state()
    return {
        "new_time_sec": new_state.current_time_sec if new_state else 0,
        "is_running": new_state.is_running if new_state else False,
    }


@router.get("/timeline", summary="Get scenario timeline")
async def get_timeline():
    """Get the planned event timeline for the current scenario"""
    engine = get_engine()
    
    if engine.scenario_runner._active_scenario is None:
        raise HTTPException(status_code=400, detail="No active scenario")
    
    return {"events": engine.scenario_runner.get_scenario_timeline()}


@router.get("/failures/active", summary="Get active failures")
async def get_active_failures():
    """Get list of currently active failures"""
    engine = get_engine()
    return {"failures": engine.scenario_runner.get_active_failures()}
