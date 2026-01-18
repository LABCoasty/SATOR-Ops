# Kairo AI Integration Guide

## Overview

Kairo AI has been integrated into SATOR Ops to provide security analysis for smart contracts before deployment and anchoring. The integration follows the sidecar pattern - it enhances security but doesn't gate core functionality.

## Setup

### 1. Set Your API Key

Add your Kairo API key to your `.env` file:

```bash
SATOR_KAIRO_API_KEY=kairo_sk_live_KYnMytOJ1z56sPIQ_bdWUpEAdXC6D1pUKtJTYZrOzN8
```

**Important**: Never commit your API key to version control. The `.env` file should be in `.gitignore`.

### 2. Verify Configuration

The integration is enabled by default when `SATOR_ENABLE_KAIRO=true` (default) and the API key is set.

## How It Works

### Integration Points

1. **Contract Analysis** (`KairoClient.analyze_contract()`)
   - Analyzes Solidity smart contract code
   - Returns security decision: `ALLOW`, `WARN`, `BLOCK`, or `ESCALATE`
   - Provides risk scores, findings, and recommendations

2. **Deploy Gate** (`KairoClient.deploy_check()`)
   - Final safety check before mainnet deployment
   - More strict than regular analysis
   - Validates contract against specific network

3. **Anchor Program Validation** (Placeholder)
   - Currently validates anchor program initialization
   - Note: Kairo API supports Solidity; your anchor program is Rust/Anchor
   - For Rust/Anchor programs, consider using:
     - `cargo-audit` for dependency vulnerabilities
     - `cargo-deny` for license and security checks
     - Or wait for Kairo to support Rust/Anchor

## API Endpoints Used

Based on [Kairo AI Documentation](https://kairoaisec.com/docs#quickstart):

- `POST /v1/analyze` - Analyze contract code
- `POST /v1/deploy/check` - Deploy gate check

## Usage Examples

### Analyze a Solidity Contract

```python
from app.integrations.kairo import get_kairo_client

client = get_kairo_client()

# Analyze contract code
analysis = await client.analyze_contract(
    contract_code="pragma solidity ^0.8.0; contract Token { ... }",
    contract_path="Token.sol",
    severity_threshold="high"
)

if analysis.decision == "BLOCK":
    print("Security issues found - do not deploy!")
    print(f"Risk score: {analysis.risk_score}")
    for warning in analysis.warnings:
        print(f"  - {warning}")
elif analysis.decision == "WARN":
    print("Minor issues found - proceed with caution")
else:
    print("Contract is safe to deploy")
```

### Deploy Gate Check

```python
# Before deploying to mainnet
check = await client.deploy_check(
    project_id="proj_xxxxx",
    contract_name="Token",
    network={"chain_id": 1, "name": "mainnet"}
)

if check.decision == "BLOCK":
    raise Exception("Deployment blocked by Kairo security check")
```

## Integration Features

### Automatic Security Checks

When artifacts are anchored, Kairo automatically:
1. Runs deploy gate security check
2. Validates deployment context (Solana network)
3. Stores analysis results in the anchor record
4. Logs security warnings/blocking decisions

### Kairo Analysis Storage

Kairo analysis results are stored in `AnchorRecord.kairo_analysis`:
```python
{
  "decision": "ALLOW" | "WARN" | "BLOCK" | "ESCALATE",
  "decision_reason": "No security issues detected...",
  "risk_score": 0.0,
  "is_safe": true,
  "warnings": [],
  "recommendations": [],
  "timestamp": "2024-01-01T00:00:00"
}
```

## Current Limitations

1. **Rust/Anchor Support**: Kairo API currently targets Solidity contracts. Your `sator-anchor` program is written in Rust/Anchor. Options:
   - Use Kairo for any Solidity components you add
   - Use Rust-specific security tools for the Anchor program
   - Wait for Kairo to add Rust/Anchor support
   - **Current**: Deploy gate validates deployment context even for Rust/Anchor programs

2. **Async/Sync Handling**: The anchor service now properly handles async Kairo checks:
   - `anchor_artifact_async()` - Full async version with Kairo checks
   - `anchor_artifact()` - Sync wrapper that runs async checks when possible
   - Falls back gracefully if async is not available

## Error Handling

The integration follows the **sidecar pattern** - if Kairo API is unavailable or fails:
- Operations continue (don't block core functionality)
- Warnings are logged
- Security checks return `WARN` decision with appropriate messages

## Testing

### 1. Health Check Endpoint

Test if Kairo is configured correctly:

```bash
curl http://localhost:8000/api/artifacts/kairo/health
```

Response:
```json
{
  "enabled": true,
  "api_key_configured": true,
  "health": {
    "status": "healthy",
    "api_url": "https://api.kairoaisec.com/v1",
    "api_key_configured": true,
    "features": ["contract_analysis", "deploy_check", "anchor_validation"]
  }
}
```

### 2. Analyze Contract Endpoint

Test contract analysis:

```bash
curl -X POST http://localhost:8000/api/artifacts/kairo/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "contract_code": "pragma solidity ^0.8.0; contract Token { uint256 public totalSupply; }",
    "contract_path": "Token.sol",
    "severity_threshold": "high"
  }'
```

### 3. Python Testing

Test the integration programmatically:

```python
from app.integrations.kairo import get_kairo_client

client = get_kairo_client()

# Check if enabled
print(f"Kairo enabled: {client.enabled}")

# Health check
health = await client.health_check()
print(health)

# Analyze a contract
analysis = await client.analyze_contract(
    contract_code="pragma solidity ^0.8.0; contract Token { ... }",
    contract_path="Token.sol"
)
print(f"Decision: {analysis.decision.value}")
print(f"Risk Score: {analysis.risk_score}")
```

## Next Steps

1. **Get Kairo Project ID**: Create a project in [Kairo Dashboard](https://app.kairoaisec.com) to use deploy gate checks
2. **CI/CD Integration**: Add Kairo security checks to your deployment pipeline
3. **Rust Security Tools**: Set up `cargo-audit` and `cargo-deny` for Anchor program security
4. **Monitor Results**: Track Kairo analysis results in your artifact metadata

## Configuration

All Kairo settings are in `config.py`:

- `enable_kairo`: Enable/disable integration (default: `True`)
- `kairo_api_key`: Your API key (from environment variable)

## Support

- Kairo Documentation: https://kairoaisec.com/docs
- Kairo Dashboard: https://app.kairoaisec.com
- API Reference: https://kairoaisec.com/docs#api-reference
