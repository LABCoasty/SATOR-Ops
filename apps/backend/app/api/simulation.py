"""
Simulation API Routes

Endpoints for controlling the simulation engine and enhanced scenario simulations.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field

from app.core.simulation import SimulationEngine, GOLDEN_SCENARIOS, get_available_scenarios
from app.models.simulation import FailureModeType, FailureInjection
from app.services.scenario_simulator import (
    create_simulator,
    get_simulator,
    get_all_simulators,
    ScenarioEvent,
    TelemetryUpdate,
    DecisionRequest,
)


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
    schedules all planned failures. For video_disaster, initializes
    the Overshoot ingest run (POST JSON to /ingest/overshoot).
    """
    engine = get_engine()

    if request.scenario_id == "video_disaster":
        engine._video_mode = True
        engine.video_manager.start()
        return StartScenarioResponse(
            scenario_id="video_disaster",
            name="Video Disaster (Live)",
            description="Disaster scenario driven by live video via Overshoot.ai. POST Overshoot JSON to /ingest/overshoot.",
            duration_sec=0.0,
            sensors=[
                "video_person_count", "video_water_level", "video_fire_detected",
                "video_smoke_level", "video_structural_damage", "video_injured_detected",
            ],
            scheduled_failures=0,
            started_at=datetime.utcnow().isoformat(),
        )

    engine._video_mode = False
    if request.scenario_id not in GOLDEN_SCENARIOS:
        raise HTTPException(
            status_code=404,
            detail=f"Scenario not found: {request.scenario_id}. Available: {list(GOLDEN_SCENARIOS.keys()) + ['video_disaster']}"
        )

    result = engine.scenario_runner.start(request.scenario_id)
    return StartScenarioResponse(**result)


@router.post("/stop", summary="Stop the current scenario")
async def stop_scenario():
    """Stop the currently running scenario"""
    engine = get_engine()

    if getattr(engine, "_video_mode", False):
        engine.video_manager.stop()
        engine._video_mode = False
        return {"scenario_id": "video_disaster", "stopped": True}

    if not engine.scenario_runner._active_scenario:
        raise HTTPException(status_code=400, detail="No active scenario")

    result = engine.scenario_runner.stop()
    return result


@router.get("/status", summary="Get scenario status")
async def get_status():
    """Get current scenario status"""
    engine = get_engine()

    if getattr(engine, "_video_mode", False):
        state = engine.video_manager.get_current_state()
        if state is None:
            return {"active": False}
        return {
            "active": state.get("is_running", False),
            "scenario_id": state.get("scenario_id", "video_disaster"),
            "current_time_sec": state.get("current_time_sec", 0.0),
            "is_paused": state.get("is_paused", False),
            "active_failures": state.get("active_failures", []),
        }

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
    the system's reaction in real-time. Not supported for video_disaster.
    """
    engine = get_engine()

    if getattr(engine, "_video_mode", False):
        raise HTTPException(status_code=400, detail="Cannot inject failures in video_disaster scenario")

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

    Returns the latest values with failure effects applied. For video_disaster,
    returns latest ingested Overshoot-derived telemetry at or before query time.
    """
    engine = get_engine()

    if getattr(engine, "_video_mode", False):
        state = engine.video_manager.get_current_state()
        if state is None:
            raise HTTPException(status_code=400, detail="No active scenario")
        query_time = time_sec if time_sec is not None else state.get("current_time_sec", 0.0)
        points = engine.video_manager.get_telemetry_at(query_time)
        values = {p.tag_id: p.value for p in points}
        quality = {p.tag_id: p.quality.value for p in points}
        return TelemetryResponse(
            timestamp=datetime.utcnow().isoformat(),
            values=values,
            quality=quality,
        )

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

    if getattr(engine, "_video_mode", False):
        if engine.video_manager.get_current_state() is None:
            raise HTTPException(status_code=400, detail="No active scenario")
        data = engine.video_manager.get_telemetry_range(start_sec, end_sec)
        return {"data": data}

    if engine.scenario_runner._active_scenario is None:
        raise HTTPException(status_code=400, detail="No active scenario")
    data = engine.scenario_runner.get_telemetry_range(start_sec, end_sec)
    result = {}
    for tag_id, points in data.items():
        result[tag_id] = [
            {"timestamp": p.timestamp.isoformat(), "value": p.value, "quality": p.quality.value}
            for p in points
        ]
    return {"data": result}


@router.post("/advance", summary="Advance simulation time")
async def advance_time(delta_sec: float = Query(1.0, description="Seconds to advance")):
    """Advance the simulation time by a specified amount"""
    engine = get_engine()

    if getattr(engine, "_video_mode", False):
        state = engine.video_manager.get_current_state()
        if state is None or not state.get("is_running", False):
            raise HTTPException(status_code=400, detail="No active scenario")
        engine.video_manager.advance_time(delta_sec)
        s = engine.video_manager.get_current_state()
        return {"new_time_sec": s.get("current_time_sec", 0.0), "is_running": s.get("is_running", False)}

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

    if getattr(engine, "_video_mode", False):
        if engine.video_manager.get_current_state() is None:
            raise HTTPException(status_code=400, detail="No active scenario")
        return {"events": engine.video_manager.get_scenario_timeline()}

    if engine.scenario_runner._active_scenario is None:
        raise HTTPException(status_code=400, detail="No active scenario")
    return {"events": engine.scenario_runner.get_scenario_timeline()}


@router.get("/failures/active", summary="Get active failures")
async def get_active_failures():
    """Get list of currently active failures"""
    engine = get_engine()
    if getattr(engine, "_video_mode", False):
        return {"failures": []}
    return {"failures": engine.scenario_runner.get_active_failures()}


# ============================================================================
# Enhanced Scenario Simulation with Decision Events (60-second scenarios)
# ============================================================================

# Storage for simulation events
_enhanced_sim_events: Dict[str, List[dict]] = {}
_enhanced_sim_telemetry: Dict[str, TelemetryUpdate] = {}
_enhanced_sim_decisions: Dict[str, List[DecisionRequest]] = {}


class EnhancedStartRequest(BaseModel):
    scenario_type: str = Field(..., description="'scenario1' or 'scenario2'")
    operator_id: str = Field(default="default_operator")


class EnhancedStateResponse(BaseModel):
    simulation_id: str
    status: str
    current_time_sec: float
    total_duration_sec: float
    progress_percent: float
    trust_score: float
    phase: str
    events_triggered: int
    pending_decisions: int
    decisions_made: int


class EnhancedDecisionResponse(BaseModel):
    decision_id: str
    event_id: str
    time_sec: float
    title: str
    description: str
    severity: str
    decision_type: str
    options: List[str]
    prompt: str
    expires_in_sec: Optional[float] = None
    responded: bool


class DecisionSubmitRequest(BaseModel):
    response: str


@router.post("/enhanced/start", summary="Start enhanced 60-second scenario")
async def start_enhanced_scenario(
    request: EnhancedStartRequest,
    background_tasks: BackgroundTasks
):
    """
    Start an enhanced scenario simulation that runs for ~60 seconds.
    
    Features:
    - Continuous telemetry updates every 2 seconds
    - Decision events at critical time points
    - Trust score tracking
    - Auto-timeout for unanswered decisions
    """
    try:
        simulator = create_simulator(request.scenario_type)
        sim_id = simulator.scenario_id
        
        # Initialize storage
        _enhanced_sim_events[sim_id] = []
        _enhanced_sim_decisions[sim_id] = []
        
        # Register callbacks
        def on_event(event: ScenarioEvent):
            _enhanced_sim_events[sim_id].append({
                "event_id": event.event_id,
                "time_sec": event.time_sec,
                "title": event.title,
                "description": event.description,
                "severity": event.severity.value,
                "requires_decision": event.requires_decision,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        def on_telemetry(telemetry: TelemetryUpdate):
            _enhanced_sim_telemetry[sim_id] = telemetry
        
        def on_decision(decision: DecisionRequest):
            _enhanced_sim_decisions[sim_id].append(decision)
        
        simulator.on_event(on_event)
        simulator.on_telemetry(on_telemetry)
        simulator.on_decision_required(on_decision)
        
        # Start simulation in background
        background_tasks.add_task(simulator.start)
        
        return {
            "success": True,
            "simulation_id": sim_id,
            "message": "Enhanced simulation started. Duration: 60 seconds with decision events.",
            "scenario_type": request.scenario_type
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/enhanced/{simulation_id}/state", response_model=EnhancedStateResponse)
async def get_enhanced_state(simulation_id: str):
    """Get current state of an enhanced simulation."""
    simulator = get_simulator(simulation_id)
    if not simulator:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    state = simulator.state
    progress = (state.current_time_sec / state.total_duration_sec) * 100
    
    return EnhancedStateResponse(
        simulation_id=simulation_id,
        status=state.status,
        current_time_sec=state.current_time_sec,
        total_duration_sec=state.total_duration_sec,
        progress_percent=min(100, progress),
        trust_score=state.trust_score,
        phase=state.phase,
        events_triggered=len(state.events_triggered),
        pending_decisions=len(state.pending_decisions),
        decisions_made=state.decisions_made
    )


@router.get("/enhanced/{simulation_id}/events")
async def get_enhanced_events(simulation_id: str, since_sec: float = 0):
    """Get events that have occurred in the enhanced simulation."""
    if simulation_id not in _enhanced_sim_events:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    events = _enhanced_sim_events.get(simulation_id, [])
    filtered = [e for e in events if e["time_sec"] >= since_sec]
    
    return {"events": filtered}


@router.get("/enhanced/{simulation_id}/telemetry")
async def get_enhanced_telemetry(simulation_id: str):
    """Get current telemetry data from enhanced simulation."""
    if simulation_id not in _enhanced_sim_telemetry:
        return {
            "time_sec": 0,
            "channels": {},
            "anomalies": [],
            "trust_score": 0.95
        }
    
    telemetry = _enhanced_sim_telemetry[simulation_id]
    return {
        "time_sec": telemetry.time_sec,
        "channels": telemetry.channels,
        "anomalies": telemetry.anomalies,
        "trust_score": telemetry.trust_score
    }


@router.get("/enhanced/{simulation_id}/decisions", response_model=List[EnhancedDecisionResponse])
async def get_enhanced_decisions(simulation_id: str):
    """Get pending decisions that require operator response."""
    simulator = get_simulator(simulation_id)
    if not simulator:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    pending = simulator.get_pending_decisions()
    now = datetime.utcnow()
    
    return [
        EnhancedDecisionResponse(
            decision_id=d.decision_id,
            event_id=d.event_id,
            time_sec=d.time_sec,
            title=d.title,
            description=d.description,
            severity=d.severity.value,
            decision_type=d.decision_type.value,
            options=d.options,
            prompt=d.prompt,
            expires_in_sec=(d.expires_at - now).total_seconds() if d.expires_at and d.expires_at > now else None,
            responded=d.responded
        )
        for d in pending
        if not d.responded
    ]


@router.post("/enhanced/{simulation_id}/decisions/{decision_id}")
async def submit_enhanced_decision(
    simulation_id: str,
    decision_id: str,
    request: DecisionSubmitRequest
):
    """Submit an operator decision for the enhanced simulation."""
    simulator = get_simulator(simulation_id)
    if not simulator:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    success = await simulator.submit_decision(decision_id, request.response)
    
    if not success:
        raise HTTPException(status_code=404, detail="Decision not found or already responded")
    
    return {
        "success": True,
        "message": "Decision recorded",
        "decision_id": decision_id,
        "response": request.response,
        "new_trust_score": simulator.state.trust_score
    }


@router.post("/enhanced/{simulation_id}/stop")
async def stop_enhanced_simulation(simulation_id: str):
    """Stop an enhanced simulation."""
    simulator = get_simulator(simulation_id)
    if not simulator:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    await simulator.stop()
    
    return {
        "success": True,
        "message": "Simulation stopped",
        "final_state": {
            "trust_score": simulator.state.trust_score,
            "decisions_made": simulator.state.decisions_made,
            "events_triggered": len(simulator.state.events_triggered)
        }
    }


@router.get("/enhanced/active")
async def list_enhanced_simulations():
    """List all active enhanced simulations."""
    simulators = get_all_simulators()
    
    return {
        "simulations": [
            {
                "simulation_id": sim_id,
                "status": sim.state.status,
                "progress_percent": (sim.state.current_time_sec / sim.state.total_duration_sec) * 100,
                "trust_score": sim.state.trust_score,
                "pending_decisions": len(sim.state.pending_decisions)
            }
            for sim_id, sim in simulators.items()
        ]
    }
