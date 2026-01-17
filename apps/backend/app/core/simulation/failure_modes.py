"""
Failure Mode Injector Module

Injects controlled failures into sensor signals to trigger Reason Codes.
Each failure mode maps to a specific RC in the Trust Layer.
"""

import numpy as np
from datetime import datetime, timedelta
from typing import Callable
from dataclasses import dataclass, field

from app.models.simulation import FailureModeType, FailureMode
from app.models.telemetry import TelemetryPoint, QualityFlag


@dataclass
class ActiveFailure:
    """Tracks an active failure injection"""
    failure_id: str
    failure_mode: FailureMode
    started_at: float  # Simulation time in seconds
    ends_at: float | None  # None = permanent
    is_active: bool = True


@dataclass
class FailureState:
    """State for ongoing failure effects"""
    tag_id: str
    failure_type: FailureModeType
    cumulative_drift: float = 0.0
    last_value: float | None = None
    flatline_start: float | None = None
    missing_until: float | None = None


class FailureModeInjector:
    """
    Injects failure modes into sensor signals.
    
    Supports the following failure types:
    - RC01: Missing Bursts (data gaps)
    - RC02: Stale Stream (no updates)
    - RC05: Range Violation (outside physical limits)
    - RC06: ROC Violation (rate of change exceeded)
    - RC07: Flatline (stuck value)
    - RC09: Drift (gradual divergence)
    - RC10: Redundancy Conflict (sensor mismatch)
    - RC11: Physics Contradiction (impossible state)
    """
    
    def __init__(self):
        self._active_failures: dict[str, ActiveFailure] = {}
        self._failure_states: dict[str, FailureState] = {}
        self._failure_counter = 0
        
        # Failure handlers
        self._handlers: dict[FailureModeType, Callable] = {
            FailureModeType.MISSING_BURSTS: self._apply_missing_bursts,
            FailureModeType.STALE_STREAM: self._apply_stale_stream,
            FailureModeType.RANGE_VIOLATION: self._apply_range_violation,
            FailureModeType.ROC_VIOLATION: self._apply_roc_violation,
            FailureModeType.FLATLINE: self._apply_flatline,
            FailureModeType.DRIFT: self._apply_drift,
            FailureModeType.REDUNDANCY_CONFLICT: self._apply_redundancy_conflict,
            FailureModeType.PHYSICS_CONTRADICTION: self._apply_physics_contradiction,
        }
    
    def reset(self) -> None:
        """Reset all failure state"""
        self._active_failures.clear()
        self._failure_states.clear()
        self._failure_counter = 0
    
    def schedule_failure(self, failure: FailureMode) -> str:
        """
        Schedule a failure for injection.
        
        Returns the failure ID.
        """
        self._failure_counter += 1
        failure_id = f"failure_{self._failure_counter}"
        
        ends_at = None
        if failure.duration_sec is not None:
            ends_at = failure.start_time_sec + failure.duration_sec
        
        self._active_failures[failure_id] = ActiveFailure(
            failure_id=failure_id,
            failure_mode=failure,
            started_at=failure.start_time_sec,
            ends_at=ends_at,
        )
        
        return failure_id
    
    def inject(
        self,
        failure_type: str | FailureModeType,
        tag_id: str,
        current_time_sec: float,
        duration_sec: float | None = None,
        **params
    ) -> dict:
        """
        Inject a failure immediately during live simulation.
        
        Returns failure details.
        """
        if isinstance(failure_type, str):
            failure_type = FailureModeType(failure_type)
        
        failure = FailureMode(
            type=failure_type,
            tag_id=tag_id,
            start_time_sec=current_time_sec,
            duration_sec=duration_sec,
            params=params,
        )
        
        failure_id = self.schedule_failure(failure)
        
        return {
            "failure_id": failure_id,
            "type": failure_type.value,
            "tag_id": tag_id,
            "started_at": current_time_sec,
            "ends_at": current_time_sec + duration_sec if duration_sec else None,
        }
    
    def apply_failures(
        self,
        point: TelemetryPoint,
        current_time_sec: float,
    ) -> TelemetryPoint:
        """
        Apply all active failures to a telemetry point.
        
        Returns the modified point (or None if point should be dropped).
        """
        # Find active failures for this tag
        active_for_tag = [
            f for f in self._active_failures.values()
            if f.failure_mode.tag_id == point.tag_id
            and f.is_active
            and f.started_at <= current_time_sec
            and (f.ends_at is None or current_time_sec < f.ends_at)
        ]
        
        if not active_for_tag:
            return point
        
        # Apply each failure in order
        modified_point = point.model_copy()
        
        for failure in active_for_tag:
            handler = self._handlers.get(failure.failure_mode.type)
            if handler:
                result = handler(modified_point, failure.failure_mode, current_time_sec)
                if result is None:
                    # Point should be dropped (missing data)
                    return None
                modified_point = result
        
        return modified_point
    
    def update_failure_states(self, current_time_sec: float) -> list[str]:
        """
        Update failure states and return IDs of failures that ended.
        """
        ended = []
        for failure_id, failure in list(self._active_failures.items()):
            if failure.ends_at is not None and current_time_sec >= failure.ends_at:
                failure.is_active = False
                ended.append(failure_id)
        return ended
    
    def get_active_failures(self, tag_id: str | None = None) -> list[dict]:
        """Get list of active failures, optionally filtered by tag"""
        result = []
        for failure in self._active_failures.values():
            if failure.is_active:
                if tag_id is None or failure.failure_mode.tag_id == tag_id:
                    result.append({
                        "failure_id": failure.failure_id,
                        "type": failure.failure_mode.type.value,
                        "tag_id": failure.failure_mode.tag_id,
                        "started_at": failure.started_at,
                        "ends_at": failure.ends_at,
                    })
        return result
    
    # === Failure Mode Handlers ===
    
    def _apply_missing_bursts(
        self,
        point: TelemetryPoint,
        failure: FailureMode,
        current_time_sec: float,
    ) -> TelemetryPoint | None:
        """
        RC01: Missing Bursts - create data gaps
        
        Params:
            gap_probability: Probability of dropping a point (0-1)
            burst_duration_sec: Duration of burst gaps
        """
        gap_prob = failure.params.get("gap_probability", 0.3)
        
        # Deterministic "randomness" based on time
        drop_seed = hash((failure.tag_id, int(current_time_sec * 10))) % 100
        if drop_seed < gap_prob * 100:
            return None  # Drop this point
        
        return point
    
    def _apply_stale_stream(
        self,
        point: TelemetryPoint,
        failure: FailureMode,
        current_time_sec: float,
    ) -> TelemetryPoint | None:
        """
        RC02: Stale Stream - stop sending updates
        
        When active, all points are dropped to simulate no updates.
        """
        return None  # Drop all points during stale period
    
    def _apply_range_violation(
        self,
        point: TelemetryPoint,
        failure: FailureMode,
        current_time_sec: float,
    ) -> TelemetryPoint:
        """
        RC05: Range Violation - push values outside physical limits
        
        Params:
            violation_value: Specific value to set (overrides calculation)
            direction: "high" or "low"
            magnitude: How far outside range (multiplier)
        """
        direction = failure.params.get("direction", "high")
        magnitude = failure.params.get("magnitude", 1.5)
        violation_value = failure.params.get("violation_value")
        
        if violation_value is not None:
            new_value = violation_value
        elif direction == "high":
            new_value = point.value * magnitude if point.value else 1000.0
        else:
            new_value = -abs(point.value or 100) * magnitude
        
        return TelemetryPoint(
            tag_id=point.tag_id,
            timestamp=point.timestamp,
            value=new_value,
            quality=QualityFlag.BAD,
            metadata={**point.metadata, "failure": "range_violation"}
        )
    
    def _apply_roc_violation(
        self,
        point: TelemetryPoint,
        failure: FailureMode,
        current_time_sec: float,
    ) -> TelemetryPoint:
        """
        RC06: ROC Violation - create sudden spikes
        
        Params:
            spike_magnitude: Size of spike (absolute change)
        """
        spike_mag = failure.params.get("spike_magnitude", 50.0)
        
        # Alternate spike direction based on time
        direction = 1 if int(current_time_sec) % 2 == 0 else -1
        new_value = (point.value or 0) + (spike_mag * direction)
        
        return TelemetryPoint(
            tag_id=point.tag_id,
            timestamp=point.timestamp,
            value=new_value,
            quality=QualityFlag.UNCERTAIN,
            metadata={**point.metadata, "failure": "roc_violation"}
        )
    
    def _apply_flatline(
        self,
        point: TelemetryPoint,
        failure: FailureMode,
        current_time_sec: float,
    ) -> TelemetryPoint:
        """
        RC07: Flatline - sensor stuck at a value
        
        Params:
            stuck_value: Value to stick at (defaults to first seen value)
        """
        state_key = f"{failure.tag_id}_flatline"
        
        if state_key not in self._failure_states:
            stuck_value = failure.params.get("stuck_value", point.value)
            self._failure_states[state_key] = FailureState(
                tag_id=failure.tag_id,
                failure_type=FailureModeType.FLATLINE,
                last_value=stuck_value,
            )
        
        stuck_value = self._failure_states[state_key].last_value
        
        return TelemetryPoint(
            tag_id=point.tag_id,
            timestamp=point.timestamp,
            value=stuck_value,
            quality=QualityFlag.GOOD,  # Flatline often looks "good" at first
            metadata={**point.metadata, "failure": "flatline"}
        )
    
    def _apply_drift(
        self,
        point: TelemetryPoint,
        failure: FailureMode,
        current_time_sec: float,
    ) -> TelemetryPoint:
        """
        RC09: Drift - gradual divergence from true value
        
        Params:
            drift_rate: Drift per second
            direction: 1 for positive, -1 for negative
        """
        drift_rate = failure.params.get("drift_rate", 0.1)
        direction = failure.params.get("direction", 1)
        
        state_key = f"{failure.tag_id}_drift"
        
        if state_key not in self._failure_states:
            self._failure_states[state_key] = FailureState(
                tag_id=failure.tag_id,
                failure_type=FailureModeType.DRIFT,
                cumulative_drift=0.0,
            )
        
        # Calculate time since failure started
        time_in_failure = current_time_sec - failure.start_time_sec
        cumulative_drift = drift_rate * time_in_failure * direction
        
        self._failure_states[state_key].cumulative_drift = cumulative_drift
        
        new_value = (point.value or 0) + cumulative_drift
        
        return TelemetryPoint(
            tag_id=point.tag_id,
            timestamp=point.timestamp,
            value=new_value,
            quality=QualityFlag.GOOD,  # Drift is subtle at first
            metadata={**point.metadata, "failure": "drift", "cumulative_drift": cumulative_drift}
        )
    
    def _apply_redundancy_conflict(
        self,
        point: TelemetryPoint,
        failure: FailureMode,
        current_time_sec: float,
    ) -> TelemetryPoint:
        """
        RC10: Redundancy Conflict - diverge from peer sensors
        
        Params:
            offset: Fixed offset from expected value
            peer_value: What the peer sensors are reading
        """
        offset = failure.params.get("offset", -60.0)  # Default: show 60 units lower
        
        new_value = (point.value or 100) + offset
        
        return TelemetryPoint(
            tag_id=point.tag_id,
            timestamp=point.timestamp,
            value=new_value,
            quality=QualityFlag.GOOD,
            metadata={**point.metadata, "failure": "redundancy_conflict"}
        )
    
    def _apply_physics_contradiction(
        self,
        point: TelemetryPoint,
        failure: FailureMode,
        current_time_sec: float,
    ) -> TelemetryPoint:
        """
        RC11: Physics Contradiction - impossible physical state
        
        This is typically used with paired sensors (e.g., valve + flow).
        
        Params:
            contradiction_type: Type of contradiction
            forced_value: Value to force that creates contradiction
        """
        contradiction_type = failure.params.get("contradiction_type", "valve_flow")
        forced_value = failure.params.get("forced_value")
        
        if forced_value is not None:
            new_value = forced_value
        else:
            # For valve_flow: if this is a flow sensor, show flow when valve is "closed"
            # The actual contradiction logic is handled by the trust layer
            new_value = point.value
        
        return TelemetryPoint(
            tag_id=point.tag_id,
            timestamp=point.timestamp,
            value=new_value,
            quality=QualityFlag.GOOD,
            metadata={**point.metadata, "failure": "physics_contradiction", "type": contradiction_type}
        )


# Convenience functions for creating failure modes

def create_missing_burst_failure(
    tag_id: str,
    start_time_sec: float,
    duration_sec: float,
    gap_probability: float = 0.5,
) -> FailureMode:
    """Create a missing bursts failure (RC01)"""
    return FailureMode(
        type=FailureModeType.MISSING_BURSTS,
        tag_id=tag_id,
        start_time_sec=start_time_sec,
        duration_sec=duration_sec,
        params={"gap_probability": gap_probability},
    )


def create_flatline_failure(
    tag_id: str,
    start_time_sec: float,
    duration_sec: float | None = None,
    stuck_value: float | None = None,
) -> FailureMode:
    """Create a flatline failure (RC07)"""
    params = {}
    if stuck_value is not None:
        params["stuck_value"] = stuck_value
    
    return FailureMode(
        type=FailureModeType.FLATLINE,
        tag_id=tag_id,
        start_time_sec=start_time_sec,
        duration_sec=duration_sec,
        params=params,
    )


def create_drift_failure(
    tag_id: str,
    start_time_sec: float,
    drift_rate: float = 0.1,
    direction: int = 1,
    duration_sec: float | None = None,
) -> FailureMode:
    """Create a drift failure (RC09)"""
    return FailureMode(
        type=FailureModeType.DRIFT,
        tag_id=tag_id,
        start_time_sec=start_time_sec,
        duration_sec=duration_sec,
        params={"drift_rate": drift_rate, "direction": direction},
    )


def create_redundancy_conflict_failure(
    tag_id: str,
    start_time_sec: float,
    offset: float = -60.0,
    duration_sec: float | None = None,
) -> FailureMode:
    """Create a redundancy conflict failure (RC10)"""
    return FailureMode(
        type=FailureModeType.REDUNDANCY_CONFLICT,
        tag_id=tag_id,
        start_time_sec=start_time_sec,
        duration_sec=duration_sec,
        params={"offset": offset},
    )


def create_physics_contradiction_failure(
    tag_id: str,
    start_time_sec: float,
    forced_value: float,
    contradiction_type: str = "valve_flow",
    duration_sec: float | None = None,
) -> FailureMode:
    """Create a physics contradiction failure (RC11)"""
    return FailureMode(
        type=FailureModeType.PHYSICS_CONTRADICTION,
        tag_id=tag_id,
        start_time_sec=start_time_sec,
        duration_sec=duration_sec,
        params={"forced_value": forced_value, "contradiction_type": contradiction_type},
    )
