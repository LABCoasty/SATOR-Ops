"""
Chain Verifier Module

Verifies integrity of the hash-chained audit log.
"""

from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from app.models.audit import AuditEvent, AuditChain
from .hasher import HashChain, verify_hash_integrity


class VerificationStatus(str, Enum):
    """Status of verification result"""
    PASS = "pass"
    FAIL = "fail"
    PARTIAL = "partial"  # Some events verified but chain incomplete


@dataclass
class VerificationResult:
    """Result of an audit chain verification"""
    status: VerificationStatus
    is_valid: bool
    events_checked: int
    events_passed: int
    events_failed: int
    first_failure_index: int | None
    error_message: str | None
    genesis_hash: str
    latest_hash: str
    verified_at: datetime
    
    def to_dict(self) -> dict:
        return {
            "status": self.status.value,
            "is_valid": self.is_valid,
            "events_checked": self.events_checked,
            "events_passed": self.events_passed,
            "events_failed": self.events_failed,
            "first_failure_index": self.first_failure_index,
            "error_message": self.error_message,
            "genesis_hash": self.genesis_hash,
            "latest_hash": self.latest_hash,
            "verified_at": self.verified_at.isoformat(),
        }


class ChainVerifier:
    """
    Verifies the integrity of hash-chained audit logs.
    
    The verifier iterates through all events, recomputing hashes
    and checking continuity to detect any tampering.
    """
    
    def __init__(self):
        self._hash_chain = HashChain()
    
    def verify_chain(
        self,
        events: list[AuditEvent] | list[dict],
        genesis_hash: str | None = None,
    ) -> VerificationResult:
        """
        Verify the integrity of an audit chain.
        
        Args:
            events: List of audit events to verify
            genesis_hash: Expected genesis hash (defaults to standard)
            
        Returns:
            VerificationResult with detailed status
        """
        verified_at = datetime.utcnow()
        
        if not events:
            return VerificationResult(
                status=VerificationStatus.PASS,
                is_valid=True,
                events_checked=0,
                events_passed=0,
                events_failed=0,
                first_failure_index=None,
                error_message=None,
                genesis_hash=HashChain.GENESIS_HASH,
                latest_hash=HashChain.GENESIS_HASH,
                verified_at=verified_at,
            )
        
        if genesis_hash is None:
            genesis_hash = HashChain.GENESIS_HASH
        
        # Convert to dicts if needed
        event_dicts = []
        for event in events:
            if isinstance(event, AuditEvent):
                event_dicts.append(event.model_dump(mode="json"))
            else:
                event_dicts.append(event)
        
        events_passed = 0
        first_failure_index = None
        error_message = None
        
        for i, event in enumerate(event_dicts):
            is_valid, error = self._verify_single_event(
                event, 
                i, 
                event_dicts[i - 1] if i > 0 else None,
                genesis_hash,
            )
            
            if is_valid:
                events_passed += 1
            else:
                if first_failure_index is None:
                    first_failure_index = i
                    error_message = error
        
        events_failed = len(event_dicts) - events_passed
        is_valid = events_failed == 0
        
        # Determine status
        if is_valid:
            status = VerificationStatus.PASS
        elif events_passed > 0:
            status = VerificationStatus.PARTIAL
        else:
            status = VerificationStatus.FAIL
        
        # Get hashes
        first_event = event_dicts[0]
        last_event = event_dicts[-1]
        
        return VerificationResult(
            status=status,
            is_valid=is_valid,
            events_checked=len(event_dicts),
            events_passed=events_passed,
            events_failed=events_failed,
            first_failure_index=first_failure_index,
            error_message=error_message,
            genesis_hash=first_event.get("current_hash", ""),
            latest_hash=last_event.get("current_hash", ""),
            verified_at=verified_at,
        )
    
    def _verify_single_event(
        self,
        event: dict,
        index: int,
        prev_event: dict | None,
        genesis_hash: str,
    ) -> tuple[bool, str | None]:
        """Verify a single event in the chain"""
        recorded_prev_hash = event.get("prev_hash")
        recorded_current_hash = event.get("current_hash")
        
        # Check for required fields
        if not recorded_prev_hash or not recorded_current_hash:
            return False, f"Event {index} missing hash fields"
        
        # Check chain continuity
        if index == 0:
            # First event should chain from genesis
            if recorded_prev_hash != genesis_hash:
                return False, f"Event 0 prev_hash doesn't match genesis"
        else:
            # Should chain from previous event
            if prev_event and recorded_prev_hash != prev_event.get("current_hash"):
                return False, f"Event {index} prev_hash doesn't match previous current_hash"
        
        # Recompute hash to verify
        event_data = self._extract_hashable_data(event)
        computed_hash = self._hash_chain.compute_hash(event_data, recorded_prev_hash)
        
        if computed_hash != recorded_current_hash:
            return False, f"Event {index} hash mismatch"
        
        return True, None
    
    def _extract_hashable_data(self, event: dict) -> dict:
        """Extract the data that should be hashed (excludes hash fields)"""
        exclude_keys = {"prev_hash", "current_hash", "anchor_tx_sig"}
        return {k: v for k, v in event.items() if k not in exclude_keys}
    
    def verify_single_hash(
        self,
        event_data: dict,
        expected_hash: str,
        prev_hash: str,
    ) -> bool:
        """Verify a single event's hash"""
        computed = self._hash_chain.compute_hash(event_data, prev_hash)
        return computed == expected_hash
    
    def quick_verify(self, chain: AuditChain) -> bool:
        """
        Quick verification using chain metadata.
        
        Verifies first and last events only - useful for fast checks.
        """
        if not chain.events:
            return chain.event_count == 0
        
        # Check event count
        if len(chain.events) != chain.event_count:
            return False
        
        # Verify first event chains from genesis
        first = chain.events[0]
        if first.prev_hash != HashChain.GENESIS_HASH:
            return False
        
        # Verify genesis hash matches
        if first.current_hash != chain.genesis_hash:
            return False
        
        # Verify latest hash matches
        last = chain.events[-1]
        if last.current_hash != chain.latest_hash:
            return False
        
        return True


def verify_audit_chain(events: list[AuditEvent]) -> dict:
    """
    Convenience function to verify an audit chain.
    
    Returns a dict suitable for API response.
    """
    verifier = ChainVerifier()
    result = verifier.verify_chain(events)
    return result.to_dict()


def verify_decision_receipt(receipt_data: dict, stored_hash: str) -> bool:
    """
    Verify a decision receipt's content hash.
    
    Ensures the receipt content hasn't been modified since creation.
    """
    from .hasher import compute_standalone_hash
    
    # Exclude the stored hash from computation
    data_to_hash = {k: v for k, v in receipt_data.items() if k != "content_hash"}
    computed_hash = compute_standalone_hash(data_to_hash)
    
    return computed_hash == stored_hash
