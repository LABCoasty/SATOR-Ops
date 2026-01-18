# Fixes Applied - Testing Your App

## Issues Found and Fixed

### 1. ✅ Improved Error Handling
- Added better error logging in scenario background tasks
- Added traceback printing for debugging
- Improved error messages

### 2. ✅ Fixed Severity Handling
- Improved severity mapping in decision card creation
- Better handling of uncertainty level to severity conversion

### 3. ✅ Created Diagnostic Tools
- `scripts/test_scenario.py` - Comprehensive diagnostic test
- `scripts/quick_test.py` - Quick scenario flow test
- `TESTING_GUIDE.md` - Complete testing documentation

## How to Test Now

### Step 1: Verify Server is Running

```bash
curl http://localhost:8000/health
```

Should return: `{"status":"healthy"}`

### Step 2: Run Diagnostic Test

```bash
cd apps/backend
python3 scripts/test_scenario.py
```

This will test:
- ✅ Data loading (telemetry, events, contradictions)
- ✅ Service initialization (incident manager, decision engine, etc.)
- ✅ API endpoints

### Step 3: Start a Scenario

```bash
curl -X POST http://localhost:8000/api/scenarios/fixed-valve-incident/start \
  -H "Content-Type: application/json" \
  -d '{"operator_id": "test-operator"}'
```

Expected response:
```json
{
  "success": true,
  "scenario_id": "fixed-valve-incident",
  "status": {
    "scenario_id": "fixed-valve-incident",
    "status": "running",
    "started_at": "...",
    "current_time_sec": 0.0,
    "active_incidents": 0,
    "mode": "data_ingest"
  },
  "message": "Fixed scenario started - loading static data"
}
```

### Step 4: Check Scenario Status

```bash
curl http://localhost:8000/api/scenarios/fixed-valve-incident/status
```

After a few seconds, you should see:
- `status: "running"`
- `active_incidents: 1` (after incident is created)
- `mode: "decision"` (after contradiction is detected)

### Step 5: Get Incidents

```bash
curl http://localhost:8000/api/incidents
```

Should show the incident created by the scenario.

## What Should Happen

When you start the `fixed-valve-incident` scenario:

1. **Background task starts** (returns immediately)
2. **Data loads** from CSV/JSON files
3. **Contradiction detected** at t=60s
4. **Incident created** with severity CRITICAL
5. **Decision card created** with evidence evaluation
6. **Operator questions generated**
7. **Status updates** to "decision" mode

## Troubleshooting

### If scenario start hangs:
1. Check server logs for errors
2. Make sure data files exist in `app/data/`
3. Check that all services initialized correctly

### If you get 404 errors:
1. Make sure server is running
2. Check that routes are registered in `main.py`
3. Visit http://localhost:8000/docs to see all endpoints

### If data loading fails:
1. Check files exist:
   - `app/data/csv/telemetry.csv`
   - `app/data/csv/events.csv`
   - `app/data/generated/contradictions.json`
2. Verify files are valid CSV/JSON

## Next Steps

Once testing works:
1. ✅ Start scenarios
2. ✅ View incidents and decision cards
3. ✅ Generate artifacts
4. ✅ Anchor to Solana Devnet (FREE!)

## Solana Devnet Setup (Optional)

If you want to test blockchain anchoring:

1. Generate a keypair:
   ```bash
   python3 scripts/generate_solana_keypair.py
   ```

2. Get FREE test SOL from faucet:
   - Visit: https://faucet.solana.com/
   - Or use CLI: `solana airdrop 1 <YOUR_PUBLIC_KEY> --url devnet`

3. Add to `.env`:
   ```
   SATOR_SOLANA_PRIVATE_KEY=<your_base58_key>
   SATOR_SOLANA_USE_SIMULATION=false
   ```

**Remember**: Solana Devnet is completely FREE - test SOL has no real value!
