"""
Replay Engine - Core logic for temporal state reconstruction.

Per spec: "Replay shows what was known at the time, not what we know now."

Loads data from CSV/JSON files and reconstructs system state at any timestamp.
CRITICAL: get_state_at() returns ONLY information available at time t.
"""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from bisect import bisect_right

from app.models.temporal import (
    AtTimeState,
    TimelineMarker,
    MarkerCluster,
    ConfidencePoint,
    IncidentTimeline,
    TrustSnapshot,
    SensorTrustSnapshot,
    Contradiction,
    OperatorAction,
    ReceiptStatus,
    ReasonCode,
    MarkerType,
    EventSeverity,
    ConfirmationStatus,
    ConfidenceLevel,
    Posture,
    ActionGating,
    TrustState,
)


# =============================================================================
# Reason Code Definitions (Dual Language)
# =============================================================================

REASON_CODES: Dict[str, ReasonCode] = {
    "RC10": ReasonCode(
        code="RC10",
        plain_english="Redundant sensors that should agree are in conflict",
        technical="Redundancy conflict: sensor disagreement"
    ),
    "RC11": ReasonCode(
        code="RC11",
        plain_english="Physical laws are being violated by sensor readings",
        technical="Physics violation: impossible state detected"
    ),
}


class ReplayEngine:
    """
    Core replay engine for temporal state reconstruction.
    
    Loads incident data and reconstructs what the system believed
    at any point in time.
    """
    
    def __init__(self, data_dir: Optional[Path] = None):
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / "data"
        self.data_dir = data_dir
        
        # Loaded data (CSV only)
        self._events: List[Dict] = []
        self._trust_timeline: List[Dict] = []
        self._sensors: Dict[str, Dict] = {}
        self._claims: List[Dict] = []
        self._zone_states: List[Dict] = []
        self._action_gates: List[Dict] = []
        self._receipts: List[Dict] = []
        

        
        # Derived data
        self._markers: List[TimelineMarker] = []
        self._sorted_timestamps: List[datetime] = []
        
        # Incident bounds
        self._incident_start: Optional[datetime] = None
        self._incident_end: Optional[datetime] = None
    
    # =========================================================================
    # Data Loading
    # =========================================================================
    
    def load_all(self) -> None:
        """Load all data from CSV files only."""
        self.load_from_csv()
        self._build_markers()
    
    def load_from_csv(self) -> None:
        """Load data from CSV files."""
        csv_dir = self.data_dir / "csv"
        
        # Events
        events_path = csv_dir / "events.csv"
        if events_path.exists():
            self._events = self._read_csv(events_path)
            # Parse timestamps
            for e in self._events:
                e["timestamp"] = self._parse_timestamp(e["timestamp"])
                e["time_sec"] = float(e.get("time_sec", 0))
        
        # Trust timeline
        trust_path = csv_dir / "trust_timeline.csv"
        if trust_path.exists():
            self._trust_timeline = self._read_csv(trust_path)
            for t in self._trust_timeline:
                t["timestamp"] = self._parse_timestamp(t["timestamp"])
                t["time_sec"] = float(t.get("time_sec", 0))
                t["trust_score"] = float(t.get("trust_score", 1.0))
        
        # Sensors
        sensors_path = csv_dir / "sensors.csv"
        if sensors_path.exists():
            sensors_list = self._read_csv(sensors_path)
            self._sensors = {s["tag_id"]: s for s in sensors_list}
        
        # NEW: Claims
        claims_path = csv_dir / "claims.csv"
        if claims_path.exists():
            self._claims = self._read_csv(claims_path)
            for c in self._claims:
                c["timestamp"] = self._parse_timestamp(c["timestamp"])
                c["time_sec"] = float(c.get("time_sec", 0))
        
        # NEW: Zone States
        zone_states_path = csv_dir / "zone_states.csv"
        if zone_states_path.exists():
            self._zone_states = self._read_csv(zone_states_path)
            for z in self._zone_states:
                z["timestamp"] = self._parse_timestamp(z["timestamp"])
                z["time_sec"] = float(z.get("time_sec", 0))
        
        # NEW: Action Gates
        action_gates_path = csv_dir / "action_gates.csv"
        if action_gates_path.exists():
            self._action_gates = self._read_csv(action_gates_path)
            for a in self._action_gates:
                a["timestamp"] = self._parse_timestamp(a["timestamp"])
                a["time_sec"] = float(a.get("time_sec", 0))
        
        # Receipts (CSV)
        receipts_path = csv_dir / "receipts.csv"
        if receipts_path.exists():
            self._receipts = self._read_csv(receipts_path)
            for r in self._receipts:
                r["timestamp"] = self._parse_timestamp(r["timestamp"])
                r["time_sec"] = float(r.get("time_sec", 0))
        
        # Set incident bounds from events
        if self._events:
            timestamps = [e["timestamp"] for e in self._events]
            self._incident_start = min(timestamps)
            self._incident_end = max(timestamps)
    

    
    def _read_csv(self, path: Path) -> List[Dict]:
        """Read CSV file and return list of dicts."""
        with open(path, newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            return list(reader)
    
    def _parse_timestamp(self, ts: str) -> datetime:
        """Parse various timestamp formats."""
        # Handle different formats
        formats = [
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(ts.strip(), fmt)
            except ValueError:
                continue
        raise ValueError(f"Cannot parse timestamp: {ts}")
    
    # =========================================================================
    # Marker Building
    # =========================================================================
    
    def _build_markers(self) -> None:
        """Build timeline markers from events."""
        self._markers = []
        
        for i, event in enumerate(self._events):
            event_type = event.get("event_type", "").lower()
            severity_str = event.get("severity", "INFO").upper()
            
            # Map event type to marker type
            marker_type = self._event_type_to_marker(event_type)
            severity = EventSeverity(severity_str.lower()) if severity_str.lower() in ["info", "warning", "alarm", "critical"] else EventSeverity.INFO
            
            marker = TimelineMarker(
                id=f"marker_{i}",
                timestamp=event["timestamp"],
                time_sec=event["time_sec"],
                marker_type=marker_type,
                severity=severity,
                label=event.get("event_type", "Event"),
                description=event.get("description", ""),
                tag_id=event.get("tag_id"),
                reason_code=event.get("reason_code"),
                has_contradiction="contradiction" in event_type.lower(),
            )
            self._markers.append(marker)
        
        # Sort by timestamp
        self._markers.sort(key=lambda m: m.timestamp)
        self._sorted_timestamps = [m.timestamp for m in self._markers]
    
    def _event_type_to_marker(self, event_type: str) -> MarkerType:
        """Map event type string to MarkerType."""
        mapping = {
            "scenario_start": MarkerType.SCENARIO_START,
            "scenario_end": MarkerType.SCENARIO_END,
            "trust_update": MarkerType.TRUST_CHANGE,
            "trust_degraded": MarkerType.TRUST_CHANGE,
            "failure_injection": MarkerType.ALARM,
            "contradiction_detected": MarkerType.CONTRADICTION_APPEARED,
            "mode_change": MarkerType.MODE_CHANGE,
            "operator_action": MarkerType.OPERATOR_ACTION,
        }
        return mapping.get(event_type.lower(), MarkerType.ALARM)
    
    # =========================================================================
    # Core: Get State at Time t
    # =========================================================================
    
    def get_state_at(self, timestamp: datetime) -> AtTimeState:
        """
        Get complete system state at timestamp t.
        
        CRITICAL: Returns ONLY information that was available at time t.
        Future evidence is NOT included.
        """
        if not self._events:
            self.load_all()
        
        time_sec = self._get_time_sec(timestamp)
        
        # Get events up to this time
        events_at_t = [e for e in self._events if e["timestamp"] <= timestamp]
        
        # Get trust state at time t
        trust_snapshot = self._get_trust_at(timestamp)
        
        # Get contradictions active at time t (not resolved)
        contradictions = self._get_contradictions_at(timestamp)
        
        # Get operator actions up to time t
        operator_history = self._get_operator_history_at(timestamp)
        
        # Get receipt status at time t
        receipt_status = self._get_receipt_status_at(timestamp)
        
        # Use CSV data if available, otherwise derive
        claim, confirmation_status, confidence = self._get_claim_at(time_sec, events_at_t, contradictions)
        posture, posture_reason = self._get_zone_posture_at(time_sec, events_at_t, contradictions, trust_snapshot)
        action_gating, allowed_actions = self._get_action_gating_at(time_sec, posture, confidence)
        mode = self._derive_mode(events_at_t)
        next_step = self._derive_next_step(posture, contradictions)
        
        # Top reason codes from active contradictions
        top_reason_codes = self._get_top_reason_codes(contradictions)
        
        return AtTimeState(
            timestamp=timestamp,
            time_sec=time_sec,
            claim=claim,
            confirmation_status=confirmation_status,
            confidence=confidence,
            trust_snapshot=trust_snapshot,
            contradictions=contradictions,
            posture=posture,
            posture_reason=posture_reason,
            action_gating=action_gating,
            allowed_actions=allowed_actions,
            operator_history=operator_history,
            receipt_status=receipt_status,
            top_reason_codes=top_reason_codes,
            next_step=next_step,
            mode=mode,
        )
    
    def _get_time_sec(self, timestamp: datetime) -> float:
        """Get seconds from incident start."""
        if self._incident_start is None:
            return 0.0
        delta = timestamp - self._incident_start
        return delta.total_seconds()
    
    def _get_trust_at(self, timestamp: datetime) -> TrustSnapshot:
        """Get trust state for all sensors at time t."""
        # Filter trust updates up to timestamp
        updates_at_t = [t for t in self._trust_timeline if t["timestamp"] <= timestamp]
        
        # Get latest trust for each sensor
        sensor_trust: Dict[str, SensorTrustSnapshot] = {}
        for update in updates_at_t:
            tag_id = update["tag_id"]
            reason_codes = update.get("reason_codes", "")
            if isinstance(reason_codes, str):
                reason_codes = [r.strip() for r in reason_codes.split(",") if r.strip()]
            
            sensor_trust[tag_id] = SensorTrustSnapshot(
                tag_id=tag_id,
                trust_score=update["trust_score"],
                trust_state=TrustState(update.get("trust_state", "trusted").lower()),
                reason_codes=reason_codes,
            )
        
        # Derive zone trust from sensors
        if sensor_trust:
            min_score = min(s.trust_score for s in sensor_trust.values())
            zone_state = self._score_to_trust_state(min_score)
            zone_confidence = self._score_to_confidence(min_score)
        else:
            zone_state = TrustState.TRUSTED
            zone_confidence = ConfidenceLevel.HIGH
        
        return TrustSnapshot(
            zone_trust_state=zone_state,
            zone_confidence=zone_confidence,
            sensors=sensor_trust,
        )
    
    def _get_contradictions_at(self, timestamp: datetime) -> List[Contradiction]:
        """Get active contradictions at time t derived from events.csv.
        
        Contradictions are detected from 'contradiction_detected' events.
        """
        active = []
        
        # Find contradiction_detected events up to this timestamp
        for e in self._events:
            if e["timestamp"] <= timestamp and e.get("event_type") == "contradiction_detected":
                reason_code = e.get("reason_code", "")
                tag_id = e.get("tag_id", "")
                
                # Avoid duplicates
                already_has = any(
                    existing.reason_code == reason_code and 
                    existing.primary_tag_id == tag_id
                    for existing in active
                )
                if not already_has:
                    active.append(Contradiction(
                        contradiction_id=f"contradiction_{reason_code}_{tag_id}",
                        timestamp=e["timestamp"],
                        primary_tag_id=tag_id,
                        secondary_tag_ids=[],
                        reason_code=reason_code,
                        description=e.get("description", ""),
                        values={},
                        expected_relationship="",
                        resolved=False,
                    ))
        return active
    
    def _get_operator_history_at(self, timestamp: datetime) -> List[OperatorAction]:
        """Get operator actions that occurred before time t."""
        actions = []
        for e in self._events:
            if e["timestamp"] <= timestamp and e.get("event_type") == "operator_action":
                actions.append(OperatorAction(
                    timestamp=e["timestamp"],
                    action_type=e.get("description", "").split(" - ")[0] if " - " in e.get("description", "") else "action",
                    description=e.get("description", ""),
                ))
        return actions
    
    def _get_receipt_status_at(self, timestamp: datetime) -> ReceiptStatus:
        """Get receipt status at time t from CSV receipts."""
        time_sec = self._get_time_sec(timestamp)
        
        # Check CSV receipts
        receipts_at_t = [r for r in self._receipts if r["time_sec"] <= time_sec]
        if receipts_at_t:
            latest = max(receipts_at_t, key=lambda r: r["time_sec"])
            status = latest.get("status", "created")
            receipt_ts = self._incident_start + __import__("datetime").timedelta(seconds=latest["time_sec"]) if self._incident_start else timestamp
            return ReceiptStatus(
                exists=True,
                receipt_id=latest.get("receipt_id", ""),
                created_at=receipt_ts,
                label=f"Receipt {status} at {receipt_ts.strftime('%H:%M:%S')}",
            )
        
        return ReceiptStatus(exists=False, label="No receipt yet")
    
    # =========================================================================
    # Derivation Logic
    # =========================================================================
    
    def _get_claim_at(
        self,
        time_sec: float,
        events_at_t: List[Dict],
        contradictions: List[Contradiction]
    ) -> Tuple[str, ConfirmationStatus, ConfidenceLevel]:
        """Get claim from claims.csv at time t, or derive if not available."""
        # Find the latest claim at or before time_sec
        claims_at_t = [c for c in self._claims if c["time_sec"] <= time_sec]
        
        if claims_at_t:
            latest = max(claims_at_t, key=lambda c: c["time_sec"])
            claim = latest.get("statement", "System operating normally")
            status_str = latest.get("confirmation_status", "confirmed").lower()
            conf_str = latest.get("confidence", "high").lower()
            
            status = ConfirmationStatus(status_str) if status_str in ["confirmed", "unconfirmed", "conflicting"] else ConfirmationStatus.CONFIRMED
            confidence = ConfidenceLevel(conf_str) if conf_str in ["high", "medium", "low"] else ConfidenceLevel.HIGH
            
            return claim, status, confidence
        
        # Fallback: derive from events/contradictions
        return self._derive_claim_fallback(events_at_t, contradictions)
    
    def _derive_claim_fallback(
        self, 
        events_at_t: List[Dict], 
        contradictions: List[Contradiction]
    ) -> Tuple[str, ConfirmationStatus, ConfidenceLevel]:
        """Fallback: derive claim from events."""
        if contradictions:
            latest = max(contradictions, key=lambda c: c.timestamp)
            claim = latest.description
            status = ConfirmationStatus.CONFLICTING
            confidence = ConfidenceLevel.LOW
        elif events_at_t:
            for e in reversed(events_at_t):
                if e.get("event_type") in ["failure_injection", "contradiction_detected", "mode_change"]:
                    claim = e.get("description", "System operating normally")
                    return claim, ConfirmationStatus.UNCONFIRMED, ConfidenceLevel.MEDIUM
            claim = "System operating normally"
            status = ConfirmationStatus.CONFIRMED
            confidence = ConfidenceLevel.HIGH
        else:
            claim = "System operating normally"
            status = ConfirmationStatus.CONFIRMED
            confidence = ConfidenceLevel.HIGH
        
        return claim, status, confidence
    
    def _get_zone_posture_at(
        self,
        time_sec: float,
        events_at_t: List[Dict],
        contradictions: List[Contradiction],
        trust: TrustSnapshot
    ) -> Tuple[Posture, str]:
        """Get posture from zone_states.csv at time t, or derive if not available."""
        # Check for operator actions first (these override)
        for e in reversed(events_at_t):
            if e.get("event_type") == "operator_action":
                desc = e.get("description", "").lower()
                if "defer" in desc:
                    return Posture.DEFER, "Operator deferred pending verification"
                elif "escalate" in desc:
                    return Posture.ESCALATE, "Operator escalated"
        
        # Find zone state from CSV
        zone_states_at_t = [z for z in self._zone_states if z["time_sec"] <= time_sec]
        
        if zone_states_at_t:
            latest = max(zone_states_at_t, key=lambda z: z["time_sec"])
            posture_str = latest.get("recommended_posture", "monitor").lower()
            rationale = latest.get("posture_rationale", "")
            
            posture = Posture(posture_str) if posture_str in ["monitor", "verify", "escalate", "contain", "defer"] else Posture.MONITOR
            return posture, rationale
        
        # Fallback: derive from trust state
        if trust.zone_trust_state == TrustState.QUARANTINED:
            return Posture.CONTAIN, "Sensors quarantined - contain situation"
        elif trust.zone_trust_state in [TrustState.UNTRUSTED, TrustState.DEGRADED]:
            return Posture.VERIFY, "Degraded trust - verify sensor data"
        elif contradictions:
            return Posture.VERIFY, "Contradictions detected - verification required"
        
        return Posture.MONITOR, "All sensors reporting normally"
    
    def _get_action_gating_at(
        self,
        time_sec: float,
        posture: Posture, 
        confidence: ConfidenceLevel
    ) -> Tuple[ActionGating, List[str]]:
        """Get action gating from action_gates.csv at time t."""
        # Get action gates at time t
        gates_at_t = [a for a in self._action_gates if a["time_sec"] <= time_sec]
        
        if gates_at_t:
            # Group by time and get latest set
            latest_time = max(a["time_sec"] for a in gates_at_t)
            latest_gates = [a for a in gates_at_t if a["time_sec"] == latest_time]
            
            # Determine overall gating from individual actions
            blocked_actions = [a["action_name"] for a in latest_gates if a["status"] == "blocked"]
            risky_actions = [a["action_name"] for a in latest_gates if a["status"] == "risky"]
            allowed_actions = [a["action_name"] for a in latest_gates if a["status"] == "allowed"]
            
            if blocked_actions:
                return ActionGating.BLOCKED, allowed_actions + risky_actions
            elif risky_actions:
                return ActionGating.RISKY, allowed_actions
            else:
                return ActionGating.ALLOWED, allowed_actions
        
        # Fallback: derive from posture/confidence
        if posture == Posture.CONTAIN:
            return ActionGating.BLOCKED, ["Acknowledge", "Request support"]
        elif posture in [Posture.VERIFY, Posture.ESCALATE]:
            return ActionGating.RISKY, ["Defer", "Request inspection", "Escalate"]
        elif posture == Posture.DEFER:
            return ActionGating.RISKY, ["Wait", "Cancel defer", "Escalate"]
        elif confidence == ConfidenceLevel.LOW:
            return ActionGating.RISKY, ["Monitor", "Request verification"]
        else:
            return ActionGating.ALLOWED, ["Monitor", "Adjust", "Defer", "Escalate"]
    
    def _derive_mode(self, events_at_t: List[Dict]) -> str:
        """Derive current mode from events."""
        for e in reversed(events_at_t):
            if e.get("event_type") == "mode_change":
                desc = e.get("description", "").lower()
                if "decision" in desc:
                    return "decision"
                elif "replay" in desc:
                    return "replay"
                elif "observe" in desc:
                    return "observe"
        return "observe"
    
    def _derive_next_step(
        self, 
        posture: Posture, 
        contradictions: List[Contradiction]
    ) -> str:
        """Derive recommended next step."""
        if posture == Posture.DEFER:
            return "Await field verification"
        elif posture == Posture.VERIFY:
            if contradictions:
                return "Investigate sensor conflict"
            return "Verify sensor readings"
        elif posture == Posture.ESCALATE:
            return "Contact supervisor"
        elif posture == Posture.CONTAIN:
            return "Isolate affected zone"
        return "Continue monitoring"
    
    def _get_top_reason_codes(
        self, 
        contradictions: List[Contradiction]
    ) -> List[ReasonCode]:
        """Get top 2 reason codes from contradictions."""
        seen = set()
        codes = []
        for c in contradictions:
            if c.reason_code and c.reason_code not in seen:
                seen.add(c.reason_code)
                if c.reason_code in REASON_CODES:
                    codes.append(REASON_CODES[c.reason_code])
                else:
                    codes.append(ReasonCode(
                        code=c.reason_code,
                        plain_english=c.description,
                        technical=c.reason_code,
                    ))
            if len(codes) >= 2:
                break
        return codes
    
    def _score_to_trust_state(self, score: float) -> TrustState:
        """Convert trust score to trust state."""
        if score >= 0.8:
            return TrustState.TRUSTED
        elif score >= 0.5:
            return TrustState.DEGRADED
        elif score >= 0.2:
            return TrustState.UNTRUSTED
        else:
            return TrustState.QUARANTINED
    
    def _score_to_confidence(self, score: float) -> ConfidenceLevel:
        """Convert trust score to confidence level."""
        if score >= 0.8:
            return ConfidenceLevel.HIGH
        elif score >= 0.5:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
    
    # =========================================================================
    # Markers and Timeline
    # =========================================================================
    
    def get_markers(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        zoom_level: int = 1,
    ) -> List[TimelineMarker]:
        """
        Get markers for timeline display.
        
        zoom_level:
          1 = Full incident (cluster markers)
          2 = 5-10 minute span
          3 = Seconds-level (all markers)
        """
        if not self._markers:
            self.load_all()
        
        markers = self._markers
        
        # Filter by time range
        if start:
            markers = [m for m in markers if m.timestamp >= start]
        if end:
            markers = [m for m in markers if m.timestamp <= end]
        
        return markers
    
    def get_clustered_markers(
        self,
        start: datetime,
        end: datetime,
        max_clusters: int = 10,
    ) -> List[MarkerCluster]:
        """Get clustered markers for zoomed-out view."""
        markers = self.get_markers(start, end)
        
        if len(markers) <= max_clusters:
            # No clustering needed
            return [
                MarkerCluster(
                    start_time=m.timestamp,
                    end_time=m.timestamp,
                    count=1,
                    dominant_type=m.marker_type,
                    label=m.label,
                    markers=[m],
                )
                for m in markers
            ]
        
        # Simple time-based clustering
        duration = (end - start).total_seconds()
        cluster_duration = duration / max_clusters
        
        clusters: List[MarkerCluster] = []
        current_cluster: List[TimelineMarker] = []
        cluster_start = start
        
        for marker in markers:
            if (marker.timestamp - cluster_start).total_seconds() > cluster_duration:
                if current_cluster:
                    clusters.append(self._make_cluster(current_cluster))
                current_cluster = [marker]
                cluster_start = marker.timestamp
            else:
                current_cluster.append(marker)
        
        if current_cluster:
            clusters.append(self._make_cluster(current_cluster))
        
        return clusters
    
    def _make_cluster(self, markers: List[TimelineMarker]) -> MarkerCluster:
        """Create a marker cluster from a list of markers."""
        from collections import Counter
        types = [m.marker_type for m in markers]
        dominant = Counter(types).most_common(1)[0][0]
        
        return MarkerCluster(
            start_time=markers[0].timestamp,
            end_time=markers[-1].timestamp,
            count=len(markers),
            dominant_type=dominant,
            label=f"{len(markers)} {dominant.value.replace('_', ' ').title()}s",
            markers=markers,
        )
    
    def get_confidence_band(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        resolution: int = 20,
    ) -> List[ConfidencePoint]:
        """
        Get confidence ribbon data points.
        
        Returns evenly spaced points showing confidence level over time.
        """
        if not self._trust_timeline:
            self.load_all()
        
        start = start or self._incident_start
        end = end or self._incident_end
        
        if not start or not end:
            return []
        
        points = []
        duration = (end - start).total_seconds()
        step = duration / resolution
        
        for i in range(resolution + 1):
            t = start + __import__("datetime").timedelta(seconds=i * step)
            trust = self._get_trust_at(t)
            
            # Get average trust score
            if trust.sensors:
                avg_score = sum(s.trust_score for s in trust.sensors.values()) / len(trust.sensors)
            else:
                avg_score = 1.0
            
            points.append(ConfidencePoint(
                timestamp=t,
                time_sec=i * step,
                confidence_level=trust.zone_confidence,
                trust_score=avg_score,
            ))
        
        return points
    
    def get_incident_timeline(self, incident_id: str = "demo") -> IncidentTimeline:
        """Get full incident timeline."""
        if not self._events:
            self.load_all()
        
        return IncidentTimeline(
            incident_id=incident_id,
            start_time=self._incident_start or datetime.now(),
            end_time=self._incident_end or datetime.now(),
            duration_sec=(self._incident_end - self._incident_start).total_seconds() if self._incident_start and self._incident_end else 0,
            markers=self._markers,
            confidence_band=self.get_confidence_band(),
            total_events=len(self._events),
            total_contradictions=len(self._contradictions),
            total_operator_actions=len([e for e in self._events if e.get("event_type") == "operator_action"]),
        )


# Singleton instance
replay_engine = ReplayEngine()
