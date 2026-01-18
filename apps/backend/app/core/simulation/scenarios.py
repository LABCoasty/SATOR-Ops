"""
Golden Scenarios Module

Pre-defined scenarios for demo purposes with deterministic failure timelines.
"""

from datetime import datetime, timedelta
from typing import Generator

from app.models.simulation import (
    ScenarioSpec, SensorSpec, FailureMode, FailureModeType, ScenarioState
)
from app.models.telemetry import TelemetryPoint
from .generator import SignalGenerator
from .failure_modes import (
    FailureModeInjector,
    create_redundancy_conflict_failure,
    create_physics_contradiction_failure,
    create_flatline_failure,
    create_drift_failure,
    create_missing_burst_failure,
)


# === Sensor Definitions ===

PRESSURE_SENSOR_A = SensorSpec(
    tag_id="pressure_sensor_a",
    name="Pressure Sensor A",
    unit="PSI",
    baseline_value=100.0,
    noise_std=0.02,
    min_value=0.0,
    max_value=200.0,
    max_roc=10.0,
    redundancy_group="pressure_main",
    oscillation_amplitude=2.0,
    oscillation_period_sec=120.0,
)

PRESSURE_SENSOR_B = SensorSpec(
    tag_id="pressure_sensor_b",
    name="Pressure Sensor B",
    unit="PSI",
    baseline_value=100.0,
    noise_std=0.02,
    min_value=0.0,
    max_value=200.0,
    max_roc=10.0,
    redundancy_group="pressure_main",
    oscillation_amplitude=2.0,
    oscillation_period_sec=120.0,
)

FLOW_METER = SensorSpec(
    tag_id="flow_meter",
    name="Flow Meter",
    unit="GPM",
    baseline_value=500.0,
    noise_std=0.03,
    min_value=0.0,
    max_value=1000.0,
    max_roc=50.0,
    oscillation_amplitude=10.0,
    oscillation_period_sec=60.0,
)

VALVE_POSITION = SensorSpec(
    tag_id="valve_position",
    name="Main Valve Position",
    unit="%",
    baseline_value=100.0,  # 100% = fully open
    noise_std=0.0,  # Valve position is usually discrete
    min_value=0.0,
    max_value=100.0,
    max_roc=50.0,
)

VIBRATION_SENSOR = SensorSpec(
    tag_id="vibration_sensor",
    name="Pump Vibration",
    unit="mm/s",
    baseline_value=2.5,
    noise_std=0.1,
    min_value=0.0,
    max_value=25.0,
    max_roc=5.0,
)

TEMPERATURE_SENSOR = SensorSpec(
    tag_id="temperature_sensor",
    name="Fluid Temperature",
    unit="°C",
    baseline_value=35.0,
    noise_std=0.01,
    min_value=-20.0,
    max_value=150.0,
    max_roc=1.0,
    trend_rate=0.001,  # Slight warming trend
)


# === Golden Scenarios ===

THE_MISMATCHED_VALVE = ScenarioSpec(
    scenario_id="mismatched_valve",
    name="The Mismatched Valve Incident",
    description="""
    A scenario demonstrating redundancy conflict and physics contradiction.
    
    Timeline:
    - 00:00: Normal operation, all sensors trusted
    - 01:00: Sensor A drops to 40 PSI while Sensor B stays at 100 PSI (RC10 - Redundancy Conflict)
    - 01:15: Valve reports CLOSED but flow meter shows 500 GPM (RC11 - Physics Contradiction)
    - 01:30: System in Decision Mode, operator must act
    - 01:45: Expected operator action (DEFER + DISPATCH)
    - 02:00: Forensic review point
    
    This scenario triggers RC10 and RC11, forcing the system into Decision Mode
    and requiring operator intervention.
    """,
    duration_sec=180.0,  # 3 minutes
    sample_rate=1.0,
    sensors=[
        PRESSURE_SENSOR_A,
        PRESSURE_SENSOR_B,
        FLOW_METER,
        VALVE_POSITION,
        VIBRATION_SENSOR,
        TEMPERATURE_SENSOR,
    ],
    failures=[
        # t=60s: Pressure Sensor A drops (RC10 - Redundancy Conflict)
        create_redundancy_conflict_failure(
            tag_id="pressure_sensor_a",
            start_time_sec=60.0,
            offset=-60.0,  # Shows 40 PSI instead of 100 PSI
        ),
        # t=75s: Valve shows CLOSED but flow continues (RC11 - Physics Contradiction)
        create_physics_contradiction_failure(
            tag_id="valve_position",
            start_time_sec=75.0,
            forced_value=0.0,  # Valve shows CLOSED (0%)
            contradiction_type="valve_flow",
        ),
    ],
    seed=42,
)

THE_STALE_SENSOR_LEAK = ScenarioSpec(
    scenario_id="stale_sensor_leak",
    name="The Stale Sensor Leak",
    description="""
    A scenario demonstrating flatline and missing data failures.
    
    Timeline:
    - 00:00: Normal operation
    - 00:30: Flow meter flatlines at current value (RC07 - Flatline)
    - 01:00: Pressure sensor starts showing gaps (RC01 - Missing Bursts)
    - 01:30: Temperature sensor begins drifting (RC09 - Drift)
    
    This scenario shows how the system handles sensors that become unreliable
    over time, requiring operator awareness but not immediate action.
    """,
    duration_sec=180.0,
    sample_rate=1.0,
    sensors=[
        PRESSURE_SENSOR_A,
        FLOW_METER,
        TEMPERATURE_SENSOR,
    ],
    failures=[
        # t=30s: Flow meter flatlines
        create_flatline_failure(
            tag_id="flow_meter",
            start_time_sec=30.0,
            stuck_value=500.0,
        ),
        # t=60s: Pressure sensor missing data
        create_missing_burst_failure(
            tag_id="pressure_sensor_a",
            start_time_sec=60.0,
            duration_sec=60.0,
            gap_probability=0.4,
        ),
        # t=90s: Temperature drift
        create_drift_failure(
            tag_id="temperature_sensor",
            start_time_sec=90.0,
            drift_rate=0.05,
            direction=1,
        ),
    ],
    seed=42,
)


# Registry of all golden scenarios
GOLDEN_SCENARIOS: dict[str, ScenarioSpec] = {
    "mismatched_valve": THE_MISMATCHED_VALVE,
    "stale_sensor_leak": THE_STALE_SENSOR_LEAK,
}


class ScenarioRunner:
    """
    Runs golden scenarios with deterministic output.
    
    Coordinates the SignalGenerator and FailureModeInjector to produce
    the expected sequence of events for demo purposes.
    """
    
    def __init__(
        self,
        generator: SignalGenerator,
        injector: FailureModeInjector,
    ):
        self.generator = generator
        self.injector = injector
        self._active_scenario: ScenarioSpec | None = None
        self._state: ScenarioState | None = None
        self._generated_data: dict[str, list[TelemetryPoint]] = {}
        self._base_time: datetime | None = None
    
    def start(self, scenario_name: str) -> dict:
        """
        Start a golden scenario.
        
        Returns scenario info and initial state.
        """
        if scenario_name not in GOLDEN_SCENARIOS:
            raise ValueError(f"Unknown scenario: {scenario_name}")
        
        scenario = GOLDEN_SCENARIOS[scenario_name]
        
        # Reset state
        self._active_scenario = scenario
        self.generator.reset(seed=scenario.seed)
        self.injector.reset()
        self._base_time = datetime.utcnow()
        self.generator.set_base_time(self._base_time)
        
        # Pre-generate all data for determinism
        self._generated_data = self._generate_scenario_data(scenario)
        
        # Schedule all failures
        for failure in scenario.failures:
            self.injector.schedule_failure(failure)
        
        # Create state tracker
        self._state = ScenarioState(
            scenario_id=scenario.scenario_id,
            started_at=self._base_time,
            current_time_sec=0.0,
            is_running=True,
        )
        
        return {
            "scenario_id": scenario.scenario_id,
            "name": scenario.name,
            "description": scenario.description,
            "duration_sec": scenario.duration_sec,
            "sensors": [s.tag_id for s in scenario.sensors],
            "scheduled_failures": len(scenario.failures),
            "started_at": self._base_time.isoformat(),
        }
    
    def _generate_scenario_data(
        self, 
        scenario: ScenarioSpec
    ) -> dict[str, list[TelemetryPoint]]:
        """Pre-generate all telemetry data for a scenario"""
        return self.generator.generate_multiple_sensors(
            sensors=scenario.sensors,
            duration_sec=scenario.duration_sec,
            sample_rate=scenario.sample_rate,
            base_time=self._base_time,
        )
    
    def get_telemetry_at(self, time_sec: float) -> list[TelemetryPoint]:
        """
        Get telemetry values at a specific time point.
        
        Applies any active failures to the base data.
        """
        if not self._active_scenario or not self._generated_data:
            return []
        
        sample_idx = int(time_sec * self._active_scenario.sample_rate)
        result = []
        
        for tag_id, points in self._generated_data.items():
            if sample_idx < len(points):
                point = points[sample_idx]
                # Apply failures
                modified = self.injector.apply_failures(point, time_sec)
                if modified is not None:
                    result.append(modified)
        
        # Update failure states
        self.injector.update_failure_states(time_sec)
        
        return result
    
    def get_telemetry_range(
        self, 
        start_sec: float, 
        end_sec: float
    ) -> dict[str, list[TelemetryPoint]]:
        """Get telemetry for a time range"""
        if not self._active_scenario:
            return {}
        
        result: dict[str, list[TelemetryPoint]] = {}
        sample_rate = self._active_scenario.sample_rate
        
        start_idx = int(start_sec * sample_rate)
        end_idx = int(end_sec * sample_rate)
        
        for tag_id, points in self._generated_data.items():
            result[tag_id] = []
            for idx in range(start_idx, min(end_idx, len(points))):
                time_sec = idx / sample_rate
                point = points[idx]
                modified = self.injector.apply_failures(point, time_sec)
                if modified is not None:
                    result[tag_id].append(modified)
        
        return result
    
    def get_current_state(self) -> ScenarioState | None:
        """Get current scenario state"""
        return self._state
    
    def advance_time(self, delta_sec: float) -> None:
        """Advance scenario time"""
        if self._state:
            self._state.current_time_sec += delta_sec
            
            # Check if scenario ended
            if self._active_scenario and self._state.current_time_sec >= self._active_scenario.duration_sec:
                self._state.is_running = False
    
    def get_active_failures(self) -> list[dict]:
        """Get currently active failures"""
        return self.injector.get_active_failures()
    
    def stop(self) -> dict:
        """Stop the current scenario"""
        if self._state:
            self._state.is_running = False
            return {
                "scenario_id": self._state.scenario_id,
                "stopped_at_sec": self._state.current_time_sec,
            }
        return {}
    
    def get_scenario_timeline(self) -> list[dict]:
        """
        Get the planned event timeline for the current scenario.
        
        Returns a list of events (failures) with their scheduled times.
        """
        if not self._active_scenario:
            return []
        
        events = []
        for i, failure in enumerate(self._active_scenario.failures):
            events.append({
                "event_id": f"planned_failure_{i}",
                "event_type": "failure_injection",
                "timestamp_sec": failure.start_time_sec,
                "failure_type": failure.type.value,
                "tag_id": failure.tag_id,
                "duration_sec": failure.duration_sec,
            })
        
        return sorted(events, key=lambda e: e["timestamp_sec"])


def get_available_scenarios() -> list[dict]:
    """Get list of available golden scenarios"""
    out = [
        {
            "scenario_id": spec.scenario_id,
            "name": spec.name,
            "description": spec.description.strip(),
            "duration_sec": spec.duration_sec,
            "sensor_count": len(spec.sensors),
            "failure_count": len(spec.failures),
        }
        for spec in GOLDEN_SCENARIOS.values()
    ]
    out.append({
        "scenario_id": "video_disaster",
        "name": "Video Disaster (Live)",
        "description": "Disaster scenario driven by live video via Overshoot.ai. Connect a camera or video stream, run Overshoot with a disaster-detection prompt and outputSchema from GET /ingest/overshoot/schema, then POST JSON to /ingest/overshoot. Telemetry and events are written to CSV for ingest.",
        "duration_sec": 0,
        "sensor_count": 6,
        "failure_count": 0,
        "source": "overshoot",
    })
    return out
