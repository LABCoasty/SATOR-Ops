"""
Overshoot JSON → SATOR CSV converter.

Maps Overshoot.ai disaster-detection JSON (from RealtimeVision outputSchema)
into telemetry.csv and events.csv row formats for data ingest.
"""

from datetime import datetime, timezone

from app.models.overshoot import (
    OvershootDisasterRecord,
    SMOKE_LEVEL_MAP,
    STRUCTURAL_DAMAGE_MAP,
)

# Virtual sensor tag_ids for video-based disaster scenario
VIDEO_TAG_IDS = [
    "video_person_count",
    "video_water_level",
    "video_fire_detected",
    "video_smoke_level",
    "video_structural_damage",
    "video_injured_detected",
]

SENSOR_NAMES = {
    "video_person_count": "Video Person Count",
    "video_water_level": "Video Water Level",
    "video_fire_detected": "Video Fire Detected",
    "video_smoke_level": "Video Smoke Level",
    "video_structural_damage": "Video Structural Damage",
    "video_injured_detected": "Video Injured Detected",
}

UNITS = {
    "video_person_count": "count",
    "video_water_level": "%",
    "video_fire_detected": "bool",
    "video_smoke_level": "level",
    "video_structural_damage": "level",
    "video_injured_detected": "bool",
}


def _ts_to_iso(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def overshoot_to_telemetry_rows(rec: OvershootDisasterRecord, time_sec: float) -> list[dict]:
    """
    Convert one Overshoot record into telemetry CSV rows (one per virtual sensor).

    CSV columns: timestamp,tag_id,sensor_name,value,unit,quality,time_sec,redundancy_group
    """
    ts = _ts_to_iso(rec.timestamp_ms)
    smoke_val = SMOKE_LEVEL_MAP.get(rec.smoke_level.lower(), 0.0) if rec.smoke_level else 0.0
    damage_val = (
        STRUCTURAL_DAMAGE_MAP.get(rec.structural_damage.lower(), 0.0) if rec.structural_damage else 0.0
    )

    rows = [
        {
            "timestamp": ts,
            "tag_id": "video_person_count",
            "sensor_name": SENSOR_NAMES["video_person_count"],
            "value": float(rec.person_count),
            "unit": UNITS["video_person_count"],
            "quality": "Good",
            "time_sec": time_sec,
            "redundancy_group": "",
        },
        {
            "timestamp": ts,
            "tag_id": "video_water_level",
            "sensor_name": SENSOR_NAMES["video_water_level"],
            "value": float(rec.water_level),
            "unit": UNITS["video_water_level"],
            "quality": "Good",
            "time_sec": time_sec,
            "redundancy_group": "",
        },
        {
            "timestamp": ts,
            "tag_id": "video_fire_detected",
            "sensor_name": SENSOR_NAMES["video_fire_detected"],
            "value": 1.0 if rec.fire_detected else 0.0,
            "unit": UNITS["video_fire_detected"],
            "quality": "Good",
            "time_sec": time_sec,
            "redundancy_group": "",
        },
        {
            "timestamp": ts,
            "tag_id": "video_smoke_level",
            "sensor_name": SENSOR_NAMES["video_smoke_level"],
            "value": smoke_val,
            "unit": UNITS["video_smoke_level"],
            "quality": "Good",
            "time_sec": time_sec,
            "redundancy_group": "",
        },
        {
            "timestamp": ts,
            "tag_id": "video_structural_damage",
            "sensor_name": SENSOR_NAMES["video_structural_damage"],
            "value": damage_val,
            "unit": UNITS["video_structural_damage"],
            "quality": "Good",
            "time_sec": time_sec,
            "redundancy_group": "",
        },
        {
            "timestamp": ts,
            "tag_id": "video_injured_detected",
            "sensor_name": SENSOR_NAMES["video_injured_detected"],
            "value": 1.0 if rec.injured_detected else 0.0,
            "unit": UNITS["video_injured_detected"],
            "quality": "Good",
            "time_sec": time_sec,
            "redundancy_group": "",
        },
    ]
    return rows


def overshoot_to_event_rows(
    rec: OvershootDisasterRecord,
    prev: OvershootDisasterRecord | None,
    time_sec: float,
) -> list[dict]:
    """
    Emit events when alarming conditions appear or escalate.

    CSV columns: timestamp,time_sec,event_type,severity,tag_id,reason_code,description,action_required
    """
    ts = _ts_to_iso(rec.timestamp_ms)
    events: list[dict] = []

    def ev(etype: str, sev: str, tag: str, desc: str, action: bool = True) -> None:
        events.append({
            "timestamp": ts,
            "time_sec": time_sec,
            "event_type": etype,
            "severity": sev,
            "tag_id": tag,
            "reason_code": "",
            "description": desc,
            "action_required": str(action).lower(),
        })

    # Fire just detected
    if rec.fire_detected and (prev is None or not prev.fire_detected):
        ev("overshoot_detection", "CRITICAL", "video_fire_detected", "Fire detected in video frame", True)

    # Injured detected
    if rec.injured_detected and (prev is None or not prev.injured_detected):
        ev("overshoot_detection", "ALARM", "video_injured_detected", "Injured person(s) detected in frame", True)

    # Smoke elevated
    if rec.smoke_level and rec.smoke_level.lower() in ("medium", "dense"):
        if prev is None or prev.smoke_level is None or prev.smoke_level.lower() not in ("medium", "dense"):
            ev("overshoot_detection", "WARNING", "video_smoke_level", f"Smoke level elevated: {rec.smoke_level}", True)

    # Severe structural damage
    if rec.structural_damage and rec.structural_damage.lower() == "severe":
        if prev is None or prev.structural_damage is None or prev.structural_damage.lower() != "severe":
            ev(
                "overshoot_detection",
                "CRITICAL",
                "video_structural_damage",
                "Severe structural damage detected",
                True,
            )

    # Water level high (e.g. > 50)
    if rec.water_level >= 50.0 and (prev is None or prev.water_level < 50.0):
        ev("overshoot_detection", "WARNING", "video_water_level", f"Water level elevated: {rec.water_level}%", True)

    return events


def get_video_sensor_csv_rows() -> list[dict]:
    """
    Static sensor definitions for video virtual sensors (sensors.csv format).

    Columns: tag_id,name,unit,location,manufacturer,model,calibration_date,
             baseline_value,min_value,max_value,max_roc,redundancy_group,physics_relationships
    """
    return [
        {
            "tag_id": "video_person_count",
            "name": SENSOR_NAMES["video_person_count"],
            "unit": "count",
            "location": "Video feed",
            "manufacturer": "Overshoot.ai",
            "model": "RealtimeVision",
            "calibration_date": "",
            "baseline_value": 0.0,
            "min_value": 0.0,
            "max_value": 500.0,
            "max_roc": 50.0,
            "redundancy_group": "",
            "physics_relationships": "",
        },
        {
            "tag_id": "video_water_level",
            "name": SENSOR_NAMES["video_water_level"],
            "unit": "%",
            "location": "Video feed",
            "manufacturer": "Overshoot.ai",
            "model": "RealtimeVision",
            "calibration_date": "",
            "baseline_value": 0.0,
            "min_value": 0.0,
            "max_value": 100.0,
            "max_roc": 20.0,
            "redundancy_group": "",
            "physics_relationships": "",
        },
        {
            "tag_id": "video_fire_detected",
            "name": SENSOR_NAMES["video_fire_detected"],
            "unit": "bool",
            "location": "Video feed",
            "manufacturer": "Overshoot.ai",
            "model": "RealtimeVision",
            "calibration_date": "",
            "baseline_value": 0.0,
            "min_value": 0.0,
            "max_value": 1.0,
            "max_roc": 1.0,
            "redundancy_group": "",
            "physics_relationships": "",
        },
        {
            "tag_id": "video_smoke_level",
            "name": SENSOR_NAMES["video_smoke_level"],
            "unit": "level",
            "location": "Video feed",
            "manufacturer": "Overshoot.ai",
            "model": "RealtimeVision",
            "calibration_date": "",
            "baseline_value": 0.0,
            "min_value": 0.0,
            "max_value": 3.0,
            "max_roc": 1.0,
            "redundancy_group": "",
            "physics_relationships": "",
        },
        {
            "tag_id": "video_structural_damage",
            "name": SENSOR_NAMES["video_structural_damage"],
            "unit": "level",
            "location": "Video feed",
            "manufacturer": "Overshoot.ai",
            "model": "RealtimeVision",
            "calibration_date": "",
            "baseline_value": 0.0,
            "min_value": 0.0,
            "max_value": 2.0,
            "max_roc": 1.0,
            "redundancy_group": "",
            "physics_relationships": "",
        },
        {
            "tag_id": "video_injured_detected",
            "name": SENSOR_NAMES["video_injured_detected"],
            "unit": "bool",
            "location": "Video feed",
            "manufacturer": "Overshoot.ai",
            "model": "RealtimeVision",
            "calibration_date": "",
            "baseline_value": 0.0,
            "min_value": 0.0,
            "max_value": 1.0,
            "max_roc": 1.0,
            "redundancy_group": "",
            "physics_relationships": "",
        },
    ]
