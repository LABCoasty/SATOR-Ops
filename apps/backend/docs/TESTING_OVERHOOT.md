# Testing Overshoot.ai Integration

Quick guide to test the Overshoot.ai integration and Scenario 2 workflow.

---

## 🚀 Quick Start

### 1. Start the Backend Server

```bash
cd apps/backend
python main.py
# or
uvicorn main:app --reload --port 8000
```

The server should start at `http://localhost:8000`

---

## 🧪 Test Endpoints

### **Get Mock Overshoot Response**

```bash
curl http://localhost:8000/overshoot-test/mock-response
```

Returns example Overshoot JSON responses for different scenarios (fire, flood, normal).

### **Test Workflow with Pre-defined Scenarios**

```bash
# Fire scenario
curl -X POST "http://localhost:8000/overshoot-test/test-workflow/fire"

# Flood scenario  
curl -X POST "http://localhost:8000/overshoot-test/test-workflow/flood"

# Normal scenario
curl -X POST "http://localhost:8000/overshoot-test/test-workflow/normal"
```

These endpoints run the full Scenario 2 workflow with mock data and return:
- Decision card
- Contradictions detected
- AI predictions
- Action recommendations

### **Get Test Examples**

```bash
curl http://localhost:8000/overshoot-test/test-example
```

Returns example cURL commands for all endpoints.

---

## 🐍 Python Test Script

Run the automated test suite:

```bash
cd apps/backend
python scripts/test_overshoot.py
```

This will:
1. Fetch mock Overshoot responses
2. Test workflow with fire, flood, and normal scenarios
3. Test with custom data
4. Display formatted output showing decision cards, contradictions, predictions

**Note**: Requires `httpx` - install with `pip install httpx`

---

## 📝 Manual Testing with Custom Data

### Test Scenario 2 Workflow

```bash
curl -X POST "http://localhost:8000/scenario2/process" \
  -H "Content-Type: application/json" \
  -d '{
    "overshoot_data": {
      "timestamp_ms": 1700000000000,
      "person_count": 5,
      "water_level": 85.0,
      "fire_detected": false,
      "smoke_level": "light",
      "structural_damage": "severe",
      "injured_detected": true
    },
    "server_telemetry": {
      "temperature_sensor": 25.0,
      "pressure_sensor_a": 70.0
    }
  }'
```

### Ingest and Process (Saves to CSV)

```bash
curl -X POST "http://localhost:8000/scenario2/ingest-and-process" \
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

This both saves to CSV files AND processes through the workflow.

---

## 🔍 Expected Response Format

### Decision Card Response

```json
{
  "decision_card": {
    "id": "dec_abc123",
    "mode": "decision",
    "allowed_actions": ["act", "escalate"],
    "uncertainty_score": 0.3,
    "timebox_seconds": 60,
    "summary": "🔥 Fire detected | ⚠️ 1 sensor contradiction(s) | Risk: CRITICAL"
  },
  "contradictions": [
    {
      "contradiction_id": "...",
      "reason_code": "RC11",
      "description": "Video shows fire but temperature sensor shows no heat rise",
      "primary_tag_id": "video_fire_detected",
      "secondary_tag_ids": ["temperature_sensor"],
      "values": {
        "video_fire_detected": 1.0,
        "temperature_sensor": 45.0
      }
    }
  ],
  "predictions": {
    "immediate_risk": "critical",
    "escalation_likelihood": 0.9,
    "estimated_impact": "high - potential structure loss"
  },
  "action_recommendations": [
    {
      "priority": "critical",
      "action": "dispatch_fire_team",
      "description": "Fire detected in video - dispatch emergency response immediately",
      "timebox_seconds": 60
    }
  ],
  "uncertainty_score": 0.3,
  "timestamp": "2026-01-17T14:38:25Z"
}
```

---

## 🎬 Testing with Real Overshoot.ai (Optional)

To test with actual Overshoot.ai API:

1. Get an API key from [Overshoot.ai](https://overshoot.ai/)
2. Use the Overshoot SDK in your frontend:

```javascript
import { RealtimeVision } from 'overshoot';

// Get schema from backend
const schemaRes = await fetch('http://localhost:8000/ingest/overshoot/schema');
const { outputSchema } = await schemaRes.json();

const vision = new RealtimeVision({
  apiUrl: 'https://cluster1.overshoot.ai/api/v0.2',
  apiKey: 'YOUR_API_KEY',
  prompt: 'Detect disaster: person count, water level 0-100, fire, smoke, structural damage, injured.',
  outputSchema,
  onResult: async (result) => {
    const data = JSON.parse(result.result);
    // Test the workflow
    const resp = await fetch('http://localhost:8000/scenario2/process', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ overshoot_data: data }),
    });
    const workflowResult = await resp.json();
    console.log('Decision Card:', workflowResult.decision_card);
  },
});
vision.start();
```

---

## 📊 View Generated CSV Files

After using `/scenario2/ingest-and-process`, check the generated files:

```bash
# Telemetry CSV
cat app/data/generated/video_disaster_telemetry.csv

# Events CSV  
cat app/data/generated/video_disaster_events.csv

# Sensors CSV
cat app/data/generated/video_disaster_sensors.csv
```

---

## 🐛 Troubleshooting

**Connection refused**: Make sure the backend server is running on port 8000

**Module not found**: Install dependencies: `pip install -r requirements.txt`

**MCP tools not working**: Check that `enable_leanmcp=True` in config (default: enabled)

**No contradictions detected**: Try scenarios with conflicting data (e.g., fire + low temperature)

---

## 📚 Related Documentation

- [OVERSHOOT_INGEST.md](./OVERSHOOT_INGEST.md) - Overshoot ingestion details
- [SCENARIO_WORKFLOWS.md](./SCENARIO_WORKFLOWS.md) - Full workflow documentation
- [Overshoot.ai Docs](https://docs.overshoot.ai/) - Official Overshoot documentation
