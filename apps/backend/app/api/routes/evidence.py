from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
from enum import Enum

from ...data.seed_data import generate_evidence, CONTRADICTIONS
from ...core.trust_calculator import trust_calculator, EvidenceInput, TrustLevel


router = APIRouter()


class EvidenceType(str, Enum):
    SENSOR = "sensor"
    LOG = "log"
    OPERATOR_NOTE = "operator_note"
    ALARM = "alarm"
    EXTERNAL = "external"


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
    trust_level: str
    trust_score: float
    metadata: Optional[dict] = None


class EvidenceConflict(BaseModel):
    id: str
    sources: List[str]
    values: List[str]
    severity: str
    resolution: str


class TrustBreakdown(BaseModel):
    composite_score: float
    factors: List[dict]
    reason_codes: List[dict]


# In-memory storage for demo
_evidence_store: List[dict] = []


@router.get("/", response_model=List[EvidenceResponse])
async def list_evidence(
    type: Optional[EvidenceType] = None,
    source: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
):
    """List all evidence items with optional filtering."""
    evidence = generate_evidence()
    
    # Apply filters
    if type:
        evidence = [e for e in evidence if e["type"] == type.value]
    if source:
        evidence = [e for e in evidence if source.lower() in e["source"].lower()]
    
    # Apply pagination
    evidence = evidence[offset:offset + limit]
    
    return [
        EvidenceResponse(
            id=e["id"],
            type=EvidenceType(e["type"]),
            source=e["source"],
            value=e["value"],
            timestamp=datetime.fromisoformat(e["timestamp"]),
            trust_level=e["trust_level"],
            trust_score=e["trust_score"],
            metadata=e.get("metadata"),
        )
        for e in evidence
    ]


@router.post("/", response_model=EvidenceResponse)
async def create_evidence(evidence: EvidenceCreate):
    """Create a new evidence item and calculate its trust score."""
    now = evidence.timestamp or datetime.utcnow()
    
    # Create evidence input for trust calculation
    value_num = 0.0
    if isinstance(evidence.value, dict):
        value_num = evidence.value.get("reading", evidence.value.get("value", 0.0))
    
    ev_input = EvidenceInput(
        id=f"ev_{len(_evidence_store) + 100:03d}",
        source=evidence.source,
        value=float(value_num) if value_num else 0.0,
        timestamp=now,
    )
    
    # Calculate trust
    result = trust_calculator.calculate_trust(ev_input)
    
    response = EvidenceResponse(
        id=ev_input.id,
        type=evidence.type,
        source=evidence.source,
        value=evidence.value,
        timestamp=now,
        trust_level=result.trust_level.value,
        trust_score=result.adjusted_score,
        metadata=evidence.metadata,
    )
    
    # Store for later retrieval
    _evidence_store.append({
        "id": response.id,
        "type": evidence.type.value,
        "source": evidence.source,
        "value": evidence.value,
        "timestamp": now.isoformat(),
        "trust_level": result.trust_level.value,
        "trust_score": result.adjusted_score,
        "metadata": evidence.metadata,
    })
    
    return response


@router.get("/conflicts", response_model=List[EvidenceConflict])
async def get_conflicts():
    """Get all detected conflicts between evidence sources."""
    return [
        EvidenceConflict(
            id=c["id"],
            sources=c["sources"],
            values=c["values"],
            severity=c["severity"],
            resolution=c["resolution"],
        )
        for c in CONTRADICTIONS
    ]


@router.get("/trust-breakdown", response_model=TrustBreakdown)
async def get_trust_breakdown():
    """Get detailed trust score breakdown."""
    evidence = generate_evidence()
    
    # Convert to EvidenceInput for calculation
    inputs = [
        EvidenceInput(
            id=e["id"],
            source=e["source"],
            value=e["value"].get("reading", 0.0),
            timestamp=datetime.fromisoformat(e["timestamp"]),
        )
        for e in evidence
    ]
    
    # Calculate individual trust scores
    results = [trust_calculator.calculate_trust(inp, inputs) for inp in inputs]
    
    # Aggregate
    aggregated = trust_calculator.aggregate_trust(results)
    
    return TrustBreakdown(
        composite_score=aggregated["composite_score"],
        factors=[
            {"label": "Evidence Corroboration", "value": 0.92, "impact": "positive"},
            {"label": "Source Reliability Avg", "value": 0.86, "impact": "positive"},
            {"label": "Contradiction Penalty", "value": -0.08, "impact": "negative"},
            {"label": "Data Freshness", "value": 0.95, "impact": "positive"},
            {"label": "Unknown Factors", "value": -0.05, "impact": "negative"},
        ],
        reason_codes=[
            {"code": "TR_0x12A", "description": "High sensor corroboration"},
            {"code": "TR_0x08B", "description": "Minor flow sensor divergence"},
            {"code": "TR_0x04C", "description": "External feed staleness"},
        ],
    )


@router.get("/{evidence_id}", response_model=EvidenceResponse)
async def get_evidence(evidence_id: str):
    """Get a specific evidence item by ID."""
    evidence = generate_evidence()
    
    for e in evidence:
        if e["id"] == evidence_id:
            return EvidenceResponse(
                id=e["id"],
                type=EvidenceType(e["type"]),
                source=e["source"],
                value=e["value"],
                timestamp=datetime.fromisoformat(e["timestamp"]),
                trust_level=e["trust_level"],
                trust_score=e["trust_score"],
            )
    
    # Check in-memory store
    for e in _evidence_store:
        if e["id"] == evidence_id:
            return EvidenceResponse(
                id=e["id"],
                type=EvidenceType(e["type"]),
                source=e["source"],
                value=e["value"],
                timestamp=datetime.fromisoformat(e["timestamp"]),
                trust_level=e["trust_level"],
                trust_score=e["trust_score"],
            )
    
    raise HTTPException(status_code=404, detail="Evidence not found")


@router.post("/{evidence_id}/trust")
async def update_trust(evidence_id: str, trust_score: float, reason: str):
    """Manually update trust score for evidence (operator override)."""
    # In production, this would update the database
    return {
        "id": evidence_id,
        "trust_score": trust_score,
        "reason": reason,
        "updated_at": datetime.utcnow().isoformat(),
        "updated_by": "operator",
    }
