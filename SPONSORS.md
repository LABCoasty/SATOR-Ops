# SATOR Ops - Sponsor Integrations

Based on the API Alignment document, SATOR Ops integrates the following sponsor tracks.

## Primary Sponsor Integrations (Required)

### Kairo AI Sec
**AI-native secure smart contract development platform (Solana-first)**

Integrated as a secure development and analysis workflow for a minimal Solana audit-anchor program. Used to validate the safety of on-chain audit receipts.

| Use Case | Description |
|----------|-------------|
| Audit Receipt Validation | Verify safety of on-chain decision receipts |
| Secure Contract Workflow | AI-native secure development for Solana programs |
| On-chain Artifacts | Tamper-evident audit trail on Solana |

```
apps/api/app/integrations/kairo/
├── client.py          # Kairo API client
└── audit_anchor.py    # Solana audit-anchor program integration
```

---

### LeanMCP
**Transport and registry layer for SATOR Ops agent tools**

Integrated as the MCP (Model Context Protocol) transport layer exposing SATOR tools to AI agents. No workshop provided, but MCP exposure of tools is sufficient to qualify.

| Use Case | Description |
|----------|-------------|
| Tool Registry | Register SATOR decision tools for agent access |
| Transport Layer | MCP-compliant tool invocation |
| Agent Integration | Enable AI agents to interact with decision infrastructure |

```
apps/api/app/integrations/leanmcp/
├── server.py          # MCP server implementation
└── tools.py           # SATOR tool definitions
```

---

## Secondary Sponsor Integrations (Optional)

### Arize
**Observability for AI agent runs**

Optional integration for tracing agent runs, tool calls, refusals, and receipts.

| Use Case | Description |
|----------|-------------|
| Agent Tracing | Track decision agent execution |
| Tool Call Logging | Log all tool invocations |
| Receipt Tracking | Monitor artifact generation |

```
apps/api/app/integrations/arize/
└── tracer.py          # Arize observability client
```

---

### Browserbase
**Headless browser for external evidence fetch**

One-time external evidence fetch (e.g., regulatory notice or public advisory) attached as EvidenceRef.

| Use Case | Description |
|----------|-------------|
| External Evidence | Fetch regulatory notices, public advisories |
| Evidence Attachment | Attach external sources to decision context |

```
apps/api/app/integrations/browserbase/
└── fetcher.py         # External evidence fetcher
```

---

## Excluded Sponsor Tracks

The following were evaluated but excluded for architectural fit:

| Sponsor | Reason |
|---------|--------|
| Polymarket | Prediction market framing conflicts with trust-first operational design |
| Overshoot | Autonomous real-time action conflicts with human-in-the-loop posture |
| Seda AI | Research publishing focus does not strengthen incident operations |
| Wood Wide AI | Overlaps with internal trust logic, risks redundancy |

---

## VC / Investor Tracks

VC and fund-sponsored tracks (e.g., a16z) do not require API integration. Submissions emphasize problem framing, system depth, and deployability.

---

## Contingency Philosophy

> If a primary sponsor API fails or is unavailable, the agent core remains fully functional without modification. Sponsor integrations are treated as sidecars and do not gate correctness or demo viability.
