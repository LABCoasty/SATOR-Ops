"""
Seed data for SATOR-Ops development and demos.

Provides realistic telemetry, evidence, and decision data.
"""

from datetime import datetime, timedelta
from typing import List
import random


def get_current_time():
    return datetime.utcnow()


# Telemetry Channels with realistic data
def generate_telemetry_channels() -> List[dict]:
    """Generate current telemetry channel data."""
    now = get_current_time()
    
    channels = [
        {
            "id": "temp_01",
            "name": "Core Temperature",
            "source": "primary_sensor_array",
            "value": 72.4 + random.uniform(-0.5, 0.5),
            "unit": "°C",
            "trend": "up",
            "status": "normal",
            "sparkline": [68, 69, 70, 71, 70, 72, 72.4],
            "summary": "Operating within normal parameters. Slight upward trend over the last hour.",
            "min_threshold": 60.0,
            "max_threshold": 85.0,
            "timestamp": now.isoformat(),
        },
        {
            "id": "pressure_01",
            "name": "System Pressure",
            "source": "primary_sensor_array",
            "value": 14.7 + random.uniform(-0.1, 0.1),
            "unit": "PSI",
            "trend": "stable",
            "status": "normal",
            "sparkline": [14.6, 14.7, 14.7, 14.8, 14.7, 14.7, 14.7],
            "summary": "Stable pressure reading. No anomalies detected.",
            "min_threshold": 12.0,
            "max_threshold": 18.0,
            "timestamp": now.isoformat(),
        },
        {
            "id": "flow_01",
            "name": "Flow Rate A",
            "source": "external_feed_alpha",
            "value": 234 + random.uniform(-5, 5),
            "unit": "L/min",
            "trend": "down",
            "status": "warning",
            "sparkline": [250, 248, 245, 240, 238, 236, 234],
            "summary": "Declining flow rate detected. May indicate partial blockage or pump degradation.",
            "min_threshold": 200.0,
            "max_threshold": 300.0,
            "timestamp": now.isoformat(),
        },
        {
            "id": "flow_02",
            "name": "Flow Rate B",
            "source": "external_feed_beta",
            "value": 248 + random.uniform(-3, 3),
            "unit": "L/min",
            "trend": "down",
            "status": "normal",
            "sparkline": [252, 250, 249, 248, 248, 248, 248],
            "summary": "Secondary flow sensor showing slightly higher values than primary.",
            "min_threshold": 200.0,
            "max_threshold": 300.0,
            "timestamp": now.isoformat(),
        },
        {
            "id": "vibration_01",
            "name": "Vibration Sensor",
            "source": "backup_telemetry",
            "value": 0.42 + random.uniform(-0.02, 0.02),
            "unit": "mm/s",
            "trend": "up",
            "status": "warning",
            "sparkline": [0.35, 0.36, 0.38, 0.39, 0.4, 0.41, 0.42],
            "summary": "Vibration levels increasing. Approaching upper threshold.",
            "min_threshold": 0.0,
            "max_threshold": 0.5,
            "timestamp": now.isoformat(),
        },
        {
            "id": "power_01",
            "name": "Power Draw",
            "source": "primary_sensor_array",
            "value": 847 + random.uniform(-10, 10),
            "unit": "kW",
            "trend": "stable",
            "status": "normal",
            "sparkline": [845, 846, 848, 847, 846, 847, 847],
            "summary": "Consistent power consumption. Operating efficiently.",
            "min_threshold": 700.0,
            "max_threshold": 1000.0,
            "timestamp": now.isoformat(),
        },
        {
            "id": "humidity_01",
            "name": "Ambient Humidity",
            "source": "backup_telemetry",
            "value": 45 + random.uniform(-2, 2),
            "unit": "%",
            "trend": "down",
            "status": "normal",
            "sparkline": [52, 50, 48, 47, 46, 45, 45],
            "summary": "Humidity decreasing. Within acceptable range for operations.",
            "min_threshold": 30.0,
            "max_threshold": 70.0,
            "timestamp": now.isoformat(),
        },
    ]
    
    # Update status based on thresholds
    for channel in channels:
        value = channel["value"]
        min_t = channel["min_threshold"]
        max_t = channel["max_threshold"]
        
        # Calculate how close to threshold
        if value < min_t or value > max_t:
            channel["status"] = "critical"
        elif value < min_t + (max_t - min_t) * 0.15 or value > max_t - (max_t - min_t) * 0.15:
            channel["status"] = "warning"
    
    return channels


# Data Sources with reliability scores
DATA_SOURCES = [
    {
        "id": "s1",
        "name": "Primary Sensor Array",
        "reliability": 0.98,
        "last_update": "2s ago",
        "status": "online",
        "type": "internal",
    },
    {
        "id": "s2",
        "name": "Backup Telemetry",
        "reliability": 0.95,
        "last_update": "5s ago",
        "status": "online",
        "type": "internal",
    },
    {
        "id": "s3",
        "name": "External Feed Alpha",
        "reliability": 0.87,
        "last_update": "12s ago",
        "status": "online",
        "type": "external",
    },
    {
        "id": "s4",
        "name": "External Feed Beta",
        "reliability": 0.72,
        "last_update": "45s ago",
        "status": "degraded",
        "type": "external",
    },
    {
        "id": "s5",
        "name": "Legacy System Link",
        "reliability": 0.65,
        "last_update": "2m ago",
        "status": "degraded",
        "type": "legacy",
    },
    {
        "id": "s6",
        "name": "Remote Station C",
        "reliability": 0.0,
        "last_update": "15m ago",
        "status": "offline",
        "type": "remote",
    },
]


# Evidence items
def generate_evidence() -> List[dict]:
    """Generate evidence items for trust calculation."""
    now = get_current_time()
    
    return [
        {
            "id": "ev_001",
            "type": "sensor",
            "source": "Primary Sensor Array",
            "value": {"metric": "temperature", "reading": 72.4, "unit": "°C"},
            "timestamp": (now - timedelta(seconds=2)).isoformat(),
            "trust_level": "high",
            "trust_score": 0.98,
        },
        {
            "id": "ev_002",
            "type": "sensor",
            "source": "Backup Telemetry",
            "value": {"metric": "temperature", "reading": 72.1, "unit": "°C"},
            "timestamp": (now - timedelta(seconds=5)).isoformat(),
            "trust_level": "high",
            "trust_score": 0.95,
        },
        {
            "id": "ev_003",
            "type": "sensor",
            "source": "External Feed Alpha",
            "value": {"metric": "pressure", "reading": 14.7, "unit": "PSI"},
            "timestamp": (now - timedelta(seconds=8)).isoformat(),
            "trust_level": "high",
            "trust_score": 0.87,
        },
        {
            "id": "ev_004",
            "type": "sensor",
            "source": "Power Monitor",
            "value": {"metric": "power", "reading": 847, "unit": "kW"},
            "timestamp": (now - timedelta(seconds=1)).isoformat(),
            "trust_level": "high",
            "trust_score": 0.92,
        },
        {
            "id": "ev_005",
            "type": "sensor",
            "source": "Vibration Sensor",
            "value": {"metric": "vibration", "reading": 0.42, "unit": "mm/s"},
            "timestamp": (now - timedelta(seconds=3)).isoformat(),
            "trust_level": "medium",
            "trust_score": 0.89,
        },
    ]


# Contradictions/Conflicts
CONTRADICTIONS = [
    {
        "id": "c1",
        "sources": ["Flow Sensor A", "Flow Sensor B"],
        "values": ["234 L/min", "248 L/min"],
        "severity": "medium",
        "resolution": "Using weighted average (0.87/0.72). Sensor B calibration pending.",
    },
    {
        "id": "c2",
        "sources": ["External Feed Alpha", "External Feed Beta"],
        "values": ["Clear conditions", "Light precipitation"],
        "severity": "low",
        "resolution": "Feed Beta update delayed. Using Alpha (higher reliability).",
    },
]


# Timeline Events
def generate_timeline_events() -> List[dict]:
    """Generate timeline events for the decision scrubber."""
    now = get_current_time()
    base_time = now - timedelta(minutes=13)
    
    return [
        {
            "time": (base_time).strftime("%H:%M:%S"),
            "timestamp": 0,
            "label": "Baseline",
            "trust_score": 0.94,
            "has_contradiction": False,
            "description": "Initial assessment started. All systems nominal.",
        },
        {
            "time": (base_time + timedelta(minutes=2, seconds=15)).strftime("%H:%M:%S"),
            "timestamp": 1,
            "label": "Anomaly detected",
            "trust_score": 0.88,
            "has_contradiction": False,
            "description": "Flow rate deviation observed in primary sensor.",
        },
        {
            "time": (base_time + timedelta(minutes=4, seconds=42)).strftime("%H:%M:%S"),
            "timestamp": 2,
            "label": "Sensor conflict",
            "trust_score": 0.71,
            "has_contradiction": True,
            "description": "Flow Sensor A and B reporting divergent values.",
        },
        {
            "time": (base_time + timedelta(minutes=7, seconds=8)).strftime("%H:%M:%S"),
            "timestamp": 3,
            "label": "Manual override",
            "trust_score": 0.76,
            "has_contradiction": False,
            "description": "Operator acknowledged anomaly. Using weighted average.",
        },
        {
            "time": (base_time + timedelta(minutes=10, seconds=30)).strftime("%H:%M:%S"),
            "timestamp": 4,
            "label": "Stabilized",
            "trust_score": 0.87,
            "has_contradiction": False,
            "description": "System returned to normal operating parameters.",
        },
        {
            "time": now.strftime("%H:%M:%S"),
            "timestamp": 5,
            "label": "Current",
            "trust_score": 0.87,
            "has_contradiction": False,
            "description": "Ongoing monitoring. No new issues detected.",
        },
    ]


# Signal Summary
def generate_signal_summary() -> dict:
    """Generate signal summary statistics."""
    return {
        "active_signals": 47,
        "sources_reporting": 12,
        "healthy": 41,
        "warnings": 4,
        "critical": 0,
        "unknown": 2,
        "last_sync": "2s ago",
        "connected": True,
    }


# Trust Breakdown
TRUST_BREAKDOWN = {
    "composite_score": 0.87,
    "factors": [
        {"label": "Evidence Corroboration", "value": 0.92, "impact": "positive"},
        {"label": "Source Reliability Avg", "value": 0.86, "impact": "positive"},
        {"label": "Contradiction Penalty", "value": -0.08, "impact": "negative"},
        {"label": "Data Freshness", "value": 0.95, "impact": "positive"},
        {"label": "Unknown Factors", "value": -0.05, "impact": "negative"},
    ],
    "reason_codes": [
        {"code": "TR_0x12A", "description": "High sensor corroboration"},
        {"code": "TR_0x08B", "description": "Minor flow sensor divergence"},
        {"code": "TR_0x04C", "description": "External feed staleness"},
    ],
}
