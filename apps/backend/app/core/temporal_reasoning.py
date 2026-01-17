"""
Temporal Reasoning Engine - Advanced analysis using CSV + JSON data.

This engine provides deeper temporal analysis capabilities:
- Trust evolution analysis (using granular JSON trust_updates)
- Audit trail verification (using chained audit_events)
- Contradiction pattern analysis (using detailed contradictions.json)
- Decision provenance (using decision_receipts.json)

Unlike ReplayEngine (CSV-only for UI playback), this engine combines
both data sources for advanced reasoning and verification.
"""

import csv
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum


# =============================================================================
# Data Models for Temporal Reasoning
# =============================================================================

@dataclass
class TrustUpdate:
    """Granular trust update event from JSON."""
    event_id: str
    run_id: str
    tag_id: str
    timestamp: datetime
    time_sec: float
    previous_score: float
    new_score: float
    delta: float
    reason_codes: List[str]
    trust_state: str


@dataclass
class AuditEvent:
    """Chained audit event from JSON."""
    event_id: str
    chain_id: str
    run_id: str
    timestamp: datetime
    actor: str
    action: str
    payload: Dict[str, Any]
    prev_hash: str
    current_hash: str


@dataclass
class ContradictionRecord:
    """Detailed contradiction from JSON."""
    contradiction_id: str
    run_id: str
    timestamp: datetime
    time_sec: float
    primary_tag_id: str
    secondary_tag_ids: List[str]
    reason_code: str
    description: str
    values: Dict[str, Any]
    expected_relationship: str
    resolved: bool


@dataclass
class DecisionReceipt:
    """Decision receipt from JSON."""
    receipt_id: str
    run_id: str
    timestamp: datetime
    time_sec: float
    operator_id: str
    action_type: str
    description: str
    rationale: str
    uncertainty_snapshot: Dict[str, Any]
    active_contradictions: List[str]
    evidence_refs: List[str]
    content_hash: str


@dataclass
class TrustEvolutionPoint:
    """Point on the trust evolution curve."""
    time_sec: float
    trust_score: float
    trust_state: str
    reason_codes: List[str]
    delta: float


@dataclass
class TrustEvolutionAnalysis:
    """Analysis of trust evolution for a sensor."""
    tag_id: str
    start_score: float
    end_score: float
    total_degradation: float
    degradation_rate: float  # per second
    time_to_quarantine: Optional[float]
    significant_drops: List[TrustEvolutionPoint]
    evolution_curve: List[TrustEvolutionPoint]


@dataclass
class AuditChainVerification:
    """Result of audit chain verification."""
    chain_id: str
    run_id: str
    total_events: int
    is_valid: bool
    first_event: Optional[AuditEvent]
    last_event: Optional[AuditEvent]
    broken_links: List[Tuple[str, str]]  # (expected_hash, actual_prev_hash)


@dataclass
class ContradictionPattern:
    """Pattern analysis of contradictions."""
    reason_code: str
    count: int
    first_occurrence: float  # time_sec
    affected_sensors: List[str]
    average_gap: float  # between occurrences
    cascading: bool  # Did it trigger other contradictions?


class TemporalReasoningEngine:
    """
    Advanced temporal reasoning using both CSV and JSON data.
    
    CSV provides incident structure (events, claims, zone_states).
    JSON provides granular data for deep analysis (trust_updates, audit_events).
    """
    
    def __init__(self, data_dir: Optional[Path] = None):
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / "data"
        self.data_dir = data_dir
        
        # CSV data (incident structure)
        self._events: List[Dict] = []
        self._claims: List[Dict] = []
        self._zone_states: List[Dict] = []
        
        # JSON data (granular analysis)
        self._trust_updates: List[TrustUpdate] = []
        self._audit_events: List[AuditEvent] = []
        self._contradictions: List[ContradictionRecord] = []
        self._receipts: List[DecisionReceipt] = []
        
        self._loaded = False
    
    # =========================================================================
    # Data Loading
    # =========================================================================
    
    def load_all(self) -> None:
        """Load all data from CSV and JSON files."""
        if self._loaded:
            return
        self._load_csv()
        self._load_json()
        self._loaded = True
    
    def _load_csv(self) -> None:
        """Load CSV data for incident structure."""
        csv_dir = self.data_dir / "csv"
        
        # Events
        events_path = csv_dir / "events.csv"
        if events_path.exists():
            self._events = self._read_csv(events_path)
            for e in self._events:
                e["timestamp"] = self._parse_timestamp(e["timestamp"])
                e["time_sec"] = float(e.get("time_sec", 0))
        
        # Claims
        claims_path = csv_dir / "claims.csv"
        if claims_path.exists():
            self._claims = self._read_csv(claims_path)
            for c in self._claims:
                c["timestamp"] = self._parse_timestamp(c["timestamp"])
                c["time_sec"] = float(c.get("time_sec", 0))
        
        # Zone States
        zone_path = csv_dir / "zone_states.csv"
        if zone_path.exists():
            self._zone_states = self._read_csv(zone_path)
            for z in self._zone_states:
                z["timestamp"] = self._parse_timestamp(z["timestamp"])
                z["time_sec"] = float(z.get("time_sec", 0))
    
    def _load_json(self) -> None:
        """Load JSON data for granular analysis."""
        gen_dir = self.data_dir / "generated"
        
        # Trust Updates
        trust_path = gen_dir / "trust_updates.json"
        if trust_path.exists():
            with open(trust_path) as f:
                data = json.load(f)
            self._trust_updates = [
                TrustUpdate(
                    event_id=d["event_id"],
                    run_id=d["run_id"],
                    tag_id=d["tag_id"],
                    timestamp=self._parse_timestamp(d["timestamp"]),
                    time_sec=d["time_sec"],
                    previous_score=d["previous_score"],
                    new_score=d["new_score"],
                    delta=d["delta"],
                    reason_codes=d.get("reason_codes", []),
                    trust_state=d["trust_state"],
                )
                for d in data
            ]
        
        # Audit Events
        audit_path = gen_dir / "audit_events.json"
        if audit_path.exists():
            with open(audit_path) as f:
                data = json.load(f)
            self._audit_events = [
                AuditEvent(
                    event_id=d["event_id"],
                    chain_id=d["chain_id"],
                    run_id=d["run_id"],
                    timestamp=self._parse_timestamp(d["timestamp"]),
                    actor=d["actor"],
                    action=d["action"],
                    payload=d.get("payload", {}),
                    prev_hash=d["prev_hash"],
                    current_hash=d["current_hash"],
                )
                for d in data
            ]
        
        # Contradictions
        contra_path = gen_dir / "contradictions.json"
        if contra_path.exists():
            with open(contra_path) as f:
                data = json.load(f)
            self._contradictions = [
                ContradictionRecord(
                    contradiction_id=d["contradiction_id"],
                    run_id=d["run_id"],
                    timestamp=self._parse_timestamp(d["timestamp"]),
                    time_sec=d["time_sec"],
                    primary_tag_id=d["primary_tag_id"],
                    secondary_tag_ids=d.get("secondary_tag_ids", []),
                    reason_code=d.get("reason_code", ""),
                    description=d.get("description", ""),
                    values=d.get("values", {}),
                    expected_relationship=d.get("expected_relationship", ""),
                    resolved=d.get("resolved", False),
                )
                for d in data
            ]
        
        # Decision Receipts
        receipts_path = gen_dir / "decision_receipts.json"
        if receipts_path.exists():
            with open(receipts_path) as f:
                data = json.load(f)
            self._receipts = [
                DecisionReceipt(
                    receipt_id=d["receipt_id"],
                    run_id=d["run_id"],
                    timestamp=self._parse_timestamp(d["timestamp"]),
                    time_sec=d.get("time_sec", 0.0),  # May not exist
                    operator_id=d["operator_id"],
                    action_type=d["action_type"],
                    description=d.get("action_description", d.get("description", "")),
                    rationale=d["rationale"],
                    uncertainty_snapshot=d.get("uncertainty_snapshot", {}),
                    active_contradictions=d.get("active_contradictions", []),
                    evidence_refs=d.get("evidence_refs", []),
                    content_hash=d["content_hash"],
                )
                for d in data
            ]
    
    def _read_csv(self, path: Path) -> List[Dict]:
        with open(path, newline='', encoding='utf-8-sig') as f:
            return list(csv.DictReader(f))
    
    def _parse_timestamp(self, ts: str) -> datetime:
        formats = ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"]
        for fmt in formats:
            try:
                return datetime.strptime(ts.strip(), fmt)
            except ValueError:
                continue
        raise ValueError(f"Cannot parse timestamp: {ts}")
    
    # =========================================================================
    # Trust Evolution Analysis
    # =========================================================================
    
    def analyze_trust_evolution(
        self,
        tag_id: str,
        run_id: Optional[str] = None,
    ) -> TrustEvolutionAnalysis:
        """
        Analyze how a sensor's trust evolved over time.
        
        Uses granular JSON trust_updates for second-by-second analysis.
        """
        self.load_all()
        
        # Filter updates for this sensor
        updates = [u for u in self._trust_updates if u.tag_id == tag_id]
        if run_id:
            updates = [u for u in updates if u.run_id == run_id]
        
        if not updates:
            return TrustEvolutionAnalysis(
                tag_id=tag_id,
                start_score=1.0,
                end_score=1.0,
                total_degradation=0.0,
                degradation_rate=0.0,
                time_to_quarantine=None,
                significant_drops=[],
                evolution_curve=[],
            )
        
        # Sort by time
        updates.sort(key=lambda u: u.time_sec)
        
        start_score = updates[0].previous_score
        end_score = updates[-1].new_score
        total_degradation = start_score - end_score
        
        # Find time to quarantine
        time_to_quarantine = None
        for u in updates:
            if u.trust_state == "quarantined":
                time_to_quarantine = u.time_sec - updates[0].time_sec
                break
        
        # Calculate degradation rate
        duration = updates[-1].time_sec - updates[0].time_sec
        degradation_rate = total_degradation / duration if duration > 0 else 0
        
        # Find significant drops (delta < -0.2)
        significant_drops = [
            TrustEvolutionPoint(
                time_sec=u.time_sec,
                trust_score=u.new_score,
                trust_state=u.trust_state,
                reason_codes=u.reason_codes,
                delta=u.delta,
            )
            for u in updates
            if u.delta < -0.2
        ]
        
        # Build evolution curve (sample every 5 seconds)
        curve = []
        for u in updates[::5]:  # Sample
            curve.append(TrustEvolutionPoint(
                time_sec=u.time_sec,
                trust_score=u.new_score,
                trust_state=u.trust_state,
                reason_codes=u.reason_codes,
                delta=u.delta,
            ))
        
        return TrustEvolutionAnalysis(
            tag_id=tag_id,
            start_score=start_score,
            end_score=end_score,
            total_degradation=total_degradation,
            degradation_rate=degradation_rate,
            time_to_quarantine=time_to_quarantine,
            significant_drops=significant_drops,
            evolution_curve=curve,
        )
    
    # =========================================================================
    # Audit Chain Verification
    # =========================================================================
    
    def verify_audit_chain(self, chain_id: Optional[str] = None) -> List[AuditChainVerification]:
        """
        Verify integrity of audit event chains.
        
        Each event's prev_hash should match the previous event's current_hash.
        """
        self.load_all()
        
        # Group by chain_id
        chains: Dict[str, List[AuditEvent]] = {}
        for event in self._audit_events:
            if chain_id and event.chain_id != chain_id:
                continue
            if event.chain_id not in chains:
                chains[event.chain_id] = []
            chains[event.chain_id].append(event)
        
        results = []
        for cid, events in chains.items():
            # Sort by timestamp
            events.sort(key=lambda e: e.timestamp)
            
            broken_links = []
            is_valid = True
            
            for i in range(1, len(events)):
                expected_prev = events[i-1].current_hash
                actual_prev = events[i].prev_hash
                if expected_prev != actual_prev:
                    is_valid = False
                    broken_links.append((expected_prev, actual_prev))
            
            results.append(AuditChainVerification(
                chain_id=cid,
                run_id=events[0].run_id if events else "",
                total_events=len(events),
                is_valid=is_valid,
                first_event=events[0] if events else None,
                last_event=events[-1] if events else None,
                broken_links=broken_links,
            ))
        
        return results
    
    # =========================================================================
    # Contradiction Pattern Analysis
    # =========================================================================
    
    def analyze_contradiction_patterns(
        self,
        run_id: Optional[str] = None,
    ) -> List[ContradictionPattern]:
        """
        Analyze patterns in contradictions.
        
        Identifies:
        - Which reason codes appear most
        - Cascading contradictions (one triggers another)
        - Affected sensor groups
        """
        self.load_all()
        
        contradictions = self._contradictions
        if run_id:
            contradictions = [c for c in contradictions if c.run_id == run_id]
        
        # Group by reason_code
        by_code: Dict[str, List[ContradictionRecord]] = {}
        for c in contradictions:
            if c.reason_code not in by_code:
                by_code[c.reason_code] = []
            by_code[c.reason_code].append(c)
        
        patterns = []
        sorted_codes = sorted(by_code.items(), key=lambda x: x[1][0].time_sec)
        
        for code, records in sorted_codes:
            records.sort(key=lambda c: c.time_sec)
            
            # Calculate average gap between occurrences
            gaps = []
            for i in range(1, len(records)):
                gaps.append(records[i].time_sec - records[i-1].time_sec)
            avg_gap = sum(gaps) / len(gaps) if gaps else 0
            
            # Collect affected sensors
            sensors = set()
            for r in records:
                sensors.add(r.primary_tag_id)
                sensors.update(r.secondary_tag_ids)
            
            # Check for cascading (another code appeared within 2 seconds)
            cascading = False
            for other_code, other_records in by_code.items():
                if other_code == code:
                    continue
                for other in other_records:
                    for rec in records:
                        if 0 < (other.time_sec - rec.time_sec) <= 2:
                            cascading = True
                            break
            
            patterns.append(ContradictionPattern(
                reason_code=code,
                count=len(records),
                first_occurrence=records[0].time_sec,
                affected_sensors=list(sensors),
                average_gap=avg_gap,
                cascading=cascading,
            ))
        
        return patterns
    
    # =========================================================================
    # Decision Provenance
    # =========================================================================
    
    def get_decision_provenance(
        self,
        receipt_id: Optional[str] = None,
        time_sec: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get decision provenance - what led to a decision.
        
        Returns the evidence chain: contradictions → trust degradation → decision.
        """
        self.load_all()
        
        # Find the receipt
        receipts = self._receipts
        if receipt_id:
            receipts = [r for r in receipts if r.receipt_id == receipt_id]
        if time_sec:
            receipts = [r for r in receipts if r.time_sec <= time_sec]
        
        provenance = []
        for receipt in receipts:
            # Find related contradictions
            related_contradictions = [
                c for c in self._contradictions
                if c.time_sec <= receipt.time_sec and c.run_id == receipt.run_id
            ]
            
            # Find trust updates that led to this
            related_trust = [
                u for u in self._trust_updates
                if u.time_sec <= receipt.time_sec and u.run_id == receipt.run_id
            ]
            
            provenance.append({
                "receipt": {
                    "id": receipt.receipt_id,
                    "time_sec": receipt.time_sec,
                    "action": receipt.action_type,
                    "rationale": receipt.rationale,
                    "content_hash": receipt.content_hash,
                },
                "contradictions": [
                    {
                        "id": c.contradiction_id,
                        "time_sec": c.time_sec,
                        "reason_code": c.reason_code,
                        "description": c.description,
                    }
                    for c in related_contradictions[-3:]  # Last 3
                ],
                "trust_degradation": [
                    {
                        "tag_id": u.tag_id,
                        "time_sec": u.time_sec,
                        "score": u.new_score,
                        "delta": u.delta,
                    }
                    for u in related_trust
                    if u.delta < 0  # Only degradations
                ][-5:],  # Last 5
            })
        
        return provenance
    
    # =========================================================================
    # Summary Statistics
    # =========================================================================
    
    def get_summary(self, run_id: Optional[str] = None) -> Dict[str, Any]:
        """Get summary statistics for temporal reasoning data."""
        self.load_all()
        
        trust_updates = self._trust_updates
        contradictions = self._contradictions
        receipts = self._receipts
        audit_events = self._audit_events
        
        if run_id:
            trust_updates = [u for u in trust_updates if u.run_id == run_id]
            contradictions = [c for c in contradictions if c.run_id == run_id]
            receipts = [r for r in receipts if r.run_id == run_id]
            audit_events = [a for a in audit_events if a.run_id == run_id]
        
        return {
            "total_trust_updates": len(trust_updates),
            "total_contradictions": len(contradictions),
            "total_receipts": len(receipts),
            "total_audit_events": len(audit_events),
            "unique_sensors": len(set(u.tag_id for u in trust_updates)),
            "unique_reason_codes": len(set(c.reason_code for c in contradictions)),
            "unique_chains": len(set(a.chain_id for a in audit_events)),
            "csv_events": len(self._events),
            "csv_claims": len(self._claims),
            "csv_zone_states": len(self._zone_states),
        }


# Singleton instance
temporal_reasoning_engine = TemporalReasoningEngine()
