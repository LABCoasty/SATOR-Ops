"""
SATOR Tool Definitions - MCP-compatible tool implementations.

Implements the five core SATOR decision tools:
- analyze_vision: Process Overshoot JSON, extract actionable insights
- detect_contradictions: Compare vision data vs sensor telemetry
- predict_issues: Predict potential problems before they occur
- recommend_action: Generate AI-powered action recommendations
- create_decision_card: Package findings into operator decision cards
"""

import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


# ============================================================================
# Tool Models
# ============================================================================

class ToolInvocation(BaseModel):
    """Record of a tool invocation."""
    invocation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tool_name: str
    parameters: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ToolResult(BaseModel):
    """Result from a tool invocation."""
    success: bool
    data: Any
    error: Optional[str] = None
    execution_time_ms: float = 0


# ============================================================================
# Vision Analysis Models
# ============================================================================

class VisionInsight(BaseModel):
    """Insight extracted from vision analysis."""
    insight_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    category: str  # equipment, operator, safety
    description: str
    confidence: float
    related_equipment_id: Optional[str] = None
    actionable: bool = False


class VisionAnalysisResult(BaseModel):
    """Result of vision analysis."""
    equipment_states: List[Dict[str, Any]]
    operator_positions: List[Dict[str, Any]]
    safety_flags: List[Dict[str, Any]]
    insights: List[VisionInsight]
    summary: str


# ============================================================================
# Contradiction Models
# ============================================================================

class DetectedContradiction(BaseModel):
    """A contradiction detected between vision and telemetry."""
    contradiction_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    reason_code: str
    category: str  # redundancy, physics, timing, vision_mismatch
    primary_source: str  # vision or sensor tag_id
    secondary_sources: List[str]
    description: str
    values: Dict[str, Any]
    confidence: float
    severity: str  # low, medium, high, critical


# ============================================================================
# Prediction Models
# ============================================================================

class IssuePrediction(BaseModel):
    """A predicted issue."""
    prediction_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    issue_type: str
    description: str
    confidence: float
    time_horizon: str  # immediate, short_term, long_term
    explanation: str
    contributing_factors: List[str]
    recommended_action: str


# ============================================================================
# Recommendation Models
# ============================================================================

class ActionRecommendation(BaseModel):
    """Action recommendation from the system."""
    recommended_action: str
    action_type: str  # act, defer, escalate
    confidence: float
    rationale: str
    alternatives: List[Dict[str, Any]]
    follow_up_questions: List[Dict[str, Any]]
    risk_assessment: str


# ============================================================================
# Decision Card Models
# ============================================================================

class DecisionCardPayload(BaseModel):
    """Complete decision card payload for UI."""
    card_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    incident_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Content
    title: str
    summary: str
    severity: str
    
    # Analysis
    predictions: List[IssuePrediction]
    contradictions: List[DetectedContradiction]
    trust_score: float
    reason_codes: List[str]
    
    # Actions
    allowed_actions: List[Dict[str, Any]]
    recommended_action_id: str
    recommendation_rationale: str
    
    # Operator Questions
    questions: List[Dict[str, Any]]
    
    # Evidence
    telemetry_snapshot: Dict[str, Any]
    vision_snapshot: Optional[Dict[str, Any]] = None


# ============================================================================
# Tool Implementations
# ============================================================================

def analyze_vision(vision_frame: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tool 1: Analyze vision frame from Overshoot.
    
    Extracts actionable insights from Overshoot vision output including:
    - Equipment states (valves, gauges, indicators)
    - Operator positions and actions
    - Safety flags (spills, leaks, PPE violations)
    
    Args:
        vision_frame: VisionFrame dictionary from Overshoot
        
    Returns:
        VisionAnalysisResult with extracted insights
    """
    equipment_states = vision_frame.get("equipment_states", [])
    operator_actions = vision_frame.get("operator_actions", [])
    safety_events = vision_frame.get("safety_events", [])
    
    insights: List[VisionInsight] = []
    
    # Analyze equipment states
    for equip in equipment_states:
        if equip.get("status") in ["warning", "critical"]:
            insights.append(VisionInsight(
                category="equipment",
                description=f"{equip.get('name', 'Equipment')} shows {equip.get('status')} status",
                confidence=equip.get("confidence", 0.8),
                related_equipment_id=equip.get("equipment_id"),
                actionable=True
            ))
        
        # Check valve positions
        if equip.get("valve_position") == "closed" and equip.get("equipment_type") == "valve":
            insights.append(VisionInsight(
                category="equipment",
                description=f"Valve {equip.get('name', '')} visually appears CLOSED",
                confidence=equip.get("confidence", 0.8),
                related_equipment_id=equip.get("equipment_id"),
                actionable=True
            ))
    
    # Analyze safety events
    safety_flags = []
    for event in safety_events:
        safety_flags.append({
            "event_type": event.get("event_type"),
            "severity": event.get("severity"),
            "description": event.get("description"),
            "location": event.get("location")
        })
        
        insights.append(VisionInsight(
            category="safety",
            description=f"Safety event: {event.get('description', 'Unknown')}",
            confidence=event.get("confidence", 0.9),
            actionable=True
        ))
    
    # Analyze operator positions
    operator_positions = []
    for action in operator_actions:
        person = action.get("person", {})
        operator_positions.append({
            "person_id": person.get("person_id"),
            "action_type": action.get("action_type"),
            "location": person.get("location"),
            "wearing_ppe": person.get("wearing_ppe", True)
        })
        
        if not person.get("wearing_ppe", True):
            insights.append(VisionInsight(
                category="safety",
                description=f"PPE violation detected for operator",
                confidence=0.85,
                actionable=True
            ))
    
    # Generate summary
    summary_parts = []
    if equipment_states:
        summary_parts.append(f"{len(equipment_states)} equipment items detected")
    if safety_flags:
        summary_parts.append(f"{len(safety_flags)} safety events")
    if operator_positions:
        summary_parts.append(f"{len(operator_positions)} operators observed")
    
    summary = "; ".join(summary_parts) if summary_parts else "No significant observations"
    
    return {
        "equipment_states": equipment_states,
        "operator_positions": operator_positions,
        "safety_flags": safety_flags,
        "insights": [i.model_dump() for i in insights],
        "summary": summary
    }


def detect_contradictions(
    vision_frame: Dict[str, Any],
    telemetry: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Tool 2: Detect contradictions between vision and telemetry.
    
    Compares Overshoot vision observations against sensor telemetry
    to find discrepancies that indicate sensor faults or anomalies.
    
    Args:
        vision_frame: VisionFrame dictionary from Overshoot
        telemetry: Current sensor readings by tag_id
        
    Returns:
        List of DetectedContradiction objects
    """
    contradictions: List[DetectedContradiction] = []
    equipment_states = vision_frame.get("equipment_states", [])
    
    for equip in equipment_states:
        mapped_tag = equip.get("mapped_tag_id")
        if not mapped_tag or mapped_tag not in telemetry:
            continue
        
        sensor_reading = telemetry[mapped_tag]
        sensor_value = sensor_reading.get("value") if isinstance(sensor_reading, dict) else sensor_reading
        
        # Check valve position contradictions (RC11 - Physics violation)
        if equip.get("equipment_type") == "valve" and equip.get("valve_position"):
            visual_position = equip.get("valve_position")
            
            # If valve visually closed but sensor says open (or vice versa)
            if visual_position == "closed" and sensor_value > 50:
                contradictions.append(DetectedContradiction(
                    reason_code="RC11",
                    category="vision_mismatch",
                    primary_source="vision",
                    secondary_sources=[mapped_tag],
                    description=f"Vision shows valve CLOSED but sensor {mapped_tag} reads {sensor_value}%",
                    values={"vision": "closed", mapped_tag: sensor_value},
                    confidence=equip.get("confidence", 0.8),
                    severity="high"
                ).model_dump())
            elif visual_position == "open" and sensor_value < 50:
                contradictions.append(DetectedContradiction(
                    reason_code="RC11",
                    category="vision_mismatch",
                    primary_source="vision",
                    secondary_sources=[mapped_tag],
                    description=f"Vision shows valve OPEN but sensor {mapped_tag} reads {sensor_value}%",
                    values={"vision": "open", mapped_tag: sensor_value},
                    confidence=equip.get("confidence", 0.8),
                    severity="high"
                ).model_dump())
        
        # Check gauge reading contradictions
        if equip.get("gauge_reading"):
            gauge = equip.get("gauge_reading", {})
            visual_value = gauge.get("value")
            
            if visual_value is not None and sensor_value is not None:
                # Check if values differ by more than 20%
                if sensor_value != 0:
                    diff_pct = abs(visual_value - sensor_value) / abs(sensor_value) * 100
                    if diff_pct > 20:
                        contradictions.append(DetectedContradiction(
                            reason_code="RC12",
                            category="vision_mismatch",
                            primary_source="vision",
                            secondary_sources=[mapped_tag],
                            description=f"Visual gauge reads {visual_value} but sensor {mapped_tag} reads {sensor_value} ({diff_pct:.0f}% difference)",
                            values={"vision": visual_value, mapped_tag: sensor_value},
                            confidence=equip.get("confidence", 0.7) * (1 - diff_pct/200),
                            severity="medium" if diff_pct < 50 else "high"
                        ).model_dump())
    
    # Check for flow/valve physics violations
    # If valve is closed (from any source) but flow is detected
    valve_readings = {k: v for k, v in telemetry.items() if "valve" in k.lower()}
    flow_readings = {k: v for k, v in telemetry.items() if "flow" in k.lower()}
    
    for valve_tag, valve_reading in valve_readings.items():
        valve_value = valve_reading.get("value") if isinstance(valve_reading, dict) else valve_reading
        if valve_value == 0:  # Valve closed
            for flow_tag, flow_reading in flow_readings.items():
                flow_value = flow_reading.get("value") if isinstance(flow_reading, dict) else flow_reading
                if flow_value > 10:  # Significant flow
                    contradictions.append(DetectedContradiction(
                        reason_code="RC11",
                        category="physics",
                        primary_source=valve_tag,
                        secondary_sources=[flow_tag],
                        description=f"Physics violation: {valve_tag} shows CLOSED but {flow_tag} reads {flow_value}",
                        values={valve_tag: valve_value, flow_tag: flow_value},
                        confidence=0.95,
                        severity="critical"
                    ).model_dump())
    
    return contradictions


def predict_issues(
    vision_frame: Dict[str, Any],
    telemetry: Dict[str, Any],
    history: Optional[List[Dict[str, Any]]] = None
) -> List[Dict[str, Any]]:
    """
    Tool 3: Predict potential issues before they occur.
    
    Analyzes current state and trends to predict problems.
    
    Args:
        vision_frame: VisionFrame dictionary from Overshoot
        telemetry: Current sensor readings
        history: Historical telemetry readings
        
    Returns:
        List of IssuePrediction objects
    """
    predictions: List[IssuePrediction] = []
    history = history or []
    
    # Analyze safety events for escalation potential
    safety_events = vision_frame.get("safety_events", [])
    for event in safety_events:
        if event.get("event_type") == "leak":
            predictions.append(IssuePrediction(
                issue_type="environmental_hazard",
                description="Leak detected - potential for escalation",
                confidence=0.85,
                time_horizon="immediate",
                explanation="Visual leak detection suggests immediate containment needed",
                contributing_factors=["visual_leak_detected", "active_flow"],
                recommended_action="isolate_area"
            ).model_dump())
        elif event.get("event_type") == "smoke":
            predictions.append(IssuePrediction(
                issue_type="fire_risk",
                description="Smoke detected - fire risk",
                confidence=0.9,
                time_horizon="immediate",
                explanation="Smoke detection requires immediate investigation",
                contributing_factors=["smoke_detected"],
                recommended_action="emergency_response"
            ).model_dump())
    
    # Analyze sensor disagreements for failure prediction
    equipment_states = vision_frame.get("equipment_states", [])
    for equip in equipment_states:
        if equip.get("status") == "warning":
            predictions.append(IssuePrediction(
                issue_type="equipment_degradation",
                description=f"{equip.get('name', 'Equipment')} showing warning signs",
                confidence=0.7,
                time_horizon="short_term",
                explanation="Visual indicators suggest equipment may be degrading",
                contributing_factors=["visual_warning_indicator"],
                recommended_action="schedule_inspection"
            ).model_dump())
    
    # Analyze telemetry trends (if history available)
    if history:
        # Check for drift patterns
        for tag_id, current_reading in telemetry.items():
            current_value = current_reading.get("value") if isinstance(current_reading, dict) else current_reading
            if current_value is None:
                continue
            
            # Get historical values for this sensor
            historical_values = []
            for h in history[-10:]:  # Last 10 readings
                if tag_id in h:
                    hist_reading = h[tag_id]
                    hist_value = hist_reading.get("value") if isinstance(hist_reading, dict) else hist_reading
                    if hist_value is not None:
                        historical_values.append(hist_value)
            
            if len(historical_values) >= 5:
                avg_historical = sum(historical_values) / len(historical_values)
                if avg_historical != 0:
                    drift_pct = abs(current_value - avg_historical) / abs(avg_historical) * 100
                    if drift_pct > 30:
                        predictions.append(IssuePrediction(
                            issue_type="sensor_drift",
                            description=f"Sensor {tag_id} showing significant drift",
                            confidence=0.65,
                            time_horizon="short_term",
                            explanation=f"Current reading {current_value} differs {drift_pct:.0f}% from recent average",
                            contributing_factors=["sensor_drift", "calibration_issue"],
                            recommended_action="verify_calibration"
                        ).model_dump())
    
    return predictions


def recommend_action(
    incident_state: Dict[str, Any],
    evidence: Dict[str, Any],
    trust_score: float,
    operator_answers: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Tool 4: Generate action recommendations with rationale.
    
    Args:
        incident_state: Current incident state
        evidence: Evidence bundle (contradictions, predictions, etc.)
        trust_score: Current trust score (0-1)
        operator_answers: Answers from operator questions
        
    Returns:
        ActionRecommendation with recommended action and alternatives
    """
    operator_answers = operator_answers or []
    contradictions = evidence.get("contradictions", [])
    predictions = evidence.get("predictions", [])
    severity = incident_state.get("severity", "warning")
    
    # Analyze operator answers for additional context
    operator_trusts_sensors = True
    visual_verification_done = False
    
    for answer in operator_answers:
        answer_value = answer.get("answer_value")
        question_category = answer.get("category")
        
        if question_category == "visual_verification":
            visual_verification_done = True
            if answer_value == "contradicts":
                operator_trusts_sensors = False
        elif question_category == "sensor_trust":
            if isinstance(answer_value, int) and answer_value <= 2:
                operator_trusts_sensors = False
    
    # Generate follow-up questions if needed
    follow_up_questions = []
    
    if not visual_verification_done and contradictions:
        follow_up_questions.append({
            "question_id": str(uuid.uuid4()),
            "question_type": "multiple_choice",
            "question_text": "Can you visually verify the equipment state?",
            "priority": 1
        })
    
    if trust_score < 0.5 and not operator_answers:
        follow_up_questions.append({
            "question_id": str(uuid.uuid4()),
            "question_type": "scale",
            "question_text": "How confident are you in the current sensor readings?",
            "priority": 2
        })
    
    # Determine recommendation based on all factors
    has_physics_violation = any(c.get("reason_code") == "RC11" for c in contradictions)
    has_safety_event = any(p.get("issue_type") in ["fire_risk", "environmental_hazard"] for p in predictions)
    
    alternatives = []
    
    if has_safety_event:
        return ActionRecommendation(
            recommended_action="emergency_response",
            action_type="escalate",
            confidence=0.95,
            rationale="Safety event detected - immediate escalation required",
            alternatives=[
                {"action": "isolate_area", "rationale": "Contain the situation first"},
                {"action": "defer_with_monitoring", "rationale": "Continue monitoring while escalating"}
            ],
            follow_up_questions=follow_up_questions,
            risk_assessment="HIGH - Safety critical situation"
        ).model_dump()
    
    if has_physics_violation:
        if visual_verification_done and not operator_trusts_sensors:
            return ActionRecommendation(
                recommended_action="flag_sensor_fault",
                action_type="act",
                confidence=0.85,
                rationale="Operator visual verification confirms sensor fault",
                alternatives=[
                    {"action": "defer_inspection", "rationale": "Wait for maintenance verification"},
                    {"action": "escalate", "rationale": "Escalate for engineering review"}
                ],
                follow_up_questions=[],
                risk_assessment="MEDIUM - Sensor fault confirmed"
            ).model_dump()
        else:
            return ActionRecommendation(
                recommended_action="defer_inspection",
                action_type="defer",
                confidence=0.8,
                rationale="Physics violation detected - physical verification required before action",
                alternatives=[
                    {"action": "escalate", "rationale": "Escalate to supervisor if urgent"},
                    {"action": "proceed_with_caution", "rationale": "Proceed if situation is time-critical"}
                ],
                follow_up_questions=follow_up_questions,
                risk_assessment="HIGH - Cannot trust sensor data"
            ).model_dump()
    
    if trust_score < 0.3:
        return ActionRecommendation(
            recommended_action="escalate",
            action_type="escalate",
            confidence=0.75,
            rationale="Critical trust level - escalation to higher authority recommended",
            alternatives=[
                {"action": "defer_inspection", "rationale": "Defer until more data available"},
            ],
            follow_up_questions=follow_up_questions,
            risk_assessment="HIGH - Critical uncertainty"
        ).model_dump()
    
    if trust_score < 0.6:
        return ActionRecommendation(
            recommended_action="defer_inspection",
            action_type="defer",
            confidence=0.7,
            rationale="Moderate uncertainty - recommend verification before action",
            alternatives=[
                {"action": "proceed_with_monitoring", "rationale": "Proceed with enhanced monitoring"},
                {"action": "escalate", "rationale": "Escalate if time-critical"}
            ],
            follow_up_questions=follow_up_questions,
            risk_assessment="MEDIUM - Elevated uncertainty"
        ).model_dump()
    
    # High trust - can proceed
    return ActionRecommendation(
        recommended_action="proceed",
        action_type="act",
        confidence=0.85,
        rationale="Trust level adequate - proceed with standard monitoring",
        alternatives=[
            {"action": "defer_brief", "rationale": "Brief delay for additional verification"}
        ],
        follow_up_questions=[],
        risk_assessment="LOW - Adequate trust level"
    ).model_dump()


def create_decision_card(
    incident_id: str,
    findings: Dict[str, Any],
    operator_questions: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Tool 5: Create operator-ready decision card.
    
    Packages all analysis findings into a decision card for operator review.
    
    Args:
        incident_id: Incident ID
        findings: Analysis findings (contradictions, predictions, recommendations)
        operator_questions: Questions to ask the operator
        
    Returns:
        Complete DecisionCardPayload
    """
    operator_questions = operator_questions or []
    
    contradictions = findings.get("contradictions", [])
    predictions = findings.get("predictions", [])
    recommendation = findings.get("recommendation", {})
    trust_score = findings.get("trust_score", 0.5)
    telemetry = findings.get("telemetry", {})
    vision = findings.get("vision", None)
    
    # Determine severity
    has_critical = any(c.get("severity") == "critical" for c in contradictions)
    has_safety = any(p.get("issue_type") in ["fire_risk", "environmental_hazard"] for p in predictions)
    
    if has_safety:
        severity = "emergency"
    elif has_critical:
        severity = "critical"
    elif trust_score < 0.5:
        severity = "warning"
    else:
        severity = "info"
    
    # Generate title and summary
    if contradictions:
        primary_contradiction = contradictions[0]
        title = f"Contradiction Detected: {primary_contradiction.get('reason_code', 'Unknown')}"
        summary = primary_contradiction.get("description", "Sensor contradiction requires attention")
    elif predictions:
        primary_prediction = predictions[0]
        title = f"Predicted Issue: {primary_prediction.get('issue_type', 'Unknown')}"
        summary = primary_prediction.get("description", "Potential issue predicted")
    else:
        title = "Decision Required"
        summary = "Operator decision requested"
    
    # Extract reason codes
    reason_codes = list(set(c.get("reason_code") for c in contradictions if c.get("reason_code")))
    
    # Build allowed actions
    recommended_action = recommendation.get("recommended_action", "defer_inspection")
    allowed_actions = [
        {
            "action_id": "act-proceed",
            "action_type": "act",
            "label": "Proceed with Action",
            "description": "Take the recommended control action",
            "risk_level": recommendation.get("risk_assessment", "medium")
        },
        {
            "action_id": "defer-inspection",
            "action_type": "defer",
            "label": "Defer - Request Inspection",
            "description": "Defer and dispatch field technician",
            "risk_level": "low"
        },
        {
            "action_id": "escalate-supervisor",
            "action_type": "escalate",
            "label": "Escalate to Supervisor",
            "description": "Transfer to higher authority",
            "risk_level": "low"
        }
    ]
    
    # Find recommended action ID
    recommended_action_id = "defer-inspection"  # Default
    if recommendation.get("action_type") == "act":
        recommended_action_id = "act-proceed"
    elif recommendation.get("action_type") == "escalate":
        recommended_action_id = "escalate-supervisor"
    
    return DecisionCardPayload(
        incident_id=incident_id,
        title=title,
        summary=summary,
        severity=severity,
        predictions=[IssuePrediction(**p) if isinstance(p, dict) else p for p in predictions],
        contradictions=[DetectedContradiction(**c) if isinstance(c, dict) else c for c in contradictions],
        trust_score=trust_score,
        reason_codes=reason_codes,
        allowed_actions=allowed_actions,
        recommended_action_id=recommended_action_id,
        recommendation_rationale=recommendation.get("rationale", ""),
        questions=operator_questions,
        telemetry_snapshot=telemetry,
        vision_snapshot=vision
    ).model_dump()


# ============================================================================
# Tool Registry
# ============================================================================

SATOR_TOOLS = [
    {
        "name": "analyze_vision",
        "handler": analyze_vision,
        "description": "Extract actionable insights from Overshoot vision output"
    },
    {
        "name": "detect_contradictions",
        "handler": detect_contradictions,
        "description": "Compare vision data vs sensor telemetry"
    },
    {
        "name": "predict_issues",
        "handler": predict_issues,
        "description": "Predict potential problems before they occur"
    },
    {
        "name": "recommend_action",
        "handler": recommend_action,
        "description": "Generate AI-powered action recommendations"
    },
    {
        "name": "create_decision_card",
        "handler": create_decision_card,
        "description": "Package findings into operator decision cards"
    }
]
