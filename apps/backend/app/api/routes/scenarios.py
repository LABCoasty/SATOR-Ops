"""
Scenarios API Routes - Manage scenario simulation and state.

Endpoints:
- GET /scenarios - List available scenarios
- GET /scenarios/{id} - Get scenario details
- POST /scenarios/{id}/start - Start a scenario simulation
- POST /scenarios/{id}/stop - Stop a scenario
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

from ...services.data_loader import get_data_loader, ScenarioData
from ...services.incident_manager import (
    get_incident_manager, 
    Incident, 
    IncidentState,
    IncidentSeverity
)
from ...services.audit_logger import get_audit_logger
from ...services.operator_questionnaire import get_questionnaire_service
from ...core.decision_engine import get_decision_engine
from ...integrations.overshoot import get_overshoot_client
from ...db import SimulationRepository, get_db


router = APIRouter(prefix="/scenarios", tags=["scenarios"])


# ============================================================================
# Models
# ============================================================================

class ScenarioType(str, Enum):
    FIXED = "fixed"
    LIVE = "live"


class ScenarioInfo(BaseModel):
    """Scenario information for listing."""
    scenario_id: str
    name: str
    description: str
    scenario_type: ScenarioType
    duration_seconds: Optional[float] = None
    available: bool = True


class ScenarioStatus(BaseModel):
    """Current status of a scenario."""
    scenario_id: str
    status: str  # idle, running, completed
    started_at: Optional[datetime] = None
    current_time_sec: float = 0.0
    active_incidents: int = 0
    mode: str = "data_ingest"  # data_ingest, decision, artifact


class StartScenarioRequest(BaseModel):
    """Request to start a scenario."""
    operator_id: str
    options: Optional[Dict[str, Any]] = None


class StartScenarioResponse(BaseModel):
    """Response from starting a scenario."""
    success: bool
    scenario_id: str
    status: ScenarioStatus
    message: str


# ============================================================================
# Scenario State
# ============================================================================

_scenario_states: Dict[str, ScenarioStatus] = {}

# MongoDB repository (if enabled)
_simulation_repo: Optional[SimulationRepository] = None
if get_db().enabled:
    try:
        _simulation_repo = SimulationRepository()
    except Exception as e:
        print(f"Warning: Could not initialize SimulationRepository: {e}")


def _persist_scenario_state(scenario_id: str, status: ScenarioStatus):
    """Persist scenario state to MongoDB if enabled"""
    if _simulation_repo:
        try:
            state_dict = status.model_dump()
            # Convert datetime to ISO string for MongoDB
            if state_dict.get("started_at"):
                state_dict["started_at"] = state_dict["started_at"].isoformat()
            _simulation_repo.upsert_scenario_state(scenario_id, state_dict)
        except Exception as e:
            print(f"Warning: Failed to persist scenario state to MongoDB: {e}")


# ============================================================================
# Endpoints
# ============================================================================

@router.get("", response_model=List[ScenarioInfo])
async def list_scenarios():
    """
    List all available scenarios.
    
    Returns both fixed (static data) and live (Overshoot) scenarios.
    """
    scenarios = [
        ScenarioInfo(
            scenario_id="fixed-valve-incident",
            name="The Mismatched Valve Incident",
            description=(
                "A fixed scenario demonstrating sensor contradictions and "
                "decision-making under uncertainty. Uses static CSV/JSON data."
            ),
            scenario_type=ScenarioType.FIXED,
            duration_seconds=180.0
        ),
        ScenarioInfo(
            scenario_id="live-vision-demo",
            name="Live Vision Demo",
            description=(
                "Real-time scenario using Overshoot AI vision to process "
                "video feed and cross-validate against telemetry."
            ),
            scenario_type=ScenarioType.LIVE,
            duration_seconds=None  # Continuous
        )
    ]
    
    return scenarios


@router.get("/{scenario_id}", response_model=ScenarioInfo)
async def get_scenario(scenario_id: str):
    """Get details for a specific scenario."""
    scenarios = await list_scenarios()
    
    for scenario in scenarios:
        if scenario.scenario_id == scenario_id:
            return scenario
    
    raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found")


@router.get("/{scenario_id}/status", response_model=ScenarioStatus)
async def get_scenario_status(scenario_id: str):
    """Get current status of a scenario."""
    # Check in-memory first
    if scenario_id in _scenario_states:
        return _scenario_states[scenario_id]
    
    # Try to load from MongoDB if enabled
    if _simulation_repo:
        try:
            state_dict = _simulation_repo.get_scenario_state(scenario_id)
            if state_dict:
                # Convert back from MongoDB format
                if state_dict.get("started_at"):
                    state_dict["started_at"] = datetime.fromisoformat(state_dict["started_at"])
                status = ScenarioStatus(**state_dict)
                _scenario_states[scenario_id] = status  # Cache in memory
                return status
        except Exception as e:
            print(f"Warning: Failed to load scenario state from MongoDB: {e}")
    
    return ScenarioStatus(
        scenario_id=scenario_id,
        status="idle"
    )


@router.post("/{scenario_id}/start", response_model=StartScenarioResponse)
async def start_scenario(
    scenario_id: str,
    request: StartScenarioRequest,
    background_tasks: BackgroundTasks
):
    """
    Start a scenario simulation.
    
    For fixed scenarios, loads static data and creates incidents.
    For live scenarios, starts listening for Overshoot vision data.
    """
    # Check if scenario exists
    scenario = await get_scenario(scenario_id)
    
    # Check if already running
    if scenario_id in _scenario_states and _scenario_states[scenario_id].status == "running":
        raise HTTPException(
            status_code=400, 
            detail=f"Scenario '{scenario_id}' is already running"
        )
    
    # Initialize status
    status = ScenarioStatus(
        scenario_id=scenario_id,
        status="running",
        started_at=datetime.utcnow(),
        mode="data_ingest"
    )
    _scenario_states[scenario_id] = status
    
    # Persist to MongoDB
    _persist_scenario_state(scenario_id, status)
    
    # Log scenario start
    audit_logger = get_audit_logger()
    audit_logger.log(
        event_type="scenario_started",
        summary=f"Scenario '{scenario.name}' started by operator",
        data={"scenario_type": scenario.scenario_type, "operator_id": request.operator_id},
        scenario_id=scenario_id,
        operator_id=request.operator_id
    )
    
    if scenario.scenario_type == ScenarioType.FIXED:
        # Start fixed scenario in background
        background_tasks.add_task(
            _run_fixed_scenario,
            scenario_id,
            request.operator_id
        )
        message = "Fixed scenario started - loading static data"
    else:
        # Start live scenario - just mark as waiting for vision
        message = "Live scenario started - awaiting Overshoot vision data"
    
    return StartScenarioResponse(
        success=True,
        scenario_id=scenario_id,
        status=status,
        message=message
    )


@router.post("/{scenario_id}/stop")
async def stop_scenario(scenario_id: str):
    """Stop a running scenario."""
    if scenario_id not in _scenario_states:
        raise HTTPException(status_code=404, detail="Scenario not running")
    
    status = _scenario_states[scenario_id]
    status.status = "stopped"
    
    # Persist to MongoDB
    _persist_scenario_state(scenario_id, status)
    
    # Log scenario stop
    audit_logger = get_audit_logger()
    audit_logger.log(
        event_type="scenario_ended",
        summary=f"Scenario stopped",
        scenario_id=scenario_id
    )
    
    return {"success": True, "message": "Scenario stopped"}


@router.post("/{scenario_id}/generate-artifact")
async def generate_artifact(scenario_id: str):
    """
    Generate a decision artifact from a completed scenario.
    
    This creates an artifact containing all evidence, decisions,
    and trust receipts from the scenario run.
    """
    from ...services.artifact_builder import get_artifact_builder
    
    artifact_builder = get_artifact_builder()
    incident_manager = get_incident_manager()
    decision_engine = get_decision_engine()
    audit_logger = get_audit_logger()
    data_loader = get_data_loader()
    
    # Get scenario status
    status = _scenario_states.get(scenario_id)
    
    # Get incidents for this scenario
    incidents = incident_manager.get_incidents_by_scenario(scenario_id)
    
    if not incidents:
        # Create a demo artifact if no incidents exist
        artifact_id = f"ART-{datetime.utcnow().strftime('%Y-%m%d')}-{scenario_id[:8]}"
        
        # Build artifact data from scenario
        artifact_data = {
            "artifact_id": artifact_id,
            "incident_id": f"INC-{scenario_id}",
            "scenario_id": scenario_id,
            "title": f"Decision Artifact for {scenario_id}",
            "created_at": datetime.utcnow().isoformat(),
            "incident": {
                "incident_id": f"INC-{scenario_id}",
                "title": "Scenario Completion Artifact",
                "scope": scenario_id,
                "severity": "medium",
                "time_window": {
                    "start": status.started_at.isoformat() if status and status.started_at else datetime.utcnow().isoformat(),
                    "end": datetime.utcnow().isoformat()
                }
            },
            "evidence": [],
            "contradictions": [],
            "trust_receipt": {
                "overall_trust_score": 0.85,
                "trust_level": "high",
                "sensor_scores": {},
                "reason_codes": ["scenario_complete"]
            },
            "operator_decisions": [],
            "timeline": [],
            "final_trust_receipt": {
                "overall_trust_score": 0.85,
                "trust_level": "high"
            }
        }
        
        return {
            "artifact_id": artifact_id,
            "scenario_id": scenario_id,
            "created_at": datetime.utcnow().isoformat(),
            "title": artifact_data["title"],
            "trust_score": 0.85,
            "incident_count": 0,
            "data": artifact_data
        }
    
    # Use the first incident to build the artifact
    incident = incidents[0]
    
    # Get decision cards for this incident
    decision_cards = decision_engine.get_decisions_for_incident(incident.incident_id)
    
    # Get trust receipts
    trust_receipts = decision_engine.get_trust_receipts(incident.incident_id)
    
    # Get audit trail
    audit_events = audit_logger.get_incident_trail(incident.incident_id)
    
    # Build comprehensive artifact
    artifact_id = f"ART-{datetime.utcnow().strftime('%Y-%m%d')}-{incident.incident_id[-3:]}"
    
    # Calculate overall trust score
    if trust_receipts:
        overall_trust = sum(r.overall_trust_score for r in trust_receipts) / len(trust_receipts)
    else:
        overall_trust = 0.85  # Default
    
    artifact_data = {
        "artifact_id": artifact_id,
        "incident_id": incident.incident_id,
        "scenario_id": scenario_id,
        "title": f"Decision Artifact: {incident.title}",
        "created_at": datetime.utcnow().isoformat(),
        "incident": {
            "incident_id": incident.incident_id,
            "title": incident.title,
            "description": incident.description,
            "severity": incident.severity.value if hasattr(incident.severity, 'value') else str(incident.severity),
            "state": incident.state.value if hasattr(incident.state, 'value') else str(incident.state),
            "created_at": incident.created_at.isoformat() if incident.created_at else None,
        },
        "evidence": [
            {
                "type": "telemetry",
                "source": "sensors",
                "timestamp": datetime.utcnow().isoformat()
            }
        ],
        "contradictions": [
            {"contradiction_id": cid} for cid in (incident.contradiction_ids or [])
        ],
        "trust_receipt": {
            "overall_trust_score": overall_trust,
            "trust_level": "high" if overall_trust >= 0.85 else "medium" if overall_trust >= 0.7 else "low",
            "reason_codes": ["cross_validated"]
        },
        "operator_decisions": [
            {
                "card_id": card.card_id,
                "title": card.title,
                "operator_choice": card.operator_choice,
                "resolved": card.resolved
            }
            for card in decision_cards
        ],
        "timeline": [
            {
                "event_id": event.event_id,
                "event_type": event.event_type,
                "timestamp": event.timestamp.isoformat() if event.timestamp else None,
                "summary": event.summary
            }
            for event in audit_events[:20]  # Limit to last 20 events
        ],
        "final_trust_receipt": {
            "overall_trust_score": overall_trust,
            "trust_level": "high" if overall_trust >= 0.85 else "medium" if overall_trust >= 0.7 else "low"
        }
    }
    
    # Log artifact generation
    audit_logger.log(
        event_type="artifact_generated",
        summary=f"Artifact {artifact_id} generated for incident {incident.incident_id}",
        data={"artifact_id": artifact_id, "trust_score": overall_trust},
        incident_id=incident.incident_id,
        scenario_id=scenario_id
    )
    
    return {
        "artifact_id": artifact_id,
        "scenario_id": scenario_id,
        "incident_id": incident.incident_id,
        "created_at": datetime.utcnow().isoformat(),
        "title": artifact_data["title"],
        "trust_score": overall_trust,
        "incident_count": len(incidents),
        "decision_count": len(decision_cards),
        "data": artifact_data
    }


# ============================================================================
# Background Tasks
# ============================================================================

async def _run_fixed_scenario(scenario_id: str, operator_id: str):
    """
    Run the fixed scenario simulation.
    
    This loads static data and simulates the timeline, creating
    incidents and decision cards at appropriate times.
    """
    import asyncio
    
    data_loader = get_data_loader()
    incident_manager = get_incident_manager()
    decision_engine = get_decision_engine()
    questionnaire = get_questionnaire_service()
    audit_logger = get_audit_logger()
    
    try:
        # Load scenario data
        scenario_data = data_loader.load_fixed_scenario()
        
        # Update status
        status = _scenario_states[scenario_id]
        
        # Simulate timeline - for demo, we'll create the incident immediately
        # In production, this would step through time_sec values
        
        # Get contradictions at t=60s (when they're detected)
        contradictions = scenario_data.contradictions
        
        if contradictions:
            # Create incident
            first_contradiction = contradictions[0]
            incident = incident_manager.create_incident(
                scenario_id=scenario_id,
                title="Sensor Contradiction Detected",
                description=first_contradiction.description,
                severity=IncidentSeverity.CRITICAL,
                contradiction_ids=[c.contradiction_id for c in contradictions]
            )
            
            # Log incident
            audit_logger.log_incident_opened(
                incident_id=incident.incident_id,
                scenario_id=scenario_id,
                title=incident.title,
                contradiction_ids=incident.contradiction_ids
            )
            
            # Update status
            status.active_incidents = 1
            status.mode = "decision"
            _persist_scenario_state(scenario_id, status)
            
            # Log mode change
            audit_logger.log_mode_changed(
                scenario_id=scenario_id,
                from_mode="data_ingest",
                to_mode="decision",
                trigger="contradiction_detected"
            )
            
            # Get telemetry at contradiction time
            telemetry_at_time = data_loader.get_telemetry_at_time(
                scenario_data.telemetry, 
                60.0
            )
            
            # Evaluate evidence
            evaluation = decision_engine.evaluate_evidence(
                telemetry=telemetry_at_time,
                events=[e for e in scenario_data.events if e.time_sec <= 60],
                contradictions=contradictions
            )
            
            # Create decision card
            card = decision_engine.create_decision(
                evaluation=evaluation,
                telemetry_snapshot=telemetry_at_time,
                title=f"Decision Required: {incident.title}",
                summary=incident.description,
                severity=scenario_data.events[4].severity if len(scenario_data.events) > 4 else evaluation.uncertainty_level.value,
                scenario_id=scenario_id,
                incident_id=incident.incident_id
            )
            
            # Link card to incident
            incident_manager.link_decision_card(incident.incident_id, card.card_id)
            
            # Generate operator questions
            questions = questionnaire.generate_questions_for_incident(
                incident_id=incident.incident_id,
                contradictions=[c.model_dump() for c in contradictions],
                sensor_readings={k: v.model_dump() for k, v in telemetry_at_time.items()},
                severity="critical"
            )
            
            # Log questions
            for q in questions:
                audit_logger.log_question_asked(
                    incident_id=incident.incident_id,
                    scenario_id=scenario_id,
                    question_id=q.question_id,
                    question_text=q.question_text
                )
                incident_manager.record_question_asked(incident.incident_id, q.question_id)
        
        # Mark scenario as ready for operator interaction
        status.current_time_sec = 60.0
        _persist_scenario_state(scenario_id, status)
        
    except Exception as e:
        print(f"Error running fixed scenario: {e}")
        if scenario_id in _scenario_states:
            _scenario_states[scenario_id].status = "error"
            _persist_scenario_state(scenario_id, _scenario_states[scenario_id])
