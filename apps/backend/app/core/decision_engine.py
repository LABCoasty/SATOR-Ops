"""
Decision Engine - Core decision compilation logic.

Evaluates evidence, computes uncertainty scores, determines allowed actions,
and generates decisions with timeboxes for operator review.
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from enum import Enum
from pydantic import BaseModel, Field

from ..services.data_loader import (
    TelemetryReading, 
    ScenarioEvent, 
    Contradiction,
    ScenarioData,
    EventSeverity
)
from ..models.decision import Decision, DecisionMode, ActionType
from ..db import DecisionRepository, get_db


# ============================================================================
# Decision Engine Models
# ============================================================================

class UncertaintyLevel(str, Enum):
    LOW = "low"           # Trust score >= 0.8
    MODERATE = "moderate" # Trust score 0.5 - 0.8
    HIGH = "high"         # Trust score 0.3 - 0.5
    CRITICAL = "critical" # Trust score < 0.3


class AllowedAction(BaseModel):
    """An action that an operator can take."""
    action_id: str
    action_type: ActionType
    label: str
    description: str
    risk_level: str  # low, moderate, high
    requires_confirmation: bool = False
    rationale: Optional[str] = None


class EvidenceEvaluation(BaseModel):
    """Result of evaluating evidence."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    overall_uncertainty: float  # 0.0 (certain) to 1.0 (completely uncertain)
    uncertainty_level: UncertaintyLevel
    sensor_trust_scores: Dict[str, float]  # tag_id -> trust score
    active_contradictions: List[str]  # contradiction IDs
    key_findings: List[str]  # Human-readable findings
    requires_decision: bool
    recommended_action: Optional[ActionType] = None
    recommendation_rationale: Optional[str] = None


class DecisionCard(BaseModel):
    """A decision card presented to the operator."""
    card_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Situation
    title: str
    summary: str
    severity: EventSeverity
    
    # Evidence
    evaluation: EvidenceEvaluation
    telemetry_snapshot: Dict[str, Any] = Field(default_factory=dict)
    
    # Actions
    allowed_actions: List[AllowedAction]
    recommended_action_id: Optional[str] = None
    
    # Timing
    timebox_seconds: int = 300
    expires_at: datetime = Field(default_factory=lambda: datetime.utcnow() + timedelta(seconds=300))
    
    # Resolution
    resolved: bool = False
    action_taken: Optional[str] = None
    action_taken_at: Optional[datetime] = None
    operator_id: Optional[str] = None


# ============================================================================
# Decision Engine
# ============================================================================

class DecisionEngine:
    """
    Core decision compilation engine.
    
    Evaluates evidence from telemetry and events, computes uncertainty scores,
    determines the bounded action space, and generates decision cards.
    """
    
    # Contradiction reason codes and their impact on trust
    CONTRADICTION_IMPACTS = {
        "RC10": 0.5,   # Redundancy conflict - moderate impact
        "RC11": 0.7,   # Physics violation - high impact
        "RC12": 0.3,   # Timing anomaly - lower impact
        "RC13": 0.6,   # Calibration drift - moderate-high impact
    }
    
    # Default timebox for decisions (seconds)
    DEFAULT_TIMEBOX = 300
    
    def __init__(self):
        """Initialize the decision engine."""
        self._active_decisions: Dict[str, DecisionCard] = {}
        self._decision_metadata: Dict[str, Dict[str, Optional[str]]] = {}  # card_id -> {scenario_id, incident_id}
        
        # MongoDB repository (if enabled)
        self._repo: Optional[DecisionRepository] = None
        if get_db().enabled:
            try:
                self._repo = DecisionRepository()
            except Exception as e:
                print(f"Warning: Could not initialize DecisionRepository: {e}")
    
    def _persist_decision(self, card: DecisionCard, scenario_id: Optional[str] = None, incident_id: Optional[str] = None):
        """Persist decision to MongoDB if enabled"""
        if self._repo:
            try:
                # Get metadata from stored mapping if not provided
                if not scenario_id or not incident_id:
                    metadata = self._decision_metadata.get(card.card_id, {})
                    scenario_id = scenario_id or metadata.get("scenario_id")
                    incident_id = incident_id or metadata.get("incident_id")
                
                card_dict = card.model_dump()
                # Add metadata
                card_dict["scenario_id"] = scenario_id
                card_dict["incident_id"] = incident_id
                # Convert enums to strings
                card_dict["severity"] = card.severity.value
                card_dict["evaluation"]["uncertainty_level"] = card.evaluation.uncertainty_level.value
                if card.evaluation.recommended_action:
                    card_dict["evaluation"]["recommended_action"] = card.evaluation.recommended_action.value
                # Convert datetime to ISO string
                card_dict["created_at"] = card.created_at.isoformat()
                card_dict["expires_at"] = card.expires_at.isoformat()
                if card.action_taken_at:
                    card_dict["action_taken_at"] = card.action_taken_at.isoformat()
                card_dict["evaluation"]["timestamp"] = card.evaluation.timestamp.isoformat()
                # Convert allowed actions
                card_dict["allowed_actions"] = [
                    {
                        **action.model_dump(),
                        "action_type": action.action_type.value
                    }
                    for action in card.allowed_actions
                ]
                self._repo.upsert_decision(card_dict)
            except Exception as e:
                print(f"Warning: Failed to persist decision to MongoDB: {e}")
    
    # ========================================================================
    # Evidence Evaluation
    # ========================================================================
    
    def evaluate_evidence(
        self,
        telemetry: Dict[str, TelemetryReading],
        events: List[ScenarioEvent],
        contradictions: List[Contradiction]
    ) -> EvidenceEvaluation:
        """
        Analyze evidence and compute uncertainty scores.
        
        Args:
            telemetry: Current telemetry readings by tag_id
            events: Recent events
            contradictions: Active contradictions
            
        Returns:
            EvidenceEvaluation with uncertainty scores and findings
        """
        # Initialize trust scores at 1.0 (full trust)
        sensor_trust_scores: Dict[str, float] = {
            tag_id: 1.0 for tag_id in telemetry.keys()
        }
        
        key_findings: List[str] = []
        active_contradiction_ids: List[str] = []
        
        # Process contradictions - reduce trust for involved sensors
        for contradiction in contradictions:
            if not contradiction.resolved:
                active_contradiction_ids.append(contradiction.contradiction_id)
                impact = self.CONTRADICTION_IMPACTS.get(contradiction.reason_code, 0.4)
                
                # Reduce trust for primary sensor
                if contradiction.primary_tag_id in sensor_trust_scores:
                    sensor_trust_scores[contradiction.primary_tag_id] *= (1 - impact)
                
                # Reduce trust for secondary sensors (less impact)
                for tag_id in contradiction.secondary_tag_ids:
                    if tag_id in sensor_trust_scores:
                        sensor_trust_scores[tag_id] *= (1 - impact * 0.5)
                
                key_findings.append(contradiction.description)
        
        # Process events that indicate sensor issues
        for event in events:
            if event.severity in [EventSeverity.ALARM, EventSeverity.CRITICAL]:
                if event.tag_id and event.tag_id in sensor_trust_scores:
                    sensor_trust_scores[event.tag_id] *= 0.8
                if event.description and "contradiction" not in event.description.lower():
                    key_findings.append(f"{event.severity.value}: {event.description}")
        
        # Calculate overall uncertainty (weighted average of distrust)
        if sensor_trust_scores:
            avg_trust = sum(sensor_trust_scores.values()) / len(sensor_trust_scores)
            overall_uncertainty = 1 - avg_trust
        else:
            overall_uncertainty = 0.5
        
        # Determine uncertainty level
        if avg_trust >= 0.8:
            uncertainty_level = UncertaintyLevel.LOW
        elif avg_trust >= 0.5:
            uncertainty_level = UncertaintyLevel.MODERATE
        elif avg_trust >= 0.3:
            uncertainty_level = UncertaintyLevel.HIGH
        else:
            uncertainty_level = UncertaintyLevel.CRITICAL
        
        # Determine if decision is required
        requires_decision = (
            len(active_contradiction_ids) > 0 or
            uncertainty_level in [UncertaintyLevel.HIGH, UncertaintyLevel.CRITICAL]
        )
        
        # Determine recommended action based on uncertainty
        recommended_action: Optional[ActionType] = None
        recommendation_rationale: Optional[str] = None
        
        if requires_decision:
            recommended_action, recommendation_rationale = self._get_recommendation(
                uncertainty_level, 
                contradictions,
                sensor_trust_scores
            )
        
        return EvidenceEvaluation(
            overall_uncertainty=overall_uncertainty,
            uncertainty_level=uncertainty_level,
            sensor_trust_scores=sensor_trust_scores,
            active_contradictions=active_contradiction_ids,
            key_findings=key_findings,
            requires_decision=requires_decision,
            recommended_action=recommended_action,
            recommendation_rationale=recommendation_rationale
        )
    
    def _get_recommendation(
        self,
        uncertainty_level: UncertaintyLevel,
        contradictions: List[Contradiction],
        trust_scores: Dict[str, float]
    ) -> Tuple[ActionType, str]:
        """
        Generate action recommendation based on current state.
        
        Returns:
            Tuple of (recommended action type, rationale)
        """
        # Check for physics violations (highest priority)
        has_physics_violation = any(
            c.reason_code == "RC11" for c in contradictions if not c.resolved
        )
        
        if has_physics_violation:
            return (
                ActionType.DEFER,
                "Physics violation detected. Cannot trust sensor data - physical "
                "verification required before any control action. Recommend dispatching "
                "field technician for visual inspection."
            )
        
        # Check for redundancy conflicts
        has_redundancy_conflict = any(
            c.reason_code == "RC10" for c in contradictions if not c.resolved
        )
        
        if has_redundancy_conflict and uncertainty_level == UncertaintyLevel.CRITICAL:
            return (
                ActionType.ESCALATE,
                "Multiple sensors in disagreement with critical uncertainty. "
                "Recommend escalating to supervisor for decision authority."
            )
        
        if has_redundancy_conflict:
            return (
                ActionType.DEFER,
                "Sensor redundancy conflict detected. Recommend deferring decision "
                "until sensor discrepancy is resolved through physical verification."
            )
        
        # Default recommendations based on uncertainty level
        if uncertainty_level == UncertaintyLevel.CRITICAL:
            return (
                ActionType.ESCALATE,
                "Critical uncertainty level. Recommend escalating to higher authority "
                "for decision review."
            )
        
        if uncertainty_level == UncertaintyLevel.HIGH:
            return (
                ActionType.DEFER,
                "High uncertainty in sensor data. Recommend deferring until "
                "additional evidence is available."
            )
        
        # Moderate uncertainty - can proceed with caution
        return (
            ActionType.ACT,
            "Moderate uncertainty. Proceed with caution and monitor closely."
        )
    
    # ========================================================================
    # Action Space
    # ========================================================================
    
    def get_allowed_actions(
        self,
        evaluation: EvidenceEvaluation,
        context: Optional[Dict[str, Any]] = None
    ) -> List[AllowedAction]:
        """
        Return bounded action space based on current state.
        
        Args:
            evaluation: The evidence evaluation
            context: Additional context (e.g., scenario type, operator role)
            
        Returns:
            List of allowed actions for the operator
        """
        actions: List[AllowedAction] = []
        
        # ACT - Take control action
        # Only allowed if uncertainty is not critical
        if evaluation.uncertainty_level != UncertaintyLevel.CRITICAL:
            actions.append(AllowedAction(
                action_id="act-proceed",
                action_type=ActionType.ACT,
                label="Proceed with Action",
                description="Take the recommended control action based on available evidence.",
                risk_level="moderate" if evaluation.uncertainty_level == UncertaintyLevel.MODERATE else "low",
                requires_confirmation=evaluation.uncertainty_level != UncertaintyLevel.LOW,
                rationale="Proceed with control action while monitoring for anomalies."
            ))
        
        # DEFER - Wait for more information
        actions.append(AllowedAction(
            action_id="defer-inspection",
            action_type=ActionType.DEFER,
            label="Defer - Request Inspection",
            description="Defer decision and dispatch field technician for physical verification.",
            risk_level="low",
            requires_confirmation=False,
            rationale="Physical verification can resolve sensor discrepancies."
        ))
        
        actions.append(AllowedAction(
            action_id="defer-wait",
            action_type=ActionType.DEFER,
            label="Defer - Wait for Data",
            description="Defer decision and wait for additional sensor data or trend analysis.",
            risk_level="low",
            requires_confirmation=False,
            rationale="Additional data may clarify the situation."
        ))
        
        # ESCALATE - Transfer to higher authority
        actions.append(AllowedAction(
            action_id="escalate-supervisor",
            action_type=ActionType.ESCALATE,
            label="Escalate to Supervisor",
            description="Transfer decision authority to supervisor for review.",
            risk_level="low",
            requires_confirmation=False,
            rationale="Supervisor may have additional context or authority."
        ))
        
        if evaluation.uncertainty_level == UncertaintyLevel.CRITICAL:
            actions.append(AllowedAction(
                action_id="escalate-emergency",
                action_type=ActionType.ESCALATE,
                label="Emergency Escalation",
                description="Immediately escalate to emergency response team.",
                risk_level="high",
                requires_confirmation=True,
                rationale="Critical uncertainty may indicate serious system issue."
            ))
        
        # Mark recommended action
        for action in actions:
            if action.action_type == evaluation.recommended_action:
                action.rationale = evaluation.recommendation_rationale
        
        return actions
    
    # ========================================================================
    # Decision Creation
    # ========================================================================
    
    def create_decision(
        self,
        evaluation: EvidenceEvaluation,
        telemetry_snapshot: Dict[str, TelemetryReading],
        title: str,
        summary: str,
        severity: EventSeverity = EventSeverity.WARNING,
        timebox_seconds: Optional[int] = None,
        scenario_id: Optional[str] = None,
        incident_id: Optional[str] = None
    ) -> DecisionCard:
        """
        Generate a decision card with timebox.
        
        Args:
            evaluation: The evidence evaluation
            telemetry_snapshot: Current sensor readings
            title: Decision card title
            summary: Situation summary
            severity: Severity level
            timebox_seconds: Time allowed for decision (default: 300s)
            
        Returns:
            DecisionCard ready for operator review
        """
        if timebox_seconds is None:
            timebox_seconds = self.DEFAULT_TIMEBOX
        
        # Get allowed actions
        allowed_actions = self.get_allowed_actions(evaluation)
        
        # Find recommended action ID
        recommended_action_id: Optional[str] = None
        for action in allowed_actions:
            if action.action_type == evaluation.recommended_action:
                recommended_action_id = action.action_id
                break
        
        # Convert telemetry to serializable format
        telemetry_dict = {
            tag_id: {
                "value": reading.value,
                "unit": reading.unit,
                "quality": reading.quality.value,
                "timestamp": reading.timestamp.isoformat()
            }
            for tag_id, reading in telemetry_snapshot.items()
        }
        
        card = DecisionCard(
            title=title,
            summary=summary,
            severity=severity,
            evaluation=evaluation,
            telemetry_snapshot=telemetry_dict,
            allowed_actions=allowed_actions,
            recommended_action_id=recommended_action_id,
            timebox_seconds=timebox_seconds,
            expires_at=datetime.utcnow() + timedelta(seconds=timebox_seconds)
        )
        
        # Store active decision
        self._active_decisions[card.card_id] = card
        
        # Store metadata for persistence
        if scenario_id or incident_id:
            self._decision_metadata[card.card_id] = {
                "scenario_id": scenario_id,
                "incident_id": incident_id
            }
        
        # Persist to MongoDB
        self._persist_decision(card, scenario_id=scenario_id, incident_id=incident_id)
        
        return card
    
    # ========================================================================
    # Action Recording
    # ========================================================================
    
    def record_action(
        self,
        card_id: str,
        action_id: str,
        operator_id: str
    ) -> Optional[DecisionCard]:
        """
        Record operator action (act/escalate/defer).
        
        Args:
            card_id: The decision card ID
            action_id: The action taken
            operator_id: The operator who took the action
            
        Returns:
            Updated DecisionCard or None if not found
        """
        if card_id not in self._active_decisions:
            return None
        
        card = self._active_decisions[card_id]
        
        # Verify action is allowed
        valid_action = any(a.action_id == action_id for a in card.allowed_actions)
        if not valid_action:
            return None
        
        # Record the action
        card.resolved = True
        card.action_taken = action_id
        card.action_taken_at = datetime.utcnow()
        card.operator_id = operator_id
        
        # Persist updated decision to MongoDB
        metadata = self._decision_metadata.get(card_id, {})
        self._persist_decision(
            card, 
            scenario_id=metadata.get("scenario_id"),
            incident_id=metadata.get("incident_id")
        )
        
        return card
    
    def get_active_decisions(self) -> List[DecisionCard]:
        """Get all active (unresolved) decision cards."""
        return [
            card for card in self._active_decisions.values()
            if not card.resolved
        ]
    
    def get_decision(self, card_id: str) -> Optional[DecisionCard]:
        """Get a specific decision card."""
        return self._active_decisions.get(card_id)
    
    # ========================================================================
    # Fixed Scenario Support
    # ========================================================================
    
    def get_recommended_resolution(self, scenario_data: ScenarioData) -> Dict[str, Any]:
        """
        Get the recommended resolution for a fixed scenario.
        
        Args:
            scenario_data: The complete scenario data
            
        Returns:
            Dictionary with recommended action and rationale
        """
        return {
            "scenario_id": scenario_data.metadata.scenario_id,
            "scenario_name": scenario_data.metadata.name,
            "recommended_action": scenario_data.metadata.recommended_action,
            "rationale": scenario_data.metadata.resolution_rationale,
            "contradictions_detected": len(scenario_data.contradictions),
            "summary": (
                f"Scenario '{scenario_data.metadata.name}' has {len(scenario_data.contradictions)} "
                f"detected contradictions. Recommended action: {scenario_data.metadata.recommended_action}. "
                f"Rationale: {scenario_data.metadata.resolution_rationale}"
            )
        }


# ============================================================================
# Singleton instance
# ============================================================================

_decision_engine: Optional[DecisionEngine] = None


def get_decision_engine() -> DecisionEngine:
    """Get the singleton DecisionEngine instance."""
    global _decision_engine
    if _decision_engine is None:
        _decision_engine = DecisionEngine()
    return _decision_engine
