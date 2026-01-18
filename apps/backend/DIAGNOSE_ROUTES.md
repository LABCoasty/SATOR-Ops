# Diagnose Route Loading Issue

If you're getting 404 on `/overshoot-test/mock-response`:

## 1. Check Server Startup Logs

When you start the server, look for:
- `✅ Overshoot test router loaded` - means it loaded successfully
- `⚠️  Failed to load overshoot_test router` - means there's an import error

## 2. Check Available Routes

Visit http://localhost:8000/docs and look for "Overshoot Testing" tag.

Or check OpenAPI spec:
```bash
curl http://localhost:8000/openapi.json | grep -A 5 "overshoot-test"
```

## 3. Test Import Directly

In your Python environment (where server runs):
```python
from app.api import overshoot_test
print(f"Router: {overshoot_test.router}")
print(f"Routes: {[r.path for r in overshoot_test.router.routes]}")
```

## 4. Common Issues

- **Import error**: Check server logs for traceback
- **Syntax error**: Run `python -m py_compile app/api/overshoot_test.py`
- **Module not found**: Make sure file exists at `app/api/overshoot_test.py`
- **Circular import**: Check if any imports cause circular dependencies

## 5. Alternative: Test Without Router

You can test the workflow directly via Scenario 2 endpoint:

```bash
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

This doesn't require the test router to work.
