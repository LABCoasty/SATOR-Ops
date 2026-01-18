"""
Kairo AI Sec - Blockchain integration for secure artifact anchoring.

Provides on-chain anchoring of artifact hashes for tamper-evident audit trail.
"""

from .anchor import (
    KairoAnchorService,
    AnchorRecord,
    AnchorRequest,
    AnchorResult,
    ArtifactHashes,
    VerificationResult,
    OperatorRole,
    get_anchor_service,
    compute_artifact_hashes,
    sha256_hash,
    canonicalize,
)

__all__ = [
    "KairoAnchorService",
    "AnchorRecord",
    "AnchorRequest",
    "AnchorResult",
    "ArtifactHashes",
    "VerificationResult",
    "OperatorRole",
    "get_anchor_service",
    "compute_artifact_hashes",
    "sha256_hash",
    "canonicalize",
]
