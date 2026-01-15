from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
from enum import Enum


router = APIRouter()


class ArtifactType(str, Enum):
    DECISION_RECEIPT = "decision_receipt"
    DEFERRAL_RECEIPT = "deferral_receipt"
    ESCALATION_RECEIPT = "escalation_receipt"
    LEGAL_POSTURE_PACKET = "legal_posture_packet"


class ArtifactResponse(BaseModel):
    id: str
    type: ArtifactType
    decision_id: str
    created_at: datetime
    content: dict
    hash: str
    verified: bool


class LegalPosturePacketCreate(BaseModel):
    decision_ids: List[str]
    include_evidence: bool = True
    include_mode_transitions: bool = True
    include_operator_actions: bool = True


@router.get("/", response_model=List[ArtifactResponse])
async def list_artifacts(
    type: Optional[ArtifactType] = None,
    decision_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    return []


@router.get("/{artifact_id}", response_model=ArtifactResponse)
async def get_artifact(artifact_id: str):
    raise HTTPException(status_code=404, detail="Artifact not found")


@router.get("/{artifact_id}/verify")
async def verify_artifact(artifact_id: str):
    raise HTTPException(status_code=404, detail="Artifact not found")


@router.post("/legal-posture-packet", response_model=ArtifactResponse)
async def create_legal_posture_packet(request: LegalPosturePacketCreate):
    return ArtifactResponse(
        id="art_placeholder",
        type=ArtifactType.LEGAL_POSTURE_PACKET,
        decision_id=request.decision_ids[0] if request.decision_ids else "",
        created_at=datetime.utcnow(),
        content={
            "decision_ids": request.decision_ids,
            "generated_at": datetime.utcnow().isoformat(),
        },
        hash="sha256_placeholder",
        verified=True,
    )


@router.get("/{artifact_id}/download")
async def download_artifact(artifact_id: str):
    raise HTTPException(status_code=404, detail="Artifact not found")
