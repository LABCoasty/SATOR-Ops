# Testing Guide - How to Test Your App

## Quick Start

### 1. Make sure the server is running

```bash
cd apps/backend
python main.py
```

You should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 2. Test the API endpoints

#### List scenarios
```bash
curl http://localhost:8000/api/scenarios
```

#### Start a scenario
```bash
curl -X POST http://localhost:8000/api/scenarios/fixed-valve-incident/start \
  -H "Content-Type: application/json" \
  -d '{"operator_id": "test-operator"}'
```

#### Check scenario status
```bash
curl http://localhost:8000/api/scenarios/fixed-valve-incident/status
```

#### Get incidents
```bash
curl http://localhost:8000/api/incidents
```

### 3. Run diagnostic tests

```bash
cd apps/backend
python3 scripts/test_scenario.py
```

This will test:
- Data loading
- Service initialization  
- API endpoints

### 4. Test scenario flow directly (without API)

```bash
cd apps/backend
python3 scripts/quick_test.py
```

## Common Issues

### Issue: "Server not responding"

**Solution**: Make sure the server is running
```bash
cd apps/backend
python main.py
```

### Issue: "Data files missing"

**Solution**: Check that data files exist:
```bash
ls -la app/data/csv/
ls -la app/data/generated/
```

Required files:
- `app/data/csv/telemetry.csv`
- `app/data/csv/events.csv`
- `app/data/generated/contradictions.json`

### Issue: "Scenario start hangs or times out"

**Solution**: 
1. Check server logs for errors
2. Make sure all services are initialized
3. Check that data files are valid JSON/CSV

### Issue: "Import errors"

**Solution**: Install dependencies
```bash
cd apps/backend
pip install -r requirements.txt
```

## API Documentation

Visit http://localhost:8000/docs for interactive API documentation.

## Next Steps

Once testing works:
1. Start scenarios via the API
2. Create incidents and decision cards
3. Generate artifacts
4. Anchor to blockchain (Solana Devnet - FREE!)
