# SATOR Ops

**Decision Infrastructure for Physical Systems**

SATOR is a decision infrastructure layer that formalizes how humans act in the physical world when telemetry can't be fully trusted — and makes those decisions defensible.

---

## Team Quick Reference

| What | Where |
|------|-------|
| Frontend code | `apps/web/` |
| Backend code | `apps/backend/` |
| Shared types | `packages/shared/` |
| API routes | `apps/backend/app/api/routes/` |
| Decision engine | `apps/backend/app/core/` |
| AI models | `apps/backend/app/ai/` |
| Sponsor integrations | `apps/backend/app/integrations/` |
| Dashboard pages | `apps/web/app/(dashboard)/` |
| UI components | `apps/web/components/` |
| Docker config | `infra/docker-compose.yml` |

---

## End-to-End Flow

SATOR supports two scenarios, both leading to **defensible artifact creation** with on-chain anchoring:

### Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SATOR OPS DECISION FLOW                           │
└─────────────────────────────────────────────────────────────────────────────┘

                    ┌──────────────────────────────────────┐
                    │         DATA INGEST LAYER            │
                    │    (Mode: data_ingest_display)       │
                    └──────────────────────────────────────┘
                                     │
            ┌────────────────────────┴────────────────────────┐
            │                                                  │
            ▼                                                  ▼
   ┌─────────────────┐                              ┌─────────────────┐
   │   SCENARIO 1    │                              │   SCENARIO 2    │
   │   Fixed Case    │                              │  Live Vision    │
   │ (Static CSV/JSON)│                              │  (Overshoot)    │
   └─────────────────┘                              └─────────────────┘
            │                                                  │
            │ Load telemetry,                      Receive vision JSON
            │ events, sensors                      via POST /vision/webhook
            │                                                  │
            ▼                                                  ▼
   ┌─────────────────┐                              ┌─────────────────┐
   │  DataLoader     │                              │ OvershootClient │
   │  Service        │                              │ + VisionFrame   │
   └─────────────────┘                              └─────────────────┘
            │                                                  │
            └────────────────────────┬─────────────────────────┘
                                     │
                                     ▼
                    ┌──────────────────────────────────────┐
                    │       CONTRADICTION DETECTION        │
                    │   (LeanMCP: detect_contradictions)   │
                    │                                      │
                    │  • Cross-validate vision vs sensors  │
                    │  • Check redundancy conflicts (RC10) │
                    │  • Check physics violations (RC11)   │
                    │  • Calculate trust scores            │
                    └──────────────────────────────────────┘
                                     │
                                     │ Contradiction detected?
                                     │
                                     ▼
                    ┌──────────────────────────────────────┐
                    │         INCIDENT CREATION            │
                    │      State: MONITORING → OPEN        │
                    │                                      │
                    │  • Create incident record            │
                    │  • Log to audit trail (hash chain)   │
                    │  • Auto-switch mode to "decision"    │
                    └──────────────────────────────────────┘
                                     │
                                     ▼
                    ┌──────────────────────────────────────┐
                    │       DECISION / TRUST LAYER         │
                    │        (Mode: decision_trust)        │
                    └──────────────────────────────────────┘
                                     │
                                     ▼
                    ┌──────────────────────────────────────┐
                    │       GENERATE DECISION CARD         │
                    │   (LeanMCP: create_decision_card)    │
                    │                                      │
                    │  • Title & summary                   │
                    │  • Trust score & reason codes        │
                    │  • Predictions (predict_issues)      │
                    │  • Recommendations (recommend_action)│
                    │  • Bounded action set                │
                    └──────────────────────────────────────┘
                                     │
                                     ▼
                    ┌──────────────────────────────────────┐
                    │      OPERATOR QUESTIONNAIRE          │
                    │                                      │
                    │  System asks targeted questions:     │
                    │  • Visual verification               │
                    │  • Sensor trust assessment           │
                    │  • Contradiction resolution          │
                    │  • Safety checklist                  │
                    │                                      │
                    │  Operator answers → trust adjusted   │
                    └──────────────────────────────────────┘
                                     │
                                     ▼
                    ┌──────────────────────────────────────┐
                    │        OPERATOR ACTION               │
                    │                                      │
                    │  Bounded action choices:             │
                    │  ┌─────────────────────────────────┐ │
                    │  │ ACT: Proceed with control action│ │
                    │  │ DEFER: Request field inspection │ │
                    │  │ ESCALATE: Transfer to supervisor│ │
                    │  └─────────────────────────────────┘ │
                    │                                      │
                    │  State: OPEN → TRIAGED → DISPATCHED  │
                    └──────────────────────────────────────┘
                                     │
                                     ▼
                    ┌──────────────────────────────────────┐
                    │         INCIDENT CLOSURE             │
                    │      State: DISPATCHED → CLOSED      │
                    │                                      │
                    │  • Resolution summary                │
                    │  • Generate final trust receipt      │
                    │  • Auto-switch mode to "artifact"    │
                    └──────────────────────────────────────┘
                                     │
                                     ▼
                    ┌──────────────────────────────────────┐
                    │     ARTIFACT CREATION LAYER          │
                    │     (Mode: artifact_creation)        │
                    └──────────────────────────────────────┘
                                     │
                                     ▼
                    ┌──────────────────────────────────────┐
                    │       BUILD ARTIFACT PACKET          │
                    │                                      │
                    │  Contains:                           │
                    │  • Incident summary & timeline       │
                    │  • Telemetry samples                 │
                    │  • Vision frames (if Scenario 2)     │
                    │  • Contradictions detected           │
                    │  • Trust receipts (hash-chained)     │
                    │  • Decision card & action taken      │
                    │  • Operator Q&A (questions/answers)  │
                    │  • Full audit trail (hash-chained)   │
                    │  • Content SHA256 hash               │
                    └──────────────────────────────────────┘
                                     │
                                     ▼
                    ┌──────────────────────────────────────┐
                    │      ON-CHAIN ANCHOR (KairoAISec)    │
                    │                                      │
                    │  Writes to blockchain:               │
                    │  • Artifact hash (NOT raw data)      │
                    │  • Timestamp                         │
                    │  • Trust score                       │
                    │  • Issuer                            │
                    │                                      │
                    │  Returns:                            │
                    │  • TX hash                           │
                    │  • Block number                      │
                    │  • Verification URL                  │
                    └──────────────────────────────────────┘
                                     │
                                     ▼
                    ┌──────────────────────────────────────┐
                    │       INTEGRITY VERIFICATION         │
                    │                                      │
                    │  ✓ Content hash matches              │
                    │  ✓ Audit chain valid                 │
                    │  ✓ On-chain anchor verified          │
                    │                                      │
                    │  → DEFENSIBLE DECISION ARTIFACT      │
                    └──────────────────────────────────────┘
```

---

## Incident Lifecycle State Machine

```
┌───────────────┐
│  MONITORING   │ ◄─── Normal operation, no active incident
└───────┬───────┘
        │ Contradiction detected
        ▼
┌───────────────┐
│     OPEN      │ ◄─── Incident created, awaiting triage
└───────┬───────┘
        │ Operator reviews & assesses
        ▼
┌───────────────┐
│    TRIAGED    │ ◄─── Initial assessment complete
└───────┬───────┘
        │ Action dispatched (ACT/DEFER/ESCALATE)
        ▼
┌───────────────┐
│  DISPATCHED   │ ◄─── Action in progress
└───────┬───────┘
        │ Resolution confirmed
        ▼
┌───────────────┐
│    CLOSED     │ ◄─── Artifact created & anchored
└───────────────┘
```

---

## UI Mode Auto-Switch Rules

| Trigger | From Mode | To Mode |
|---------|-----------|---------|
| Contradiction detected | `data_ingest` | `decision` |
| All questions answered | `decision` | `decision` (same) |
| Action confirmed | `decision` | `artifact` |
| Artifact anchored | `artifact` | `data_ingest` |
| Incident closed | `decision` | `artifact` |

---

## Operator Questionnaire System

The system asks **targeted questions** based on incident context. Operator answers **update trust scores** and inform recommendations.

### Question Types

| Type | Description | Example |
|------|-------------|---------|
| `visual_verification` | Confirm sensor readings visually | "Can you see the valve position?" |
| `sensor_trust` | Rate confidence in sensor (1-5) | "How much do you trust PT-001?" |
| `contradiction_resolution` | Choose which sensor to trust | "Sensor A says X, Sensor B says Y. Which is correct?" |
| `safety_check` | Confirm safety conditions | "Is the area clear? PPE worn?" |
| `action_confirmation` | Confirm understanding of action | "You are about to... Confirm?" |

### Answer Impact

```python
# Example: Operator confirms vision contradicts sensor
answer = "contradicts"
impact = {
    "trust_adjustment": -0.4,  # Decreases sensor trust
    "triggers_action": "flag_sensor_fault",
    "explanation": "Operator visual verification confirms sensor fault"
}
```

---

## LeanMCP Tool Reference

SATOR exposes 5 MCP-compliant decision tools:

| Tool | Purpose | Input | Output |
|------|---------|-------|--------|
| `analyze_vision` | Extract insights from Overshoot frame | VisionFrame | Equipment states, insights, summary |
| `detect_contradictions` | Cross-validate vision vs telemetry | VisionFrame + Telemetry | List of contradictions with reason codes |
| `predict_issues` | Predict problems before they occur | VisionFrame + Telemetry + History | Predictions with confidence |
| `recommend_action` | Generate bounded recommendations | Incident state + Evidence + Trust | Recommended action + alternatives |
| `create_decision_card` | Package findings for operator | Incident ID + Findings | Complete decision card |

### Reason Codes

| Code | Description |
|------|-------------|
| `RC10` | Redundancy conflict - sensors that should agree don't |
| `RC11` | Physics violation - impossible state (e.g., flow with closed valve) |
| `RC12` | Vision mismatch - visual observation differs from sensor |
| `RC13` | Calibration drift - sensor trending away from baseline |

---

## Data Schemas

### Trust Receipt
```json
{
  "receipt_id": "uuid",
  "incident_id": "uuid",
  "generated_at": "2024-01-17T12:00:00Z",
  "overall_trust_score": 0.42,
  "trust_level": "low",
  "sensor_scores": {"PT-001": 0.8, "VALVE-101": 0.3},
  "reason_codes": ["RC10", "RC11"],
  "contradictions_count": 2,
  "vision_validated": true,
  "questions_asked": 5,
  "questions_answered": 4,
  "operator_trust_adjustments": -0.15,
  "content_hash": "sha256:...",
  "previous_receipt_hash": "sha256:..."
}
```

### Artifact Packet
```json
{
  "artifact_id": "uuid",
  "incident_id": "uuid",
  "scenario_id": "fixed-valve-incident",
  "created_at": "2024-01-17T12:05:00Z",
  "title": "Sensor Contradiction Detected",
  "incident_summary": "...",
  "resolution_summary": "Deferred to field inspection",
  "incident_opened_at": "...",
  "incident_closed_at": "...",
  "total_duration_seconds": 180.0,
  "telemetry_samples": [...],
  "vision_frames": [...],
  "contradictions": [...],
  "final_trust_receipt": {...},
  "trust_history": [...],
  "decision_card": {...},
  "action_taken": "defer",
  "action_rationale": "...",
  "operator_id": "operator-001",
  "questions_asked": [...],
  "questions_answered": [...],
  "audit_trail": [...],
  "audit_chain_valid": true,
  "content_hash": "sha256:...",
  "on_chain_anchor": {
    "tx_hash": "0x...",
    "block_number": 12345678,
    "chain": "solana",
    "verification_url": "https://explorer.solana.com/tx/..."
  }
}
```

---

## API Endpoints

### Scenarios
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/scenarios` | List available scenarios |
| GET | `/api/scenarios/{id}` | Get scenario details |
| POST | `/api/scenarios/{id}/start` | Start scenario simulation |
| POST | `/api/scenarios/{id}/stop` | Stop scenario |

### Incidents
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/incidents` | List incidents |
| GET | `/api/incidents/{id}` | Get incident details + questions |
| POST | `/api/incidents/{id}/triage` | Triage incident |
| POST | `/api/incidents/{id}/dispatch` | Dispatch action |
| POST | `/api/incidents/{id}/close` | Close & create artifact |
| POST | `/api/incidents/{id}/questions/{qid}/answer` | Answer question |

### Vision (Overshoot)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/vision/webhook` | Receive Overshoot JSON |
| GET | `/api/vision/latest` | Get latest vision frame |
| POST | `/api/vision/simulate` | Simulate vision for demo |

### Artifacts
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/artifacts` | List artifacts |
| GET | `/api/artifacts/{id}` | Get full artifact |
| POST | `/api/artifacts/{id}/anchor` | Anchor on-chain |
| GET | `/api/artifacts/{id}/verify` | Verify integrity |
| GET | `/api/artifacts/{id}/export` | Export as JSON |

### WebSocket Events
| Event | Channel | Description |
|-------|---------|-------------|
| `vision_frame` | `vision` | New Overshoot frame |
| `contradiction_detected` | `contradictions` | Contradiction found |
| `prediction_alert` | `predictions` | Issue predicted |
| `decision_card_created` | `decisions` | New decision card |
| `trust_updated` | `trust` | Trust score changed |
| `incident_state_changed` | `incidents` | Incident transitioned |
| `question_asked` | `questions` | New operator question |
| `artifact_ready` | `artifacts` | Artifact built |
| `mode_changed` | (broadcast) | UI mode changed |

---

## Quick Start

### Prerequisites

- Node.js >= 18.0.0
- pnpm >= 8.0.0
- Python >= 3.11
- Docker (optional, for local Postgres)

### Installation

```bash
# Install frontend dependencies
pnpm install

# Set up Python environment
cd apps/backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cd ../..

# Set up environment
cp env.example .env
# Edit .env with your API keys

# Start dev servers
pnpm dev
```

### Run Tests

```bash
# Run the full E2E flow test with mock data
cd apps/backend
source venv/bin/activate
python tests/test_sator_flow.py
```

### Development URLs

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |

---

## Sponsor Integrations

### Primary (Required)

| Sponsor | Purpose | Location |
|---------|---------|----------|
| **Overshoot** | Real-time AI vision from video | `apps/backend/app/integrations/overshoot/` |
| **LeanMCP** | MCP transport for decision tools | `apps/backend/app/integrations/leanmcp/` |
| **Kairo AI Sec** | On-chain artifact anchoring | `apps/backend/app/integrations/kairo/` |

### Secondary (Optional)

| Sponsor | Purpose | Location |
|---------|---------|----------|
| **Arize** | Agent observability | `apps/backend/app/integrations/arize/` |
| **Browserbase** | External evidence fetch | `apps/backend/app/integrations/browserbase/` |

See [SPONSORS.md](SPONSORS.md) for full integration details.

---

## Scripts

| Command | Description |
|---------|-------------|
| `pnpm dev` | Start all dev servers |
| `pnpm dev:web` | Start frontend only |
| `pnpm dev:backend` | Start backend only |
| `pnpm build` | Build all packages |
| `pnpm lint` | Lint all packages |

---

## Environment Variables

Copy `env.example` to `.env` and configure:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/sator

# Primary Sponsors
KAIRO_API_KEY=
LEANMCP_REGISTRY_URL=
OVERSHOOT_API_KEY=
OVERSHOOT_WEBHOOK_SECRET=

# Optional Sponsors
ARIZE_API_KEY=
BROWSERBASE_API_KEY=
```

---

## License

Proprietary - All rights reserved
