# Replay & Temporal Reasoning API Documentation

## Overview
The backend provides two API modules for temporal features:

1. **Replay Engine** (`/api/replay/*`) - Historical timeline reconstruction
2. **Temporal Reasoning** (`/api/temporal/*`) - Trust evolution & contradiction analysis

---

## 🕐 Replay Engine APIs

### GET `/api/replay/bounds`
Get incident time boundaries.

**Response:**
```json
{
  "start": "2026-01-14T10:00:00",
  "end": "2026-01-14T10:03:00",
  "duration_sec": 180
}
```

---

### GET `/api/replay/markers`
Get timeline markers for Event Timeline scrubber.

**Query Params:**
- `start` (optional): ISO timestamp
- `end` (optional): ISO timestamp  
- `zoom` (optional): 1=full, 2=minutes, 3=seconds

**Response:**
```json
[
  {
    "timestamp": "2026-01-14T10:00:00",
    "time_sec": 0,
    "event_type": "sensor_event",
    "marker_type": "snap_point",
    "label": "System online - normal operation",
    "severity": "info",
    "tag_id": "pressure_sensor_a",
    "reason_code": null,
    "description": "System online - normal operation",
    "requires_action": false
  }
]
```

---

### GET `/api/replay/state-at?t={timestamp}`
Get complete system state at any point in time.

**Query Params:**
- `t` (required): ISO timestamp (e.g., `2026-01-14T10:01:00`)

**Response:**
```json
{
  "timestamp": "2026-01-14T10:01:00",
  "time_sec": 60,
  "claim": "Possible sensor discrepancy under investigation",
  "confirmation_status": "conflicting",
  "confidence": "medium",
  "posture": "verify",
  "posture_reason": "Contradiction detected - verification needed",
  "action_gating": "limited",
  "allowed_actions": ["defer", "investigate"],
  "mode": "decision",
  "trust_snapshot": {
    "zone_trust_state": "degraded",
    "zone_confidence": "medium",
    "sensors": {
      "pressure_sensor_a": {
        "tag_id": "pressure_sensor_a",
        "trust_score": 0.5,
        "trust_state": "degraded",
        "reason_codes": ["RC10"]
      }
    }
  },
  "contradictions": [
    {
      "contradiction_id": "c1",
      "timestamp": "2026-01-14T10:00:30",
      "primary_tag_id": "pressure_sensor_a",
      "reason_code": "RC10",
      "description": "Redundant sensor mismatch"
    }
  ],
  "operator_history": [],
  "receipt_status": {
    "exists": false,
    "label": "No receipt"
  }
}
```

---

### GET `/api/replay/confidence-band`
Get confidence ribbon data for timeline background.

**Response:**
```json
[
  {
    "timestamp": "2026-01-14T10:00:00",
    "time_sec": 0,
    "confidence": "high",
    "value": 0.9
  }
]
```

---

## 🧠 Temporal Reasoning APIs

### GET `/api/temporal/summary`
Get summary statistics.

**Response:**
```json
{
  "total_trust_updates": 1455,
  "total_contradictions": 10,
  "total_receipts": 5,
  "total_audit_events": 110,
  "unique_sensors": 3,
  "unique_reason_codes": 2,
  "unique_chains": 5,
  "csv_events": 12,
  "csv_claims": 3,
  "csv_zone_states": 3
}
```

---

### GET `/api/temporal/trust-evolution/{tag_id}`
Get trust evolution analysis for a specific sensor.

**Path Params:**
- `tag_id`: Sensor ID (e.g., `pressure_sensor_a`)

**Response:**
```json
{
  "tag_id": "pressure_sensor_a",
  "start_score": 1.0,
  "end_score": 0.0,
  "total_degradation": 1.0,
  "degradation_rate": 0.0167,
  "time_to_quarantine": 2.0,
  "significant_drops": [
    {
      "time_sec": 30,
      "trust_score": 0.5,
      "trust_state": "degraded",
      "reason_codes": ["RC10"],
      "delta": -0.5
    }
  ],
  "evolution_curve": [
    {"time_sec": 0, "trust_score": 1.0, "trust_state": "trusted"},
    {"time_sec": 30, "trust_score": 0.5, "trust_state": "degraded"}
  ]
}
```

---

### GET `/api/temporal/contradiction-patterns`
Get contradiction pattern analysis.

**Response:**
```json
[
  {
    "reason_code": "RC10",
    "count": 5,
    "first_occurrence_sec": 30,
    "affected_sensors": ["pressure_sensor_a", "pressure_sensor_b"],
    "average_gap_sec": 10.5,
    "cascading": false
  },
  {
    "reason_code": "RC11",
    "count": 5,
    "first_occurrence_sec": 60,
    "affected_sensors": ["valve_position", "flow_meter"],
    "average_gap_sec": 12.0,
    "cascading": false
  }
]
```

---

### GET `/api/temporal/audit-chains`
Get audit chain verification results.

**Response:**
```json
[
  {
    "chain_id": "dd707c4d-...",
    "run_id": "87029089-...",
    "total_events": 22,
    "is_valid": true,
    "broken_links_count": 0,
    "first_event_time": "2026-01-12T18:11:07",
    "last_event_time": "2026-01-12T18:11:49"
  }
]
```

---

### GET `/api/temporal/decision-provenance`
Get decision provenance (evidence chain).

**Query Params:**
- `receipt_id` (optional): Specific receipt ID
- `time_sec` (optional): Filter by time

**Response:**
```json
[
  {
    "receipt": {
      "id": "204335de-...",
      "time_sec": 0,
      "action": "defer",
      "rationale": "Cannot trust sensor data...",
      "content_hash": "397fb3c9..."
    },
    "contradictions": [...],
    "trust_degradation": [...]
  }
]
```

---

## 🔌 Frontend Integration Guide

### For Event Timeline (TimelineScrubber)
```javascript
// 1. Get bounds first
const bounds = await fetch('/api/replay/bounds').then(r => r.json())

// 2. Get markers for timeline
const markers = await fetch('/api/replay/markers').then(r => r.json())

// 3. When user clicks a marker, fetch state
const state = await fetch(`/api/replay/state-at?t=${timestamp}`).then(r => r.json())
```

### For Trust Breakdown Panel
```javascript
// Get trust evolution for the main sensor
const evolution = await fetch('/api/temporal/trust-evolution/pressure_sensor_a').then(r => r.json())

// Use evolution.end_score for COMPOSITE TRUST SCORE
// Use evolution.time_to_quarantine for "Time to quarantine"
// Use evolution.significant_drops for Contributing Factors
```

### For Detected Contradictions Panel
```javascript
// Get contradiction patterns
const patterns = await fetch('/api/temporal/contradiction-patterns').then(r => r.json())

// Each pattern has: reason_code, count, affected_sensors, cascading
```

### For Temporal Analysis Stats
```javascript
// Get summary
const summary = await fetch('/api/temporal/summary').then(r => r.json())

// Display: total_trust_updates, total_contradictions, total_audit_events, total_receipts
```

---

## 🚀 Running the Backend

```bash
cd apps/backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

API docs available at: http://localhost:8000/docs
