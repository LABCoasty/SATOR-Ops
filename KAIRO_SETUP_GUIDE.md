# Kairo AI Smart Contract Management & CI/CD Setup Guide

This guide shows you how to use Kairo AI to manage your smart contracts and set up safe CI/CD with pre-deployment checks.

## Overview

Kairo AI provides:
- **Contract Security Analysis** - AI-powered vulnerability detection
- **Deployment Gates** - Pre-deployment safety checks
- **Contract Management** - Version tracking and registration
- **CI/CD Integration** - Automated security checks in your pipeline

## Prerequisites

1. **Kairo API Key**: Get one from [https://app.kairoaisec.com](https://app.kairoaisec.com)
2. **Configure Environment**: Add to your `.env`:
   ```bash
   SATOR_KAIRO_API_KEY=kairo_sk_live_xxxxx
   SATOR_ENABLE_KAIRO=true
   ```

## Step 1: Register Your Smart Contracts

### For Solidity Contracts

```python
from app.integrations.kairo.contract_manager import get_contract_manager

manager = get_contract_manager()

# Register a new contract version
version = await manager.register_contract(
    contract_name="MyToken",
    code="""
        pragma solidity ^0.8.0;
        contract MyToken {
            // Your contract code
        }
    """,
    language="solidity",
    version="1.0.0",
    network="devnet"
)

print(f"Contract registered: {version.contract_name} v{version.version}")
print(f"Security decision: {version.last_analysis.decision.value}")
```

### For Anchor/Rust Programs

Since Kairo currently supports Solidity, for Anchor programs:

1. **Option A**: Use Kairo for deployment context validation (already integrated)
2. **Option B**: Convert critical logic to Solidity for analysis
3. **Option C**: Use Rust-specific tools (`cargo-audit`, `cargo-deny`) alongside Kairo

The current integration uses `deploy_check` which validates deployment context even for Anchor programs.

## Step 2: Pre-Deployment Checks

Before deploying to any network, run a pre-deployment check:

```python
from app.integrations.kairo.contract_manager import get_contract_manager

manager = get_contract_manager()

# Run pre-deployment check
gate = await manager.pre_deployment_check(
    contract_name="sator_anchor",
    version="latest",
    network={"chain_id": 103, "name": "devnet"}
)

if gate.can_deploy:
    print("✅ Safe to deploy")
else:
    print(f"❌ Deployment blocked: {gate.decision.value}")
    print(f"Warnings: {gate.warnings}")
```

## Step 3: CI/CD Integration

### GitHub Actions (Already Configured)

The workflow `.github/workflows/kairo-pre-deploy.yml` automatically:
- Runs on pushes to `main`/`develop`
- Triggers on contract file changes
- Runs Kairo security checks
- Uploads security reports

### Manual CI Check

Run the CI check script:

```bash
cd apps/backend
python scripts/kairo_ci_check.py \
    --contract sator_anchor \
    --network devnet \
    --fail-on-warn
```

**Exit Codes:**
- `0` = Check passed, safe to deploy
- `1` = Check failed, deployment blocked

### Local Pre-Commit Hook

Add to `.git/hooks/pre-push`:

```bash
#!/bin/bash
cd apps/backend
python scripts/kairo_ci_check.py --contract sator_anchor --network devnet
if [ $? -ne 0 ]; then
    echo "❌ Kairo security check failed. Push blocked."
    exit 1
fi
```

## Step 4: API Endpoints

### Register Contract

```bash
POST /api/kairo/contracts/register
{
  "contract_name": "MyToken",
  "code": "pragma solidity ^0.8.0; ...",
  "language": "solidity",
  "version": "1.0.0",
  "network": "devnet"
}
```

### Pre-Deployment Check

```bash
POST /api/kairo/contracts/pre-deploy-check
{
  "contract_name": "sator_anchor",
  "version": "latest",
  "network": {"chain_id": 103, "name": "devnet"}
}
```

### Analyze Contract Code

```bash
POST /api/kairo/contracts/analyze
{
  "code": "pragma solidity ^0.8.0; ...",
  "contract_path": "MyToken.sol",
  "severity_threshold": "high"
}
```

### Get Contract Versions

```bash
GET /api/kairo/contracts/{contract_name}/versions
GET /api/kairo/contracts/{contract_name}/latest
```

## Step 5: Deployment Workflow

### Recommended Flow

```
1. Develop Contract
   ↓
2. Register with Kairo (stores version)
   ↓
3. Run Analysis (get security feedback)
   ↓
4. Fix Issues (if any)
   ↓
5. Pre-Deployment Check (final gate)
   ↓
6. Deploy to Network
   ↓
7. Update Version (mark as deployed)
```

### Example: Complete Workflow

```python
import asyncio
from app.integrations.kairo.contract_manager import get_contract_manager

async def deploy_contract():
    manager = get_contract_manager()
    
    # 1. Register contract
    version = await manager.register_contract(
        contract_name="MyToken",
        code=open("MyToken.sol").read(),
        language="solidity",
        version="1.0.0"
    )
    
    # 2. Check if safe
    if not version.last_analysis.is_safe:
        print("⚠️ Security issues found:")
        for warning in version.last_analysis.warnings:
            print(f"  - {warning}")
        return
    
    # 3. Pre-deployment check
    gate = await manager.pre_deployment_check(
        contract_name="MyToken",
        version="1.0.0",
        network={"chain_id": 103, "name": "devnet"}
    )
    
    if not gate.can_deploy:
        print(f"❌ Deployment blocked: {gate.decision.value}")
        return
    
    # 4. Deploy (your deployment logic here)
    print("✅ Pre-deployment check passed, deploying...")
    # deploy_to_solana(...)

asyncio.run(deploy_contract())
```

## Step 6: Monitoring & Alerts

### Check Contract Health

```python
# Get latest version and its analysis
latest = manager.get_latest_version("sator_anchor")
if latest.last_analysis:
    if latest.last_analysis.risk_score > 0.7:
        print("⚠️ High risk detected!")
```

### Set Up Alerts

You can integrate with monitoring systems to alert on:
- High risk scores (> 0.7)
- BLOCK decisions
- New security findings

## Current Integration Status

✅ **Already Integrated:**
- Kairo client with API calls
- Pre-deployment checks in anchor flow
- Contract analysis endpoints
- CI/CD script ready

✅ **New Features Added:**
- Contract version management
- Deployment gate validation
- GitHub Actions workflow
- API endpoints for contract management

## Next Steps

1. **Get Kairo API Key**: Sign up at [https://app.kairoaisec.com](https://app.kairoaisec.com)
2. **Register Your Contracts**: Use the API or Python client
3. **Set Up CI/CD**: The GitHub Actions workflow is ready
4. **Test Pre-Deployment**: Run `python scripts/kairo_ci_check.py`
5. **Monitor Deployments**: Use the API endpoints to track contract health

## Troubleshooting

### "Kairo integration disabled"
- Check `SATOR_ENABLE_KAIRO=true` in `.env`
- Verify `SATOR_KAIRO_API_KEY` is set

### "API key not configured"
- Get API key from Kairo dashboard
- Add to `.env` file

### "Contract not found"
- Register contract first using `/api/kairo/contracts/register`
- Or use the contract manager Python API

## Resources

- [Kairo AI Documentation](https://kairoaisec.com/client/docs)
- [Kairo API Reference](https://kairoaisec.com/docs#quickstart)
- [GitHub Actions Docs](https://docs.github.com/en/actions)
