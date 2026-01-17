"""
Data Loader Service - Load and manage scenario data from CSV/JSON files.

Provides typed interfaces for accessing telemetry, events, contradictions,
and other scenario data for both fixed and live scenarios.
"""

import csv
import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


# ============================================================================
# Data Models
# ============================================================================

class SensorQuality(str, Enum):
    GOOD = "Good"
    BAD = "Bad"
    UNCERTAIN = "Uncertain"


class TelemetryReading(BaseModel):
    """Single telemetry reading from a sensor."""
    timestamp: datetime
    tag_id: str
    sensor_name: str
    value: float
    unit: str
    quality: SensorQuality = SensorQuality.GOOD
    time_sec: float
    redundancy_group: Optional[str] = None


class EventSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ALARM = "ALARM"
    CRITICAL = "CRITICAL"


class ScenarioEvent(BaseModel):
    """Event that occurred during a scenario."""
    timestamp: datetime
    time_sec: float
    event_type: str
    severity: EventSeverity
    tag_id: Optional[str] = None
    reason_code: Optional[str] = None
    description: str
    action_required: bool = False


class Contradiction(BaseModel):
    """Detected contradiction between sensors or physics."""
    contradiction_id: str
    run_id: str
    timestamp: datetime
    time_sec: float
    primary_tag_id: str
    secondary_tag_ids: List[str]
    reason_code: str
    description: str
    values: Dict[str, float]
    expected_relationship: str
    resolved: bool = False


class DecisionReceipt(BaseModel):
    """Receipt for a decision made by an operator."""
    receipt_id: str
    run_id: str
    timestamp: datetime
    operator_id: str
    action_type: str
    action_description: str
    rationale: str
    uncertainty_snapshot: Dict[str, float]
    active_contradictions: List[str]
    evidence_refs: List[str]
    content_hash: str


class SensorConfig(BaseModel):
    """Configuration for a sensor."""
    tag_id: str
    sensor_name: str
    unit: str
    normal_min: float
    normal_max: float
    alarm_low: Optional[float] = None
    alarm_high: Optional[float] = None
    redundancy_group: Optional[str] = None


class ScenarioMetadata(BaseModel):
    """Metadata about a scenario."""
    scenario_id: str
    name: str
    description: str
    duration_seconds: float
    has_contradiction: bool = False
    recommended_action: Optional[str] = None
    resolution_rationale: Optional[str] = None


class ScenarioData(BaseModel):
    """Complete data for a scenario."""
    metadata: ScenarioMetadata
    telemetry: List[TelemetryReading] = Field(default_factory=list)
    events: List[ScenarioEvent] = Field(default_factory=list)
    contradictions: List[Contradiction] = Field(default_factory=list)
    receipts: List[DecisionReceipt] = Field(default_factory=list)
    sensors: List[SensorConfig] = Field(default_factory=list)


# ============================================================================
# Data Loader
# ============================================================================

class DataLoader:
    """
    Load and manage scenario data from CSV/JSON files.
    
    Provides methods to load telemetry, events, contradictions, and other
    scenario data with proper typing and validation.
    """
    
    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize the data loader.
        
        Args:
            data_dir: Path to the data directory. Defaults to app/data/
        """
        if data_dir is None:
            # Default to the data directory relative to this file
            self.data_dir = Path(__file__).parent.parent / "data"
        else:
            self.data_dir = Path(data_dir)
        
        self.csv_dir = self.data_dir / "csv"
        self.generated_dir = self.data_dir / "generated"
    
    # ========================================================================
    # CSV Loaders
    # ========================================================================
    
    def load_telemetry(self, filepath: Optional[Path] = None) -> List[TelemetryReading]:
        """Load telemetry data from CSV file."""
        if filepath is None:
            filepath = self.csv_dir / "telemetry.csv"
        
        readings = []
        with open(filepath, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                readings.append(TelemetryReading(
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    tag_id=row["tag_id"],
                    sensor_name=row["sensor_name"],
                    value=float(row["value"]),
                    unit=row["unit"],
                    quality=SensorQuality(row.get("quality", "Good")),
                    time_sec=float(row["time_sec"]),
                    redundancy_group=row.get("redundancy_group") or None
                ))
        return readings
    
    def load_events(self, filepath: Optional[Path] = None) -> List[ScenarioEvent]:
        """Load scenario events from CSV file."""
        if filepath is None:
            filepath = self.csv_dir / "events.csv"
        
        events = []
        with open(filepath, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                events.append(ScenarioEvent(
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    time_sec=float(row["time_sec"]),
                    event_type=row["event_type"],
                    severity=EventSeverity(row["severity"]),
                    tag_id=row.get("tag_id") or None,
                    reason_code=row.get("reason_code") or None,
                    description=row["description"],
                    action_required=row.get("action_required", "").lower() == "true"
                ))
        return events
    
    def load_sensors(self, filepath: Optional[Path] = None) -> List[SensorConfig]:
        """Load sensor configuration from CSV file."""
        if filepath is None:
            filepath = self.csv_dir / "sensors.csv"
        
        sensors = []
        with open(filepath, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Handle different column name conventions
                sensor_name = row.get("sensor_name") or row.get("name", row["tag_id"])
                normal_min = row.get("normal_min") or row.get("min_value", "0")
                normal_max = row.get("normal_max") or row.get("max_value", "100")
                
                sensors.append(SensorConfig(
                    tag_id=row["tag_id"],
                    sensor_name=sensor_name,
                    unit=row["unit"],
                    normal_min=float(normal_min),
                    normal_max=float(normal_max),
                    alarm_low=float(row["alarm_low"]) if row.get("alarm_low") else None,
                    alarm_high=float(row["alarm_high"]) if row.get("alarm_high") else None,
                    redundancy_group=row.get("redundancy_group") or None
                ))
        return sensors
    
    # ========================================================================
    # JSON Loaders
    # ========================================================================
    
    def load_contradictions(self, filepath: Optional[Path] = None) -> List[Contradiction]:
        """Load contradictions from JSON file."""
        if filepath is None:
            filepath = self.generated_dir / "contradictions.json"
        
        with open(filepath, "r") as f:
            data = json.load(f)
        
        contradictions = []
        for item in data:
            contradictions.append(Contradiction(
                contradiction_id=item["contradiction_id"],
                run_id=item["run_id"],
                timestamp=datetime.fromisoformat(item["timestamp"]),
                time_sec=item["time_sec"],
                primary_tag_id=item["primary_tag_id"],
                secondary_tag_ids=item["secondary_tag_ids"],
                reason_code=item["reason_code"],
                description=item["description"],
                values=item["values"],
                expected_relationship=item["expected_relationship"],
                resolved=item.get("resolved", False)
            ))
        return contradictions
    
    def load_decision_receipts(self, filepath: Optional[Path] = None) -> List[DecisionReceipt]:
        """Load decision receipts from JSON file."""
        if filepath is None:
            filepath = self.generated_dir / "decision_receipts.json"
        
        with open(filepath, "r") as f:
            data = json.load(f)
        
        receipts = []
        for item in data:
            receipts.append(DecisionReceipt(
                receipt_id=item["receipt_id"],
                run_id=item["run_id"],
                timestamp=datetime.fromisoformat(item["timestamp"]),
                operator_id=item["operator_id"],
                action_type=item["action_type"],
                action_description=item["action_description"],
                rationale=item["rationale"],
                uncertainty_snapshot=item["uncertainty_snapshot"],
                active_contradictions=item["active_contradictions"],
                evidence_refs=item["evidence_refs"],
                content_hash=item["content_hash"]
            ))
        return receipts
    
    def load_json_telemetry(self, filepath: Optional[Path] = None) -> List[Dict[str, Any]]:
        """Load telemetry from JSON file (generated format)."""
        if filepath is None:
            filepath = self.generated_dir / "telemetry.json"
        
        with open(filepath, "r") as f:
            return json.load(f)
    
    # ========================================================================
    # Scenario Loaders
    # ========================================================================
    
    def load_fixed_scenario(self) -> ScenarioData:
        """
        Load the fixed case scenario with predefined data.
        
        This scenario demonstrates "The Mismatched Valve Incident" where
        pressure sensors disagree and the valve position contradicts flow readings.
        """
        telemetry = self.load_telemetry()
        events = self.load_events()
        contradictions = self.load_contradictions()
        receipts = self.load_decision_receipts()
        
        # Try to load sensors, use empty list if not available
        try:
            sensors = self.load_sensors()
        except FileNotFoundError:
            sensors = []
        
        metadata = ScenarioMetadata(
            scenario_id="fixed-valve-incident",
            name="The Mismatched Valve Incident",
            description=(
                "A scenario where pressure sensors disagree and the valve position "
                "sensor contradicts flow meter readings. Demonstrates decision-making "
                "under sensor uncertainty."
            ),
            duration_seconds=180.0,
            has_contradiction=True,
            recommended_action="defer",
            resolution_rationale=(
                "Cannot trust sensor data - physical verification required before "
                "control action. Defer decision and dispatch field technician for "
                "visual inspection."
            )
        )
        
        return ScenarioData(
            metadata=metadata,
            telemetry=telemetry,
            events=events,
            contradictions=contradictions,
            receipts=receipts,
            sensors=sensors
        )
    
    def get_telemetry_at_time(
        self, 
        telemetry: List[TelemetryReading], 
        time_sec: float
    ) -> Dict[str, TelemetryReading]:
        """
        Get the latest telemetry readings at a specific time.
        
        Args:
            telemetry: List of telemetry readings
            time_sec: Time in seconds from scenario start
            
        Returns:
            Dictionary mapping tag_id to the latest reading at that time
        """
        latest: Dict[str, TelemetryReading] = {}
        for reading in telemetry:
            if reading.time_sec <= time_sec:
                if reading.tag_id not in latest or reading.time_sec > latest[reading.tag_id].time_sec:
                    latest[reading.tag_id] = reading
        return latest
    
    def get_events_in_range(
        self,
        events: List[ScenarioEvent],
        start_sec: float,
        end_sec: float
    ) -> List[ScenarioEvent]:
        """Get events within a time range."""
        return [e for e in events if start_sec <= e.time_sec <= end_sec]
    
    def get_active_contradictions(
        self,
        contradictions: List[Contradiction],
        time_sec: float
    ) -> List[Contradiction]:
        """Get contradictions that are active at a specific time."""
        return [
            c for c in contradictions 
            if c.time_sec <= time_sec and not c.resolved
        ]


# ============================================================================
# Singleton instance for easy access
# ============================================================================

_data_loader: Optional[DataLoader] = None


def get_data_loader() -> DataLoader:
    """Get the singleton DataLoader instance."""
    global _data_loader
    if _data_loader is None:
        _data_loader = DataLoader()
    return _data_loader
