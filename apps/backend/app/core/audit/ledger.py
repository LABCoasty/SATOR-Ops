"""
Audit Ledger Module

Append-only audit log with hash chaining for tamper evidence.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from app.models.audit import AuditEvent, AuditChain, DecisionReceipt
from .hasher import HashChain, compute_standalone_hash
from config import config


class AuditLedger:
    """
    Append-only audit log with SHA-256 hash chaining.
    
    Provides tamper-evident logging of all critical system events:
    - Incident creation
    - Trust updates
    - State transitions
    - Operator actions
    - Decision receipts
    
    The hash chain creates a mathematical dependency between events,
    making any modification to historical records detectable.
    """
    
    def __init__(self, anchor=None):
        """
        Initialize the audit ledger.
        
        Args:
            anchor: Optional AuditAnchor implementation for on-chain anchoring (Kairo)
        """
        self._hash_chain = HashChain()
        self._events: list[AuditEvent] = []
        self._chain_id = str(uuid.uuid4())
        self._created_at = datetime.utcnow()
        self._data_path = Path(config.data_dir) / "audit"
        self._anchor = anchor
    
    @property
    def chain_id(self) -> str:
        return self._chain_id
    
    @property
    def event_count(self) -> int:
        return len(self._events)
    
    @property
    def latest_hash(self) -> str:
        return self._hash_chain.latest_hash
    
    @property
    def genesis_hash(self) -> str:
        if self._events:
            return self._events[0].current_hash
        return HashChain.GENESIS_HASH
    
    async def log_event(
        self,
        action: str,
        actor: Literal["system", "user", "agent"],
        payload: dict,
        actor_id: str | None = None,
        data_ref: str | None = None,
        anchor_on_chain: bool = False,
    ) -> AuditEvent:
        """
        Log an event to the audit ledger.
        
        Args:
            action: Type of action (see AuditAction constants)
            actor: Who/what caused the event
            payload: Event-specific data
            actor_id: Specific actor identifier
            data_ref: Reference to related artifact
            anchor_on_chain: Whether to anchor on Solana via Kairo
            
        Returns:
            The created AuditEvent
        """
        event_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()
        
        # Prepare event data for hashing (excludes hash fields)
        event_data = {
            "event_id": event_id,
            "timestamp": timestamp.isoformat(),
            "actor": actor,
            "actor_id": actor_id,
            "action": action,
            "payload": payload,
            "data_ref": data_ref,
        }
        
        # Compute hashes
        prev_hash, current_hash = self._hash_chain.add_event(event_data)
        
        # Create event
        event = AuditEvent(
            event_id=event_id,
            timestamp=timestamp,
            actor=actor,
            actor_id=actor_id,
            action=action,
            payload=payload,
            data_ref=data_ref,
            prev_hash=prev_hash,
            current_hash=current_hash,
        )
        
        # Anchor on-chain if requested and anchor is available
        if anchor_on_chain and self._anchor:
            try:
                receipt = await self._anchor.anchor_hash(
                    current_hash,
                    {"event_id": event_id, "action": action}
                )
                if receipt:
                    event.anchor_tx_sig = receipt.tx_signature
            except Exception as e:
                # Anchor failure doesn't block logging (sidecar pattern)
                print(f"Warning: On-chain anchor failed: {e}")
        
        # Append to ledger
        self._events.append(event)
        
        # Persist to storage
        await self._persist_event(event)
        
        return event
    
    async def log_incident_created(
        self,
        incident_id: str,
        description: str,
        triggered_by: str,
        confidence: float,
    ) -> AuditEvent:
        """Log incident creation"""
        return await self.log_event(
            action="incident_created",
            actor="system",
            payload={
                "incident_id": incident_id,
                "description": description,
                "triggered_by": triggered_by,
                "initial_confidence": confidence,
            },
            data_ref=incident_id,
        )
    
    async def log_trust_updated(
        self,
        tag_id: str,
        old_score: float,
        new_score: float,
        reason_codes: list[str],
        evidence_refs: list[str],
    ) -> AuditEvent:
        """Log trust score update"""
        return await self.log_event(
            action="trust_updated",
            actor="system",
            payload={
                "tag_id": tag_id,
                "old_score": old_score,
                "new_score": new_score,
                "reason_codes": reason_codes,
                "evidence_refs": evidence_refs,
            },
        )
    
    async def log_state_transition(
        self,
        old_mode: str,
        new_mode: str,
        trigger: str,
    ) -> AuditEvent:
        """Log operational mode transition"""
        return await self.log_event(
            action="state_transition",
            actor="system",
            payload={
                "old_mode": old_mode,
                "new_mode": new_mode,
                "trigger": trigger,
            },
        )
    
    async def log_operator_action(
        self,
        operator_id: str,
        action_type: str,
        action_description: str,
        rationale: str,
        incident_id: str | None = None,
    ) -> AuditEvent:
        """Log operator action/decision"""
        return await self.log_event(
            action="operator_action",
            actor="user",
            actor_id=operator_id,
            payload={
                "action_type": action_type,
                "action_description": action_description,
                "rationale": rationale,
                "incident_id": incident_id,
            },
            data_ref=incident_id,
            anchor_on_chain=True,  # Anchor decisions on-chain
        )
    
    async def log_decision_receipt(
        self,
        receipt: DecisionReceipt,
    ) -> AuditEvent:
        """Log a decision receipt"""
        return await self.log_event(
            action="decision_receipt",
            actor="system",
            payload={
                "receipt_id": receipt.receipt_id,
                "content_hash": receipt.content_hash,
                "operator_id": receipt.operator_id,
                "action_type": receipt.action_type,
            },
            data_ref=receipt.receipt_id,
            anchor_on_chain=True,  # Decision receipts are anchored
        )
    
    async def log_chain_verified(
        self,
        is_valid: bool,
        events_checked: int,
        error_message: str | None = None,
    ) -> AuditEvent:
        """Log audit chain verification"""
        return await self.log_event(
            action="chain_verified",
            actor="system",
            payload={
                "is_valid": is_valid,
                "events_checked": events_checked,
                "error_message": error_message,
            },
        )
    
    def get_events(
        self,
        start_idx: int = 0,
        limit: int | None = None,
        action_filter: str | None = None,
    ) -> list[AuditEvent]:
        """Get events from the ledger"""
        events = self._events[start_idx:]
        
        if action_filter:
            events = [e for e in events if e.action == action_filter]
        
        if limit:
            events = events[:limit]
        
        return events
    
    def get_event_by_id(self, event_id: str) -> AuditEvent | None:
        """Get a specific event by ID"""
        for event in self._events:
            if event.event_id == event_id:
                return event
        return None
    
    def get_chain_info(self) -> dict:
        """Get chain metadata"""
        return {
            "chain_id": self._chain_id,
            "created_at": self._created_at.isoformat(),
            "event_count": len(self._events),
            "genesis_hash": self.genesis_hash,
            "latest_hash": self.latest_hash,
        }
    
    def export_chain(self) -> AuditChain:
        """Export the complete audit chain"""
        return AuditChain(
            chain_id=self._chain_id,
            created_at=self._created_at,
            genesis_hash=self.genesis_hash,
            latest_hash=self.latest_hash,
            event_count=len(self._events),
            events=self._events.copy(),
        )
    
    async def _persist_event(self, event: AuditEvent) -> None:
        """Persist an event to storage"""
        self._data_path.mkdir(parents=True, exist_ok=True)
        
        # Append to chain file
        chain_file = self._data_path / f"chain_{self._chain_id}.jsonl"
        
        with open(chain_file, "a") as f:
            f.write(event.model_dump_json() + "\n")
    
    async def load_from_storage(self, chain_id: str | None = None) -> bool:
        """
        Load audit chain from storage.
        
        Returns True if a chain was loaded.
        """
        if not self._data_path.exists():
            return False
        
        # Find chain file
        if chain_id:
            chain_file = self._data_path / f"chain_{chain_id}.jsonl"
        else:
            # Load most recent chain
            chain_files = list(self._data_path.glob("chain_*.jsonl"))
            if not chain_files:
                return False
            chain_file = max(chain_files, key=lambda p: p.stat().st_mtime)
            chain_id = chain_file.stem.replace("chain_", "")
        
        if not chain_file.exists():
            return False
        
        # Load events
        self._events.clear()
        self._chain_id = chain_id
        
        with open(chain_file) as f:
            for line in f:
                if line.strip():
                    event = AuditEvent.model_validate_json(line)
                    self._events.append(event)
        
        # Update hash chain state
        if self._events:
            self._hash_chain.set_state(
                self._events[-1].current_hash,
                len(self._events),
            )
            self._created_at = self._events[0].timestamp
        
        return True


def create_decision_receipt(
    operator_id: str,
    action_type: str,
    action_description: str,
    rationale: str,
    uncertainty_snapshot: dict,
    active_contradictions: list[str],
    evidence_refs: list[str],
) -> DecisionReceipt:
    """
    Create a decision receipt for an operator action.
    
    This is the immutable record generated the moment an action is taken.
    """
    receipt_id = str(uuid.uuid4())
    timestamp = datetime.utcnow()
    
    # Compute content hash
    content = {
        "receipt_id": receipt_id,
        "timestamp": timestamp.isoformat(),
        "operator_id": operator_id,
        "action_type": action_type,
        "action_description": action_description,
        "rationale": rationale,
        "uncertainty_snapshot": uncertainty_snapshot,
        "active_contradictions": active_contradictions,
        "evidence_refs": evidence_refs,
    }
    content_hash = compute_standalone_hash(content)
    
    return DecisionReceipt(
        receipt_id=receipt_id,
        timestamp=timestamp,
        operator_id=operator_id,
        action_type=action_type,
        action_description=action_description,
        rationale=rationale,
        uncertainty_snapshot=uncertainty_snapshot,
        active_contradictions=active_contradictions,
        evidence_refs=evidence_refs,
        content_hash=content_hash,
    )
