"""
Operator Questionnaire Service - Interactive questions for operator input.

The system asks operators targeted questions based on the incident context.
Operator answers update the decision, trust scores, and audit trail.
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any, Callable
from enum import Enum
from pydantic import BaseModel, Field


# ============================================================================
# Question Types and Models
# ============================================================================

class QuestionType(str, Enum):
    """Types of questions that can be asked."""
    YES_NO = "yes_no"
    MULTIPLE_CHOICE = "multiple_choice"
    SCALE = "scale"  # 1-5 or 1-10
    TEXT = "text"
    CONFIRMATION = "confirmation"
    CHECKLIST = "checklist"


class QuestionCategory(str, Enum):
    """Categories of questions."""
    VISUAL_VERIFICATION = "visual_verification"
    SENSOR_TRUST = "sensor_trust"
    PHYSICAL_STATE = "physical_state"
    SAFETY_CHECK = "safety_check"
    ACTION_CONFIRMATION = "action_confirmation"
    CONTEXT_GATHERING = "context_gathering"


class QuestionOption(BaseModel):
    """Option for multiple choice questions."""
    option_id: str
    label: str
    description: Optional[str] = None
    impact_on_trust: Optional[float] = None  # How much this affects trust score
    triggers_action: Optional[str] = None  # Action to trigger if selected


class OperatorQuestion(BaseModel):
    """A question to be asked to the operator."""
    question_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    incident_id: str
    
    # Question content
    question_type: QuestionType
    category: QuestionCategory
    question_text: str
    context: Optional[str] = None  # Additional context for the question
    
    # Options (for multiple choice / checklist)
    options: List[QuestionOption] = Field(default_factory=list)
    
    # Scale config (for scale questions)
    scale_min: int = 1
    scale_max: int = 5
    scale_labels: Dict[int, str] = Field(default_factory=dict)
    
    # Metadata
    priority: int = 1  # Higher = more important
    required: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    
    # Related entities
    related_sensor_id: Optional[str] = None
    related_equipment_id: Optional[str] = None
    related_contradiction_id: Optional[str] = None
    
    # Answer
    answered: bool = False
    answer: Optional[Any] = None
    answered_at: Optional[datetime] = None
    answered_by: Optional[str] = None


class QuestionAnswer(BaseModel):
    """Answer submitted by operator."""
    question_id: str
    operator_id: str
    answer_value: Any  # The actual answer
    confidence: Optional[int] = None  # Operator's confidence 1-5
    notes: Optional[str] = None  # Additional notes
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class QuestionImpact(BaseModel):
    """Impact of an answer on the decision."""
    trust_adjustment: float = 0.0
    reason_codes_added: List[str] = Field(default_factory=list)
    reason_codes_removed: List[str] = Field(default_factory=list)
    contradictions_resolved: List[str] = Field(default_factory=list)
    recommended_action_change: Optional[str] = None
    incident_state_change: Optional[str] = None
    explanation: str = ""


# ============================================================================
# Question Templates
# ============================================================================

class QuestionTemplates:
    """Pre-defined question templates for common scenarios."""
    
    @staticmethod
    def visual_valve_verification(
        incident_id: str,
        sensor_id: str,
        sensor_reading: str,
        equipment_id: Optional[str] = None
    ) -> OperatorQuestion:
        """Ask operator to visually verify valve position."""
        return OperatorQuestion(
            incident_id=incident_id,
            question_type=QuestionType.MULTIPLE_CHOICE,
            category=QuestionCategory.VISUAL_VERIFICATION,
            question_text=f"Can you visually confirm the valve position? Sensor {sensor_id} shows: {sensor_reading}",
            context="Visual verification helps resolve sensor discrepancies.",
            options=[
                QuestionOption(
                    option_id="matches",
                    label="Matches sensor reading",
                    description="Visual observation matches what the sensor reports",
                    impact_on_trust=0.3
                ),
                QuestionOption(
                    option_id="contradicts",
                    label="Contradicts sensor reading",
                    description="Visual observation differs from sensor reading",
                    impact_on_trust=-0.4,
                    triggers_action="flag_sensor_fault"
                ),
                QuestionOption(
                    option_id="cannot_see",
                    label="Cannot visually verify",
                    description="Unable to see the valve from current position",
                    impact_on_trust=0.0
                ),
                QuestionOption(
                    option_id="partial",
                    label="Partially open",
                    description="Valve appears to be partially open",
                    impact_on_trust=-0.2
                )
            ],
            related_sensor_id=sensor_id,
            related_equipment_id=equipment_id,
            priority=1
        )
    
    @staticmethod
    def sensor_trust_assessment(
        incident_id: str,
        sensor_id: str,
        sensor_name: str
    ) -> OperatorQuestion:
        """Ask operator about their trust in a specific sensor."""
        return OperatorQuestion(
            incident_id=incident_id,
            question_type=QuestionType.SCALE,
            category=QuestionCategory.SENSOR_TRUST,
            question_text=f"How much do you trust the readings from {sensor_name}?",
            context="Based on your experience and recent observations.",
            scale_min=1,
            scale_max=5,
            scale_labels={
                1: "Do not trust at all",
                2: "Low trust",
                3: "Moderate trust",
                4: "High trust",
                5: "Fully trust"
            },
            related_sensor_id=sensor_id,
            priority=2
        )
    
    @staticmethod
    def safety_check(
        incident_id: str,
        area: str
    ) -> OperatorQuestion:
        """Safety checklist before taking action."""
        return OperatorQuestion(
            incident_id=incident_id,
            question_type=QuestionType.CHECKLIST,
            category=QuestionCategory.SAFETY_CHECK,
            question_text=f"Please confirm the following safety checks for {area}:",
            options=[
                QuestionOption(
                    option_id="area_clear",
                    label="Area is clear of personnel",
                    impact_on_trust=0.1
                ),
                QuestionOption(
                    option_id="ppe_worn",
                    label="Required PPE is being worn",
                    impact_on_trust=0.1
                ),
                QuestionOption(
                    option_id="lockout_verified",
                    label="Lockout/tagout verified (if applicable)",
                    impact_on_trust=0.1
                ),
                QuestionOption(
                    option_id="comm_established",
                    label="Communication with control room established",
                    impact_on_trust=0.1
                )
            ],
            priority=1,
            required=True
        )
    
    @staticmethod
    def action_confirmation(
        incident_id: str,
        action_description: str,
        consequences: str
    ) -> OperatorQuestion:
        """Confirm operator understands action consequences."""
        return OperatorQuestion(
            incident_id=incident_id,
            question_type=QuestionType.CONFIRMATION,
            category=QuestionCategory.ACTION_CONFIRMATION,
            question_text=f"You are about to: {action_description}",
            context=f"Potential consequences: {consequences}",
            options=[
                QuestionOption(
                    option_id="confirm",
                    label="I understand and confirm this action",
                    triggers_action="proceed"
                ),
                QuestionOption(
                    option_id="cancel",
                    label="Cancel - I need more information",
                    triggers_action="cancel"
                )
            ],
            priority=1,
            required=True
        )
    
    @staticmethod
    def contradiction_resolution(
        incident_id: str,
        contradiction_id: str,
        sensor_a: str,
        sensor_b: str,
        value_a: float,
        value_b: float
    ) -> OperatorQuestion:
        """Ask operator to help resolve a contradiction."""
        return OperatorQuestion(
            incident_id=incident_id,
            question_type=QuestionType.MULTIPLE_CHOICE,
            category=QuestionCategory.PHYSICAL_STATE,
            question_text=f"Sensors disagree: {sensor_a} reads {value_a}, but {sensor_b} reads {value_b}. Which do you believe is correct?",
            context="Your field observation can help determine which sensor to trust.",
            options=[
                QuestionOption(
                    option_id="trust_a",
                    label=f"Trust {sensor_a} ({value_a})",
                    impact_on_trust=0.2
                ),
                QuestionOption(
                    option_id="trust_b",
                    label=f"Trust {sensor_b} ({value_b})",
                    impact_on_trust=0.2
                ),
                QuestionOption(
                    option_id="trust_neither",
                    label="Neither - both may be faulty",
                    impact_on_trust=-0.3,
                    triggers_action="flag_both_sensors"
                ),
                QuestionOption(
                    option_id="need_inspection",
                    label="Need physical inspection to determine",
                    triggers_action="dispatch_inspection"
                )
            ],
            related_contradiction_id=contradiction_id,
            priority=1
        )
    
    @staticmethod
    def observed_anomaly(
        incident_id: str
    ) -> OperatorQuestion:
        """Ask operator if they've observed any anomalies."""
        return OperatorQuestion(
            incident_id=incident_id,
            question_type=QuestionType.TEXT,
            category=QuestionCategory.CONTEXT_GATHERING,
            question_text="Have you observed any unusual conditions, sounds, or smells in the area?",
            context="Your observations provide valuable context for the decision.",
            required=False,
            priority=3
        )


# ============================================================================
# Questionnaire Service
# ============================================================================

class OperatorQuestionnaireService:
    """
    Service for managing operator questions and processing answers.
    
    - Generates contextual questions based on incident state
    - Processes answers and calculates impact
    - Updates decision engine with new information
    """
    
    def __init__(self):
        self._questions: Dict[str, OperatorQuestion] = {}
        self._incident_questions: Dict[str, List[str]] = {}  # incident_id -> question_ids
        self._answer_handlers: List[Callable[[QuestionAnswer, QuestionImpact], None]] = []
    
    def generate_questions_for_incident(
        self,
        incident_id: str,
        contradictions: List[Dict[str, Any]],
        sensor_readings: Dict[str, Any],
        severity: str
    ) -> List[OperatorQuestion]:
        """
        Generate relevant questions based on incident context.
        
        Args:
            incident_id: The incident ID
            contradictions: Active contradictions
            sensor_readings: Current sensor readings
            severity: Incident severity level
            
        Returns:
            List of questions for the operator
        """
        questions = []
        
        # Generate questions for each contradiction
        for contradiction in contradictions:
            if contradiction.get("reason_code") == "RC10":
                # Redundancy conflict - ask which sensor to trust
                q = QuestionTemplates.contradiction_resolution(
                    incident_id=incident_id,
                    contradiction_id=contradiction.get("contradiction_id", ""),
                    sensor_a=contradiction.get("primary_tag_id", "Sensor A"),
                    sensor_b=contradiction.get("secondary_tag_ids", ["Sensor B"])[0] if contradiction.get("secondary_tag_ids") else "Sensor B",
                    value_a=contradiction.get("values", {}).get(contradiction.get("primary_tag_id", ""), 0),
                    value_b=contradiction.get("values", {}).get(contradiction.get("secondary_tag_ids", [""])[0], 0) if contradiction.get("secondary_tag_ids") else 0
                )
                questions.append(q)
            
            elif contradiction.get("reason_code") == "RC11":
                # Physics violation - ask for visual verification
                q = QuestionTemplates.visual_valve_verification(
                    incident_id=incident_id,
                    sensor_id=contradiction.get("primary_tag_id", ""),
                    sensor_reading=str(contradiction.get("values", {}).get(contradiction.get("primary_tag_id", ""), "unknown")),
                    equipment_id=contradiction.get("primary_tag_id")
                )
                questions.append(q)
        
        # Add general observation question
        questions.append(QuestionTemplates.observed_anomaly(incident_id))
        
        # Add safety check for critical incidents
        if severity in ["critical", "emergency"]:
            questions.append(QuestionTemplates.safety_check(incident_id, "affected area"))
        
        # Store questions
        for q in questions:
            self._questions[q.question_id] = q
        
        self._incident_questions[incident_id] = [q.question_id for q in questions]
        
        return questions
    
    def get_pending_questions(self, incident_id: str) -> List[OperatorQuestion]:
        """Get unanswered questions for an incident."""
        question_ids = self._incident_questions.get(incident_id, [])
        return [
            self._questions[qid] 
            for qid in question_ids 
            if qid in self._questions and not self._questions[qid].answered
        ]
    
    def get_all_questions(self, incident_id: str) -> List[OperatorQuestion]:
        """Get all questions for an incident."""
        question_ids = self._incident_questions.get(incident_id, [])
        return [self._questions[qid] for qid in question_ids if qid in self._questions]
    
    def submit_answer(self, answer: QuestionAnswer) -> QuestionImpact:
        """
        Process an operator's answer.
        
        Args:
            answer: The submitted answer
            
        Returns:
            QuestionImpact describing how this affects the decision
        """
        question = self._questions.get(answer.question_id)
        if not question:
            raise ValueError(f"Question {answer.question_id} not found")
        
        if question.answered:
            raise ValueError(f"Question {answer.question_id} already answered")
        
        # Mark question as answered
        question.answered = True
        question.answer = answer.answer_value
        question.answered_at = answer.timestamp
        question.answered_by = answer.operator_id
        
        # Calculate impact
        impact = self._calculate_impact(question, answer)
        
        # Notify handlers
        for handler in self._answer_handlers:
            try:
                handler(answer, impact)
            except Exception as e:
                print(f"Error in answer handler: {e}")
        
        return impact
    
    def _calculate_impact(
        self, 
        question: OperatorQuestion, 
        answer: QuestionAnswer
    ) -> QuestionImpact:
        """Calculate the impact of an answer on the decision."""
        impact = QuestionImpact()
        
        if question.question_type == QuestionType.MULTIPLE_CHOICE:
            # Find selected option
            selected = next(
                (opt for opt in question.options if opt.option_id == answer.answer_value),
                None
            )
            if selected:
                if selected.impact_on_trust:
                    impact.trust_adjustment = selected.impact_on_trust
                if selected.triggers_action:
                    impact.incident_state_change = selected.triggers_action
                impact.explanation = f"Operator selected: {selected.label}"
        
        elif question.question_type == QuestionType.SCALE:
            # Scale answer affects trust
            scale_value = int(answer.answer_value)
            normalized = (scale_value - question.scale_min) / (question.scale_max - question.scale_min)
            impact.trust_adjustment = (normalized - 0.5) * 0.4  # -0.2 to +0.2
            impact.explanation = f"Operator rated {scale_value}/{question.scale_max}"
        
        elif question.question_type == QuestionType.CHECKLIST:
            # Checklist - trust increases with more items checked
            checked_items = answer.answer_value if isinstance(answer.answer_value, list) else []
            total_items = len(question.options)
            checked_count = len(checked_items)
            
            if total_items > 0:
                completion_rate = checked_count / total_items
                impact.trust_adjustment = completion_rate * 0.3
                impact.explanation = f"Safety checklist: {checked_count}/{total_items} items confirmed"
        
        elif question.question_type == QuestionType.CONFIRMATION:
            selected = next(
                (opt for opt in question.options if opt.option_id == answer.answer_value),
                None
            )
            if selected and selected.triggers_action:
                impact.incident_state_change = selected.triggers_action
                impact.explanation = f"Operator {selected.triggers_action}ed the action"
        
        elif question.question_type == QuestionType.TEXT:
            # Text answers are logged but don't directly affect trust
            if answer.answer_value and len(str(answer.answer_value).strip()) > 0:
                impact.explanation = f"Operator observation recorded: {answer.answer_value[:100]}..."
            else:
                impact.explanation = "No additional observations"
        
        # Handle contradiction resolution
        if question.related_contradiction_id and question.category == QuestionCategory.PHYSICAL_STATE:
            impact.contradictions_resolved.append(question.related_contradiction_id)
        
        return impact
    
    def on_answer(self, handler: Callable[[QuestionAnswer, QuestionImpact], None]):
        """Register callback for when answers are submitted."""
        self._answer_handlers.append(handler)
    
    def add_followup_question(
        self,
        incident_id: str,
        question: OperatorQuestion
    ) -> OperatorQuestion:
        """Add a follow-up question based on previous answers."""
        question.incident_id = incident_id
        self._questions[question.question_id] = question
        
        if incident_id not in self._incident_questions:
            self._incident_questions[incident_id] = []
        self._incident_questions[incident_id].append(question.question_id)
        
        return question


# ============================================================================
# Singleton instance
# ============================================================================

_questionnaire_service: Optional[OperatorQuestionnaireService] = None


def get_questionnaire_service() -> OperatorQuestionnaireService:
    """Get the singleton OperatorQuestionnaireService instance."""
    global _questionnaire_service
    if _questionnaire_service is None:
        _questionnaire_service = OperatorQuestionnaireService()
    return _questionnaire_service
