"""
Scenario Simulator Service - Manages 60-second scenario simulations with decision events.

This service handles:
- Timeline-based scenario progression
- Real-time telemetry updates
- Critical decision events at key time points
- Operator response tracking
"""

import asyncio
import random
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from enum import Enum
from pydantic import BaseModel
from dataclasses import dataclass, field


class EventSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class DecisionType(str, Enum):
    ACKNOWLEDGE = "acknowledge"  # Simple acknowledgment
    BINARY = "binary"  # Yes/No decision
    MULTI_CHOICE = "multi_choice"  # Multiple options
    ESCALATE = "escalate"  # Escalation decision


class ScenarioEvent(BaseModel):
    """A time-based event in the scenario."""
    event_id: str
    time_sec: float
    title: str
    description: str
    severity: EventSeverity
    requires_decision: bool = False
    decision_type: Optional[DecisionType] = None
    decision_options: Optional[List[str]] = None
    decision_prompt: Optional[str] = None
    auto_resolve_sec: Optional[float] = None  # Auto-resolve after X seconds if no response


class DecisionRequest(BaseModel):
    """A decision request sent to the operator."""
    decision_id: str
    event_id: str
    scenario_id: str
    time_sec: float
    title: str
    description: str
    severity: EventSeverity
    decision_type: DecisionType
    options: List[str]
    prompt: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    responded: bool = False
    response: Optional[str] = None
    response_time_sec: Optional[float] = None


class TelemetryUpdate(BaseModel):
    """Real-time telemetry update."""
    time_sec: float
    channels: Dict[str, Any]
    anomalies: List[str] = []
    trust_score: float = 0.95


class ScenarioState(BaseModel):
    """Current state of a running scenario."""
    scenario_id: str
    status: str  # idle, running, paused, completed, error
    started_at: Optional[datetime] = None
    current_time_sec: float = 0.0
    total_duration_sec: float = 60.0
    events_triggered: List[str] = []
    pending_decisions: List[str] = []
    decisions_made: int = 0
    trust_score: float = 0.95
    phase: str = "monitoring"  # monitoring, alert, decision, resolution


# Scenario 1: Fixed Data Scenario - The Valve Incident (20 seconds)
SCENARIO_1_EVENTS: List[ScenarioEvent] = [
    ScenarioEvent(
        event_id="s1_start",
        time_sec=0,
        title="Scenario Started",
        description="Monitoring system initialized. All sensors reporting normal.",
        severity=EventSeverity.INFO,
    ),
    ScenarioEvent(
        event_id="s1_temp_rise",
        time_sec=3,
        title="Temperature Anomaly Detected",
        description="Core temperature rising above normal baseline. Currently at 74.2°C.",
        severity=EventSeverity.WARNING,
    ),
    ScenarioEvent(
        event_id="s1_decision_1",
        time_sec=5,
        title="Temperature Alert",
        description="Core temperature has exceeded warning threshold (75°C). Flow Rate A showing 6% deviation from expected values.",
        severity=EventSeverity.WARNING,
        requires_decision=True,
        decision_type=DecisionType.BINARY,
        decision_options=["Continue Monitoring", "Initiate Diagnostic"],
        decision_prompt="Temperature is elevated but within operational limits. Do you want to initiate a diagnostic check or continue monitoring?",
        auto_resolve_sec=5,
    ),
    ScenarioEvent(
        event_id="s1_pressure_spike",
        time_sec=8,
        title="Pressure Fluctuation",
        description="System pressure showing irregular patterns. Backup telemetry confirms deviation.",
        severity=EventSeverity.WARNING,
    ),
    ScenarioEvent(
        event_id="s1_contradiction",
        time_sec=12,
        title="Sensor Contradiction Detected",
        description="CRITICAL: Flow Rate A (233.8 L/min) and Flow Rate B (249.7 L/min) show 6.8% divergence. External feeds show conflicting data.",
        severity=EventSeverity.CRITICAL,
        requires_decision=True,
        decision_type=DecisionType.MULTI_CHOICE,
        decision_options=[
            "Trust Primary Sensors",
            "Trust External Feed Alpha", 
            "Trust External Feed Beta",
            "Request Manual Verification"
        ],
        decision_prompt="Conflicting sensor readings detected. Which data source should be prioritized for the trust calculation?",
        auto_resolve_sec=5,
    ),
    ScenarioEvent(
        event_id="s1_decision_2",
        time_sec=15,
        title="Escalation Required",
        description="Trust score dropped to 0.72. Multiple contradictions unresolved. Remote Station C is offline.",
        severity=EventSeverity.CRITICAL,
        requires_decision=True,
        decision_type=DecisionType.ESCALATE,
        decision_options=[
            "Approve Current Assessment",
            "Request Additional Evidence",
            "Escalate to Supervisor",
            "Override with Manual Decision"
        ],
        decision_prompt="Trust score is below acceptable threshold. How do you want to proceed with the decision artifact?",
        auto_resolve_sec=5,
    ),
    ScenarioEvent(
        event_id="s1_resolution",
        time_sec=18,
        title="Scenario Resolution",
        description="All operator decisions recorded. Generating decision artifact with full audit trail.",
        severity=EventSeverity.INFO,
    ),
]

# Scenario 2: Live Vision Scenario - Oil Rig (20 seconds)
SCENARIO_2_EVENTS: List[ScenarioEvent] = [
    ScenarioEvent(
        event_id="s2_start",
        time_sec=0,
        title="Vision Analysis Started",
        description="Video feed connected. AI vision system analyzing frames.",
        severity=EventSeverity.INFO,
    ),
    ScenarioEvent(
        event_id="s2_first_detection",
        time_sec=3,
        title="Object Detected",
        description="Vision system detected potential safety concern in frame.",
        severity=EventSeverity.WARNING,
    ),
    ScenarioEvent(
        event_id="s2_decision_1",
        time_sec=6,
        title="Safety Event Classification",
        description="AI detected possible safety violation. Confidence: 78%",
        severity=EventSeverity.WARNING,
        requires_decision=True,
        decision_type=DecisionType.BINARY,
        decision_options=["Confirm Safety Event", "Mark as False Positive"],
        decision_prompt="The vision system detected a potential safety concern but confidence is moderate. Please review and classify.",
        auto_resolve_sec=5,
    ),
    ScenarioEvent(
        event_id="s2_telemetry_correlation",
        time_sec=9,
        title="Cross-Validation Alert",
        description="Vision detection correlating with sensor anomalies. Temperature spike coincides with detected event.",
        severity=EventSeverity.CRITICAL,
    ),
    ScenarioEvent(
        event_id="s2_decision_2",
        time_sec=12,
        title="Incident Confirmation Required",
        description="Multiple indicators suggest genuine safety incident. Vision + Telemetry + External feed all show anomalies.",
        severity=EventSeverity.CRITICAL,
        requires_decision=True,
        decision_type=DecisionType.MULTI_CHOICE,
        decision_options=[
            "Confirm Incident - High Priority",
            "Confirm Incident - Standard Priority",
            "Request Additional Analysis",
            "Dismiss - Insufficient Evidence"
        ],
        decision_prompt="Cross-validation complete. Multiple data sources indicate potential incident. How should this be classified?",
        auto_resolve_sec=5,
    ),
    ScenarioEvent(
        event_id="s2_prediction",
        time_sec=16,
        title="Predictive Alert",
        description="Based on current trends, AI predicts escalation within 5 minutes if unaddressed.",
        severity=EventSeverity.CRITICAL,
        requires_decision=True,
        decision_type=DecisionType.ESCALATE,
        decision_options=[
            "Initiate Preventive Action",
            "Alert On-Site Team",
            "Continue Monitoring",
            "Escalate to Management"
        ],
        decision_prompt="Predictive model suggests potential escalation. What preventive action should be taken?",
        auto_resolve_sec=5,
    ),
    ScenarioEvent(
        event_id="s2_resolution",
        time_sec=19,
        title="Scenario Complete",
        description="All events processed. Decision artifact ready for review.",
        severity=EventSeverity.INFO,
    ),
]

# Scenario 3: Water Pipe Leakage Monitoring (20 seconds)
SCENARIO_3_EVENTS: List[ScenarioEvent] = [
    ScenarioEvent(
        event_id="s3_start",
        time_sec=0,
        title="Water Infrastructure Monitoring Started",
        description="Video feed connected. AI monitoring water pipeline infrastructure.",
        severity=EventSeverity.INFO,
    ),
    ScenarioEvent(
        event_id="s3_moisture_detected",
        time_sec=3,
        title="Moisture Anomaly Detected",
        description="Vision system detected unusual moisture patterns near pipe junction.",
        severity=EventSeverity.WARNING,
    ),
    ScenarioEvent(
        event_id="s3_decision_1",
        time_sec=6,
        title="Leak Classification Required",
        description="AI detected possible water leak. Visual analysis confidence: 82%",
        severity=EventSeverity.WARNING,
        requires_decision=True,
        decision_type=DecisionType.BINARY,
        decision_options=["Confirm Leak Detected", "Mark as Condensation"],
        decision_prompt="The vision system detected moisture accumulation that may indicate a leak. Please review and classify.",
        auto_resolve_sec=5,
    ),
    ScenarioEvent(
        event_id="s3_pressure_drop",
        time_sec=8,
        title="Pressure Drop Detected",
        description="Water pressure sensors showing 12% decrease from baseline. Correlates with visual detection.",
        severity=EventSeverity.CRITICAL,
    ),
    ScenarioEvent(
        event_id="s3_flow_correlation",
        time_sec=10,
        title="Flow Rate Discrepancy",
        description="Inlet flow (450 L/min) differs from outlet flow (398 L/min). 52 L/min unaccounted.",
        severity=EventSeverity.CRITICAL,
    ),
    ScenarioEvent(
        event_id="s3_decision_2",
        time_sec=13,
        title="Leak Severity Assessment",
        description="Multiple indicators confirm water loss. Vision + Flow + Pressure all indicate leak.",
        severity=EventSeverity.CRITICAL,
        requires_decision=True,
        decision_type=DecisionType.MULTI_CHOICE,
        decision_options=[
            "Minor Leak - Schedule Repair",
            "Moderate Leak - Urgent Repair",
            "Major Leak - Immediate Shutdown",
            "Request Inspection Team"
        ],
        decision_prompt="Confirmed water leak detected. Based on flow discrepancy of 52 L/min, classify severity and response.",
        auto_resolve_sec=5,
    ),
    ScenarioEvent(
        event_id="s3_damage_prediction",
        time_sec=16,
        title="Infrastructure Risk Alert",
        description="AI predicts potential structural impact if leak continues. Estimated water loss: 3,120 L/hour.",
        severity=EventSeverity.CRITICAL,
        requires_decision=True,
        decision_type=DecisionType.ESCALATE,
        decision_options=[
            "Initiate Emergency Shutoff",
            "Deploy Repair Team",
            "Continue Monitoring",
            "Escalate to Utility Management"
        ],
        decision_prompt="Continued leakage may cause structural damage. Recommend immediate action.",
        auto_resolve_sec=5,
    ),
    ScenarioEvent(
        event_id="s3_resolution",
        time_sec=19,
        title="Scenario Complete",
        description="Water leak monitoring complete. Decision artifact generated with full timeline.",
        severity=EventSeverity.INFO,
    ),
]

# Scenario 4: Data Center Arc Flash Monitoring (20 seconds)
SCENARIO_4_EVENTS: List[ScenarioEvent] = [
    ScenarioEvent(
        event_id="s4_start",
        time_sec=0,
        title="Data Center Monitoring Started",
        description="Video feed connected. AI monitoring electrical infrastructure for arc flash hazards.",
        severity=EventSeverity.INFO,
    ),
    ScenarioEvent(
        event_id="s4_thermal_anomaly",
        time_sec=3,
        title="Thermal Anomaly Detected",
        description="Infrared sensors detecting elevated temperature on Bus Bar 3. Currently 15°C above baseline.",
        severity=EventSeverity.WARNING,
    ),
    ScenarioEvent(
        event_id="s4_decision_1",
        time_sec=6,
        title="Electrical Hazard Classification",
        description="Vision system detected potential arc flash precursor. Thermal signature confidence: 85%",
        severity=EventSeverity.WARNING,
        requires_decision=True,
        decision_type=DecisionType.BINARY,
        decision_options=["Confirm Electrical Hazard", "Mark as Normal Variation"],
        decision_prompt="The vision system detected thermal buildup that may indicate arc flash risk. Please review and classify.",
        auto_resolve_sec=5,
    ),
    ScenarioEvent(
        event_id="s4_current_spike",
        time_sec=8,
        title="Current Spike Detected",
        description="PDU monitoring shows 340% current spike on Circuit 7. Duration: 0.3 seconds.",
        severity=EventSeverity.CRITICAL,
    ),
    ScenarioEvent(
        event_id="s4_smoke_detection",
        time_sec=10,
        title="Smoke Particles Detected",
        description="Vision AI detected smoke particles near switchgear. Correlating with thermal data.",
        severity=EventSeverity.CRITICAL,
    ),
    ScenarioEvent(
        event_id="s4_decision_2",
        time_sec=13,
        title="Arc Flash Risk Assessment",
        description="Multiple indicators confirm electrical fault. Vision + Thermal + Current all indicate imminent arc flash.",
        severity=EventSeverity.CRITICAL,
        requires_decision=True,
        decision_type=DecisionType.MULTI_CHOICE,
        decision_options=[
            "Immediate Power Isolation",
            "Controlled Shutdown Sequence",
            "Deploy Fire Suppression",
            "Request Electrical Team"
        ],
        decision_prompt="Confirmed arc flash risk. Potential incident energy: 8.2 cal/cm². Recommend immediate action.",
        auto_resolve_sec=5,
    ),
    ScenarioEvent(
        event_id="s4_evacuation_alert",
        time_sec=16,
        title="Personnel Safety Alert",
        description="AI recommends immediate evacuation of Server Room B. Arc flash boundary: 12 feet.",
        severity=EventSeverity.CRITICAL,
        requires_decision=True,
        decision_type=DecisionType.ESCALATE,
        decision_options=[
            "Initiate Emergency Shutdown",
            "Sound Evacuation Alarm",
            "Continue Monitoring",
            "Escalate to Facility Manager"
        ],
        decision_prompt="Personnel safety at risk. Arc flash incident probability: 78%. Recommend evacuation.",
        auto_resolve_sec=5,
    ),
    ScenarioEvent(
        event_id="s4_resolution",
        time_sec=19,
        title="Scenario Complete",
        description="Arc flash monitoring complete. Decision artifact generated with full timeline.",
        severity=EventSeverity.INFO,
    ),
]


@dataclass
class ScenarioSimulator:
    """Manages scenario simulation with real-time updates."""
    
    scenario_id: str
    events: List[ScenarioEvent]
    duration_sec: float = 20.0
    state: ScenarioState = field(default=None)
    _running: bool = False
    _task: Optional[asyncio.Task] = None
    _event_callbacks: List[Callable] = field(default_factory=list)
    _telemetry_callbacks: List[Callable] = field(default_factory=list)
    _decision_callbacks: List[Callable] = field(default_factory=list)
    _pending_decisions: Dict[str, DecisionRequest] = field(default_factory=dict)
    
    def __post_init__(self):
        self.state = ScenarioState(
            scenario_id=self.scenario_id,
            status="idle",
            total_duration_sec=self.duration_sec
        )
        self._event_callbacks = []
        self._telemetry_callbacks = []
        self._decision_callbacks = []
        self._pending_decisions = {}
    
    def on_event(self, callback: Callable):
        """Register callback for scenario events."""
        self._event_callbacks.append(callback)
    
    def on_telemetry(self, callback: Callable):
        """Register callback for telemetry updates."""
        self._telemetry_callbacks.append(callback)
    
    def on_decision_required(self, callback: Callable):
        """Register callback for decision requests."""
        self._decision_callbacks.append(callback)
    
    async def start(self):
        """Start the scenario simulation."""
        if self._running:
            return
        
        self._running = True
        self.state.status = "running"
        self.state.started_at = datetime.utcnow()
        self.state.current_time_sec = 0
        self.state.events_triggered = []
        self.state.pending_decisions = []
        self.state.decisions_made = 0
        self.state.trust_score = 0.95
        self.state.phase = "monitoring"
        
        self._task = asyncio.create_task(self._run_simulation())
    
    async def stop(self):
        """Stop the scenario simulation."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self.state.status = "stopped"
    
    async def submit_decision(self, decision_id: str, response: str) -> bool:
        """Submit an operator decision."""
        if decision_id not in self._pending_decisions:
            return False
        
        decision = self._pending_decisions[decision_id]
        decision.responded = True
        decision.response = response
        decision.response_time_sec = self.state.current_time_sec - decision.time_sec
        
        # Remove from pending
        if decision_id in self.state.pending_decisions:
            self.state.pending_decisions.remove(decision_id)
        self.state.decisions_made += 1
        
        # Adjust trust score based on response time
        if decision.response_time_sec < 5:
            self.state.trust_score = min(1.0, self.state.trust_score + 0.02)
        elif decision.response_time_sec > 15:
            self.state.trust_score = max(0.5, self.state.trust_score - 0.03)
        
        return True
    
    def get_pending_decisions(self) -> List[DecisionRequest]:
        """Get all pending decision requests."""
        return list(self._pending_decisions.values())
    
    async def _run_simulation(self):
        """Main simulation loop."""
        update_interval = 0.75  # Update every 0.75 seconds for fast updates
        event_index = 0
        
        while self._running and self.state.current_time_sec < self.duration_sec:
            # Check for events to trigger
            while (event_index < len(self.events) and 
                   self.events[event_index].time_sec <= self.state.current_time_sec):
                event = self.events[event_index]
                await self._trigger_event(event)
                event_index += 1
            
            # Generate telemetry update
            telemetry = self._generate_telemetry()
            for callback in self._telemetry_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(telemetry)
                    else:
                        callback(telemetry)
                except Exception as e:
                    print(f"Telemetry callback error: {e}")
            
            # Check for expired decisions
            await self._check_decision_timeouts()
            
            # Wait for next update
            await asyncio.sleep(update_interval)
            self.state.current_time_sec += update_interval
        
        # Scenario complete
        self._running = False
        self.state.status = "completed"
        self.state.phase = "resolution"
    
    async def _trigger_event(self, event: ScenarioEvent):
        """Trigger a scenario event."""
        self.state.events_triggered.append(event.event_id)
        
        # Update phase based on severity
        if event.severity == EventSeverity.CRITICAL:
            self.state.phase = "decision"
        elif event.severity == EventSeverity.WARNING:
            self.state.phase = "alert"
        
        # Adjust trust score for critical events
        if event.severity == EventSeverity.CRITICAL:
            self.state.trust_score = max(0.5, self.state.trust_score - 0.08)
        elif event.severity == EventSeverity.WARNING:
            self.state.trust_score = max(0.6, self.state.trust_score - 0.03)
        
        # Notify event callbacks
        for callback in self._event_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                print(f"Event callback error: {e}")
        
        # Create decision request if needed
        if event.requires_decision:
            decision = DecisionRequest(
                decision_id=f"dec_{event.event_id}_{int(self.state.current_time_sec)}",
                event_id=event.event_id,
                scenario_id=self.scenario_id,
                time_sec=self.state.current_time_sec,
                title=event.title,
                description=event.description,
                severity=event.severity,
                decision_type=event.decision_type,
                options=event.decision_options or [],
                prompt=event.decision_prompt or "",
                created_at=datetime.utcnow(),
            )
            
            if event.auto_resolve_sec:
                from datetime import timedelta
                decision.expires_at = datetime.utcnow() + timedelta(seconds=event.auto_resolve_sec)
            
            self._pending_decisions[decision.decision_id] = decision
            self.state.pending_decisions.append(decision.decision_id)
            
            # Notify decision callbacks
            for callback in self._decision_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(decision)
                    else:
                        callback(decision)
                except Exception as e:
                    print(f"Decision callback error: {e}")
    
    async def _check_decision_timeouts(self):
        """Check for expired decision requests."""
        now = datetime.utcnow()
        expired = []
        
        for dec_id, decision in self._pending_decisions.items():
            if decision.expires_at and now >= decision.expires_at and not decision.responded:
                decision.responded = True
                decision.response = "AUTO_TIMEOUT"
                expired.append(dec_id)
                self.state.trust_score = max(0.5, self.state.trust_score - 0.05)
        
        for dec_id in expired:
            if dec_id in self.state.pending_decisions:
                self.state.pending_decisions.remove(dec_id)
    
    def _generate_telemetry(self) -> TelemetryUpdate:
        """Generate telemetry data for current time with scenario-specific anomalies."""
        t = self.state.current_time_sec
        anomalies = []
        
        # Detect which scenario we're running
        is_scenario2 = self.scenario_id.startswith("scenario2")
        is_scenario3 = self.scenario_id.startswith("scenario3")
        is_scenario4 = self.scenario_id.startswith("scenario4")
        is_vision_scenario = is_scenario2 or is_scenario3 or is_scenario4
        
        # Progress factor (0 to 1) - how far into the scenario we are
        progress = min(1.0, t / 20.0)
        
        # After 5 seconds (when video appears), start degrading sensors
        video_shown = t >= 5.0
        degradation_factor = max(0, (t - 5) / 15.0) if video_shown else 0  # 0 to 1 over remaining 15 seconds
        
        # Base values - start normal, then degrade
        if is_vision_scenario and video_shown:
            # Temperature rises dramatically
            base_temp = 72.0 + (degradation_factor * 15) + random.uniform(-0.5, 0.5)
            # Pressure drops
            base_pressure = 14.5 - (degradation_factor * 4) + random.uniform(-0.3, 0.3)
            # Flow rates diverge
            base_flow_a = 230 - (degradation_factor * 50) + random.uniform(-5, 5)
            base_flow_b = 245 + (degradation_factor * 20) + random.uniform(-3, 3)
            # Vibration increases
            base_vibration = 0.3 + (degradation_factor * 1.5) + random.uniform(0, 0.3)
            # Power fluctuates wildly for scenario 4
            if is_scenario4:
                base_power = 850 + (degradation_factor * 400) * random.uniform(0.5, 1.5) + random.uniform(-50, 50)
            else:
                base_power = 850 - (degradation_factor * 100) + random.uniform(-20, 20)
            # Humidity changes
            base_humidity = 43 + (degradation_factor * 25 if is_scenario3 else degradation_factor * 10) + random.uniform(-3, 3)
        else:
            # Normal baseline values
            base_temp = 72.0 + random.uniform(-0.5, 0.5)
            base_pressure = 14.5 + random.uniform(-0.3, 0.3)
            base_flow_a = 230 + random.uniform(-2, 2)
            base_flow_b = 245 + random.uniform(-2, 2)
            base_vibration = 0.3 + random.uniform(0, 0.1)
            base_power = 850 + random.uniform(-10, 10)
            base_humidity = 43 + random.uniform(-2, 2)
        
        # Determine status based on thresholds
        def get_status(value, warning_threshold, critical_threshold, higher_is_worse=True):
            if higher_is_worse:
                if value >= critical_threshold:
                    return "critical"
                elif value >= warning_threshold:
                    return "warning"
            else:
                if value <= critical_threshold:
                    return "critical"
                elif value <= warning_threshold:
                    return "warning"
            return "normal"
        
        # Build channels with dynamic status
        temp_status = get_status(base_temp, 78, 85, higher_is_worse=True)
        pressure_status = get_status(base_pressure, 12, 10, higher_is_worse=False)
        flow_divergence = abs(base_flow_a - base_flow_b)
        flow_a_status = get_status(flow_divergence, 20, 40, higher_is_worse=True)
        vibration_status = get_status(base_vibration, 1.0, 1.5, higher_is_worse=True)
        power_status = get_status(abs(base_power - 850), 100, 200, higher_is_worse=True)
        humidity_status = get_status(base_humidity, 55, 65, higher_is_worse=True) if is_scenario3 else "normal"
        
        # Track anomalies
        if temp_status != "normal":
            anomalies.append("temperature_spike")
        if pressure_status != "normal":
            anomalies.append("pressure_drop")
        if flow_a_status != "normal":
            anomalies.append("flow_divergence")
        if vibration_status != "normal":
            anomalies.append("vibration_alert")
        if power_status != "normal":
            anomalies.append("power_fluctuation")
        if humidity_status != "normal":
            anomalies.append("humidity_alert")
        
        channels = {
            "core_temp": {"value": round(base_temp, 1), "unit": "°C", "status": temp_status},
            "pressure": {"value": round(max(8, base_pressure), 1), "unit": "PSI", "status": pressure_status},
            "flow_a": {"value": round(max(150, base_flow_a), 1), "unit": "L/min", "status": flow_a_status},
            "flow_b": {"value": round(base_flow_b, 1), "unit": "L/min", "status": "normal"},
            "vibration": {"value": round(base_vibration, 2), "unit": "mm/s", "status": vibration_status},
            "power": {"value": round(base_power, 1), "unit": "kW", "status": power_status},
            "humidity": {"value": round(base_humidity, 1), "unit": "%", "status": humidity_status},
        }
        
        # For Scenario 4 (Data Center), add electrical-specific channels
        if is_scenario4:
            electrical_load = 75 + (degradation_factor * 25) + random.uniform(-5, 5) if video_shown else 75 + random.uniform(-2, 2)
            bus_temp = 45 + (degradation_factor * 35) + random.uniform(-2, 2) if video_shown else 45 + random.uniform(-1, 1)
            arc_risk = min(100, degradation_factor * 100 + random.uniform(-5, 5)) if video_shown else random.uniform(0, 5)
            
            channels["electrical_load"] = {
                "value": round(min(100, electrical_load), 1),
                "unit": "%",
                "status": get_status(electrical_load, 85, 95, higher_is_worse=True)
            }
            channels["bus_bar_temp"] = {
                "value": round(bus_temp, 1),
                "unit": "°C",
                "status": get_status(bus_temp, 65, 75, higher_is_worse=True)
            }
            channels["arc_flash_risk"] = {
                "value": round(arc_risk, 1),
                "unit": "%",
                "status": get_status(arc_risk, 50, 75, higher_is_worse=True)
            }
            
            if channels["electrical_load"]["status"] != "normal":
                anomalies.append("electrical_overload")
            if channels["bus_bar_temp"]["status"] != "normal":
                anomalies.append("thermal_buildup")
            if channels["arc_flash_risk"]["status"] != "normal":
                anomalies.append("arc_flash_warning")
        
        return TelemetryUpdate(
            time_sec=t,
            channels=channels,
            anomalies=anomalies,
            trust_score=self.state.trust_score
        )


# Global simulator instances
_simulators: Dict[str, ScenarioSimulator] = {}


def get_simulator(scenario_id: str) -> Optional[ScenarioSimulator]:
    """Get an existing simulator instance."""
    return _simulators.get(scenario_id)


def create_simulator(scenario_type: str) -> ScenarioSimulator:
    """Create a new scenario simulator."""
    if scenario_type == "scenario1" or scenario_type == "fixed-valve-incident":
        scenario_id = f"scenario1_{int(datetime.utcnow().timestamp())}"
        simulator = ScenarioSimulator(
            scenario_id=scenario_id,
            events=SCENARIO_1_EVENTS,
            duration_sec=20.0
        )
    elif scenario_type == "scenario2" or scenario_type == "live-vision-demo":
        scenario_id = f"scenario2_{int(datetime.utcnow().timestamp())}"
        simulator = ScenarioSimulator(
            scenario_id=scenario_id,
            events=SCENARIO_2_EVENTS,
            duration_sec=20.0
        )
    elif scenario_type == "scenario3" or scenario_type == "water-pipe-leakage":
        scenario_id = f"scenario3_{int(datetime.utcnow().timestamp())}"
        simulator = ScenarioSimulator(
            scenario_id=scenario_id,
            events=SCENARIO_3_EVENTS,
            duration_sec=20.0
        )
    elif scenario_type == "scenario4" or scenario_type == "data-center-arc-flash":
        scenario_id = f"scenario4_{int(datetime.utcnow().timestamp())}"
        simulator = ScenarioSimulator(
            scenario_id=scenario_id,
            events=SCENARIO_4_EVENTS,
            duration_sec=20.0
        )
    else:
        raise ValueError(f"Unknown scenario type: {scenario_type}")
    
    _simulators[scenario_id] = simulator
    return simulator


def get_all_simulators() -> Dict[str, ScenarioSimulator]:
    """Get all simulator instances."""
    return _simulators
