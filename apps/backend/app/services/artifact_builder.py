"""
Artifact Builder - Compiles complete decision packets for export and anchoring.

Creates the final ArtifactPacket that contains all evidence, decisions,
audit trail, and verification data for an incident.
"""

import uuid
import hashlib
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from .incident_manager import Incident, get_incident_manager
from .audit_logger import AuditLogEvent, get_audit_logger
from .data_loader import TelemetryReading, Contradiction
from ..integrations.overshoot.models import VisionFrame
from ..integrations.kairo.anchor import (
    get_anchor_service, 
    AnchorRequest,
    AnchorRecord
)


# ============================================================================
# Artifact Models
# ============================================================================

class TrustReceipt(BaseModel):
    """Trust receipt documenting trust calculation."""
    receipt_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    incident_id: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Trust Calculation
    overall_trust_score: float
    trust_level: str  # high, moderate, low, critical
    
    # Breakdown
    sensor_scores: Dict[str, float]
    reason_codes: List[str]
    
    # Evidence Summary
    contradictions_count: int
    evidence_sources: List[str]
    vision_validated: bool = False
    
    # Operator Input
    questions_asked: int = 0
    questions_answered: int = 0
    operator_trust_adjustments: float = 0.0
    
    # Cryptographic
    content_hash: str = ""
    previous_receipt_hash: Optional[str] = None


class ArtifactPacket(BaseModel):
    """Complete decision packet for export and verification."""
    artifact_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    incident_id: str
    scenario_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Summary
    title: str
    incident_summary: str
    resolution_summary: str
    
    # Timeline
    incident_opened_at: datetime
    incident_closed_at: datetime
    total_duration_seconds: float
    
    # Evidence Bundle
    telemetry_samples: List[Dict[str, Any]] = Field(default_factory=list)
    vision_frames: List[Dict[str, Any]] = Field(default_factory=list)
    contradictions: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Trust
    final_trust_receipt: TrustReceipt
    trust_history: List[TrustReceipt] = Field(default_factory=list)
    
    # Decision
    decision_card: Dict[str, Any]
    action_taken: str
    action_rationale: str
    operator_id: str
    
    # Operator Interaction
    questions_asked: List[Dict[str, Any]] = Field(default_factory=list)
    questions_answered: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Audit
    audit_trail: List[Dict[str, Any]] = Field(default_factory=list)
    audit_chain_valid: bool = True
    
    # Verification
    content_hash: str = ""
    on_chain_anchor: Optional[Dict[str, Any]] = None
    
    # Export
    exportable_formats: List[str] = Field(default_factory=lambda: ["json", "pdf"])


# ============================================================================
# Artifact Builder Service
# ============================================================================

class ArtifactBuilderService:
    """
    Service for building complete artifact packets.
    
    Responsibilities:
    - Compile all incident data into artifact
    - Generate trust receipts
    - Compute content hashes
    - Coordinate with Kairo for on-chain anchoring
    """
    
    def __init__(self):
        self._artifacts: Dict[str, ArtifactPacket] = {}
        self._trust_receipts: Dict[str, List[TrustReceipt]] = {}  # incident_id -> receipts
    
    # ========================================================================
    # Trust Receipt Generation
    # ========================================================================
    
    def generate_trust_receipt(
        self,
        incident_id: str,
        trust_score: float,
        sensor_scores: Dict[str, float],
        reason_codes: List[str],
        contradictions: List[Any],
        evidence_sources: List[str],
        vision_validated: bool = False,
        questions_asked: int = 0,
        questions_answered: int = 0,
        operator_adjustments: float = 0.0
    ) -> TrustReceipt:
        """
        Generate a trust receipt for the current state.
        
        Args:
            incident_id: The incident ID
            trust_score: Overall trust score
            sensor_scores: Individual sensor trust scores
            reason_codes: Active reason codes
            contradictions: List of contradictions
            evidence_sources: Sources of evidence used
            vision_validated: Whether vision validation was done
            questions_asked: Number of operator questions asked
            questions_answered: Number answered
            operator_adjustments: Trust adjustments from operator input
            
        Returns:
            Generated TrustReceipt
        """
        # Get previous receipt hash for chaining
        previous_hash = None
        if incident_id in self._trust_receipts and self._trust_receipts[incident_id]:
            previous_hash = self._trust_receipts[incident_id][-1].content_hash
        
        # Determine trust level
        if trust_score >= 0.8:
            trust_level = "high"
        elif trust_score >= 0.5:
            trust_level = "moderate"
        elif trust_score >= 0.3:
            trust_level = "low"
        else:
            trust_level = "critical"
        
        receipt = TrustReceipt(
            incident_id=incident_id,
            overall_trust_score=trust_score,
            trust_level=trust_level,
            sensor_scores=sensor_scores,
            reason_codes=reason_codes,
            contradictions_count=len(contradictions),
            evidence_sources=evidence_sources,
            vision_validated=vision_validated,
            questions_asked=questions_asked,
            questions_answered=questions_answered,
            operator_trust_adjustments=operator_adjustments,
            previous_receipt_hash=previous_hash
        )
        
        # Compute content hash
        receipt.content_hash = self._compute_receipt_hash(receipt)
        
        # Store receipt
        if incident_id not in self._trust_receipts:
            self._trust_receipts[incident_id] = []
        self._trust_receipts[incident_id].append(receipt)
        
        return receipt
    
    def _compute_receipt_hash(self, receipt: TrustReceipt) -> str:
        """Compute hash for trust receipt."""
        content = {
            "receipt_id": receipt.receipt_id,
            "incident_id": receipt.incident_id,
            "generated_at": receipt.generated_at.isoformat(),
            "trust_score": receipt.overall_trust_score,
            "sensor_scores": receipt.sensor_scores,
            "reason_codes": receipt.reason_codes,
            "previous_hash": receipt.previous_receipt_hash
        }
        content_str = json.dumps(content, sort_keys=True, default=str)
        return hashlib.sha256(content_str.encode()).hexdigest()
    
    def get_trust_receipts(self, incident_id: str) -> List[TrustReceipt]:
        """Get all trust receipts for an incident."""
        return self._trust_receipts.get(incident_id, [])
    
    # ========================================================================
    # Artifact Building
    # ========================================================================
    
    def build_artifact(
        self,
        incident: Incident,
        telemetry_samples: List[TelemetryReading],
        contradictions: List[Contradiction],
        decision_card: Dict[str, Any],
        vision_frames: Optional[List[VisionFrame]] = None,
        questions_asked: Optional[List[Dict[str, Any]]] = None,
        questions_answered: Optional[List[Dict[str, Any]]] = None
    ) -> ArtifactPacket:
        """
        Build complete artifact packet for an incident.
        
        Args:
            incident: The closed incident
            telemetry_samples: Telemetry data from the incident
            contradictions: Detected contradictions
            decision_card: The decision card used
            vision_frames: Vision frames (if Scenario 2)
            questions_asked: Operator questions
            questions_answered: Operator answers
            
        Returns:
            Complete ArtifactPacket
        """
        # Get audit trail
        audit_logger = get_audit_logger()
        audit_trail = audit_logger.get_incident_trail(incident.incident_id)
        audit_chain_valid = audit_logger.verify_chain()
        
        # Get trust receipts
        trust_receipts = self.get_trust_receipts(incident.incident_id)
        
        # Generate final trust receipt if none exists
        if not trust_receipts:
            # Create a basic receipt
            final_receipt = self.generate_trust_receipt(
                incident_id=incident.incident_id,
                trust_score=0.5,
                sensor_scores={},
                reason_codes=[],
                contradictions=contradictions,
                evidence_sources=["telemetry"],
                vision_validated=bool(vision_frames),
                questions_asked=len(questions_asked or []),
                questions_answered=len(questions_answered or [])
            )
        else:
            final_receipt = trust_receipts[-1]
        
        # Calculate duration
        if incident.closed_at and incident.created_at:
            duration = (incident.closed_at - incident.created_at).total_seconds()
        else:
            duration = 0.0
        
        # Build artifact
        artifact = ArtifactPacket(
            incident_id=incident.incident_id,
            scenario_id=incident.scenario_id,
            
            # Summary
            title=incident.title,
            incident_summary=incident.description,
            resolution_summary=incident.resolution_summary or "Incident resolved",
            
            # Timeline
            incident_opened_at=incident.created_at,
            incident_closed_at=incident.closed_at or datetime.utcnow(),
            total_duration_seconds=duration,
            
            # Evidence
            telemetry_samples=[t.model_dump() if hasattr(t, 'model_dump') else t for t in telemetry_samples],
            vision_frames=[v.model_dump() if hasattr(v, 'model_dump') else v for v in (vision_frames or [])],
            contradictions=[c.model_dump() if hasattr(c, 'model_dump') else c for c in contradictions],
            
            # Trust
            final_trust_receipt=final_receipt,
            trust_history=trust_receipts,
            
            # Decision
            decision_card=decision_card,
            action_taken=incident.action_taken or "unknown",
            action_rationale=incident.action_rationale or "",
            operator_id=incident.assigned_operator_id or "unknown",
            
            # Operator Interaction
            questions_asked=questions_asked or [],
            questions_answered=questions_answered or [],
            
            # Audit
            audit_trail=[e.model_dump() if hasattr(e, 'model_dump') else e for e in audit_trail],
            audit_chain_valid=audit_chain_valid
        )
        
        # Compute content hash
        artifact.content_hash = self._compute_artifact_hash(artifact)
        
        # Store artifact
        self._artifacts[artifact.artifact_id] = artifact
        
        # Log artifact creation
        audit_logger.log_artifact_created(
            incident_id=incident.incident_id,
            scenario_id=incident.scenario_id,
            artifact_id=artifact.artifact_id,
            content_hash=artifact.content_hash
        )
        
        return artifact
    
    def _compute_artifact_hash(self, artifact: ArtifactPacket) -> str:
        """Compute hash of entire artifact packet."""
        # Exclude the content_hash field itself and on_chain_anchor
        content = artifact.model_dump(exclude={"content_hash", "on_chain_anchor"})
        content_str = json.dumps(content, sort_keys=True, default=str)
        return hashlib.sha256(content_str.encode()).hexdigest()
    
    # ========================================================================
    # On-Chain Anchoring
    # ========================================================================
    
    def anchor_artifact(self, artifact_id: str) -> Optional[AnchorRecord]:
        """
        Anchor an artifact on-chain via KairoAISec.
        
        Args:
            artifact_id: The artifact ID to anchor
            
        Returns:
            AnchorRecord if successful, None otherwise
        """
        artifact = self._artifacts.get(artifact_id)
        if not artifact:
            return None
        
        anchor_service = get_anchor_service()
        
        request = AnchorRequest(
            artifact_id=artifact_id,
            incident_id=artifact.incident_id,
            artifact_data=artifact.model_dump(),
            trust_score=artifact.final_trust_receipt.overall_trust_score,
            issuer="sator-ops"
        )
        
        result = anchor_service.anchor_artifact(request)
        
        if result.success and result.anchor_record:
            # Update artifact with anchor info
            artifact.on_chain_anchor = result.anchor_record.model_dump()
            
            # Log anchoring
            audit_logger = get_audit_logger()
            audit_logger.log_artifact_anchored(
                incident_id=artifact.incident_id,
                scenario_id=artifact.scenario_id,
                artifact_id=artifact_id,
                tx_hash=result.anchor_record.tx_hash or ""
            )
            
            return result.anchor_record
        
        return None
    
    # ========================================================================
    # Queries
    # ========================================================================
    
    def get_artifact(self, artifact_id: str) -> Optional[ArtifactPacket]:
        """Get an artifact by ID."""
        return self._artifacts.get(artifact_id)
    
    def get_artifact_by_incident(self, incident_id: str) -> Optional[ArtifactPacket]:
        """Get artifact for an incident."""
        for artifact in self._artifacts.values():
            if artifact.incident_id == incident_id:
                return artifact
        return None
    
    def export_artifact(self, artifact_id: str, format: str = "json") -> Optional[str]:
        """
        Export artifact in specified format.
        
        Args:
            artifact_id: The artifact ID
            format: Export format (json, pdf)
            
        Returns:
            Exported content as string
        """
        artifact = self._artifacts.get(artifact_id)
        if not artifact:
            return None
        
        if format == "json":
            return artifact.model_dump_json(indent=2)
        elif format == "pdf":
            # PDF generation would be implemented here
            return f"PDF export not implemented - artifact_id: {artifact_id}"
        
        return None
    
    def verify_artifact(self, artifact_id: str) -> Dict[str, Any]:
        """
        Verify artifact integrity.
        
        Checks:
        - Content hash matches
        - Audit chain is valid
        - On-chain anchor matches (if anchored)
        
        Returns:
            Verification result
        """
        artifact = self._artifacts.get(artifact_id)
        if not artifact:
            return {"verified": False, "error": "Artifact not found"}
        
        # Recompute hash
        computed_hash = self._compute_artifact_hash(artifact)
        hash_valid = computed_hash == artifact.content_hash
        
        # Check on-chain anchor
        anchor_valid = True
        if artifact.on_chain_anchor:
            anchor_service = get_anchor_service()
            anchor_result = anchor_service.verify_anchor(
                artifact.on_chain_anchor.get("anchor_id", "")
            )
            anchor_valid = anchor_result.get("verified", False)
        
        return {
            "verified": hash_valid and artifact.audit_chain_valid and anchor_valid,
            "content_hash_valid": hash_valid,
            "audit_chain_valid": artifact.audit_chain_valid,
            "on_chain_valid": anchor_valid,
            "content_hash": artifact.content_hash,
            "on_chain_anchor": artifact.on_chain_anchor
        }


# ============================================================================
# Singleton instance
# ============================================================================

_artifact_builder: Optional[ArtifactBuilderService] = None


def get_artifact_builder() -> ArtifactBuilderService:
    """Get the singleton ArtifactBuilderService instance."""
    global _artifact_builder
    if _artifact_builder is None:
        _artifact_builder = ArtifactBuilderService()
    return _artifact_builder
