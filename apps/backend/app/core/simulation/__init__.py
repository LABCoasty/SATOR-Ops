"""
Simulation Engine Module

Generates deterministic time-series data with controlled failure modes.
"""

from .generator import SignalGenerator
from .failure_modes import FailureModeInjector
from .scenarios import ScenarioRunner, GOLDEN_SCENARIOS, get_available_scenarios

__all__ = [
    "SignalGenerator",
    "FailureModeInjector",
    "ScenarioRunner",
    "GOLDEN_SCENARIOS",
    "get_available_scenarios",
]


class SimulationEngine:
    """
    Main simulation engine that orchestrates signal generation and failure injection.
    
    This is the "story machine" that produces deterministic telemetry data
    with controlled failures for demo purposes.
    """
    
    def __init__(self, seed: int = 42):
        self.seed = seed
        self.generator = SignalGenerator(seed=seed)
        self.injector = FailureModeInjector()
        self.scenario_runner = ScenarioRunner(self.generator, self.injector)
        self._active_scenario: str | None = None
        self._current_time: float = 0.0
    
    def start_scenario(self, scenario_name: str) -> dict:
        """Start a named Golden Scenario"""
        if scenario_name not in GOLDEN_SCENARIOS:
            raise ValueError(f"Unknown scenario: {scenario_name}. Available: {list(GOLDEN_SCENARIOS.keys())}")
        
        self._active_scenario = scenario_name
        self._current_time = 0.0
        return self.scenario_runner.start(scenario_name)
    
    def get_current_telemetry(self) -> list:
        """Get current telemetry values for all sensors"""
        if not self._active_scenario:
            return []
        return self.scenario_runner.get_telemetry_at(self._current_time)
    
    def inject_failure(self, failure_type: str, tag_id: str, **params) -> dict:
        """Inject a failure during live demo"""
        return self.injector.inject(failure_type, tag_id, self._current_time, **params)
    
    def advance_time(self, delta_sec: float) -> None:
        """Advance simulation time"""
        self._current_time += delta_sec
    
    @property
    def is_active(self) -> bool:
        return self._active_scenario is not None
