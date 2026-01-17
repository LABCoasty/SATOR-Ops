"""
Artifacts API Routes - Manage decision artifacts and on-chain anchoring.

Endpoints:
- GET /artifacts - List artifacts
- GET /artifacts/{id} - Get artifact details
- POST /artifacts/{id}/anchor - Anchor artifact on-chain
- GET /artifacts/{id}/verify - Verify artifact integrity
- GET /artifacts/{id}/export - Export artifact
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

from ...services.artifact_builder import get_artifact_builder, ArtifactPacket
from ...services.audit_logger import get_audit_logger
from ...integrations.kairo.anchor import get_anchor_service


router = APIRouter(prefix="/artifacts", tags=["artifacts"])


# ============================================================================
# Models
# ============================================================================

class ArtifactSummary(BaseModel):
    """Summary of an artifact for listing."""
    artifact_id: str
    incident_id: str
    scenario_id: str
    created_at: datetime
    title: str
    trust_score: float
    is_anchored: bool
    content_hash: str


class AnchorRequest(BaseModel):
    """Request to anchor artifact on-chain."""
    confirm: bool = True  # Confirmation flag


class AnchorResponse(BaseModel):
    """Response from anchoring operation."""
    success: bool
    artifact_id: str
    tx_hash: Optional[str] = None
    verification_url: Optional[str] = None
    error: Optional[str] = None


class VerificationResponse(BaseModel):
    """Response from verification."""
    verified: bool
    content_hash_valid: bool
    audit_chain_valid: bool
    on_chain_valid: bool
    details: Dict[str, Any]


# ============================================================================
# Endpoints
# ============================================================================

@router.get("", response_model=List[ArtifactSummary])
async def list_artifacts():
    """List all artifacts."""
    artifact_builder = get_artifact_builder()
    
    artifacts = list(artifact_builder._artifacts.values())
    
    return [
        ArtifactSummary(
            artifact_id=a.artifact_id,
            incident_id=a.incident_id,
            scenario_id=a.scenario_id,
            created_at=a.created_at,
            title=a.title,
            trust_score=a.final_trust_receipt.overall_trust_score,
            is_anchored=a.on_chain_anchor is not None,
            content_hash=a.content_hash
        )
        for a in artifacts
    ]


@router.get("/{artifact_id}")
async def get_artifact(artifact_id: str):
    """Get full artifact details."""
    artifact_builder = get_artifact_builder()
    
    artifact = artifact_builder.get_artifact(artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    
    return artifact.model_dump()


@router.post("/{artifact_id}/anchor", response_model=AnchorResponse)
async def anchor_artifact(artifact_id: str, request: AnchorRequest):
    """
    Anchor artifact on-chain via KairoAISec.
    
    This writes the artifact hash and metadata to the blockchain
    for tamper-evident verification.
    """
    if not request.confirm:
        raise HTTPException(
            status_code=400, 
            detail="Anchoring requires confirmation (confirm=true)"
        )
    
    artifact_builder = get_artifact_builder()
    audit_logger = get_audit_logger()
    
    artifact = artifact_builder.get_artifact(artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    
    if artifact.on_chain_anchor:
        return AnchorResponse(
            success=True,
            artifact_id=artifact_id,
            tx_hash=artifact.on_chain_anchor.get("tx_hash"),
            verification_url=artifact.on_chain_anchor.get("verification_url"),
            error="Artifact already anchored"
        )
    
    # Anchor the artifact
    anchor_record = artifact_builder.anchor_artifact(artifact_id)
    
    if anchor_record:
        return AnchorResponse(
            success=True,
            artifact_id=artifact_id,
            tx_hash=anchor_record.tx_hash,
            verification_url=anchor_record.verification_url
        )
    else:
        return AnchorResponse(
            success=False,
            artifact_id=artifact_id,
            error="Failed to anchor artifact"
        )


@router.get("/{artifact_id}/verify", response_model=VerificationResponse)
async def verify_artifact(artifact_id: str):
    """
    Verify artifact integrity.
    
    Checks:
    - Content hash matches computed hash
    - Audit chain is valid
    - On-chain anchor matches (if anchored)
    """
    artifact_builder = get_artifact_builder()
    
    artifact = artifact_builder.get_artifact(artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    
    result = artifact_builder.verify_artifact(artifact_id)
    
    return VerificationResponse(
        verified=result.get("verified", False),
        content_hash_valid=result.get("content_hash_valid", False),
        audit_chain_valid=result.get("audit_chain_valid", False),
        on_chain_valid=result.get("on_chain_valid", True),
        details=result
    )


@router.get("/{artifact_id}/export")
async def export_artifact(artifact_id: str, format: str = "json"):
    """
    Export artifact in specified format.
    
    Formats:
    - json: Full JSON export
    - pdf: PDF report (not implemented)
    """
    artifact_builder = get_artifact_builder()
    
    artifact = artifact_builder.get_artifact(artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    
    content = artifact_builder.export_artifact(artifact_id, format)
    
    if format == "json":
        return JSONResponse(
            content=artifact.model_dump(),
            headers={
                "Content-Disposition": f"attachment; filename=artifact_{artifact_id}.json"
            }
        )
    else:
        raise HTTPException(status_code=400, detail=f"Format '{format}' not supported")


@router.get("/{artifact_id}/trust-receipts")
async def get_trust_receipts(artifact_id: str):
    """Get all trust receipts for an artifact's incident."""
    artifact_builder = get_artifact_builder()
    
    artifact = artifact_builder.get_artifact(artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    
    receipts = artifact_builder.get_trust_receipts(artifact.incident_id)
    
    return {
        "incident_id": artifact.incident_id,
        "receipts": [r.model_dump() for r in receipts],
        "count": len(receipts)
    }


@router.get("/{artifact_id}/audit-trail")
async def get_audit_trail(artifact_id: str):
    """Get audit trail for an artifact's incident."""
    artifact_builder = get_artifact_builder()
    audit_logger = get_audit_logger()
    
    artifact = artifact_builder.get_artifact(artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    
    events = audit_logger.get_incident_trail(artifact.incident_id)
    
    return {
        "incident_id": artifact.incident_id,
        "events": [e.model_dump() for e in events],
        "count": len(events),
        "chain_valid": audit_logger.verify_chain()
    }


@router.get("/security-report")
async def get_security_report():
    """
    Get KairoAISec security report.
    
    This report covers contract security validation for the
    on-chain anchoring system.
    """
    anchor_service = get_anchor_service()
    report = anchor_service.generate_security_report()
    
    return report
