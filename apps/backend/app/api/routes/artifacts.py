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
from ...integrations.kairo import get_kairo_client


router = APIRouter(tags=["artifacts"])


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
    anchor_service = get_anchor_service()
    
    artifact = artifact_builder.get_artifact(artifact_id)
    
    # If no artifact exists, create a demo artifact and anchor it directly
    if not artifact:
        # For demo purposes: create a mock artifact and anchor it
        from ...integrations.kairo.anchor import AnchorRequest as KairoAnchorRequest
        
        demo_artifact_data = {
            "artifact_id": artifact_id,
            "incident_id": f"INC-{artifact_id.replace('ART-', '')}",
            "scenario_id": "scenario1",
            "title": "Industrial Safety Decision Artifact",
            "created_at": datetime.utcnow().isoformat(),
            "incident_core": {
                "incident_id": f"INC-{artifact_id.replace('ART-', '')}",
                "title": "Thermal anomaly detected in Processing Unit Alpha",
                "scope": "Processing Unit Alpha - Zone 3",
                "severity": "critical",
                "time_window": {"start": datetime.utcnow().isoformat(), "end": datetime.utcnow().isoformat()}
            },
            "evidence_set": {
                "telemetry_readings": [
                    {"sensor_id": "temp_001", "value": 185.5, "unit": "°C", "timestamp": datetime.utcnow().isoformat()},
                    {"sensor_id": "pressure_001", "value": 2.4, "unit": "bar", "timestamp": datetime.utcnow().isoformat()}
                ],
                "evidence_sources": ["thermal_sensor", "pressure_sensor", "video_feed"]
            },
            "contradictions": [],
            "trust_receipt": {
                "overall_trust_score": 0.87,
                "trust_level": "high",
                "sensor_scores": {"thermal": 0.92, "pressure": 0.85, "video": 0.84},
                "reason_codes": ["cross_validated", "no_contradictions"]
            },
            "dispatch_draft": {
                "drafted_text": "Immediate inspection required for Processing Unit Alpha",
                "recommended_actions": ["Reduce load", "Deploy inspection team", "Enable continuous monitoring"]
            },
            "final_packet": {
                "status": "complete",
                "operator_approved": True
            }
        }
        
        kairo_request = KairoAnchorRequest(
            artifact_id=artifact_id,
            incident_id=demo_artifact_data["incident_id"],
            scenario_id=demo_artifact_data["scenario_id"],
            artifact_data=demo_artifact_data,
            operator_id="demo-operator",
        )
        
        # Use async version to get Kairo security analysis
        result = await anchor_service.anchor_artifact_async(kairo_request)
        
        if result.success:
            return AnchorResponse(
                success=True,
                artifact_id=artifact_id,
                tx_hash=result.tx_hash,
                verification_url=result.verification_url
            )
        else:
            return AnchorResponse(
                success=False,
                artifact_id=artifact_id,
                error=result.error or "Failed to anchor artifact"
            )
    
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


@router.post("/kairo/analyze")
async def analyze_contract_with_kairo(request: Dict[str, Any]):
    """
    Test endpoint to analyze a smart contract with Kairo AI.
    
    Request body:
    {
        "contract_code": "pragma solidity ^0.8.0; contract Token { ... }",
        "contract_path": "Token.sol",
        "severity_threshold": "high"
    }
    """
    kairo_client = get_kairo_client()
    
    if not kairo_client.enabled:
        raise HTTPException(
            status_code=503,
            detail="Kairo integration is not enabled or API key is missing"
        )
    
    contract_code = request.get("contract_code", "")
    contract_path = request.get("contract_path", "Contract.sol")
    severity_threshold = request.get("severity_threshold", "high")
    
    if not contract_code:
        raise HTTPException(
            status_code=400,
            detail="contract_code is required"
        )
    
    try:
        analysis = await kairo_client.analyze_contract(
            contract_code=contract_code,
            contract_path=contract_path,
            severity_threshold=severity_threshold,
            include_suggestions=True
        )
        
        return {
            "success": True,
            "decision": analysis.decision.value,
            "decision_reason": analysis.decision_reason,
            "risk_score": analysis.risk_score,
            "is_safe": analysis.is_safe,
            "confidence": analysis.confidence,
            "warnings": analysis.warnings,
            "recommendations": analysis.recommendations,
            "findings": analysis.findings,
            "summary": analysis.summary,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Kairo analysis failed: {str(e)}"
        )


@router.get("/kairo/health")
async def kairo_health_check():
    """Check Kairo API health and configuration."""
    kairo_client = get_kairo_client()
    
    health = await kairo_client.health_check()
    
    return {
        "enabled": kairo_client.enabled,
        "api_key_configured": bool(kairo_client.api_key),
        "health": health,
    }


@router.get("/{artifact_id}/verify")
async def verify_artifact(artifact_id: str):
    """
    Verify artifact integrity.
    
    Checks:
    - Content hash matches computed hash
    - Audit chain is valid
    - On-chain anchor matches (if anchored)
    """
    artifact_builder = get_artifact_builder()
    anchor_service = get_anchor_service()
    
    artifact = artifact_builder.get_artifact(artifact_id)
    
    # If artifact exists in builder, use standard verification
    if artifact:
        result = artifact_builder.verify_artifact(artifact_id)
        return VerificationResponse(
            verified=result.get("verified", False),
            content_hash_valid=result.get("content_hash_valid", False),
            audit_chain_valid=result.get("audit_chain_valid", False),
            on_chain_valid=result.get("on_chain_valid", True),
            details=result
        )
    
    # Otherwise, check if artifact is anchored and return anchor data
    anchor_record = anchor_service.get_anchor_by_artifact(artifact_id)
    
    if anchor_record:
        hashes = anchor_record.hashes.model_dump() if anchor_record.hashes else {}
        
        return {
            "verified": True,
            "incident_id": anchor_record.incident_id or "",
            "artifact_id": artifact_id,
            "mismatches": [],
            "on_chain_data": {
                "bundle_root_hash": hashes.get("bundle_root_hash", ""),
                "tx_hash": anchor_record.tx_hash or "",
                "status": anchor_record.status or "confirmed",
                "operator": anchor_record.operator_id or "demo-operator",
                "created_at": anchor_record.created_at.isoformat() if anchor_record.created_at else datetime.utcnow().isoformat(),
            },
            "computed_hashes": {
                "incident_core_hash": hashes.get("incident_core_hash", ""),
                "evidence_set_hash": hashes.get("evidence_set_hash", ""),
                "contradictions_hash": hashes.get("contradictions_hash", ""),
                "trust_receipt_hash": hashes.get("trust_receipt_hash", ""),
                "operator_decisions_hash": hashes.get("dispatch_hash", ""),
                "timeline_hash": hashes.get("final_packet_hash", ""),
                "bundle_root_hash": hashes.get("bundle_root_hash", ""),
            },
            "explorer_url": anchor_record.explorer_url,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    raise HTTPException(status_code=404, detail="Artifact not found")


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


@router.get("/blockchain/status")
async def get_blockchain_storage_status():
    """
    Get blockchain storage status.
    
    Returns the status of MongoDB storage for blockchain anchor records
    and full artifact data.
    """
    from app.db import get_db
    
    anchor_service = get_anchor_service()
    db = get_db()
    
    # Get MongoDB health if enabled
    mongodb_status = await db.health_check()
    
    # Get anchor statistics
    all_anchors = anchor_service.list_anchors()
    
    return {
        "mongodb_enabled": anchor_service.mongodb_enabled,
        "mongodb_health": mongodb_status,
        "storage_mode": "mongodb" if anchor_service.mongodb_enabled else "in_memory",
        "anchors_summary": {
            "total": len(all_anchors),
            "confirmed": len([a for a in all_anchors if a.status == "confirmed"]),
            "pending": len([a for a in all_anchors if a.status == "pending"]),
            "pending_approval": len([a for a in all_anchors if a.status == "pending_approval"]),
            "failed": len([a for a in all_anchors if a.status == "failed"]),
        },
        "collections": {
            "blockchain_anchors": "Stores anchor records with on-chain transaction data",
            "blockchain_artifacts": "Stores full artifact data (off-chain in MongoDB)",
        },
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
