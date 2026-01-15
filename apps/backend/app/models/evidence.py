from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class EvidenceType(str, Enum):
    SENSOR = "sensor"
    LOG = "log"
    OPERATOR_NOTE = "operator_note"
    ALARM = "alarm"
    EXTERNAL = "external"


class TrustLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    CONFLICTING = "conflicting"


class Evidence(BaseModel):
    id: str
    type: EvidenceType
    source: str
    value: Dict[str, Any]

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    ingested_at: datetime = Field(default_factory=datetime.utcnow)

    trust_level: TrustLevel = TrustLevel.MEDIUM
    trust_score: float = 0.5
    trust_reason: Optional[str] = None

    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[Dict[str, str]] = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class EvidenceConflict(BaseModel):
    id: str
    evidence_ids: list[str]
    conflict_type: str
    description: str
    severity: float
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    resolved: bool = False
    resolution: Optional[str] = None
