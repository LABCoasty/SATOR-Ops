# Quick Fix for Testing Issues

## Problem
The scenario start API endpoint is timing out, preventing you from testing the app.

## Root Cause
The endpoint was blocking on MongoDB operations and audit logging, even though these should be non-blocking.

## Solution Applied
I've moved MongoDB persistence and audit logging to background tasks so the API returns immediately.

## How to Test Now

### 1. Restart the Server
The server needs to be restarted to pick up the changes:

```bash
# Stop the current server (Ctrl+C in the terminal where it's running)
# Then restart:
cd apps/backend
python main.py
```

### 2. Test the Endpoint
```bash
curl -X POST http://localhost:8000/api/scenarios/fixed-valve-incident/start \
  -H "Content-Type: application/json" \
  -d '{"operator_id": "test-operator"}'
```

This should now return **immediately** (within 1-2 seconds) instead of timing out.

### 3. Verify It Works
```bash
# Check scenario status
curl http://localhost:8000/api/scenarios/fixed-valve-incident/status

# List incidents (should show the incident created by the scenario)
curl http://localhost:8000/api/incidents
```

## What Changed

1. **MongoDB persistence** moved to background task - won't block API response
2. **Audit logging** moved to background task - won't block API response  
3. **Better error handling** - failures won't crash the endpoint

## If It Still Times Out

1. **Check server logs** - look for errors when starting
2. **Verify server is running**: `ps aux | grep uvicorn`
3. **Check port**: `lsof -i :8000`
4. **Try restarting the server** completely

## Next Steps

Once the endpoint works:
1. ✅ Start scenarios
2. ✅ View incidents  
3. ✅ Test decision cards
4. ✅ Generate artifacts
5. ✅ Anchor to blockchain (Solana Devnet - FREE!)
