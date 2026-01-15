from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, Field


class ArtifactType(str, Enum):
    DECISION_RECEIPT = "decision_receipt"
    DEFERRAL_RECEIPT = "deferral_receipt"
    ESCALATION_RECEIPT = "escalation_receipt"
    LEGAL_POSTURE_PACKET = "legal_posture_packet"


class Artifact(BaseModel):
    id: str
    type: ArtifactType
    decision_id: str

    created_at: datetime = Field(default_factory=datetime.utcnow)
    content: Dict[str, Any]

    hash: str
    previous_hash: Optional[str] = None

    verified: bool = False
    verified_at: Optional[datetime] = None

    metadata: Optional[Dict[str, Any]] = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class DecisionReceipt(BaseModel):
    decision_id: str
    decision_posture: str
    allowed_actions: List[str]
    action_selected: str
    uncertainty_snapshot: float
    evidence_references: List[str]
    operator_confirmation: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class LegalPosturePacket(BaseModel):
    packet_id: str
    decision_timeline: List[Dict[str, Any]]
    mode_transitions: List[Dict[str, Any]]
    evidence_chain: List[str]
    receipts: List[str]
    system_config: Dict[str, Any]
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    tamper_evident_hash: str
