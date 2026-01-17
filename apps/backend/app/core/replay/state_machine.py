"""
State Machine Module

Reconstructs system belief state at any point in time.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from app.models.events import SystemState, OperationalMode, Contradiction, TrustUpdate
from app.models.telemetry import TelemetryPoint, TrustState
from config import config


class StateReconstructor:
    """
    Reconstructs the system's belief state at any timestamp.
    
    This is the core of the replay functionality - it proves the system
    understands causality by reconstructing what was known at time t.
    """
    
    def __init__(self):
        self._telemetry_cache: dict[str, list[TelemetryPoint]] = {}
        self._trust_updates: list[TrustUpdate] = []
        self._contradictions: list[Contradiction] = []
        self._mode_transitions: list[dict] = []
        self._data_path = Path(config.data_dir)
    
    def record_telemetry(self, point: TelemetryPoint) -> None:
        """Record a telemetry point for later reconstruction"""
        if point.tag_id not in self._telemetry_cache:
            self._telemetry_cache[point.tag_id] = []
        self._telemetry_cache[point.tag_id].append(point)
    
    def record_trust_update(self, update: TrustUpdate) -> None:
        """Record a trust update event"""
        self._trust_updates.append(update)
    
    def record_contradiction(self, contradiction: Contradiction) -> None:
        """Record a contradiction"""
        self._contradictions.append(contradiction)
    
    def record_mode_transition(
        self, 
        timestamp: datetime, 
        new_mode: OperationalMode,
        trigger: str | None = None
    ) -> None:
        """Record a mode transition"""
        self._mode_transitions.append({
            "timestamp": timestamp,
            "mode": new_mode,
            "trigger": trigger,
        })
    
    async def reconstruct(self, timestamp_iso: str) -> dict:
        """
        Reconstruct the complete system state at a specific timestamp.
        
        Returns the exact state that would have been seen by an operator
        at that time, including:
        - Last known telemetry values
        - Trust scores and reason codes
        - Unresolved contradictions
        - Operational mode
        """
        target_time = datetime.fromisoformat(timestamp_iso.replace("Z", "+00:00"))
        
        # Get last telemetry for each tag before target time
        telemetry = self._get_last_telemetry_before(target_time)
        
        # Get trust state at target time
        trust_scores, reason_codes = self._get_trust_state_at(target_time)
        
        # Get unresolved contradictions
        contradictions = self._get_unresolved_contradictions_at(target_time)
        
        # Get operational mode
        mode, decision_clock = self._get_mode_at(target_time)
        
        state = SystemState(
            timestamp=target_time,
            telemetry=telemetry,
            trust_scores=trust_scores,
            active_reason_codes=reason_codes,
            unresolved_contradictions=contradictions,
            operational_mode=mode,
            decision_clock_started=decision_clock,
        )
        
        return state.model_dump(mode="json")
    
    def _get_last_telemetry_before(
        self, 
        target_time: datetime
    ) -> dict[str, float | None]:
        """Get the last known value for each sensor before target time"""
        result = {}
        
        for tag_id, points in self._telemetry_cache.items():
            last_value = None
            for point in points:
                if point.timestamp <= target_time:
                    last_value = point.value
                else:
                    break
            result[tag_id] = last_value
        
        return result
    
    def _get_trust_state_at(
        self, 
        target_time: datetime
    ) -> tuple[dict[str, float], dict[str, list[str]]]:
        """Get trust scores and reason codes at target time"""
        trust_scores: dict[str, float] = {}
        reason_codes: dict[str, list[str]] = {}
        
        # Group updates by tag and find the latest before target time
        for update in self._trust_updates:
            if update.timestamp <= target_time:
                trust_scores[update.tag_id] = update.new_score
                reason_codes[update.tag_id] = [rc.value for rc in update.reason_codes]
        
        return trust_scores, reason_codes
    
    def _get_unresolved_contradictions_at(
        self, 
        target_time: datetime
    ) -> list[str]:
        """Get IDs of contradictions that were unresolved at target time"""
        unresolved = []
        
        for contradiction in self._contradictions:
            # Was it created before target time?
            if contradiction.timestamp <= target_time:
                # Was it still unresolved at target time?
                if not contradiction.resolved or (
                    contradiction.resolved_at and 
                    contradiction.resolved_at > target_time
                ):
                    unresolved.append(contradiction.contradiction_id)
        
        return unresolved
    
    def _get_mode_at(
        self, 
        target_time: datetime
    ) -> tuple[OperationalMode, datetime | None]:
        """Get operational mode at target time"""
        current_mode = OperationalMode.OBSERVE
        decision_clock_start = None
        
        for transition in self._mode_transitions:
            if transition["timestamp"] <= target_time:
                current_mode = transition["mode"]
                if current_mode == OperationalMode.DECISION:
                    decision_clock_start = transition["timestamp"]
                else:
                    decision_clock_start = None
        
        return current_mode, decision_clock_start
    
    def get_state_snapshot(self) -> dict:
        """Get a snapshot of current reconstruction state for debugging"""
        return {
            "telemetry_tags": list(self._telemetry_cache.keys()),
            "telemetry_points": sum(len(v) for v in self._telemetry_cache.values()),
            "trust_updates": len(self._trust_updates),
            "contradictions": len(self._contradictions),
            "mode_transitions": len(self._mode_transitions),
        }
    
    def clear(self) -> None:
        """Clear all cached state"""
        self._telemetry_cache.clear()
        self._trust_updates.clear()
        self._contradictions.clear()
        self._mode_transitions.clear()
    
    async def load_from_storage(self) -> None:
        """Load historical data from JSON file storage"""
        # Load telemetry
        telemetry_path = self._data_path / "telemetry"
        if telemetry_path.exists():
            for file_path in telemetry_path.glob("*.json"):
                with open(file_path) as f:
                    data = json.load(f)
                    for point_data in data.get("points", []):
                        point = TelemetryPoint(**point_data)
                        self.record_telemetry(point)
        
        # Load events
        events_path = self._data_path / "events"
        if events_path.exists():
            for file_path in events_path.glob("*.json"):
                with open(file_path) as f:
                    data = json.load(f)
                    event_type = data.get("type")
                    
                    if event_type == "trust_update":
                        update = TrustUpdate(**data["data"])
                        self.record_trust_update(update)
                    elif event_type == "contradiction":
                        contradiction = Contradiction(**data["data"])
                        self.record_contradiction(contradiction)
                    elif event_type == "mode_transition":
                        self.record_mode_transition(
                            datetime.fromisoformat(data["data"]["timestamp"]),
                            OperationalMode(data["data"]["mode"]),
                            data["data"].get("trigger"),
                        )
    
    async def save_telemetry_batch(
        self, 
        tag_id: str, 
        points: list[TelemetryPoint]
    ) -> None:
        """Save a batch of telemetry points to storage"""
        telemetry_path = self._data_path / "telemetry"
        telemetry_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        file_path = telemetry_path / f"{tag_id}_{timestamp}.json"
        
        data = {
            "tag_id": tag_id,
            "saved_at": datetime.utcnow().isoformat(),
            "points": [p.model_dump(mode="json") for p in points],
        }
        
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2, default=str)
