"""
Audit Logger - Tamper-evident audit trail for all system events.

Creates append-only JSON event logs with hash chaining for integrity verification.
"""

import json
import hashlib
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field

from ..db import AuditRepository, get_db


# ============================================================================
# Audit Event Types
# ============================================================================

AuditEventType = Literal[
    # Incident lifecycle
    "incident_opened",
    "incident_triaged",
    "incident_dispatched",
    "incident_closed",
    
    # Detection events
    "contradiction_detected",
    "contradiction_resolved",
    "prediction_generated",
    "safety_event_detected",
    
    # Trust events
    "trust_updated",
    "trust_receipt_generated",
    
    # Operator events
    "operator_assigned",
    "question_asked",
    "question_answered",
    "action_taken",
    "action_confirmed",
    
    # Vision events (Overshoot)
    "vision_frame_received",
    "vision_analysis_complete",
    "vision_equipment_detected",
    "vision_safety_event",
    
    # Artifact events
    "artifact_created",
    "artifact_exported",
    "artifact_anchored",
    
    # Mode events
    "mode_changed",
    
    # System events
    "scenario_started",
    "scenario_ended",
    "system_error"
]


# ============================================================================
# Audit Event Model
# ============================================================================

class AuditLogEvent(BaseModel):
    """Single audit log event with hash chaining."""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    sequence_number: int
    
    # Event classification
    event_type: AuditEventType
    severity: str = "info"  # info, warning, error, critical
    
    # Context
    scenario_id: Optional[str] = None
    incident_id: Optional[str] = None
    operator_id: Optional[str] = None
    
    # Event data
    summary: str
    data: Dict[str, Any] = Field(default_factory=dict)
    
    # Integrity chain
    previous_hash: str
    content_hash: str = ""  # Computed after creation
    
    def compute_hash(self) -> str:
        """Compute SHA256 hash of event content."""
        content = {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "sequence_number": self.sequence_number,
            "event_type": self.event_type,
            "severity": self.severity,
            "scenario_id": self.scenario_id,
            "incident_id": self.incident_id,
            "operator_id": self.operator_id,
            "summary": self.summary,
            "data": self.data,
            "previous_hash": self.previous_hash
        }
        content_str = json.dumps(content, sort_keys=True, default=str)
        return hashlib.sha256(content_str.encode()).hexdigest()


# ============================================================================
# Audit Logger
# ============================================================================

class AuditLogger:
    """
    Tamper-evident audit trail logger.
    
    Features:
    - Append-only event log
    - SHA256 hash chaining for integrity
    - JSON export for verification
    - Event filtering and queries
    """
    
    GENESIS_HASH = "0" * 64  # Genesis block hash
    
    def __init__(self, log_dir: Optional[Path] = None):
        """
        Initialize the audit logger.
        
        Args:
            log_dir: Directory for storing audit logs
        """
        self._events: List[AuditLogEvent] = []
        self._sequence_counter = 0
        self._latest_hash = self.GENESIS_HASH
        
        if log_dir:
            self.log_dir = Path(log_dir)
            self.log_dir.mkdir(parents=True, exist_ok=True)
        else:
            self.log_dir = None
        
        # MongoDB repository (if enabled)
        self._repo: Optional[AuditRepository] = None
        if get_db().enabled:
            try:
                self._repo = AuditRepository()
            except Exception as e:
                print(f"Warning: Could not initialize AuditRepository: {e}")
    
    # ========================================================================
    # Event Logging
    # ========================================================================
    
    def log(
        self,
        event_type: AuditEventType,
        summary: str,
        data: Optional[Dict[str, Any]] = None,
        scenario_id: Optional[str] = None,
        incident_id: Optional[str] = None,
        operator_id: Optional[str] = None,
        severity: str = "info"
    ) -> AuditLogEvent:
        """
        Log an audit event.
        
        Args:
            event_type: Type of event
            summary: Human-readable summary
            data: Event-specific data
            scenario_id: Related scenario ID
            incident_id: Related incident ID
            operator_id: Related operator ID
            severity: Event severity
            
        Returns:
            The created AuditLogEvent
        """
        self._sequence_counter += 1
        
        event = AuditLogEvent(
            sequence_number=self._sequence_counter,
            event_type=event_type,
            severity=severity,
            summary=summary,
            data=data or {},
            scenario_id=scenario_id,
            incident_id=incident_id,
            operator_id=operator_id,
            previous_hash=self._latest_hash
        )
        
        # Compute and set content hash
        event.content_hash = event.compute_hash()
        self._latest_hash = event.content_hash
        
        # Store event
        self._events.append(event)
        
        # Persist to file if log_dir configured
        if self.log_dir:
            self._persist_event_to_file(event)
        
        # Persist to MongoDB if enabled
        self._persist_event_to_db(event)
        
        return event
    
    def _persist_event_to_file(self, event: AuditLogEvent):
        """Persist event to file."""
        log_file = self.log_dir / f"audit_{event.scenario_id or 'global'}.jsonl"
        with open(log_file, "a") as f:
            f.write(event.model_dump_json() + "\n")
    
    def _persist_event_to_db(self, event: AuditLogEvent):
        """Persist event to MongoDB if enabled"""
        if self._repo:
            try:
                event_dict = event.model_dump()
                # Convert datetime to ISO string for MongoDB
                event_dict["timestamp"] = event.timestamp.isoformat()
                self._repo.insert_audit_event(event_dict)
            except Exception as e:
                print(f"Warning: Failed to persist audit event to MongoDB: {e}")
    
    # ========================================================================
    # Convenience Methods
    # ========================================================================
    
    def log_incident_opened(
        self,
        incident_id: str,
        scenario_id: str,
        title: str,
        contradiction_ids: List[str]
    ) -> AuditLogEvent:
        """Log incident opened event."""
        return self.log(
            event_type="incident_opened",
            summary=f"Incident opened: {title}",
            data={
                "title": title,
                "contradiction_ids": contradiction_ids,
                "contradiction_count": len(contradiction_ids)
            },
            scenario_id=scenario_id,
            incident_id=incident_id,
            severity="warning"
        )
    
    def log_incident_triaged(
        self,
        incident_id: str,
        scenario_id: str,
        operator_id: str,
        assessment: str
    ) -> AuditLogEvent:
        """Log incident triaged event."""
        return self.log(
            event_type="incident_triaged",
            summary=f"Incident triaged by operator",
            data={"assessment": assessment},
            scenario_id=scenario_id,
            incident_id=incident_id,
            operator_id=operator_id
        )
    
    def log_incident_dispatched(
        self,
        incident_id: str,
        scenario_id: str,
        operator_id: str,
        action_type: str,
        action_details: str
    ) -> AuditLogEvent:
        """Log incident dispatched event."""
        return self.log(
            event_type="incident_dispatched",
            summary=f"Action dispatched: {action_type}",
            data={
                "action_type": action_type,
                "action_details": action_details
            },
            scenario_id=scenario_id,
            incident_id=incident_id,
            operator_id=operator_id
        )
    
    def log_incident_closed(
        self,
        incident_id: str,
        scenario_id: str,
        operator_id: str,
        resolution: str
    ) -> AuditLogEvent:
        """Log incident closed event."""
        return self.log(
            event_type="incident_closed",
            summary=f"Incident closed: {resolution[:50]}...",
            data={"resolution": resolution},
            scenario_id=scenario_id,
            incident_id=incident_id,
            operator_id=operator_id
        )
    
    def log_contradiction_detected(
        self,
        incident_id: str,
        scenario_id: str,
        contradiction_id: str,
        reason_code: str,
        description: str
    ) -> AuditLogEvent:
        """Log contradiction detected event."""
        return self.log(
            event_type="contradiction_detected",
            summary=f"Contradiction detected: {reason_code}",
            data={
                "contradiction_id": contradiction_id,
                "reason_code": reason_code,
                "description": description
            },
            scenario_id=scenario_id,
            incident_id=incident_id,
            severity="warning"
        )
    
    def log_trust_updated(
        self,
        incident_id: str,
        scenario_id: str,
        trust_score: float,
        reason: str
    ) -> AuditLogEvent:
        """Log trust score update."""
        return self.log(
            event_type="trust_updated",
            summary=f"Trust score updated to {trust_score:.2f}",
            data={
                "trust_score": trust_score,
                "reason": reason
            },
            scenario_id=scenario_id,
            incident_id=incident_id
        )
    
    def log_question_asked(
        self,
        incident_id: str,
        scenario_id: str,
        question_id: str,
        question_text: str
    ) -> AuditLogEvent:
        """Log question asked to operator."""
        return self.log(
            event_type="question_asked",
            summary=f"Question asked: {question_text[:50]}...",
            data={
                "question_id": question_id,
                "question_text": question_text
            },
            scenario_id=scenario_id,
            incident_id=incident_id
        )
    
    def log_question_answered(
        self,
        incident_id: str,
        scenario_id: str,
        operator_id: str,
        question_id: str,
        answer: Any,
        impact: Dict[str, Any]
    ) -> AuditLogEvent:
        """Log operator answer to question."""
        return self.log(
            event_type="question_answered",
            summary=f"Question answered by operator",
            data={
                "question_id": question_id,
                "answer": str(answer),
                "impact": impact
            },
            scenario_id=scenario_id,
            incident_id=incident_id,
            operator_id=operator_id
        )
    
    def log_action_taken(
        self,
        incident_id: str,
        scenario_id: str,
        operator_id: str,
        action_id: str,
        action_type: str,
        rationale: str
    ) -> AuditLogEvent:
        """Log operator action taken."""
        return self.log(
            event_type="action_taken",
            summary=f"Action taken: {action_type}",
            data={
                "action_id": action_id,
                "action_type": action_type,
                "rationale": rationale
            },
            scenario_id=scenario_id,
            incident_id=incident_id,
            operator_id=operator_id
        )
    
    def log_vision_received(
        self,
        scenario_id: str,
        frame_id: str,
        equipment_count: int,
        safety_event_count: int
    ) -> AuditLogEvent:
        """Log vision frame received from Overshoot."""
        return self.log(
            event_type="vision_frame_received",
            summary=f"Vision frame received: {equipment_count} equipment, {safety_event_count} events",
            data={
                "frame_id": frame_id,
                "equipment_detected": equipment_count,
                "safety_events": safety_event_count
            },
            scenario_id=scenario_id
        )
    
    def log_artifact_created(
        self,
        incident_id: str,
        scenario_id: str,
        artifact_id: str,
        content_hash: str
    ) -> AuditLogEvent:
        """Log artifact creation."""
        return self.log(
            event_type="artifact_created",
            summary=f"Artifact created: {artifact_id}",
            data={
                "artifact_id": artifact_id,
                "content_hash": content_hash
            },
            scenario_id=scenario_id,
            incident_id=incident_id
        )
    
    def log_artifact_anchored(
        self,
        incident_id: str,
        scenario_id: str,
        artifact_id: str,
        tx_hash: str,
        chain: str = "solana"
    ) -> AuditLogEvent:
        """Log artifact anchored on chain."""
        return self.log(
            event_type="artifact_anchored",
            summary=f"Artifact anchored on {chain}",
            data={
                "artifact_id": artifact_id,
                "tx_hash": tx_hash,
                "chain": chain
            },
            scenario_id=scenario_id,
            incident_id=incident_id
        )
    
    def log_mode_changed(
        self,
        scenario_id: str,
        from_mode: str,
        to_mode: str,
        trigger: str
    ) -> AuditLogEvent:
        """Log UI mode change."""
        return self.log(
            event_type="mode_changed",
            summary=f"Mode changed: {from_mode} → {to_mode}",
            data={
                "from_mode": from_mode,
                "to_mode": to_mode,
                "trigger": trigger
            },
            scenario_id=scenario_id
        )
    
    # ========================================================================
    # Queries
    # ========================================================================
    
    def get_events(
        self,
        scenario_id: Optional[str] = None,
        incident_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        limit: int = 100
    ) -> List[AuditLogEvent]:
        """Query audit events with filters."""
        events = self._events
        
        if scenario_id:
            events = [e for e in events if e.scenario_id == scenario_id]
        
        if incident_id:
            events = [e for e in events if e.incident_id == incident_id]
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        return events[-limit:]
    
    def get_incident_trail(self, incident_id: str) -> List[AuditLogEvent]:
        """Get complete audit trail for an incident."""
        return [e for e in self._events if e.incident_id == incident_id]
    
    def get_latest_hash(self) -> str:
        """Get the latest hash in the chain."""
        return self._latest_hash
    
    # ========================================================================
    # Integrity Verification
    # ========================================================================
    
    def verify_chain(self) -> bool:
        """Verify the integrity of the audit chain."""
        if not self._events:
            return True
        
        expected_hash = self.GENESIS_HASH
        
        for event in self._events:
            # Verify previous hash
            if event.previous_hash != expected_hash:
                return False
            
            # Verify content hash
            computed_hash = event.compute_hash()
            if event.content_hash != computed_hash:
                return False
            
            expected_hash = event.content_hash
        
        return True
    
    def export_chain(self, scenario_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Export audit chain as JSON-serializable list."""
        events = self._events
        if scenario_id:
            events = [e for e in events if e.scenario_id == scenario_id]
        
        return [e.model_dump(mode="json") for e in events]


# ============================================================================
# Singleton instance
# ============================================================================

_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get the singleton AuditLogger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger
