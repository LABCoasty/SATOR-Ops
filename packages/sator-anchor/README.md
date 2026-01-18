# SATOR Anchor - Solana Blockchain Witness

Tamper-evident blockchain anchoring for SATOR Ops Decision Artifacts.

## Overview

SATOR Anchor writes cryptographic commitments to Solana Devnet, creating an immutable audit trail for decision artifacts. This enables:

- **Tamper Evidence**: Any modification to artifacts can be detected
- **Audit Trail**: Complete history of all events and decisions
- **Verification**: Anyone can verify artifact integrity against on-chain data
- **Role Hierarchy**: Employee → Supervisor → Admin approval chain

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    SATOR OPS ARTIFACT                       │
│  ┌─────────────┬─────────────┬─────────────┬─────────────┐  │
│  │   Incident  │  Evidence   │  Trust      │  Decisions  │  │
│  │   Core      │  Set        │  Receipt    │  Timeline   │  │
│  └──────┬──────┴──────┬──────┴──────┬──────┴──────┬──────┘  │
│         │             │             │             │         │
│         ▼             ▼             ▼             ▼         │
│     SHA-256       SHA-256       SHA-256       SHA-256       │
│         │             │             │             │         │
│         └─────────────┴──────┬──────┴─────────────┘         │
│                              ▼                              │
│                      BUNDLE ROOT HASH                       │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 SOLANA DEVNET (FREE)                        │
│                                                             │
│  IncidentAnchor PDA:                                        │
│  ├── operator: Pubkey                                       │
│  ├── incident_id: u64                                       │
│  ├── incident_core_hash: [u8; 32]                          │
│  ├── evidence_set_hash: [u8; 32]                           │
│  ├── contradictions_hash: [u8; 32]                         │
│  ├── trust_receipt_hash: [u8; 32]                          │
│  ├── operator_decisions_hash: [u8; 32]                     │
│  ├── timeline_hash: [u8; 32]                               │
│  ├── bundle_root_hash: [u8; 32]                            │
│  ├── event_chain_head: [u8; 32]                            │
│  ├── event_count: u32                                       │
│  ├── operator_role: u8                                      │
│  ├── packet_uri: String                                     │
│  └── timestamps                                             │
└─────────────────────────────────────────────────────────────┘
```

## Usage

### TypeScript Client

```typescript
import { 
  SatorAnchorClient, 
  computeArtifactHashes,
  DEVNET_RPC 
} from "@sator-ops/anchor";

// Initialize client
const client = new SatorAnchorClient(DEVNET_RPC);

// Compute hashes from artifact
const hashes = computeArtifactHashes(artifact);

// Verify against on-chain data
const result = await client.verifyArtifact(incidentId, artifact);

if (result.verified) {
  console.log("✅ Artifact integrity verified!");
} else {
  console.log("❌ Mismatches found:", result.mismatches);
}
```

### Python Backend

```python
from app.integrations.kairo.anchor import (
    get_anchor_service,
    AnchorRequest,
    OperatorRole
)

# Get service
anchor_service = get_anchor_service()

# Anchor an artifact
result = anchor_service.anchor_artifact(AnchorRequest(
    artifact_id="ART-001",
    incident_id="INC-001",
    scenario_id="scenario1",
    artifact_data=artifact_dict,
    operator_id="operator_001",
    operator_role=OperatorRole.EMPLOYEE
))

if result.success:
    print(f"Anchored! TX: {result.tx_hash}")
```

## Deployment to Devnet

### Prerequisites

```bash
# Install Solana CLI
sh -c "$(curl -sSfL https://release.solana.com/v1.18.4/install)"

# Install Anchor
cargo install --git https://github.com/coral-xyz/anchor avm --locked
avm install latest
avm use latest

# Configure for Devnet
solana config set --url devnet

# Create wallet
solana-keygen new --outfile ~/.config/solana/id.json

# Get free SOL
solana airdrop 2
```

### Deploy

```bash
cd packages/sator-anchor

# Build
anchor build

# Deploy to devnet
anchor deploy --provider.cluster devnet

# Note the program ID and update:
# - Anchor.toml
# - src/pda.ts PROGRAM_ID
```

## Verification Flow

1. **Fetch On-Chain Data**: Read IncidentAnchor PDA from Solana
2. **Recompute Hashes**: Hash each artifact section using RFC 8785 canonicalization
3. **Compare**: Match computed hashes against on-chain values
4. **Result**: Any mismatch indicates tampering

## Role Hierarchy

| Role | Can Create | Can Update | Can Approve |
|------|-----------|------------|-------------|
| Employee (0) | ✅ (needs approval) | Own only | ❌ |
| Supervisor (1) | ✅ | Own + team | ✅ |
| Admin (2) | ✅ | All | ✅ |

## Security

- **PDA Seeds**: `["incident_anchor", incident_id.to_le_bytes()]`
- **Operator Authority**: Only anchor creator can modify
- **Immutable Hashes**: Once anchored, hashes cannot be changed
- **Event Chain**: Rolling hash prevents event reordering

## Cost (Devnet = FREE)

| Operation | Devnet | Mainnet Est. |
|-----------|--------|--------------|
| Create Anchor | Free | ~$0.004 |
| Append Event | Free | ~$0.00001 |
| Update Artifacts | Free | ~$0.00001 |

## Explorer URLs

- **Solana Explorer**: `https://explorer.solana.com/tx/{txHash}?cluster=devnet`
- **Solscan**: `https://solscan.io/tx/{txHash}?cluster=devnet`

## License

MIT
