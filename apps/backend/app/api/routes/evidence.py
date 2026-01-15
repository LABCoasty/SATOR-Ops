from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
from enum import Enum


router = APIRouter()


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


class EvidenceCreate(BaseModel):
    type: EvidenceType
    source: str
    value: dict
    timestamp: Optional[datetime] = None
    metadata: Optional[dict] = None


class EvidenceResponse(BaseModel):
    id: str
    type: EvidenceType
    source: str
    value: dict
    timestamp: datetime
    trust_level: TrustLevel
    trust_score: float
    metadata: Optional[dict] = None


class EvidenceConflict(BaseModel):
    evidence_ids: List[str]
    conflict_type: str
    description: str
    severity: float


@router.get("/", response_model=List[EvidenceResponse])
async def list_evidence(
    type: Optional[EvidenceType] = None,
    source: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
):
    return []


@router.post("/", response_model=EvidenceResponse)
async def create_evidence(evidence: EvidenceCreate):
    return EvidenceResponse(
        id="ev_placeholder",
        type=evidence.type,
        source=evidence.source,
        value=evidence.value,
        timestamp=evidence.timestamp or datetime.utcnow(),
        trust_level=TrustLevel.MEDIUM,
        trust_score=0.75,
        metadata=evidence.metadata,
    )


@router.get("/conflicts", response_model=List[EvidenceConflict])
async def get_conflicts():
    return []


@router.get("/{evidence_id}", response_model=EvidenceResponse)
async def get_evidence(evidence_id: str):
    raise HTTPException(status_code=404, detail="Evidence not found")


@router.post("/{evidence_id}/trust")
async def update_trust(evidence_id: str, trust_score: float, reason: str):
    raise HTTPException(status_code=404, detail="Evidence not found")
