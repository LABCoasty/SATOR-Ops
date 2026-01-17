"""
WebSocket API - Real-time updates for SATOR dashboard.

Streams:
- Telemetry updates
- Vision events (from Overshoot)
- Contradiction detections
- Prediction alerts
- Decision cards
- Trust receipt updates
- Incident state transitions
- Mode changes
- Artifact ready events
"""

from typing import Set, Dict, List, Any, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import asyncio
from datetime import datetime
from enum import Enum

from ..data.seed_data import generate_telemetry_channels, generate_signal_summary


router = APIRouter()


# ============================================================================
# Event Types
# ============================================================================

class EventType(str, Enum):
    # Connection
    CONNECTED = "connected"
    SUBSCRIBED = "subscribed"
    UNSUBSCRIBED = "unsubscribed"
    ERROR = "error"
    PONG = "pong"
    
    # Telemetry
    TELEMETRY_UPDATE = "telemetry_update"
    
    # Vision (Overshoot)
    VISION_FRAME = "vision_frame"
    VISION_ANALYSIS = "vision_analysis"
    VISION_EQUIPMENT = "vision_equipment"
    VISION_SAFETY_EVENT = "vision_safety_event"
    
    # Contradictions
    CONTRADICTION_DETECTED = "contradiction_detected"
    CONTRADICTION_RESOLVED = "contradiction_resolved"
    
    # Predictions
    PREDICTION_ALERT = "prediction_alert"
    
    # Decisions
    DECISION_CARD_CREATED = "decision_card_created"
    DECISION_CARD_UPDATED = "decision_card_updated"
    DECISION_ACTION_TAKEN = "decision_action_taken"
    
    # Trust
    TRUST_UPDATED = "trust_updated"
    TRUST_RECEIPT_GENERATED = "trust_receipt_generated"
    
    # Incidents
    INCIDENT_OPENED = "incident_opened"
    INCIDENT_STATE_CHANGED = "incident_state_changed"
    INCIDENT_CLOSED = "incident_closed"
    
    # Questions
    QUESTION_ASKED = "question_asked"
    QUESTION_ANSWERED = "question_answered"
    
    # Artifacts
    ARTIFACT_READY = "artifact_ready"
    ARTIFACT_ANCHORED = "artifact_anchored"
    
    # Mode
    MODE_CHANGED = "mode_changed"
    
    # Scenario
    SCENARIO_STARTED = "scenario_started"
    SCENARIO_ENDED = "scenario_ended"


# ============================================================================
# Connection Manager
# ============================================================================

class ConnectionManager:
    """
    Manages WebSocket connections and event broadcasting.
    
    Features:
    - Connection tracking
    - Channel subscriptions
    - Targeted and broadcast messaging
    - Event queuing
    """
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.subscriptions: Dict[WebSocket, Set[str]] = {}
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
    
    async def connect(self, websocket: WebSocket):
        """Accept and track a new connection."""
        await websocket.accept()
        self.active_connections.add(websocket)
        self.subscriptions[websocket] = set()
    
    def disconnect(self, websocket: WebSocket):
        """Remove a disconnected client."""
        self.active_connections.discard(websocket)
        self.subscriptions.pop(websocket, None)
    
    def subscribe(self, websocket: WebSocket, channel: str):
        """Subscribe a connection to a channel."""
        if websocket in self.subscriptions:
            self.subscriptions[websocket].add(channel)
    
    def unsubscribe(self, websocket: WebSocket, channel: str):
        """Unsubscribe a connection from a channel."""
        if websocket in self.subscriptions:
            self.subscriptions[websocket].discard(channel)
    
    async def broadcast(self, message: dict, channel: Optional[str] = None):
        """
        Broadcast message to all connections or channel subscribers.
        
        Args:
            message: Message to send
            channel: Optional channel to target
        """
        for connection in list(self.active_connections):
            try:
                if channel:
                    if channel in self.subscriptions.get(connection, set()):
                        await connection.send_json(message)
                else:
                    await connection.send_json(message)
            except Exception:
                self.disconnect(connection)
    
    async def send_personal(self, websocket: WebSocket, message: dict):
        """Send message to a specific connection."""
        try:
            await websocket.send_json(message)
        except Exception:
            self.disconnect(websocket)
    
    async def broadcast_event(
        self,
        event_type: EventType,
        data: Dict[str, Any],
        channel: Optional[str] = None
    ):
        """
        Broadcast a typed event.
        
        Args:
            event_type: Type of event
            data: Event data
            channel: Optional channel to target
        """
        message = {
            "type": event_type.value,
            "timestamp": datetime.utcnow().isoformat(),
            **data
        }
        await self.broadcast(message, channel)
    
    def queue_event(self, event_type: EventType, data: Dict[str, Any], channel: Optional[str] = None):
        """Queue an event for async broadcast."""
        self._event_queue.put_nowait({
            "event_type": event_type,
            "data": data,
            "channel": channel
        })


# Global manager instance
manager = ConnectionManager()


# ============================================================================
# Event Emission Functions (called by other services)
# ============================================================================

async def emit_vision_frame(frame_data: Dict[str, Any]):
    """Emit a vision frame event."""
    await manager.broadcast_event(
        EventType.VISION_FRAME,
        {"frame": frame_data},
        channel="vision"
    )


async def emit_contradiction_detected(contradiction: Dict[str, Any], incident_id: str):
    """Emit a contradiction detection event."""
    await manager.broadcast_event(
        EventType.CONTRADICTION_DETECTED,
        {
            "contradiction": contradiction,
            "incident_id": incident_id
        },
        channel="contradictions"
    )


async def emit_prediction_alert(prediction: Dict[str, Any], incident_id: Optional[str] = None):
    """Emit a prediction alert event."""
    await manager.broadcast_event(
        EventType.PREDICTION_ALERT,
        {
            "prediction": prediction,
            "incident_id": incident_id
        },
        channel="predictions"
    )


async def emit_decision_card(card: Dict[str, Any]):
    """Emit a new decision card event."""
    await manager.broadcast_event(
        EventType.DECISION_CARD_CREATED,
        {"card": card},
        channel="decisions"
    )


async def emit_trust_updated(incident_id: str, trust_score: float, reason: str):
    """Emit a trust score update event."""
    await manager.broadcast_event(
        EventType.TRUST_UPDATED,
        {
            "incident_id": incident_id,
            "trust_score": trust_score,
            "reason": reason
        },
        channel="trust"
    )


async def emit_incident_state_changed(
    incident_id: str,
    from_state: str,
    to_state: str,
    triggered_by: str
):
    """Emit an incident state change event."""
    await manager.broadcast_event(
        EventType.INCIDENT_STATE_CHANGED,
        {
            "incident_id": incident_id,
            "from_state": from_state,
            "to_state": to_state,
            "triggered_by": triggered_by
        },
        channel="incidents"
    )


async def emit_mode_changed(from_mode: str, to_mode: str, trigger: str):
    """Emit a mode change event."""
    await manager.broadcast_event(
        EventType.MODE_CHANGED,
        {
            "from_mode": from_mode,
            "to_mode": to_mode,
            "trigger": trigger
        }
    )


async def emit_artifact_ready(artifact_id: str, incident_id: str, content_hash: str):
    """Emit an artifact ready event."""
    await manager.broadcast_event(
        EventType.ARTIFACT_READY,
        {
            "artifact_id": artifact_id,
            "incident_id": incident_id,
            "content_hash": content_hash
        },
        channel="artifacts"
    )


async def emit_question_asked(question: Dict[str, Any], incident_id: str):
    """Emit an operator question event."""
    await manager.broadcast_event(
        EventType.QUESTION_ASKED,
        {
            "question": question,
            "incident_id": incident_id
        },
        channel="questions"
    )


# ============================================================================
# Telemetry Streaming
# ============================================================================

async def telemetry_stream(websocket: WebSocket):
    """Stream telemetry updates every 2 seconds."""
    while True:
        try:
            if "telemetry" in manager.subscriptions.get(websocket, set()):
                channels = generate_telemetry_channels()
                summary = generate_signal_summary()
                
                await manager.send_personal(websocket, {
                    "type": EventType.TELEMETRY_UPDATE.value,
                    "timestamp": datetime.utcnow().isoformat(),
                    "channels": channels,
                    "summary": summary,
                })
            await asyncio.sleep(2)
        except Exception:
            break


# ============================================================================
# WebSocket Endpoints
# ============================================================================

@router.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    """
    Main WebSocket endpoint for real-time updates.
    
    Supports subscribing to channels:
    - telemetry: Sensor telemetry updates
    - vision: Overshoot vision events
    - contradictions: Contradiction detections
    - predictions: Prediction alerts
    - decisions: Decision card events
    - trust: Trust score updates
    - incidents: Incident state changes
    - questions: Operator questions
    - artifacts: Artifact events
    """
    await manager.connect(websocket)
    
    # Start telemetry streaming task
    stream_task = asyncio.create_task(telemetry_stream(websocket))
    
    try:
        await manager.send_personal(
            websocket,
            {
                "type": EventType.CONNECTED.value,
                "message": "Connected to SATOR real-time feed",
                "timestamp": datetime.utcnow().isoformat(),
                "available_channels": [
                    "telemetry", "vision", "contradictions", "predictions",
                    "decisions", "trust", "incidents", "questions", "artifacts"
                ]
            },
        )
        
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                msg_type = message.get("type")
                
                if msg_type == "subscribe":
                    channel = message.get("channel")
                    manager.subscribe(websocket, channel)
                    await manager.send_personal(
                        websocket,
                        {
                            "type": EventType.SUBSCRIBED.value,
                            "channel": channel,
                            "timestamp": datetime.utcnow().isoformat(),
                        },
                    )
                    
                    # Send initial data for the channel
                    if channel == "telemetry":
                        channels = generate_telemetry_channels()
                        summary = generate_signal_summary()
                        await manager.send_personal(websocket, {
                            "type": EventType.TELEMETRY_UPDATE.value,
                            "timestamp": datetime.utcnow().isoformat(),
                            "channels": channels,
                            "summary": summary,
                        })
                
                elif msg_type == "unsubscribe":
                    channel = message.get("channel")
                    manager.unsubscribe(websocket, channel)
                    await manager.send_personal(
                        websocket,
                        {
                            "type": EventType.UNSUBSCRIBED.value,
                            "channel": channel
                        },
                    )
                
                elif msg_type == "ping":
                    await manager.send_personal(
                        websocket,
                        {
                            "type": EventType.PONG.value,
                            "timestamp": datetime.utcnow().isoformat()
                        },
                    )
                
                elif msg_type == "get_telemetry":
                    channels = generate_telemetry_channels()
                    await manager.send_personal(websocket, {
                        "type": "telemetry_data",
                        "channels": channels,
                        "timestamp": datetime.utcnow().isoformat(),
                    })
                
                elif msg_type == "get_summary":
                    summary = generate_signal_summary()
                    await manager.send_personal(websocket, {
                        "type": "summary_data",
                        "summary": summary,
                        "timestamp": datetime.utcnow().isoformat(),
                    })
                    
            except json.JSONDecodeError:
                await manager.send_personal(
                    websocket,
                    {
                        "type": EventType.ERROR.value,
                        "message": "Invalid JSON"
                    }
                )
                
    except WebSocketDisconnect:
        stream_task.cancel()
        manager.disconnect(websocket)


@router.websocket("/telemetry")
async def telemetry_websocket(websocket: WebSocket):
    """Dedicated WebSocket for telemetry streaming."""
    await manager.connect(websocket)
    manager.subscribe(websocket, "telemetry")
    
    try:
        # Send initial data
        channels = generate_telemetry_channels()
        summary = generate_signal_summary()
        
        await manager.send_personal(websocket, {
            "type": EventType.TELEMETRY_UPDATE.value,
            "timestamp": datetime.utcnow().isoformat(),
            "channels": channels,
            "summary": summary,
        })
        
        # Start streaming
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=2.0)
                message = json.loads(data)
                if message.get("type") == "ping":
                    await manager.send_personal(websocket, {"type": "pong"})
            except asyncio.TimeoutError:
                pass
            
            # Send update
            channels = generate_telemetry_channels()
            summary = generate_signal_summary()
            
            await manager.send_personal(websocket, {
                "type": EventType.TELEMETRY_UPDATE.value,
                "timestamp": datetime.utcnow().isoformat(),
                "channels": channels,
                "summary": summary,
            })
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.websocket("/decisions")
async def decisions_websocket(websocket: WebSocket):
    """WebSocket for decision card updates."""
    await manager.connect(websocket)
    manager.subscribe(websocket, "decisions")
    manager.subscribe(websocket, "questions")
    manager.subscribe(websocket, "trust")
    
    try:
        await manager.send_personal(
            websocket,
            {
                "type": EventType.CONNECTED.value,
                "message": "Connected to decisions feed",
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
        
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "ping":
                await manager.send_personal(websocket, {"type": "pong"})
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.websocket("/mode")
async def mode_websocket(websocket: WebSocket):
    """WebSocket for mode transition updates."""
    await manager.connect(websocket)
    
    try:
        await manager.send_personal(
            websocket,
            {
                "type": EventType.MODE_CHANGED.value,
                "from_mode": None,
                "to_mode": "data_ingest",
                "trigger": "initial",
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
        
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "set_mode":
                new_mode = message.get("mode", "data_ingest")
                old_mode = message.get("current_mode", "data_ingest")
                
                await manager.broadcast({
                    "type": EventType.MODE_CHANGED.value,
                    "from_mode": old_mode,
                    "to_mode": new_mode,
                    "trigger": "operator",
                    "timestamp": datetime.utcnow().isoformat(),
                })
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.websocket("/vision")
async def vision_websocket(websocket: WebSocket):
    """WebSocket for Overshoot vision events."""
    await manager.connect(websocket)
    manager.subscribe(websocket, "vision")
    
    try:
        await manager.send_personal(
            websocket,
            {
                "type": EventType.CONNECTED.value,
                "message": "Connected to vision feed",
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
        
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "ping":
                await manager.send_personal(websocket, {"type": "pong"})
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
