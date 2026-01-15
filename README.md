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

### Development URLs

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |

---

## Project Structure

```
sator/
│
├── apps/
│   ├── web/                        # FRONTEND (Next.js)
│   │   ├── app/
│   │   │   ├── (dashboard)/
│   │   │   │   ├── observe/        # Observe Mode - passive monitoring
│   │   │   │   ├── decision/       # Decision Mode - formal commitment
│   │   │   │   └── replay/         # Replay Mode - audit/forensics
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx            # Landing page
│   │   │   └── globals.css
│   │   ├── components/
│   │   │   ├── ui/                 # shadcn components (button, card, badge)
│   │   │   ├── dashboard/          # Dashboard widgets
│   │   │   ├── decision-card/      # Decision card stack
│   │   │   └── mode-switcher/      # Mode transition UI
│   │   ├── lib/
│   │   │   ├── utils.ts            # Utility functions
│   │   │   └── api-client.ts       # Backend API client
│   │   └── hooks/                  # Custom React hooks
│   │
│   └── backend/                    # BACKEND (FastAPI + Python)
│       ├── main.py                 # App entry point
│       ├── app/
│       │   ├── config.py           # Environment config
│       │   ├── api/
│       │   │   ├── routes/
│       │   │   │   ├── decisions.py    # Decision CRUD
│       │   │   │   ├── evidence.py     # Evidence ingestion
│       │   │   │   ├── artifacts.py    # Receipt generation
│       │   │   │   └── telemetry.py    # Telemetry ingest
│       │   │   └── websocket.py        # Real-time updates
│       │   ├── core/                   # CORE LOGIC
│       │   │   ├── decision_engine.py  # Decision compilation
│       │   │   ├── trust_calculator.py # Trust scoring
│       │   │   └── mode_manager.py     # Mode transitions
│       │   ├── ai/                     # AI/ML MODELS (PyTorch)
│       │   │   ├── anomaly_detector.py
│       │   │   ├── trust_scorer.py
│       │   │   ├── time_series.py
│       │   │   └── nlp_processor.py
│       │   ├── integrations/           # SPONSOR INTEGRATIONS
│       │   │   ├── kairo/              # Primary - Solana audit receipts
│       │   │   ├── leanmcp/            # Primary - MCP tool transport
│       │   │   ├── arize/              # Optional - Observability
│       │   │   └── browserbase/        # Optional - Evidence fetch
│       │   ├── models/                 # Pydantic models
│       │   │   ├── decision.py
│       │   │   ├── evidence.py
│       │   │   └── artifact.py
│       │   └── db/                     # Database
│       │       ├── database.py
│       │       └── models.py
│       ├── tests/
│       ├── requirements.txt
│       └── Dockerfile
│
├── packages/
│   └── shared/                     # SHARED TYPES (TypeScript)
│       └── src/types/
│           ├── decision.ts
│           ├── evidence.ts
│           └── artifact.ts
│
├── infra/                          # INFRASTRUCTURE
│   └── docker-compose.yml          # Local Postgres
│
├── pnpm-workspace.yaml
├── package.json
├── env.example
├── README.md
└── SPONSORS.md
```

---

## Core Concepts

### Three Modes

| Mode | Purpose | Key UI Elements |
|------|---------|-----------------|
| **Observe** | Passive situational awareness | Dashboard, trust indicators, signals |
| **Decision** | Formal commitment under uncertainty | Decision cards, timer, bounded actions |
| **Replay** | Truth reconstruction for audits | Timeline scrubber, state transitions |

### Artifacts

| Artifact | When Generated |
|----------|----------------|
| Decision Receipt | When operator takes action |
| Deferral Receipt | When decision is deferred/escalated |
| Legal Posture Packet | Post-incident or on-demand |

---

## Sponsor Integrations

### Primary (Required)
| Sponsor | Purpose | Location |
|---------|---------|----------|
| **Kairo AI Sec** | Solana audit receipts, secure contracts | `apps/backend/app/integrations/kairo/` |
| **LeanMCP** | MCP transport for agent tools | `apps/backend/app/integrations/leanmcp/` |

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

# Optional Sponsors
ARIZE_API_KEY=
BROWSERBASE_API_KEY=
```

---

## License

Proprietary - All rights reserved
