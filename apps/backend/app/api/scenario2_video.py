"""
Scenario 2 Video Processing API - Process video through Overshoot AI + LeanMCP.

This endpoint handles the Scenario 2 workflow:
1. Receive video URL or file
2. Process frames through Overshoot AI (simulated or real)
3. Run results through LeanMCP pipeline
4. Create incidents and decision cards
5. Return aggregated results
"""

import asyncio
import httpx
from datetime import datetime, timezone
from typing import Optional, List
from uuid import uuid4
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from config import config

router = APIRouter()


# ============================================================================
# Models
# ============================================================================

class VideoProcessRequest(BaseModel):
    """Request to process a video through Scenario 2 pipeline."""
    video_url: str = Field(..., description="URL to the video file")
    fps: float = Field(default=1.0, description="Frames per second to analyze")
    max_frames: int = Field(default=10, description="Maximum frames to process")
    scenario_id: Optional[str] = Field(default=None, description="Scenario ID")


class IncidentSummary(BaseModel):
    """Summary of a created incident."""
    incident_id: str
    title: str
    severity: str


class VideoProcessResponse(BaseModel):
    """Response from video processing."""
    success: bool
    video_url: str
    frame_count: int = 0
    incidents_created: int = 0
    contradictions_found: int = 0
    predictions_made: int = 0
    processing_time_ms: int = 0
    incidents: List[IncidentSummary] = []
    error: Optional[str] = None


class ProcessingStatus(BaseModel):
    """Status of ongoing processing."""
    job_id: str
    status: str  # pending, processing, completed, error
    progress: int  # 0-100
    message: str
    result: Optional[VideoProcessResponse] = None


# ============================================================================
# In-memory job tracking
# ============================================================================

_processing_jobs: dict[str, ProcessingStatus] = {}


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/process-video", response_model=ProcessingStatus)
async def process_video(
    request: VideoProcessRequest,
    background_tasks: BackgroundTasks
):
    """
    Start processing a video through the Scenario 2 pipeline.
    
    This endpoint:
    1. Validates the video URL
    2. Starts background processing
    3. Returns a job ID for status polling
    
    The background process will:
    - Download/stream the video
    - Extract frames at specified FPS
    - Send each frame to Overshoot AI for analysis
    - Process results through LeanMCP
    - Create incidents for detected issues
    """
    job_id = str(uuid4())
    
    # Initialize job status
    _processing_jobs[job_id] = ProcessingStatus(
        job_id=job_id,
        status="pending",
        progress=0,
        message="Initializing video processing..."
    )
    
    # Start background processing
    background_tasks.add_task(
        _process_video_background,
        job_id,
        request.video_url,
        request.fps,
        request.max_frames,
        request.scenario_id
    )
    
    return _processing_jobs[job_id]


@router.get("/process-video/{job_id}", response_model=ProcessingStatus)
async def get_processing_status(job_id: str):
    """Get the status of a video processing job."""
    if job_id not in _processing_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return _processing_jobs[job_id]


@router.post("/process-video-sync", response_model=VideoProcessResponse)
async def process_video_sync(request: VideoProcessRequest):
    """
    Process a video synchronously (for smaller videos or demos).
    
    This blocks until processing is complete.
    """
    start_time = datetime.now(timezone.utc)
    
    try:
        result = await _run_video_processing(
            video_url=request.video_url,
            fps=request.fps,
            max_frames=request.max_frames,
            scenario_id=request.scenario_id
        )
        
        processing_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        result.processing_time_ms = int(processing_time)
        
        return result
        
    except Exception as e:
        return VideoProcessResponse(
            success=False,
            video_url=request.video_url,
            error=str(e)
        )


# ============================================================================
# Background Processing
# ============================================================================

async def _process_video_background(
    job_id: str,
    video_url: str,
    fps: float,
    max_frames: int,
    scenario_id: Optional[str]
):
    """Background task to process video."""
    job = _processing_jobs[job_id]
    start_time = datetime.now(timezone.utc)
    
    try:
        job.status = "processing"
        job.progress = 10
        job.message = "Downloading video..."
        
        await asyncio.sleep(0.5)  # Simulate download
        
        job.progress = 30
        job.message = "Extracting frames..."
        
        result = await _run_video_processing(
            video_url=video_url,
            fps=fps,
            max_frames=max_frames,
            scenario_id=scenario_id,
            progress_callback=lambda p, m: _update_job(job_id, p, m)
        )
        
        processing_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        result.processing_time_ms = int(processing_time)
        
        job.status = "completed"
        job.progress = 100
        job.message = "Processing complete"
        job.result = result
        
    except Exception as e:
        job.status = "error"
        job.message = f"Error: {str(e)}"
        job.result = VideoProcessResponse(
            success=False,
            video_url=video_url,
            error=str(e)
        )


def _update_job(job_id: str, progress: int, message: str):
    """Update job progress."""
    if job_id in _processing_jobs:
        _processing_jobs[job_id].progress = progress
        _processing_jobs[job_id].message = message


async def _run_video_processing(
    video_url: str,
    fps: float,
    max_frames: int,
    scenario_id: Optional[str],
    progress_callback: Optional[callable] = None
) -> VideoProcessResponse:
    """
    Core video processing logic.
    
    Simulates Overshoot AI processing and runs through LeanMCP.
    """
    from ..services.vision_processor import get_vision_queue
    from ..services.incident_manager import get_incident_manager
    
    vision_queue = get_vision_queue()
    incident_manager = get_incident_manager()
    
    if not vision_queue._is_running:
        vision_queue.start()
    
    scenario_id = scenario_id or f"scenario2-{uuid4().hex[:8]}"
    
    # Generate simulated frames (in production, would extract from video)
    frames_to_process = []
    for i in range(max_frames):
        frame = _generate_simulated_frame(i, fps, video_url)
        frames_to_process.append(frame)
    
    if progress_callback:
        progress_callback(40, "Sending frames to Overshoot AI...")
    
    # Process frames through vision queue
    total_contradictions = 0
    total_predictions = 0
    
    for i, frame_data in enumerate(frames_to_process):
        if progress_callback:
            pct = 40 + int((i / max_frames) * 40)
            progress_callback(pct, f"Processing frame {i + 1}/{max_frames}...")
        
        # Queue frame for LeanMCP processing
        queued = vision_queue.enqueue(frame_data, scenario_id)
        
        # Process immediately for sync results
        result = await vision_queue.process_next()
        
        if result:
            total_contradictions += result.get("contradictions_count", 0)
            total_predictions += result.get("predictions_count", 0)
    
    if progress_callback:
        progress_callback(90, "Finalizing incidents...")
    
    # Get created incidents
    all_incidents = incident_manager.get_incidents_for_scenario(scenario_id)
    incident_summaries = [
        IncidentSummary(
            incident_id=inc.incident_id,
            title=inc.title,
            severity=inc.severity.value
        )
        for inc in all_incidents
    ]
    
    return VideoProcessResponse(
        success=True,
        video_url=video_url,
        frame_count=len(frames_to_process),
        incidents_created=len(incident_summaries),
        contradictions_found=total_contradictions,
        predictions_made=total_predictions,
        incidents=incident_summaries
    )


def _generate_simulated_frame(
    frame_index: int,
    fps: float,
    video_url: str
) -> dict:
    """
    Generate a simulated Overshoot AI frame response.
    
    In production, this would call the actual Overshoot API.
    """
    import random
    
    timestamp_ms = int(frame_index * (1000 / fps))
    has_anomaly = random.random() > 0.6  # 40% chance of anomaly
    
    equipment_states = [
        {
            "equipment_id": f"valve-{frame_index % 3 + 1}",
            "equipment_type": "valve",
            "status": "warning" if has_anomaly else "normal",
            "confidence": 0.85 + random.random() * 0.1,
        },
        {
            "equipment_id": f"gauge-{frame_index % 2 + 1}",
            "equipment_type": "gauge",
            "status": "normal",
            "confidence": 0.9 + random.random() * 0.05,
        }
    ]
    
    safety_events = []
    if has_anomaly:
        event_types = ["leak", "pressure_warning", "temperature_high", "vibration"]
        severities = ["warning", "critical"]
        
        safety_events.append({
            "event_id": f"evt-{frame_index}-{uuid4().hex[:4]}",
            "event_type": random.choice(event_types),
            "severity": random.choice(severities),
            "description": f"Anomaly detected in frame {frame_index}",
            "confidence": 0.7 + random.random() * 0.2,
            "acknowledged": False,
            "resolved": False,
            "related_equipment": [equipment_states[0]["equipment_id"]],
            "related_persons": []
        })
    
    return {
        "frame_id": f"frame-{frame_index}-{uuid4().hex[:6]}",
        "timestamp_ms": timestamp_ms,
        "video_source": video_url,
        "equipment_states": equipment_states,
        "safety_events": safety_events,
        "scene_description": f"Industrial scene at frame {frame_index}"
    }
