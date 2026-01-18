# How to See Kairo in Action

## Quick Test Options

### Option 1: Test via API (Recommended)

**Prerequisites:** Your FastAPI server must be running

```bash
# Start your server first (in another terminal)
cd apps/backend
uvicorn main:app --reload

# Then in this terminal, test Kairo:
```

#### 1. Check Kairo Health
```bash
curl http://localhost:8000/api/artifacts/kairo/health
```

#### 2. Test Contract Analysis
```bash
curl -X POST http://localhost:8000/api/artifacts/kairo/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "contract_code": "pragma solidity ^0.8.0; contract Token { uint256 public totalSupply; function transfer(address to, uint256 amount) public { totalSupply -= amount; } }",
    "contract_path": "Token.sol",
    "severity_threshold": "high"
  }'
```

**Watch your server console** - you'll see detailed Kairo logging!

#### 3. Test Full Anchoring Flow (with Kairo)
```bash
curl -X POST http://localhost:8000/api/artifacts/ART-TEST-123/anchor \
  -H "Content-Type: application/json" \
  -d '{"confirm": true}'
```

**Watch your server console** - you'll see:
- Kairo security validation
- Hash computation
- Solana transaction submission
- Complete flow with all steps logged

### Option 2: Check Server Logs

When you anchor an artifact through the UI or API, the server logs will show:

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
✅ Artifact ART-TEST-123 successfully anchored!
   Kairo Decision: ALLOW
============================================================
🏁 ANCHORING COMPLETE
============================================================
```

### Option 3: View Kairo Analysis in Anchor Records

After anchoring, check the anchor record:

```bash
# Get anchor details (if you have an endpoint for this)
# The anchor record includes kairo_analysis field with all results
```

## What Kairo Does

1. **Before Anchoring**: Runs security validation
   - Calls Kairo API: `POST /v1/deploy/check`
   - Validates deployment context (Solana network)
   - Returns security decision

2. **Analysis Results Stored**:
   - Decision: ALLOW/WARN/BLOCK/ESCALATE
   - Risk Score: 0.0 to 1.0
   - Warnings: Any security concerns
   - Recommendations: Suggested improvements

3. **Non-Blocking**: Following sidecar pattern
   - If Kairo fails, anchoring still proceeds
   - Warnings are logged but don't stop the process

## Troubleshooting

### If Kairo API calls fail:
- Check your API key in `.env`: `SATOR_KAIRO_API_KEY=kairo_sk_live_...`
- Verify network connectivity
- Check Kairo API status

### If you don't see logs:
- Make sure server is running with proper log level
- Check that Kairo is enabled: `SATOR_ENABLE_KAIRO=true`

### To see more detail:
- All Kairo interactions are logged with emoji markers (🔍, 📡, 📊, etc.)
- Look for these in your server console output

## Next Steps

1. **Start your server** if not running
2. **Anchor an artifact** through the UI or API
3. **Watch the console** to see Kairo in action
4. **Check the anchor record** to see stored Kairo analysis

The integration is fully functional - just start your server and anchor an artifact to see it work!
