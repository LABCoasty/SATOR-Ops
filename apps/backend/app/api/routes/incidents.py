"""
Incidents API Routes - Manage incident lifecycle.

Endpoints:
- GET /incidents - List incidents
- GET /incidents/{id} - Get incident details
- POST /incidents/{id}/triage - Triage an incident
- POST /incidents/{id}/dispatch - Dispatch action
- POST /incidents/{id}/close - Close incident
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

from ...services.incident_manager import (
    get_incident_manager,
    Incident,
    IncidentState,
    IncidentSeverity
)
from ...services.audit_logger import get_audit_logger
from ...services.artifact_builder import get_artifact_builder
from ...services.data_loader import get_data_loader
from ...services.operator_questionnaire import get_questionnaire_service, QuestionAnswer
from ...core.decision_engine import get_decision_engine


router = APIRouter(prefix="/incidents", tags=["incidents"])


# ============================================================================
# Models
# ============================================================================

class IncidentSummary(BaseModel):
    """Summary of an incident for listing."""
    incident_id: str
    scenario_id: str
    title: str
    state: IncidentState
    severity: IncidentSeverity
    created_at: datetime
    has_decision_card: bool
    questions_pending: int


class TriageRequest(BaseModel):
    """Request to triage an incident."""
    operator_id: str
    initial_assessment: str


class DispatchRequest(BaseModel):
    """Request to dispatch action."""
    operator_id: str
    action_type: str  # act, defer, escalate
    action_id: str
    action_details: str


class CloseRequest(BaseModel):
    """Request to close an incident."""
    operator_id: str
    resolution_summary: str


class AnswerQuestionRequest(BaseModel):
    """Request to answer an operator question."""
    operator_id: str
    question_id: str
    answer_value: Any
    confidence: Optional[int] = None
    notes: Optional[str] = None


# ============================================================================
# Endpoints
# ============================================================================

@router.get("", response_model=List[IncidentSummary])
async def list_incidents(scenario_id: Optional[str] = None):
    """
    List all incidents, optionally filtered by scenario.
    """
    incident_manager = get_incident_manager()
    questionnaire = get_questionnaire_service()
    
    if scenario_id:
        incidents = incident_manager.get_incidents_for_scenario(scenario_id)
    else:
        incidents = list(incident_manager._incidents.values())
    
    summaries = []
    for incident in incidents:
        pending_questions = len(questionnaire.get_pending_questions(incident.incident_id))
        summaries.append(IncidentSummary(
            incident_id=incident.incident_id,
            scenario_id=incident.scenario_id,
            title=incident.title,
            state=incident.state,
            severity=incident.severity,
            created_at=incident.created_at,
            has_decision_card=incident.decision_card_id is not None,
            questions_pending=pending_questions
        ))
    
    return summaries


@router.get("/{incident_id}")
async def get_incident(incident_id: str):
    """Get full details for an incident."""
    incident_manager = get_incident_manager()
    questionnaire = get_questionnaire_service()
    decision_engine = get_decision_engine()
    
    incident = incident_manager.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    # Get decision card if exists
    decision_card = None
    if incident.decision_card_id:
        decision_card = decision_engine.get_decision(incident.decision_card_id)
    
    # Get questions
    questions = questionnaire.get_all_questions(incident_id)
    
    return {
        "incident": incident.model_dump(),
        "decision_card": decision_card.model_dump() if decision_card else None,
        "questions": [q.model_dump() for q in questions],
        "pending_questions": len([q for q in questions if not q.answered])
    }


@router.post("/{incident_id}/triage")
async def triage_incident(incident_id: str, request: TriageRequest):
    """
    Triage an incident - operator has reviewed and made initial assessment.
    
    Transitions incident from OPEN to TRIAGED.
    """
    incident_manager = get_incident_manager()
    audit_logger = get_audit_logger()
    
    incident = incident_manager.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    try:
        incident = incident_manager.triage(
            incident_id=incident_id,
            operator_id=request.operator_id,
            initial_assessment=request.initial_assessment
        )
        
        # Log triage
        audit_logger.log_incident_triaged(
            incident_id=incident_id,
            scenario_id=incident.scenario_id,
            operator_id=request.operator_id,
            assessment=request.initial_assessment
        )
        
        return {"success": True, "incident": incident.model_dump()}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{incident_id}/dispatch")
async def dispatch_incident(incident_id: str, request: DispatchRequest):
    """
    Dispatch action for an incident.
    
    Records the operator's chosen action and transitions to DISPATCHED.
    """
    incident_manager = get_incident_manager()
    audit_logger = get_audit_logger()
    decision_engine = get_decision_engine()
    artifact_builder = get_artifact_builder()
    
    incident = incident_manager.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    try:
        # Record action on decision card
        if incident.decision_card_id:
            decision_engine.record_action(
                card_id=incident.decision_card_id,
                action_id=request.action_id,
                operator_id=request.operator_id
            )
        
        # Dispatch incident
        incident = incident_manager.dispatch(
            incident_id=incident_id,
            operator_id=request.operator_id,
            action_type=request.action_type,
            action_details=request.action_details
        )
        
        # Log action
        audit_logger.log_action_taken(
            incident_id=incident_id,
            scenario_id=incident.scenario_id,
            operator_id=request.operator_id,
            action_id=request.action_id,
            action_type=request.action_type,
            rationale=request.action_details
        )
        
        # Generate trust receipt
        decision_card = decision_engine.get_decision(incident.decision_card_id) if incident.decision_card_id else None
        if decision_card:
            receipt = artifact_builder.generate_trust_receipt(
                incident_id=incident_id,
                trust_score=1 - decision_card.evaluation.overall_uncertainty,
                sensor_scores=decision_card.evaluation.sensor_trust_scores,
                reason_codes=list(set(
                    c.get("reason_code", "") 
                    for c in decision_card.evaluation.active_contradictions
                )) if isinstance(decision_card.evaluation.active_contradictions[0], dict) else decision_card.evaluation.active_contradictions,
                contradictions=decision_card.evaluation.active_contradictions,
                evidence_sources=["telemetry"],
                questions_asked=len(incident.questions_asked),
                questions_answered=len(incident.questions_answered)
            )
            incident_manager.link_trust_receipt(incident_id, receipt.receipt_id)
        
        return {"success": True, "incident": incident.model_dump()}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{incident_id}/close")
async def close_incident(incident_id: str, request: CloseRequest):
    """
    Close an incident and trigger artifact creation.
    
    This is the final step - creates the artifact packet and
    prepares for on-chain anchoring.
    """
    incident_manager = get_incident_manager()
    audit_logger = get_audit_logger()
    artifact_builder = get_artifact_builder()
    decision_engine = get_decision_engine()
    data_loader = get_data_loader()
    questionnaire = get_questionnaire_service()
    
    incident = incident_manager.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    try:
        # Close incident
        incident = incident_manager.close(
            incident_id=incident_id,
            operator_id=request.operator_id,
            resolution_summary=request.resolution_summary
        )
        
        # Log closure
        audit_logger.log_incident_closed(
            incident_id=incident_id,
            scenario_id=incident.scenario_id,
            operator_id=request.operator_id,
            resolution=request.resolution_summary
        )
        
        # Build artifact
        scenario_data = data_loader.load_fixed_scenario()
        decision_card = decision_engine.get_decision(incident.decision_card_id) if incident.decision_card_id else None
        questions = questionnaire.get_all_questions(incident_id)
        
        artifact = artifact_builder.build_artifact(
            incident=incident,
            telemetry_samples=scenario_data.telemetry[:50],  # Sample
            contradictions=scenario_data.contradictions,
            decision_card=decision_card.model_dump() if decision_card else {},
            questions_asked=[q.model_dump() for q in questions],
            questions_answered=[q.model_dump() for q in questions if q.answered]
        )
        
        # Link artifact to incident
        incident_manager.link_artifact(incident_id, artifact.artifact_id)
        
        # Log mode change to artifact creation
        audit_logger.log_mode_changed(
            scenario_id=incident.scenario_id,
            from_mode="decision",
            to_mode="artifact",
            trigger="incident_closed"
        )
        
        return {
            "success": True,
            "incident": incident.model_dump(),
            "artifact_id": artifact.artifact_id,
            "artifact_hash": artifact.content_hash
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{incident_id}/questions/{question_id}/answer")
async def answer_question(
    incident_id: str, 
    question_id: str, 
    request: AnswerQuestionRequest
):
    """
    Submit an answer to an operator question.
    
    The answer is processed and may affect trust scores and recommendations.
    """
    incident_manager = get_incident_manager()
    questionnaire = get_questionnaire_service()
    audit_logger = get_audit_logger()
    artifact_builder = get_artifact_builder()
    
    incident = incident_manager.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    try:
        # Submit answer
        answer = QuestionAnswer(
            question_id=question_id,
            operator_id=request.operator_id,
            answer_value=request.answer_value,
            confidence=request.confidence,
            notes=request.notes
        )
        
        impact = questionnaire.submit_answer(answer)
        
        # Record answer on incident
        incident_manager.record_question_answered(incident_id, question_id)
        
        # Log answer
        audit_logger.log_question_answered(
            incident_id=incident_id,
            scenario_id=incident.scenario_id,
            operator_id=request.operator_id,
            question_id=question_id,
            answer=request.answer_value,
            impact=impact.model_dump()
        )
        
        # Update trust if significant impact
        if impact.trust_adjustment != 0:
            # Generate updated trust receipt
            current_receipts = artifact_builder.get_trust_receipts(incident_id)
            current_trust = current_receipts[-1].overall_trust_score if current_receipts else 0.5
            new_trust = max(0, min(1, current_trust + impact.trust_adjustment))
            
            audit_logger.log_trust_updated(
                incident_id=incident_id,
                scenario_id=incident.scenario_id,
                trust_score=new_trust,
                reason=impact.explanation
            )
        
        return {
            "success": True,
            "impact": impact.model_dump(),
            "questions_remaining": len(questionnaire.get_pending_questions(incident_id))
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
