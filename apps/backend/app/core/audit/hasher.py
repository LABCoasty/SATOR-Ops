"""
Hash Chain Module

Implements SHA-256 hash chaining for tamper-evident audit logging.
"""

import hashlib
import json
from datetime import datetime
from typing import Any


class HashChain:
    """
    Implements cryptographic hash chaining for tamper-evidence.
    
    Each event hash includes the previous event's hash, creating a
    mathematical dependency that breaks if any historical record is modified.
    
    Formula: H_n = SHA256(CanonicalJSON(E_n) + H_{n-1})
    """
    
    # Genesis hash for the first event in a chain
    GENESIS_HASH = "0" * 64  # 64 hex chars = 256 bits
    
    def __init__(self):
        self._latest_hash = self.GENESIS_HASH
        self._chain_length = 0
    
    @property
    def latest_hash(self) -> str:
        """Get the hash of the most recent event"""
        return self._latest_hash
    
    @property
    def chain_length(self) -> int:
        """Get the number of events in the chain"""
        return self._chain_length
    
    def compute_hash(self, event_data: dict, prev_hash: str | None = None) -> str:
        """
        Compute SHA-256 hash of event data chained with previous hash.
        
        Args:
            event_data: Event data to hash (will be canonicalized)
            prev_hash: Hash of previous event (uses latest if not provided)
            
        Returns:
            SHA-256 hash as hex string
        """
        if prev_hash is None:
            prev_hash = self._latest_hash
        
        # Canonical JSON: sorted keys, no whitespace
        canonical_json = self.canonicalize(event_data)
        
        # Combine with previous hash
        combined = canonical_json + prev_hash
        
        # Compute SHA-256
        hash_bytes = hashlib.sha256(combined.encode("utf-8")).digest()
        return hash_bytes.hex()
    
    def add_event(self, event_data: dict) -> tuple[str, str]:
        """
        Add an event to the chain.
        
        Args:
            event_data: Event data to add
            
        Returns:
            Tuple of (previous_hash, current_hash)
        """
        prev_hash = self._latest_hash
        current_hash = self.compute_hash(event_data, prev_hash)
        
        self._latest_hash = current_hash
        self._chain_length += 1
        
        return prev_hash, current_hash
    
    def verify_event(
        self, 
        event_data: dict, 
        expected_hash: str, 
        prev_hash: str
    ) -> bool:
        """
        Verify that an event's hash is correct.
        
        Args:
            event_data: Event data to verify
            expected_hash: The hash that was recorded for this event
            prev_hash: The hash of the previous event
            
        Returns:
            True if the hash is valid
        """
        computed_hash = self.compute_hash(event_data, prev_hash)
        return computed_hash == expected_hash
    
    @staticmethod
    def canonicalize(data: dict) -> str:
        """
        Convert data to canonical JSON string.
        
        Canonical form:
        - Keys sorted alphabetically (recursive)
        - No whitespace
        - Consistent separator format
        
        This ensures the same data always produces the same hash,
        preventing "false tampering" alerts from key reordering.
        """
        return json.dumps(
            data,
            sort_keys=True,
            separators=(",", ":"),
            default=_json_serializer,
        )
    
    def reset(self) -> None:
        """Reset the chain to initial state"""
        self._latest_hash = self.GENESIS_HASH
        self._chain_length = 0
    
    def set_state(self, latest_hash: str, chain_length: int) -> None:
        """Set chain state (used when loading from storage)"""
        self._latest_hash = latest_hash
        self._chain_length = chain_length


def _json_serializer(obj: Any) -> str:
    """Custom JSON serializer for types not natively supported"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def compute_standalone_hash(data: dict) -> str:
    """
    Compute a standalone SHA-256 hash of data.
    
    Useful for hashing individual items like Decision Receipts.
    """
    canonical = HashChain.canonicalize(data)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def verify_hash_integrity(events: list[dict], genesis_hash: str | None = None) -> tuple[bool, str | None]:
    """
    Verify the integrity of a sequence of hash-chained events.
    
    Args:
        events: List of events with prev_hash and current_hash fields
        genesis_hash: Expected hash of the genesis block (defaults to standard)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not events:
        return True, None
    
    if genesis_hash is None:
        genesis_hash = HashChain.GENESIS_HASH
    
    chain = HashChain()
    
    for i, event in enumerate(events):
        # Extract hash fields
        recorded_prev_hash = event.get("prev_hash")
        recorded_current_hash = event.get("current_hash")
        
        if not recorded_prev_hash or not recorded_current_hash:
            return False, f"Event {i} missing hash fields"
        
        # First event should chain from genesis
        if i == 0:
            if recorded_prev_hash != genesis_hash:
                return False, f"Event 0 prev_hash doesn't match genesis hash"
        else:
            # Check continuity
            prev_event = events[i - 1]
            if recorded_prev_hash != prev_event.get("current_hash"):
                return False, f"Event {i} prev_hash doesn't match previous event's current_hash"
        
        # Verify the hash computation
        # Create event data without hash fields for verification
        event_data = {k: v for k, v in event.items() if k not in ("prev_hash", "current_hash", "anchor_tx_sig")}
        
        computed_hash = chain.compute_hash(event_data, recorded_prev_hash)
        
        if computed_hash != recorded_current_hash:
            return False, f"Event {i} hash mismatch: computed {computed_hash}, recorded {recorded_current_hash}"
    
    return True, None
