"""
Audit Data Models

Models for the hash-chained tamper-evident audit log.
"""

from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, Field


class AuditAction(str):
    """Standard audit actions"""
    INCIDENT_CREATED = "incident_created"
    TRUST_UPDATED = "trust_updated"
    STATE_TRANSITION = "state_transition"
    OPERATOR_ACTION = "operator_action"
    DECISION_RECEIPT = "decision_receipt"
    CHAIN_VERIFIED = "chain_verified"
    SYSTEM_START = "system_start"
    SYSTEM_STOP = "system_stop"


class AuditEvent(BaseModel):
    """
    A single event in the hash-chained audit log.
    
    Each event contains a hash of itself combined with the previous
    event's hash, creating a tamper-evident chain.
    """
    event_id: str = Field(..., description="Unique event identifier (UUID)")
    timestamp: datetime = Field(..., description="ISO8601 timestamp")
    
    # Actor information
    actor: Literal["system", "user", "agent"] = Field(
        ..., 
        description="Who/what caused this event"
    )
    actor_id: str | None = Field(None, description="Specific actor identifier")
    
    # Action details
    action: str = Field(..., description="Type of action (see AuditAction)")
    
    # Payload - the actual event data
    payload: dict[str, Any] = Field(
        default_factory=dict, 
        description="Event-specific data"
    )
    
    # References
    data_ref: str | None = Field(
        None, 
        description="ID of associated TrustReceipt, Decision, or other artifact"
    )
    
    # Hash chain
    prev_hash: str = Field(..., description="Hash of the previous event")
    current_hash: str = Field(..., description="Hash of this event (including prev_hash)")
    
    # Optional on-chain anchor (Kairo integration)
    anchor_tx_sig: str | None = Field(
        None, 
        description="Solana transaction signature if anchored on-chain"
    )
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AuditChain(BaseModel):
    """
    Represents the complete audit chain or a subset.
    
    Used for verification and export.
    """
    chain_id: str = Field(..., description="Identifier for this chain")
    created_at: datetime = Field(..., description="When chain was started")
    
    # Chain metadata
    genesis_hash: str = Field(..., description="Hash of the first event")
    latest_hash: str = Field(..., description="Hash of the most recent event")
    event_count: int = Field(default=0, description="Total events in chain")
    
    # Verification status
    last_verified_at: datetime | None = Field(None, description="Last verification time")
    is_valid: bool = Field(default=True, description="Whether chain is intact")
    
    # Events (may be a subset for large chains)
    events: list[AuditEvent] = Field(default_factory=list, description="Chain events")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AnchorReceipt(BaseModel):
    """
    Receipt for an on-chain anchor operation (Kairo integration).
    
    Provides cryptographic proof that an audit hash existed at a specific time.
    """
    receipt_id: str = Field(..., description="Receipt identifier")
    timestamp: datetime = Field(..., description="When anchor was created")
    
    # What was anchored
    audit_event_id: str = Field(..., description="ID of the anchored audit event")
    anchored_hash: str = Field(..., description="The hash that was anchored")
    
    # Solana transaction details
    tx_signature: str = Field(..., description="Solana transaction signature")
    slot: int = Field(..., description="Solana slot number")
    block_time: datetime | None = Field(None, description="Block timestamp")
    
    # Verification
    verified: bool = Field(default=False, description="Whether anchor was verified")
    verified_at: datetime | None = Field(None, description="When verification occurred")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DecisionReceipt(BaseModel):
    """
    Immutable record of a decision made in the system.
    
    Generated the moment an action is taken, capturing the complete
    context for defensibility.
    """
    receipt_id: str = Field(..., description="Receipt identifier")
    timestamp: datetime = Field(..., description="When decision was made")
    
    # Decision details
    operator_id: str = Field(..., description="Who made the decision")
    action_type: str = Field(..., description="act, escalate, or defer")
    action_description: str = Field(..., description="What was decided")
    rationale: str = Field(..., description="Why this decision was made")
    
    # Context snapshot
    uncertainty_snapshot: dict = Field(
        ..., 
        description="Trust scores and reason codes at decision time"
    )
    active_contradictions: list[str] = Field(
        default_factory=list,
        description="Contradiction IDs active at decision time"
    )
    evidence_refs: list[str] = Field(
        default_factory=list,
        description="Evidence item IDs considered"
    )
    
    # Hash for audit log
    content_hash: str = Field(..., description="SHA-256 hash of receipt content")
    
    # Audit chain reference
    audit_event_id: str | None = Field(
        None, 
        description="ID of audit event recording this receipt"
    )
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
