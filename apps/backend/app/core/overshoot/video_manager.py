"""
Video Disaster scenario manager.

Handles start/stop, ingest of Overshoot JSON, and telemetry/event CSV persistence
for the live video disaster scenario.
"""

import csv
from datetime import datetime, timezone
from pathlib import Path

from app.models.overshoot import OvershootDisasterRecord
from app.models.telemetry import QualityFlag, TelemetryPoint

from .converter import (
    get_video_sensor_csv_rows,
    overshoot_to_event_rows,
    overshoot_to_telemetry_rows,
)

TELEMETRY_FIELDS = [
    "timestamp", "tag_id", "sensor_name", "value", "unit", "quality", "time_sec", "redundancy_group"
]
EVENTS_FIELDS = [
    "timestamp", "time_sec", "event_type", "severity", "tag_id", "reason_code", "description", "action_required"
]
SENSORS_FIELDS = [
    "tag_id", "name", "unit", "location", "manufacturer", "model", "calibration_date",
    "baseline_value", "min_value", "max_value", "max_roc", "redundancy_group", "physics_relationships",
]


class VideoDisasterManager:
    """
    Manages the video_disaster scenario: CSV ingest from Overshoot JSON,
    and telemetry/state for simulation and replay.
    """

    def __init__(self, base_path: Path):
        self._base_path = Path(base_path)
        self._telemetry_path = self._base_path / "video_disaster_telemetry.csv"
        self._events_path = self._base_path / "video_disaster_events.csv"
        self._sensors_path = self._base_path / "video_disaster_sensors.csv"

        self._base_ts_ms: int | None = None
        self._last_rec: OvershootDisasterRecord | None = None
        self._current_time_sec: float = 0.0
        self._running: bool = False

    def start(self) -> None:
        """Start a new video disaster run: reset state and create/truncate CSV files with headers."""
        self._base_ts_ms = None
        self._last_rec = None
        self._current_time_sec = 0.0
        self._running = True

        self._base_path.mkdir(parents=True, exist_ok=True)

        with open(self._telemetry_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=TELEMETRY_FIELDS)
            w.writeheader()

        with open(self._events_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=EVENTS_FIELDS)
            w.writeheader()

        sensor_rows = get_video_sensor_csv_rows()
        with open(self._sensors_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=SENSORS_FIELDS)
            w.writeheader()
            w.writerows(sensor_rows)

    def stop(self) -> None:
        """Stop the current run."""
        self._running = False

    def ingest(
        self,
        records: OvershootDisasterRecord | list[OvershootDisasterRecord] | list[dict],
    ) -> dict:
        """
        Ingest one or more Overshoot JSON records: convert to CSV rows and append.

        Accepts OvershootDisasterRecord, list of them, or list of dicts (parsed JSON).
        Returns { "ingested": int, "time_sec": float }.
        """
        if isinstance(records, (OvershootDisasterRecord, dict)):
            records = [records]

        parsed: list[OvershootDisasterRecord] = []
        for r in records:
            if isinstance(r, dict):
                parsed.append(OvershootDisasterRecord.model_validate(r))
            else:
                parsed.append(r)

        if not parsed:
            return {"ingested": 0, "time_sec": self._current_time_sec}

        for rec in parsed:
            if self._base_ts_ms is None:
                self._base_ts_ms = rec.timestamp_ms
            time_sec = (rec.timestamp_ms - self._base_ts_ms) / 1000.0

            telemetry_rows = overshoot_to_telemetry_rows(rec, time_sec)
            event_rows = overshoot_to_event_rows(rec, self._last_rec, time_sec)

            with open(self._telemetry_path, "a", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=TELEMETRY_FIELDS)
                w.writerows(telemetry_rows)

            if event_rows:
                with open(self._events_path, "a", newline="", encoding="utf-8") as f:
                    w = csv.DictWriter(f, fieldnames=EVENTS_FIELDS)
                    w.writerows(event_rows)

            self._last_rec = rec
            self._current_time_sec = time_sec

        return {"ingested": len(parsed), "time_sec": self._current_time_sec}

    def get_telemetry_at(self, time_sec: float) -> list[TelemetryPoint]:
        """
        Return telemetry at or before time_sec: for each tag_id, the latest row with time_sec <= time_sec.
        """
        if not self._telemetry_path.exists():
            return []

        by_tag: dict[str, dict] = {}
        with open(self._telemetry_path, "r", encoding="utf-8") as f:
            r = csv.DictReader(f)
            for row in r:
                try:
                    t = float(row.get("time_sec", 0))
                except (ValueError, TypeError):
                    continue
                if t > time_sec:
                    continue
                tag = row.get("tag_id", "")
                if not tag:
                    continue
                if tag not in by_tag or t >= float(by_tag[tag].get("time_sec", -1)):
                    by_tag[tag] = row

        out: list[TelemetryPoint] = []
        for row in by_tag.values():
            ts = row.get("timestamp", "")
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except Exception:
                dt = datetime.now(timezone.utc)
            try:
                val = float(row.get("value", 0))
            except (ValueError, TypeError):
                val = None
            out.append(
                TelemetryPoint(
                    tag_id=row.get("tag_id", ""),
                    timestamp=dt,
                    value=val,
                    quality=QualityFlag.GOOD,
                )
            )
        return out

    def get_telemetry_range(
        self,
        start_sec: float,
        end_sec: float,
    ) -> dict[str, list[dict]]:
        """Return { tag_id: [ {timestamp, value, quality}, ... ] } for time_sec in [start_sec, end_sec]."""
        if not self._telemetry_path.exists():
            return {}

        result: dict[str, list[dict]] = {}
        with open(self._telemetry_path, "r", encoding="utf-8") as f:
            r = csv.DictReader(f)
            for row in r:
                try:
                    t = float(row.get("time_sec", 0))
                except (ValueError, TypeError):
                    continue
                if not (start_sec <= t <= end_sec):
                    continue
                tag = row.get("tag_id", "")
                if tag not in result:
                    result[tag] = []
                result[tag].append({
                    "timestamp": row.get("timestamp", ""),
                    "value": float(row["value"]) if row.get("value") not in ("", None) else None,
                    "quality": row.get("quality", "Good"),
                })
        for tag in result:
            result[tag].sort(key=lambda x: x["timestamp"])
        return result

    def get_current_state(self) -> dict | None:
        """State compatible with ScenarioState for simulation API (is_running, scenario_id, current_time_sec, etc.)."""
        if not self._running:
            return None
        return {
            "scenario_id": "video_disaster",
            "is_running": self._running,
            "current_time_sec": self._current_time_sec,
            "is_paused": False,
            "active_failures": [],
            "completed_failures": [],
        }

    def advance_time(self, delta_sec: float) -> None:
        """Advance current_time_sec for replay/scrub."""
        self._current_time_sec = max(0.0, self._current_time_sec + delta_sec)

    def get_scenario_timeline(self) -> list[dict]:
        """Events from the events CSV as a timeline (for replay/forensic)."""
        if not self._events_path.exists():
            return []
        out: list[dict] = []
        with open(self._events_path, "r", encoding="utf-8") as f:
            r = csv.DictReader(f)
            for row in r:
                try:
                    t = float(row.get("time_sec", 0))
                except (ValueError, TypeError):
                    t = 0.0
                out.append({
                    "event_id": f"overshoot_{len(out)}",
                    "event_type": row.get("event_type", "overshoot_detection"),
                    "timestamp_sec": t,
                    "failure_type": "overshoot",
                    "tag_id": row.get("tag_id", ""),
                    "duration_sec": 0,
                    "severity": row.get("severity", "WARNING"),
                    "description": row.get("description", ""),
                })
        return sorted(out, key=lambda e: e["timestamp_sec"])
