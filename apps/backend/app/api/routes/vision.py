"""
Vision API Routes - Handle Overshoot vision webhook with LeanMCP processing.

Endpoints:
- POST /vision/webhook - Receive Overshoot vision JSON (with configurable delay)
- GET /vision/latest - Get latest vision frame
- GET /vision/history - Get recent vision frames
- GET /vision/queue/status - Get processing queue status
- POST /vision/queue/start - Start the processing queue
- POST /vision/queue/stop - Stop the processing queue

LeanMCP Integration:
Per https://docs.leanmcp.com/api-reference/introduction, the MCP server
processes vision frames through 5 decision tools with configurable delays
to sync with the timeline workflow.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from config import config
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
from ...services.vision_processor import (
    get_vision_queue,
    process_vision_with_delay,
    VisionProcessingQueue,
)


router = APIRouter(prefix="/vision", tags=["vision"])


# ============================================================================
# Models
# ============================================================================

class VisionWebhookResponse(BaseModel):
    """Response from vision webhook."""
    success: bool
    frame_id: Optional[str] = None
    processed: bool = False
    queued: bool = False
    processing_delay_ms: int = 0
    timeline_time_sec: float = 0.0
    incident_created: Optional[str] = None
    message: str


class VisionProcessRequest(BaseModel):
    """Request for immediate vision processing with delay."""
    frame_data: Dict[str, Any] = Field(..., description="Overshoot vision frame")
    scenario_id: Optional[str] = Field(None, description="Associated scenario ID")
    delay_ms: Optional[int] = Field(None, description="Override processing delay (ms)")
    process_immediately: bool = Field(True, description="Process now vs queue")


class QueueStatusResponse(BaseModel):
    """Response with queue status."""
    is_running: bool
    queue_size: int
    processed_count: int
    delay_ms: int
    batch_size: int
    timeline_sync_enabled: bool
    timeline_offset_sec: float


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
    Receive vision data from Overshoot with delayed LeanMCP processing.
    
    Supports multiple payload formats:
    - Full Overshoot format: {"session_id": "...", "frame": {...}}
    - Nested frame: {"frame": {...}}
    - Simple frame (for testing): {"frame_id": "...", "equipment_states": [], ...}
    """
    overshoot_client = get_overshoot_client()
    audit_logger = get_audit_logger()
    vision_queue = get_vision_queue()
    
    try:
        # Support both full OvershootWebhookPayload and simple VisionFrame format
        frame: Optional[VisionFrame] = None
        
        if "session_id" in payload:
            # Full Overshoot webhook format
            webhook_data = overshoot_client.process_webhook(payload)
            frame = webhook_data.frame
        elif "frame" in payload:
            # Nested frame format without session_id
            frame = VisionFrame(**payload["frame"])
            overshoot_client._handle_frame(frame)
        elif "frame_id" in payload:
            # Simple frame format (for testing)
            frame = VisionFrame(**payload)
            overshoot_client._handle_frame(frame)
        
        if not frame:
            return VisionWebhookResponse(
                success=True,
                processed=False,
                queued=False,
                processing_delay_ms=0,
                message="No frame data. Expected session_id+frame, frame, or frame_id field."
            )
        
        # Log vision received
        audit_logger.log_vision_received(
            scenario_id=_active_scenario_id or "unknown",
            frame_id=frame.frame_id,
            equipment_count=len(frame.equipment_states),
            safety_event_count=len(frame.safety_events)
        )
        
        # Ensure queue is started
        if not vision_queue._is_running:
            vision_queue.start()
        
        # Queue the frame for delayed processing
        queued_frame = vision_queue.enqueue(
            frame_data=frame.model_dump(),
            scenario_id=_active_scenario_id
        )
        
        # Process in background with delay
        if frame.has_detections():
            background_tasks.add_task(
                _process_vision_frame_with_delay,
                frame,
                _active_scenario_id
            )
        
        return VisionWebhookResponse(
            success=True,
            frame_id=frame.frame_id,
            processed=False,
            queued=True,
            processing_delay_ms=config.vision_processing_delay_ms,
            timeline_time_sec=queued_frame.timeline_time_sec,
            incident_created=None,
            message=f"Vision frame queued (delay: {config.vision_processing_delay_ms}ms)"
        )
        
    except Exception as e:
        return VisionWebhookResponse(
            success=False,
            message=f"Error processing vision data: {str(e)}"
        )


@router.post("/process", summary="Process vision frame with configurable delay")
async def process_vision_frame_endpoint(request: VisionProcessRequest):
    """Process a vision frame through LeanMCP with configurable delay."""
    try:
        if request.process_immediately:
            result = await process_vision_with_delay(
                frame_data=request.frame_data,
                scenario_id=request.scenario_id,
                delay_override_ms=request.delay_ms
            )
            return result
        else:
            queue = get_vision_queue()
            if not queue._is_running:
                queue.start()
            
            queued = queue.enqueue(
                frame_data=request.frame_data,
                scenario_id=request.scenario_id
            )
            
            return {
                "success": True,
                "queued": True,
                "frame_id": queued.frame_id,
                "timeline_time_sec": queued.timeline_time_sec,
                "queue_size": queue.queue_size,
                "message": "Frame queued for processing"
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/queue/status", response_model=QueueStatusResponse)
async def get_queue_status():
    """Get the vision processing queue status."""
    queue = get_vision_queue()
    status = queue.get_status()
    return QueueStatusResponse(**status)


@router.post("/queue/start")
async def start_queue(timeline_offset_sec: float = 0.0):
    """Start the vision processing queue."""
    queue = get_vision_queue()
    queue.start(timeline_offset_sec=timeline_offset_sec)
    return {
        "success": True,
        "message": "Vision processing queue started",
        "timeline_offset_sec": timeline_offset_sec,
        "delay_ms": queue.delay_ms
    }


@router.post("/queue/stop")
async def stop_queue():
    """Stop the vision processing queue."""
    queue = get_vision_queue()
    queue.stop()
    return {
        "success": True,
        "message": "Vision processing queue stopped",
        "processed_count": queue._processed_count
    }


@router.post("/queue/process-batch")
async def process_queue_batch():
    """Process a batch of queued frames."""
    queue = get_vision_queue()
    
    if not queue._is_running:
        queue.start()
    
    results = await queue.process_batch()
    
    return {
        "success": True,
        "processed_count": len(results),
        "remaining_in_queue": queue.queue_size,
        "results": results
    }


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
    """Simulate a vision frame for demo purposes."""
    overshoot_client = get_overshoot_client()
    
    try:
        frame = overshoot_client.simulate_frame(frame_data)
        
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
# Background Processing with LeanMCP Delay
# ============================================================================

async def _process_vision_frame_with_delay(frame: VisionFrame, scenario_id: Optional[str]):
    """Process a vision frame through the LeanMCP pipeline with configurable delay."""
    from ...services.data_loader import get_data_loader
    
    incident_manager = get_incident_manager()
    questionnaire = get_questionnaire_service()
    audit_logger = get_audit_logger()
    
    try:
        result = await process_vision_with_delay(
            frame_data=frame.model_dump(),
            scenario_id=scenario_id
        )
        
        if not result.get("success"):
            print(f"Vision processing failed: {result.get('error')}")
            return
        
        contradictions = result.get("steps", {}).get("detect_contradictions", [])
        predictions = result.get("steps", {}).get("predict_issues", [])
        vision_analysis = result.get("steps", {}).get("analyze_vision", {})
        
        if result.get("requires_incident"):
            has_safety_event = len(frame.safety_events) > 0
            has_critical = any(c.get("severity") == "critical" for c in contradictions)
            
            if any(e.severity in ["critical", "emergency"] for e in frame.safety_events):
                severity = IncidentSeverity.EMERGENCY
            elif has_critical:
                severity = IncidentSeverity.CRITICAL
            else:
                severity = IncidentSeverity.WARNING
            
            title = "Vision Alert: "
            if has_safety_event:
                title += frame.safety_events[0].description
            elif contradictions:
                title += contradictions[0].get("description", "Contradiction detected")
            
            incident = incident_manager.create_incident(
                scenario_id=scenario_id or "live-vision-demo",
                title=title,
                description=vision_analysis.get("summary", "Vision analysis detected an issue"),
                severity=severity,
                contradiction_ids=[c.get("contradiction_id", "") for c in contradictions]
            )
            
            audit_logger.log_incident_opened(
                incident_id=incident.incident_id,
                scenario_id=scenario_id or "live-vision-demo",
                title=incident.title,
                contradiction_ids=incident.contradiction_ids
            )
            
            telemetry_dict = result.get("telemetry_snapshot", {})
            questions = questionnaire.generate_questions_for_incident(
                incident_id=incident.incident_id,
                contradictions=contradictions,
                sensor_readings=telemetry_dict,
                severity=severity.value
            )
            
            audit_logger.log_mode_changed(
                scenario_id=scenario_id or "live-vision-demo",
                from_mode="data_ingest",
                to_mode="decision",
                trigger="vision_event"
            )
            
            print(f"Incident created: {incident.incident_id} "
                  f"(delay: {result.get('processing_delay_ms', 0)}ms, "
                  f"timeline: {result.get('timeline_time_sec', 0):.2f}s)")
            
    except Exception as e:
        print(f"Error processing vision frame: {e}")
        import traceback
        traceback.print_exc()


async def _process_vision_frame(frame: VisionFrame, scenario_id: Optional[str]):
    """Legacy wrapper - redirects to delayed processing."""
    await _process_vision_frame_with_delay(frame, scenario_id)
