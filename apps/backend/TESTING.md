# Quick Testing Guide

## Issue: 404 on `/overshoot-test/mock-response`

**Solution**: The server needs to be **restarted** after adding new routers.

### Steps to Fix:

1. **Stop the current server** (Ctrl+C in the terminal where it's running)

2. **Restart the server**:
   ```bash
   cd apps/backend
   python main.py
   # or
   uvicorn main:app --reload --port 8000
   ```

3. **Verify the endpoint exists**:
   ```bash
   curl http://localhost:8000/overshoot-test/mock-response
   ```
   
   Or check the API docs: http://localhost:8000/docs

4. **Run the test script**:
   ```bash
   python scripts/test_overshoot.py
   ```

---

## Quick Test Commands

```bash
# 1. Check if server is running
curl http://localhost:8000/health

# 2. Get mock Overshoot response
curl http://localhost:8000/overshoot-test/mock-response

# 3. Test fire scenario
curl -X POST "http://localhost:8000/overshoot-test/test-workflow/fire"

# 4. Test with custom data
curl -X POST "http://localhost:8000/scenario2/process" \
  -H "Content-Type: application/json" \
  -d '{
    "overshoot_data": {
      "timestamp_ms": 1700000000000,
      "person_count": 3,
      "fire_detected": true,
      "smoke_level": "dense"
    }
  }'
```

---

## If Still Getting 404

1. Check that the router is in `main.py`:
   ```python
   app.include_router(overshoot_test.router, prefix="/overshoot-test", tags=["Overshoot Testing"])
   ```

2. Check for import errors in server logs when starting

3. Visit http://localhost:8000/docs to see all available endpoints
