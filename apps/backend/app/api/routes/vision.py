"""
Vision API Routes - Handle Overshoot vision webhook.

Endpoints:
- POST /vision/webhook - Receive Overshoot vision JSON
- GET /vision/latest - Get latest vision frame
- GET /vision/history - Get recent vision frames
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

from ...integrations.overshoot import (
    get_overshoot_client,
    VisionFrame,
    OvershootWebhookPayload
)
from ...integrations.leanmcp import (
    get_mcp_server,
    MCPRequest,
    analyze_vision,
    detect_contradictions,
    predict_issues,
    recommend_action,
    create_decision_card
)
from ...services.incident_manager import (
    get_incident_manager,
    IncidentSeverity
)
from ...services.audit_logger import get_audit_logger
from ...services.operator_questionnaire import get_questionnaire_service


router = APIRouter(prefix="/vision", tags=["vision"])


# ============================================================================
# Models
# ============================================================================

class VisionWebhookResponse(BaseModel):
    """Response from vision webhook."""
    success: bool
    frame_id: Optional[str] = None
    processed: bool = False
    incident_created: Optional[str] = None
    message: str


# ============================================================================
# State
# ============================================================================

_active_scenario_id: Optional[str] = None


def set_active_scenario(scenario_id: str):
    """Set the active scenario for vision processing."""
    global _active_scenario_id
    _active_scenario_id = scenario_id


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/webhook", response_model=VisionWebhookResponse)
async def vision_webhook(
    payload: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """
    Receive vision data from Overshoot.
    
    This webhook is called by Overshoot with real-time vision analysis.
    The data is processed through LeanMCP tools to:
    1. Extract actionable insights
    2. Cross-validate against telemetry
    3. Detect contradictions
    4. Generate predictions
    5. Create decision cards if needed
    """
    overshoot_client = get_overshoot_client()
    audit_logger = get_audit_logger()
    
    try:
        # Process webhook payload
        webhook_data = overshoot_client.process_webhook(payload)
        
        if not webhook_data.frame:
            return VisionWebhookResponse(
                success=True,
                processed=False,
                message="No frame data in payload"
            )
        
        frame = webhook_data.frame
        
        # Log vision received
        audit_logger.log_vision_received(
            scenario_id=_active_scenario_id or "unknown",
            frame_id=frame.frame_id,
            equipment_count=len(frame.equipment_states),
            safety_event_count=len(frame.safety_events)
        )
        
        # Process frame in background
        incident_id = None
        if frame.has_detections():
            background_tasks.add_task(
                _process_vision_frame,
                frame,
                _active_scenario_id
            )
        
        return VisionWebhookResponse(
            success=True,
            frame_id=frame.frame_id,
            processed=True,
            incident_created=incident_id,
            message="Vision frame received and queued for processing"
        )
        
    except Exception as e:
        return VisionWebhookResponse(
            success=False,
            message=f"Error processing vision data: {str(e)}"
        )


@router.get("/latest")
async def get_latest_vision():
    """Get the most recent vision frame."""
    overshoot_client = get_overshoot_client()
    frame = overshoot_client.get_latest_frame()
    
    if not frame:
        return {"frame": None, "message": "No vision frames received yet"}
    
    return {"frame": frame.model_dump()}


@router.get("/history")
async def get_vision_history(limit: int = 10):
    """Get recent vision frame history."""
    overshoot_client = get_overshoot_client()
    frames = overshoot_client.get_frame_history(limit)
    
    return {
        "frames": [f.model_dump() for f in frames],
        "count": len(frames)
    }


@router.post("/simulate")
async def simulate_vision_frame(
    frame_data: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """
    Simulate a vision frame for demo purposes.
    
    This allows testing the vision pipeline without Overshoot.
    """
    overshoot_client = get_overshoot_client()
    
    try:
        frame = overshoot_client.simulate_frame(frame_data)
        
        # Process in background
        if frame.has_detections():
            background_tasks.add_task(
                _process_vision_frame,
                frame,
                _active_scenario_id
            )
        
        return {
            "success": True,
            "frame_id": frame.frame_id,
            "message": "Simulated frame processed"
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Background Processing
# ============================================================================

async def _process_vision_frame(frame: VisionFrame, scenario_id: Optional[str]):
    """
    Process a vision frame through the LeanMCP pipeline.
    
    Steps:
    1. Analyze vision to extract insights
    2. Get current telemetry
    3. Detect contradictions between vision and telemetry
    4. Generate predictions
    5. Create incident and decision card if needed
    """
    from ...services.data_loader import get_data_loader
    
    mcp_server = get_mcp_server()
    incident_manager = get_incident_manager()
    questionnaire = get_questionnaire_service()
    audit_logger = get_audit_logger()
    data_loader = get_data_loader()
    
    try:
        # Step 1: Analyze vision
        vision_analysis = analyze_vision(frame.model_dump())
        
        # Step 2: Get telemetry (use scenario data or live)
        try:
            scenario_data = data_loader.load_fixed_scenario()
            telemetry = data_loader.get_telemetry_at_time(scenario_data.telemetry, 60.0)
            telemetry_dict = {k: v.model_dump() for k, v in telemetry.items()}
        except:
            telemetry_dict = {}
        
        # Step 3: Detect contradictions
        contradictions = detect_contradictions(
            vision_frame=frame.model_dump(),
            telemetry=telemetry_dict
        )
        
        # Step 4: Generate predictions
        predictions = predict_issues(
            vision_frame=frame.model_dump(),
            telemetry=telemetry_dict,
            history=[]
        )
        
        # Step 5: Check for safety events or contradictions
        has_safety_event = len(frame.safety_events) > 0
        has_contradiction = len(contradictions) > 0
        
        if has_safety_event or has_contradiction:
            # Determine severity
            if any(e.severity in ["critical", "emergency"] for e in frame.safety_events):
                severity = IncidentSeverity.EMERGENCY
            elif has_contradiction:
                severity = IncidentSeverity.CRITICAL
            else:
                severity = IncidentSeverity.WARNING
            
            # Create incident
            title = "Vision Alert: "
            if has_safety_event:
                title += frame.safety_events[0].description
            elif has_contradiction:
                title += contradictions[0].get("description", "Contradiction detected")
            
            incident = incident_manager.create_incident(
                scenario_id=scenario_id or "live-vision-demo",
                title=title,
                description=vision_analysis.get("summary", "Vision analysis detected an issue"),
                severity=severity,
                contradiction_ids=[c.get("contradiction_id", "") for c in contradictions]
            )
            
            # Log incident
            audit_logger.log_incident_opened(
                incident_id=incident.incident_id,
                scenario_id=scenario_id or "live-vision-demo",
                title=incident.title,
                contradiction_ids=incident.contradiction_ids
            )
            
            # Generate recommendation
            recommendation = recommend_action(
                incident_state={"severity": severity.value, "state": "open"},
                evidence={
                    "contradictions": contradictions,
                    "predictions": predictions,
                    "vision_analysis": vision_analysis
                },
                trust_score=0.5  # Default for vision-based incidents
            )
            
            # Create decision card
            card_data = create_decision_card(
                incident_id=incident.incident_id,
                findings={
                    "contradictions": contradictions,
                    "predictions": predictions,
                    "recommendation": recommendation,
                    "trust_score": 0.5,
                    "telemetry": telemetry_dict,
                    "vision": frame.model_dump()
                },
                operator_questions=[]
            )
            
            # Generate questions
            questions = questionnaire.generate_questions_for_incident(
                incident_id=incident.incident_id,
                contradictions=contradictions,
                sensor_readings=telemetry_dict,
                severity=severity.value
            )
            
            # Log mode change
            audit_logger.log_mode_changed(
                scenario_id=scenario_id or "live-vision-demo",
                from_mode="data_ingest",
                to_mode="decision",
                trigger="vision_event"
            )
            
    except Exception as e:
        print(f"Error processing vision frame: {e}")
