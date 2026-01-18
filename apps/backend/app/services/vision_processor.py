"""
Vision Processor - Delayed processing of Overshoot frames via LeanMCP.

Implements a queue-based processing system with configurable delays
to sync vision frames with the timeline workflow per the SATOR architecture.

Flow:
1. Receive Overshoot vision frame
2. Queue with timestamp
3. Apply processing delay (configurable)
4. Process through LeanMCP tools
5. Generate timeline events
6. Trigger incident creation if needed
"""

import asyncio
from collections import deque
from datetime import datetime, timezone
from typing import Any, Optional
from dataclasses import dataclass, field
from uuid import uuid4

from config import config


@dataclass
class QueuedVisionFrame:
    """A vision frame queued for processing."""
    frame_id: str
    frame_data: dict[str, Any]
    received_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    scenario_id: Optional[str] = None
    timeline_time_sec: float = 0.0
    processed: bool = False
    processing_started_at: Optional[datetime] = None


class VisionProcessingQueue:
    """
    Async queue for delayed vision frame processing.
    
    Implements timeline-synchronized processing with configurable delays
    to properly integrate Overshoot data into the SATOR workflow.
    """
    
    def __init__(self):
        self._queue: deque[QueuedVisionFrame] = deque()
        self._processing_lock = asyncio.Lock()
        self._is_running = False
        self._timeline_offset_sec: float = 0.0
        self._start_time: Optional[datetime] = None
        self._processed_count = 0
        self._callbacks: list = []
        self._background_task: Optional[asyncio.Task] = None
    
    @property
    def delay_ms(self) -> int:
        """Get configured processing delay in milliseconds."""
        return config.vision_processing_delay_ms
    
    @property
    def batch_size(self) -> int:
        """Get configured batch size."""
        return config.vision_queue_batch_size
    
    @property
    def queue_size(self) -> int:
        """Current queue size."""
        return len(self._queue)
    
    def start(self, timeline_offset_sec: float = 0.0):
        """Start the processing queue and background processor."""
        self._is_running = True
        self._start_time = datetime.now(timezone.utc)
        self._timeline_offset_sec = timeline_offset_sec
        self._processed_count = 0
        
        # Start background processing loop
        if self._background_task is None or self._background_task.done():
            try:
                loop = asyncio.get_running_loop()
                self._background_task = loop.create_task(self._background_processor())
                print("✅ Vision queue background processor started")
            except RuntimeError:
                # No running loop yet, will be started later
                pass
    
    def stop(self):
        """Stop the processing queue and background processor."""
        self._is_running = False
        if self._background_task and not self._background_task.done():
            self._background_task.cancel()
            self._background_task = None
        print("Vision queue stopped")
    
    async def _background_processor(self):
        """
        Background task that continuously processes frames from the queue.
        
        This runs in a loop while the queue is running, processing frames
        with the configured delay.
        """
        print(f"Background processor loop started (delay: {self.delay_ms}ms)")
        while self._is_running:
            try:
                if self._queue:
                    result = await self.process_next()
                    if result and result.get("success"):
                        print(f"✅ Processed frame via LeanMCP: {result.get('frame_id')} "
                              f"(contradictions: {result.get('contradictions_count', 0)}, "
                              f"predictions: {result.get('predictions_count', 0)})")
                        
                        # Create incident if needed
                        if result.get("requires_incident"):
                            await self._create_incident_from_result(result)
                else:
                    # No frames to process, sleep briefly
                    await asyncio.sleep(0.1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Background processor error: {e}")
                await asyncio.sleep(1)  # Avoid tight loop on error
        
        print("Background processor loop stopped")
    
    async def _create_incident_from_result(self, result: dict):
        """Create an incident from the MCP processing result."""
        try:
            from ..services.incident_manager import get_incident_manager, IncidentSeverity
            from ..services.audit_logger import get_audit_logger
            
            incident_manager = get_incident_manager()
            audit_logger = get_audit_logger()
            
            # Determine severity
            contradictions = result.get("steps", {}).get("detect_contradictions", [])
            has_critical = any(c.get("severity") == "critical" for c in contradictions)
            
            if has_critical:
                severity = IncidentSeverity.CRITICAL
            elif result.get("contradictions_count", 0) > 0:
                severity = IncidentSeverity.WARNING
            else:
                severity = IncidentSeverity.INFO
            
            # Create incident
            incident = incident_manager.create_incident(
                scenario_id="vision-live-feed",
                title=f"Vision Alert: Frame {result.get('frame_id', 'unknown')}",
                description=f"Detected {result.get('contradictions_count', 0)} contradictions, "
                           f"{result.get('predictions_count', 0)} predictions",
                severity=severity,
                contradiction_ids=[c.get("contradiction_id", "") for c in contradictions]
            )
            
            # Log to audit
            audit_logger.log_incident_opened(
                incident_id=incident.incident_id,
                scenario_id="vision-live-feed",
                title=incident.title,
                contradiction_ids=incident.contradiction_ids
            )
            
            print(f"📋 Created incident: {incident.incident_id} (severity: {severity.value})")
            
        except Exception as e:
            print(f"Error creating incident: {e}")
    
    def enqueue(
        self,
        frame_data: dict[str, Any],
        scenario_id: Optional[str] = None,
    ) -> QueuedVisionFrame:
        """
        Add a vision frame to the processing queue.
        
        Args:
            frame_data: Vision frame data from Overshoot
            scenario_id: Associated scenario ID
            
        Returns:
            QueuedVisionFrame with assigned ID and timestamp
        """
        # Calculate timeline position
        if self._start_time and config.vision_timeline_sync:
            elapsed = (datetime.now(timezone.utc) - self._start_time).total_seconds()
            timeline_time_sec = self._timeline_offset_sec + elapsed
        else:
            timeline_time_sec = 0.0
        
        queued_frame = QueuedVisionFrame(
            frame_id=frame_data.get("frame_id") or str(uuid4()),
            frame_data=frame_data,
            scenario_id=scenario_id,
            timeline_time_sec=timeline_time_sec,
        )
        
        self._queue.append(queued_frame)
        return queued_frame
    
    async def process_next(self) -> Optional[dict[str, Any]]:
        """
        Process the next frame in the queue with delay.
        
        Applies the configured delay before processing through LeanMCP.
        
        Returns:
            Processing result or None if queue is empty
        """
        if not self._queue:
            return None
        
        async with self._processing_lock:
            if not self._queue:
                return None
            
            frame = self._queue.popleft()
            frame.processing_started_at = datetime.now(timezone.utc)
            
            # Apply processing delay
            delay_sec = self.delay_ms / 1000.0
            if delay_sec > 0:
                await asyncio.sleep(delay_sec)
            
            # Process through LeanMCP
            result = await self._process_frame_via_mcp(frame)
            
            frame.processed = True
            self._processed_count += 1
            
            # Notify callbacks
            for callback in self._callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(frame, result)
                    else:
                        callback(frame, result)
                except Exception as e:
                    print(f"Callback error: {e}")
            
            return result
    
    async def process_batch(self) -> list[dict[str, Any]]:
        """
        Process a batch of frames with delays between each.
        
        Returns:
            List of processing results
        """
        results = []
        count = min(self.batch_size, len(self._queue))
        
        for _ in range(count):
            result = await self.process_next()
            if result:
                results.append(result)
        
        return results
    
    async def _process_frame_via_mcp(
        self,
        queued_frame: QueuedVisionFrame
    ) -> dict[str, Any]:
        """
        Process a vision frame through LeanMCP tools.
        
        Uses the MCP server to invoke tools in sequence:
        1. analyze_vision - Extract insights
        2. detect_contradictions - Compare with telemetry
        3. predict_issues - Generate predictions
        4. recommend_action - Get recommendation
        5. create_decision_card - Build decision card
        
        Args:
            queued_frame: The queued vision frame
            
        Returns:
            Complete processing result
        """
        from ..integrations.leanmcp.server import get_mcp_server, MCPRequest
        from ..integrations.leanmcp.tools import (
            analyze_vision,
            detect_contradictions,
            predict_issues,
            recommend_action,
            create_decision_card,
        )
        from ..services.data_loader import get_data_loader
        
        mcp_server = get_mcp_server()
        frame_data = queued_frame.frame_data
        
        result = {
            "frame_id": queued_frame.frame_id,
            "timeline_time_sec": queued_frame.timeline_time_sec,
            "received_at": queued_frame.received_at.isoformat(),
            "processing_delay_ms": self.delay_ms,
            "steps": {},
        }
        
        try:
            # Step 1: Analyze vision via MCP
            analysis_request = MCPRequest(
                tool_name="analyze_vision",
                parameters={"vision_frame": frame_data}
            )
            analysis_response = mcp_server.invoke(analysis_request)
            
            if analysis_response.success:
                result["steps"]["analyze_vision"] = analysis_response.result
            else:
                # Fallback to direct call
                result["steps"]["analyze_vision"] = analyze_vision(frame_data)
            
            vision_analysis = result["steps"]["analyze_vision"]
            
            # Step 2: Get telemetry for contradiction detection
            telemetry_dict = {}
            try:
                data_loader = get_data_loader()
                scenario_data = data_loader.load_fixed_scenario()
                telemetry = data_loader.get_telemetry_at_time(
                    scenario_data.telemetry,
                    queued_frame.timeline_time_sec
                )
                telemetry_dict = {k: v.model_dump() for k, v in telemetry.items()}
            except Exception:
                pass  # Use empty telemetry if not available
            
            result["telemetry_snapshot"] = telemetry_dict
            
            # Step 3: Detect contradictions via MCP
            contradict_request = MCPRequest(
                tool_name="detect_contradictions",
                parameters={
                    "vision_frame": frame_data,
                    "telemetry": telemetry_dict
                }
            )
            contradict_response = mcp_server.invoke(contradict_request)
            
            if contradict_response.success:
                result["steps"]["detect_contradictions"] = contradict_response.result
            else:
                result["steps"]["detect_contradictions"] = detect_contradictions(
                    vision_frame=frame_data,
                    telemetry=telemetry_dict
                )
            
            contradictions = result["steps"]["detect_contradictions"]
            
            # Step 4: Predict issues via MCP
            predict_request = MCPRequest(
                tool_name="predict_issues",
                parameters={
                    "vision_frame": frame_data,
                    "telemetry": telemetry_dict,
                    "history": []
                }
            )
            predict_response = mcp_server.invoke(predict_request)
            
            if predict_response.success:
                result["steps"]["predict_issues"] = predict_response.result
            else:
                result["steps"]["predict_issues"] = predict_issues(
                    vision_frame=frame_data,
                    telemetry=telemetry_dict,
                    history=[]
                )
            
            predictions = result["steps"]["predict_issues"]
            
            # Step 5: Generate recommendation via MCP
            recommend_request = MCPRequest(
                tool_name="recommend_action",
                parameters={
                    "incident_state": {"severity": "warning", "state": "open"},
                    "evidence": {
                        "contradictions": contradictions,
                        "predictions": predictions,
                        "vision_analysis": vision_analysis
                    },
                    "trust_score": 0.5
                }
            )
            recommend_response = mcp_server.invoke(recommend_request)
            
            if recommend_response.success:
                result["steps"]["recommend_action"] = recommend_response.result
            else:
                result["steps"]["recommend_action"] = recommend_action(
                    incident_state={"severity": "warning", "state": "open"},
                    evidence={
                        "contradictions": contradictions,
                        "predictions": predictions,
                        "vision_analysis": vision_analysis
                    },
                    trust_score=0.5
                )
            
            recommendation = result["steps"]["recommend_action"]
            
            # Determine if incident creation is needed
            has_safety_event = len(frame_data.get("safety_events", [])) > 0
            has_contradiction = len(contradictions) > 0
            
            result["requires_incident"] = has_safety_event or has_contradiction
            result["contradictions_count"] = len(contradictions)
            result["predictions_count"] = len(predictions)
            
            # Step 6: Create decision card if needed
            if result["requires_incident"]:
                incident_id = f"inc_{uuid4().hex[:12]}"
                
                card_request = MCPRequest(
                    tool_name="create_decision_card",
                    parameters={
                        "incident_id": incident_id,
                        "findings": {
                            "contradictions": contradictions,
                            "predictions": predictions,
                            "recommendation": recommendation,
                            "trust_score": 0.5,
                            "telemetry": telemetry_dict,
                            "vision": frame_data
                        },
                        "operator_questions": []
                    }
                )
                card_response = mcp_server.invoke(card_request)
                
                if card_response.success:
                    result["steps"]["create_decision_card"] = card_response.result
                else:
                    result["steps"]["create_decision_card"] = create_decision_card(
                        incident_id=incident_id,
                        findings={
                            "contradictions": contradictions,
                            "predictions": predictions,
                            "recommendation": recommendation,
                            "trust_score": 0.5,
                            "telemetry": telemetry_dict,
                            "vision": frame_data
                        },
                        operator_questions=[]
                    )
                
                result["incident_id"] = incident_id
                result["decision_card"] = result["steps"]["create_decision_card"]
            
            result["success"] = True
            result["processed_at"] = datetime.now(timezone.utc).isoformat()
            
        except Exception as e:
            result["success"] = False
            result["error"] = str(e)
        
        return result
    
    def add_callback(self, callback):
        """Add a callback to be called after each frame is processed."""
        self._callbacks.append(callback)
    
    def get_status(self) -> dict[str, Any]:
        """Get current queue status."""
        return {
            "is_running": self._is_running,
            "queue_size": len(self._queue),
            "processed_count": self._processed_count,
            "delay_ms": self.delay_ms,
            "batch_size": self.batch_size,
            "timeline_sync_enabled": config.vision_timeline_sync,
            "timeline_offset_sec": self._timeline_offset_sec,
        }


# Singleton instance
_vision_queue: Optional[VisionProcessingQueue] = None


def get_vision_queue() -> VisionProcessingQueue:
    """Get or create the vision processing queue."""
    global _vision_queue
    if _vision_queue is None:
        _vision_queue = VisionProcessingQueue()
    return _vision_queue


async def process_vision_with_delay(
    frame_data: dict[str, Any],
    scenario_id: Optional[str] = None,
    delay_override_ms: Optional[int] = None,
) -> dict[str, Any]:
    """
    Process a single vision frame with delay.
    
    Convenience function for processing a single frame without
    using the full queue system.
    
    Args:
        frame_data: Vision frame data from Overshoot
        scenario_id: Associated scenario ID
        delay_override_ms: Override the default delay
        
    Returns:
        Processing result
    """
    queue = get_vision_queue()
    
    if not queue._is_running:
        queue.start()
    
    # Enqueue the frame
    queued = queue.enqueue(frame_data, scenario_id)
    
    # Apply delay override if specified
    original_delay = config.vision_processing_delay_ms
    if delay_override_ms is not None:
        # Temporarily override (not thread-safe, but works for demo)
        config.vision_processing_delay_ms = delay_override_ms
    
    try:
        # Process immediately
        result = await queue.process_next()
        return result or {"success": False, "error": "Queue was empty"}
    finally:
        # Restore original delay
        if delay_override_ms is not None:
            config.vision_processing_delay_ms = original_delay
