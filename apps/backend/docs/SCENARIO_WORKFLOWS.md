# SATOR Ops Scenario Workflows

This document describes the two main scenario workflows in SATOR Ops.

---

## **Scenario 1: CSV/JSON Data → Decision Engine → Predefined Resolution**

**Purpose**: Process historical or pre-recorded data files through the decision engine to demonstrate predefined resolution paths.

### Flow

```
CSV/JSON data files → Data loader → Decision engine → Predefined resolution
```

### Components

1. **Data Loader** (`ReplayEngine`, `TemporalReasoningEngine`)
   - Loads data from `app/data/csv/` (telemetry.csv, events.csv, zone_states.csv, etc.)
   - Loads JSON from `app/data/generated/` (trust_updates.json, contradictions.json, etc.)

2. **Decision Engine** (`ReplayEngine.get_state_at_t()`)
   - Reconstructs system state at any timestamp
   - Calculates trust scores, contradictions, reason codes
   - Derives operational mode (OBSERVE → DECISION → REPLAY)

3. **Predefined Resolution**
   - Based on scenario specifications (e.g., "mismatched_valve", "stale_sensor_leak")
   - Resolution paths are deterministic based on the data files
   - Used for demos and forensic analysis

### API Endpoints

- `GET /replay/state?timestamp=<ISO8601>` - Get system state at time t
- `GET /simulation/scenarios` - List available scenarios
- `POST /simulation/start` with `{"scenario_id": "mismatched_valve"}` - Start predefined scenario
- `GET /simulation/telemetry?time_sec=<float>` - Get telemetry at time
- `GET /simulation/timeline` - Get event timeline

---

## **Scenario 2: Live Video → Overshoot → LeanMCP → Decision Cards**

**Purpose**: Real-time disaster detection using live video analysis, AI processing, and decision card generation.

### Flow

```
Live video → Overshoot.ai Vision → Vision JSON output → LeanMCP server
Server telemetry → LeanMCP server
LeanMCP server → AI predictions, contradiction detection, action recommendations → Decision cards
```

### Components

#### 1. **Live Video → Overshoot.ai Vision**

Frontend (JavaScript):
```javascript
import { RealtimeVision } from 'overshoot';

const vision = new RealtimeVision({
  apiUrl: 'https://cluster1.overshoot.ai/api/v0.2',
  apiKey: process.env.OVERSHOOT_API_KEY,
  prompt: 'Detect disaster: person count, water level 0-100, fire, smoke, structural damage, injured.',
  outputSchema: await fetch('/ingest/overshoot/schema').then(r => r.json()).then(d => d.outputSchema),
  onResult: async (result) => {
    const data = JSON.parse(result.result);
    // POST to Scenario 2 workflow
    await fetch('/scenario2/ingest-and-process', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        overshoot_data: data,
        server_telemetry: await getServerTelemetry(), // Optional
      }),
    });
  },
});
vision.start();
```

#### 2. **Overshoot JSON → LeanMCP Server**

The backend receives Overshoot JSON and optionally server telemetry:

- **Ingest**: Converts Overshoot JSON to telemetry CSV (via `VideoDisasterManager`)
- **Workflow**: Processes through `Scenario2Workflow` which uses LeanMCP tools

#### 3. **LeanMCP Server Analysis**

The workflow uses LeanMCP tools:
- `get_state_at_t` - Get system state to detect existing contradictions
- `explain_trust_score` - Check trust scores for video sensors
- `list_contradictions` - Find conflicts between video evidence and telemetry

#### 4. **Contradiction Detection**

Automatically detects conflicts:
- **RC11 (Physics Contradiction)**: Video shows fire but temperature sensor shows no heat rise
- **RC11**: High water level in video but low pressure sensor reading
- **RC10 (Redundancy Conflict)**: Video sensor conflicts with redundant server sensors

#### 5. **AI Predictions & Recommendations**

Generates:
- **Immediate risk level**: low / medium / high / critical
- **Escalation likelihood**: 0.0 - 1.0
- **Estimated impact**: Description of potential consequences
- **Action recommendations**: Prioritized list with timeboxes

Example recommendations:
```json
{
  "priority": "critical",
  "action": "dispatch_fire_team",
  "description": "Fire detected in video - dispatch emergency response immediately",
  "timebox_seconds": 60
}
```

#### 6. **Decision Cards**

Decision cards include:
- **ID**: Unique identifier
- **Mode**: `observe` | `decision` | `replay`
- **Allowed actions**: Based on urgency (`["act", "escalate"]` for critical, `["act", "escalate", "defer"]` for high priority)
- **Uncertainty score**: 0.0 (certain) to 1.0 (highly uncertain)
- **Timebox**: Auto-expires after N seconds
- **Contradictions**: List of detected sensor conflicts
- **Predictions**: Risk assessment and escalation likelihood
- **Recommendations**: Prioritized action list

### API Endpoints

#### Scenario 2 Workflow

| Method | Path | Description |
|--------|------|-------------|
| **POST** | `/scenario2/process` | Process Overshoot JSON + telemetry → decision card |
| **POST** | `/scenario2/ingest-and-process` | Combined: ingest to CSV + process workflow |

#### Request Example

```json
POST /scenario2/process
{
  "overshoot_data": {
    "timestamp_ms": 1700000000000,
    "person_count": 5,
    "water_level": 0.0,
    "fire_detected": true,
    "smoke_level": "dense",
    "structural_damage": "none",
    "injured_detected": false
  },
  "server_telemetry": {
    "temperature_sensor": 45.0,
    "pressure_sensor_a": 100.0
  }
}
```

#### Response Example

```json
{
  "decision_card": {
    "id": "dec_abc123",
    "mode": "decision",
    "allowed_actions": ["act", "escalate"],
    "uncertainty_score": 0.3,
    "timebox_seconds": 60,
    "summary": "🔥 Fire detected | ⚠️ 1 sensor contradiction(s) | Risk: CRITICAL"
  },
  "contradictions": [
    {
      "contradiction_id": "...",
      "reason_code": "RC11",
      "description": "Video shows fire but temperature sensor shows no heat rise",
      "primary_tag_id": "video_fire_detected",
      "secondary_tag_ids": ["temperature_sensor"]
    }
  ],
  "predictions": {
    "immediate_risk": "critical",
    "escalation_likelihood": 0.9,
    "estimated_impact": "high - potential structure loss"
  },
  "action_recommendations": [
    {
      "priority": "critical",
      "action": "dispatch_fire_team",
      "description": "Fire detected in video - dispatch emergency response immediately",
      "timebox_seconds": 60
    }
  ]
}
```

---

## **Comparison**

| Aspect | Scenario 1 | Scenario 2 |
|--------|-----------|------------|
| **Data Source** | CSV/JSON files | Live video (Overshoot) + telemetry |
| **Processing** | Deterministic replay | Real-time AI analysis |
| **Resolution** | Predefined scenarios | Dynamic decision cards |
| **Use Case** | Demos, forensic analysis | Live disaster monitoring |
| **Decision Engine** | ReplayEngine (state reconstruction) | Scenario2Workflow (AI + LeanMCP) |
| **Output** | Historical state snapshots | Real-time decision cards |

---

## **Integration Flow**

For a complete Scenario 2 implementation:

1. **Frontend**: Set up Overshoot RealtimeVision with disaster detection prompt
2. **Frontend**: On `onResult`, POST to `/scenario2/ingest-and-process`
3. **Backend**: Ingests to CSV (for historical tracking)
4. **Backend**: Processes through workflow → decision card
5. **Frontend**: Displays decision card in Decision Mode UI
6. **Frontend**: Operator selects action → POST to `/api/decisions/{id}/action`
7. **Backend**: Creates decision receipt → logs to audit ledger

---

## **Next Steps**

- Connect decision cards to the frontend Decision Mode UI
- Implement decision receipt generation on action selection
- Add LeanMCP tool handlers for advanced AI analysis
- Create Scenario 1 data loader UI for selecting CSV/JSON files
