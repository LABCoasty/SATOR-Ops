# Kairo Integration Demo Guide

This guide shows you how to test and see Kairo AI security analysis in action.

## Quick Start

### 1. Check Kairo Health

First, verify Kairo is configured:

```bash
curl http://localhost:8000/api/artifacts/kairo/health
```

Expected response:
```json
{
  "enabled": true,
  "api_key_configured": true,
  "api_key_preview": "kairo_sk_live_KYnMyt...",
  "base_url": "https://api.kairoaisec.com/v1",
  "health": {
    "status": "healthy",
    "api_url": "https://api.kairoaisec.com/v1",
    "api_key_configured": true,
    "features": ["contract_analysis", "deploy_check", "anchor_validation"]
  }
}
```

### 2. Test Contract Analysis

Analyze a sample Solidity contract:

```bash
curl -X POST http://localhost:8000/api/artifacts/kairo/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "contract_code": "pragma solidity ^0.8.0; contract Token { uint256 public totalSupply; function transfer(address to, uint256 amount) public { totalSupply -= amount; } }",
    "contract_path": "Token.sol",
    "severity_threshold": "high"
  }'
```

**Watch your server console** - you'll see detailed logging:
```
============================================================
🔍 KAIRO SECURITY ANALYSIS REQUEST
============================================================
📄 Contract: Token.sol
⚙️  Severity Threshold: high
📡 Calling Kairo API: https://api.kairoaisec.com/v1/analyze
------------------------------------------------------------
📤 Preparing Kairo API request...
   Endpoint: https://api.kairoaisec.com/v1/analyze
   Contract: Token.sol (123 chars)
🚀 Sending request to Kairo API...
📥 Received response: 200
✅ Kairo API response parsed successfully
------------------------------------------------------------
📊 KAIRO ANALYSIS RESULTS
------------------------------------------------------------
✅ Decision: ALLOW
📈 Risk Score: 0.15
🎯 Confidence: 85.00%
💬 Reason: No security issues detected. Safe to proceed.
⚠️  Warnings (1):
   1. [MEDIUM] Missing access control on transfer function
💡 Recommendations (1):
   1. Add access control modifiers to prevent unauthorized transfers
============================================================
```

### 3. Test Artifact Anchoring (with Kairo)

Anchor an artifact and see Kairo security check in action:

```bash
curl -X POST http://localhost:8000/api/artifacts/ART-123/anchor \
  -H "Content-Type: application/json" \
  -d '{"confirm": true}'
```

**Watch your server console** - you'll see the full flow:
```
============================================================
🚀 STARTING ARTIFACT ANCHORING WITH KAIRO
============================================================
🔍 Starting Kairo security validation...
📡 Calling Kairo deploy_check API for project 'sator_ops', contract 'sator_anchor' on devnet...
📤 Preparing Kairo deploy check request...
   Endpoint: https://api.kairoaisec.com/v1/deploy/check
   Project: sator_ops
   Contract: sator_anchor
   Network: devnet (chain_id: 103)
🚀 Sending deploy check to Kairo API...
📥 Received response: 200
✅ Kairo deploy check response parsed successfully
📊 Kairo Analysis Results:
   Decision: ALLOW
   Risk Score: 0.05
   Reason: Deployment context validated successfully
✅ Kairo security check passed: ALLOW
   Confidence: 95.00%
🔐 Computing artifact hashes...
   Bundle Root Hash: a1b2c3d4e5f6...
📍 Derived PDA: 7xK8...
💾 Storing artifact data...
📝 Creating anchor record...
⛓️  Submitting to Solana blockchain...
✅ Solana transaction confirmed: 5j7x...
💾 Persisting anchor record...
✅ Artifact ART-123 successfully anchored!
   Kairo Decision: ALLOW
============================================================
🏁 ANCHORING COMPLETE
============================================================
```

## What You'll See

### In the API Response

The API returns structured data:
```json
{
  "success": true,
  "artifact_id": "ART-123",
  "tx_hash": "5j7xK8...",
  "verification_url": "https://explorer.solana.com/tx/5j7xK8..."
}
```

### In Server Logs

Detailed step-by-step logging shows:
1. **Kairo Security Check** - API call, response, decision
2. **Hash Computation** - Bundle root hash generation
3. **Solana Submission** - Transaction creation and confirmation
4. **Persistence** - MongoDB storage (if enabled)

### In Anchor Record

The anchor record includes Kairo analysis:
```json
{
  "anchor_id": "anchor_ART-123",
  "kairo_analysis": {
    "decision": "ALLOW",
    "decision_reason": "Deployment context validated successfully",
    "risk_score": 0.05,
    "is_safe": true,
    "warnings": [],
    "recommendations": [],
    "timestamp": "2024-01-01T00:00:00"
  },
  "tx_hash": "5j7xK8...",
  ...
}
```

## Testing Different Scenarios

### Test with Vulnerable Contract

```bash
curl -X POST http://localhost:8000/api/artifacts/kairo/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "contract_code": "pragma solidity ^0.8.0; contract Unsafe { function withdraw() public { payable(msg.sender).transfer(address(this).balance); } }",
    "contract_path": "Unsafe.sol"
  }'
```

This should trigger warnings or BLOCK decision.

### Test Deploy Check

The deploy check runs automatically when anchoring, but you can see it in the logs. It validates:
- Network configuration (Solana devnet/mainnet)
- Deployment context
- Contract safety for the target network

## Troubleshooting

### Kairo Not Enabled

If you see `"enabled": false`:
1. Check `.env` file has `SATOR_KAIRO_API_KEY` set
2. Verify API key format: `kairo_sk_live_...`
3. Restart the server after setting the key

### API Errors

If you see API errors in logs:
- Check API key is valid
- Verify network connectivity
- Check Kairo API status

### No Logging

If you don't see detailed logs:
- Check log level is set to INFO or DEBUG
- Verify logger is configured in your FastAPI app

## Next Steps

1. **Monitor Logs** - Watch server console during artifact anchoring
2. **Check Results** - Review Kairo analysis in anchor records
3. **Test Contracts** - Try different Solidity contracts to see various decisions
4. **Review Recommendations** - Use Kairo suggestions to improve contract security

The integration is now fully functional and will show you exactly what Kairo is doing at each step!
