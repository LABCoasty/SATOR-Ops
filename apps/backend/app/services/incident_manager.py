"""
Incident Manager - State machine and lifecycle management for incidents.

Manages incident lifecycle: Open → Triaged → Dispatched → Closed
Each transition generates audit log entries and can trigger artifact creation.
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any, Callable
from enum import Enum
from pydantic import BaseModel, Field

from ..db import IncidentRepository, get_db


# ============================================================================
# Incident States and Transitions
# ============================================================================

class IncidentState(str, Enum):
    """Incident lifecycle states."""
    MONITORING = "monitoring"  # No active incident
    OPEN = "open"              # Contradiction detected, incident created
    TRIAGED = "triaged"        # Operator has reviewed and taken initial action
    DISPATCHED = "dispatched"  # Field action dispatched (defer/escalate)
    CLOSED = "closed"          # Incident resolved, ready for artifact


class IncidentSeverity(str, Enum):
    """Incident severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class StateTransition(BaseModel):
    """Record of a state transition."""
    transition_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    from_state: IncidentState
    to_state: IncidentState
    triggered_by: str  # operator_id or "system"
    reason: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Incident Model
# ============================================================================

class Incident(BaseModel):
    """Complete incident record."""
    incident_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    scenario_id: str
    
    # State
    state: IncidentState = IncidentState.OPEN
    severity: IncidentSeverity = IncidentSeverity.WARNING
    
    # Timing
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    triaged_at: Optional[datetime] = None
    dispatched_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    
    # Summary
    title: str
    description: str
    
    # Evidence references
    contradiction_ids: List[str] = Field(default_factory=list)
    decision_card_id: Optional[str] = None
    trust_receipt_ids: List[str] = Field(default_factory=list)
    
    # Operator interaction
    assigned_operator_id: Optional[str] = None
    questions_asked: List[str] = Field(default_factory=list)  # question_ids
    questions_answered: List[str] = Field(default_factory=list)
    
    # Resolution
    action_taken: Optional[str] = None
    action_rationale: Optional[str] = None
    resolution_summary: Optional[str] = None
    
    # Artifact
    artifact_id: Optional[str] = None
    on_chain_tx: Optional[str] = None
    
    # History
    state_transitions: List[StateTransition] = Field(default_factory=list)
    
    def can_transition_to(self, target_state: IncidentState) -> bool:
        """Check if transition to target state is allowed."""
        valid_transitions = {
            IncidentState.MONITORING: [IncidentState.OPEN],
            IncidentState.OPEN: [IncidentState.TRIAGED],
            IncidentState.TRIAGED: [IncidentState.DISPATCHED, IncidentState.CLOSED],
            IncidentState.DISPATCHED: [IncidentState.CLOSED],
            IncidentState.CLOSED: [],  # Terminal state
        }
        return target_state in valid_transitions.get(self.state, [])


# ============================================================================
# Incident Manager
# ============================================================================

class IncidentManager:
    """
    Manages incident lifecycle and state transitions.
    
    Responsibilities:
    - Create incidents when contradictions detected
    - Manage state transitions
    - Track operator interactions
    - Trigger artifact creation on close
    """
    
    # Valid state transitions
    VALID_TRANSITIONS = {
        IncidentState.MONITORING: [IncidentState.OPEN],
        IncidentState.OPEN: [IncidentState.TRIAGED],
        IncidentState.TRIAGED: [IncidentState.DISPATCHED, IncidentState.CLOSED],
        IncidentState.DISPATCHED: [IncidentState.CLOSED],
        IncidentState.CLOSED: [],
    }
    
    def __init__(self):
        self._incidents: Dict[str, Incident] = {}
        self._scenario_incidents: Dict[str, List[str]] = {}  # scenario_id -> incident_ids
        self._transition_handlers: List[Callable[[Incident, StateTransition], None]] = []
        self._close_handlers: List[Callable[[Incident], None]] = []
        
        # MongoDB repository (if enabled)
        self._repo: Optional[IncidentRepository] = None
        if get_db().enabled:
            try:
                self._repo = IncidentRepository()
            except Exception as e:
                print(f"Warning: Could not initialize IncidentRepository: {e}")
    
    def _persist_incident(self, incident: Incident):
        """Persist incident to MongoDB if enabled"""
        if self._repo:
            try:
                incident_dict = incident.model_dump()
                # Convert enums to strings for MongoDB
                incident_dict["state"] = incident.state.value
                incident_dict["severity"] = incident.severity.value
                # Convert state transitions
                incident_dict["state_transitions"] = [
                    {
                        **t.model_dump(),
                        "from_state": t.from_state.value,
                        "to_state": t.to_state.value
                    }
                    for t in incident.state_transitions
                ]
                self._repo.upsert_incident(incident_dict)
            except Exception as e:
                print(f"Warning: Failed to persist incident to MongoDB: {e}")
    
    # ========================================================================
    # Incident Creation
    # ========================================================================
    
    def create_incident(
        self,
        scenario_id: str,
        title: str,
        description: str,
        severity: IncidentSeverity = IncidentSeverity.WARNING,
        contradiction_ids: Optional[List[str]] = None
    ) -> Incident:
        """
        Create a new incident.
        
        Args:
            scenario_id: The scenario this incident belongs to
            title: Incident title
            description: Incident description
            severity: Severity level
            contradiction_ids: Related contradiction IDs
            
        Returns:
            Created Incident
        """
        incident = Incident(
            scenario_id=scenario_id,
            title=title,
            description=description,
            severity=severity,
            contradiction_ids=contradiction_ids or [],
            state=IncidentState.OPEN
        )
        
        # Record initial transition
        transition = StateTransition(
            from_state=IncidentState.MONITORING,
            to_state=IncidentState.OPEN,
            triggered_by="system",
            reason="Contradiction detected - incident opened automatically",
            metadata={"contradiction_count": len(incident.contradiction_ids)}
        )
        incident.state_transitions.append(transition)
        
        # Store incident
        self._incidents[incident.incident_id] = incident
        
        if scenario_id not in self._scenario_incidents:
            self._scenario_incidents[scenario_id] = []
        self._scenario_incidents[scenario_id].append(incident.incident_id)
        
        # Persist to MongoDB
        self._persist_incident(incident)
        
        # Notify handlers
        self._notify_transition(incident, transition)
        
        return incident
    
    # ========================================================================
    # State Transitions
    # ========================================================================
    
    def transition_to(
        self,
        incident_id: str,
        target_state: IncidentState,
        triggered_by: str,
        reason: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Incident:
        """
        Transition an incident to a new state.
        
        Args:
            incident_id: The incident ID
            target_state: Target state
            triggered_by: Who triggered the transition
            reason: Reason for transition
            metadata: Additional transition metadata
            
        Returns:
            Updated Incident
        """
        incident = self._incidents.get(incident_id)
        if not incident:
            raise ValueError(f"Incident {incident_id} not found")
        
        # Validate transition
        if not incident.can_transition_to(target_state):
            raise ValueError(
                f"Invalid transition: {incident.state} → {target_state}"
            )
        
        # Record transition
        transition = StateTransition(
            from_state=incident.state,
            to_state=target_state,
            triggered_by=triggered_by,
            reason=reason,
            metadata=metadata or {}
        )
        
        # Update incident
        incident.state = target_state
        incident.updated_at = datetime.utcnow()
        incident.state_transitions.append(transition)
        
        # Update timestamps
        if target_state == IncidentState.TRIAGED:
            incident.triaged_at = datetime.utcnow()
        elif target_state == IncidentState.DISPATCHED:
            incident.dispatched_at = datetime.utcnow()
        elif target_state == IncidentState.CLOSED:
            incident.closed_at = datetime.utcnow()
            # Trigger close handlers
            self._notify_close(incident)
        
        # Persist to MongoDB
        self._persist_incident(incident)
        
        # Notify transition handlers
        self._notify_transition(incident, transition)
        
        return incident
    
    def triage(
        self,
        incident_id: str,
        operator_id: str,
        initial_assessment: str
    ) -> Incident:
        """Transition incident to TRIAGED state."""
        return self.transition_to(
            incident_id=incident_id,
            target_state=IncidentState.TRIAGED,
            triggered_by=operator_id,
            reason=initial_assessment,
            metadata={"operator_id": operator_id}
        )
    
    def dispatch(
        self,
        incident_id: str,
        operator_id: str,
        action_type: str,
        action_details: str
    ) -> Incident:
        """Transition incident to DISPATCHED state."""
        incident = self._incidents.get(incident_id)
        if incident:
            incident.action_taken = action_type
            incident.action_rationale = action_details
        
        return self.transition_to(
            incident_id=incident_id,
            target_state=IncidentState.DISPATCHED,
            triggered_by=operator_id,
            reason=f"Action dispatched: {action_type}",
            metadata={
                "operator_id": operator_id,
                "action_type": action_type,
                "action_details": action_details
            }
        )
    
    def close(
        self,
        incident_id: str,
        operator_id: str,
        resolution_summary: str,
        action_taken: Optional[str] = None,
        action_rationale: Optional[str] = None
    ) -> Incident:
        """Close an incident and prepare for artifact creation."""
        incident = self._incidents.get(incident_id)
        if incident:
            incident.resolution_summary = resolution_summary
            if action_taken:
                incident.action_taken = action_taken
            if action_rationale:
                incident.action_rationale = action_rationale
        
        return self.transition_to(
            incident_id=incident_id,
            target_state=IncidentState.CLOSED,
            triggered_by=operator_id,
            reason=resolution_summary,
            metadata={
                "operator_id": operator_id,
                "resolution_summary": resolution_summary
            }
        )
    
    # ========================================================================
    # Queries
    # ========================================================================
    
    def get_incident(self, incident_id: str) -> Optional[Incident]:
        """Get an incident by ID."""
        return self._incidents.get(incident_id)
    
    def get_incidents_for_scenario(self, scenario_id: str) -> List[Incident]:
        """Get all incidents for a scenario."""
        incident_ids = self._scenario_incidents.get(scenario_id, [])
        return [self._incidents[iid] for iid in incident_ids if iid in self._incidents]
    
    def get_open_incidents(self, scenario_id: Optional[str] = None) -> List[Incident]:
        """Get all open (non-closed) incidents."""
        incidents = self._incidents.values()
        if scenario_id:
            incidents = [i for i in incidents if i.scenario_id == scenario_id]
        return [i for i in incidents if i.state != IncidentState.CLOSED]
    
    def get_closed_incidents_pending_artifact(self) -> List[Incident]:
        """Get closed incidents that need artifact creation."""
        return [
            i for i in self._incidents.values()
            if i.state == IncidentState.CLOSED and not i.artifact_id
        ]
    
    # ========================================================================
    # Operator Interaction
    # ========================================================================
    
    def assign_operator(self, incident_id: str, operator_id: str) -> Incident:
        """Assign an operator to an incident."""
        incident = self._incidents.get(incident_id)
        if incident:
            incident.assigned_operator_id = operator_id
            incident.updated_at = datetime.utcnow()
            self._persist_incident(incident)
        return incident
    
    def record_question_asked(self, incident_id: str, question_id: str):
        """Record that a question was asked for this incident."""
        incident = self._incidents.get(incident_id)
        if incident and question_id not in incident.questions_asked:
            incident.questions_asked.append(question_id)
            incident.updated_at = datetime.utcnow()
            self._persist_incident(incident)
    
    def record_question_answered(self, incident_id: str, question_id: str):
        """Record that a question was answered for this incident."""
        incident = self._incidents.get(incident_id)
        if incident and question_id not in incident.questions_answered:
            incident.questions_answered.append(question_id)
            incident.updated_at = datetime.utcnow()
            self._persist_incident(incident)
    
    def link_decision_card(self, incident_id: str, card_id: str):
        """Link a decision card to the incident."""
        incident = self._incidents.get(incident_id)
        if incident:
            incident.decision_card_id = card_id
            incident.updated_at = datetime.utcnow()
            self._persist_incident(incident)
    
    def link_trust_receipt(self, incident_id: str, receipt_id: str):
        """Link a trust receipt to the incident."""
        incident = self._incidents.get(incident_id)
        if incident:
            incident.trust_receipt_ids.append(receipt_id)
            incident.updated_at = datetime.utcnow()
            self._persist_incident(incident)
    
    def link_artifact(self, incident_id: str, artifact_id: str, tx_hash: Optional[str] = None):
        """Link the final artifact to the incident."""
        incident = self._incidents.get(incident_id)
        if incident:
            incident.artifact_id = artifact_id
            incident.on_chain_tx = tx_hash
            incident.updated_at = datetime.utcnow()
            self._persist_incident(incident)
    
    # ========================================================================
    # Event Handlers
    # ========================================================================
    
    def on_transition(self, handler: Callable[[Incident, StateTransition], None]):
        """Register handler for state transitions."""
        self._transition_handlers.append(handler)
    
    def on_close(self, handler: Callable[[Incident], None]):
        """Register handler for incident closure (artifact creation trigger)."""
        self._close_handlers.append(handler)
    
    def _notify_transition(self, incident: Incident, transition: StateTransition):
        """Notify all transition handlers."""
        for handler in self._transition_handlers:
            try:
                handler(incident, transition)
            except Exception as e:
                print(f"Error in transition handler: {e}")
    
    def _notify_close(self, incident: Incident):
        """Notify all close handlers."""
        for handler in self._close_handlers:
            try:
                handler(incident)
            except Exception as e:
                print(f"Error in close handler: {e}")


# ============================================================================
# Singleton instance
# ============================================================================

_incident_manager: Optional[IncidentManager] = None


def get_incident_manager() -> IncidentManager:
    """Get the singleton IncidentManager instance."""
    global _incident_manager
    if _incident_manager is None:
        _incident_manager = IncidentManager()
    return _incident_manager
