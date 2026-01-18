"""
Test endpoint for Overshoot.ai integration - simulates Overshoot responses

Use this to test the Scenario 2 workflow without needing an actual Overshoot API key or video.
"""

from fastapi import APIRouter
from datetime import datetime, timezone

from app.models.overshoot import OvershootDisasterRecord

router = APIRouter()


@router.get("/mock-response", summary="Get mock Overshoot response for testing")
async def get_mock_overshoot_response():
    """
    Returns a mock Overshoot.ai response matching the disaster detection schema.
    Use this to test the workflow without video input.
    """
    # Simulate different disaster scenarios
    scenarios = {
        "fire": {
            "timestamp_ms": int(datetime.now(timezone.utc).timestamp() * 1000),
            "person_count": 3,
            "water_level": 0.0,
            "fire_detected": True,
            "smoke_level": "dense",
            "structural_damage": "moderate",
            "injured_detected": True,
            "disaster_type": "fire",
            "location_id": "zone-5",
            "objects": [
                {"label": "person", "confidence": 0.85},
                {"label": "flame", "confidence": 0.92},
            ],
        },
        "flood": {
            "timestamp_ms": int(datetime.now(timezone.utc).timestamp() * 1000),
            "person_count": 8,
            "water_level": 75.0,
            "fire_detected": False,
            "smoke_level": "none",
            "structural_damage": "moderate",
            "injured_detected": False,
            "disaster_type": "flood",
            "location_id": "zone-3",
            "objects": [
                {"label": "person", "confidence": 0.78},
                {"label": "vehicle", "confidence": 0.65},
            ],
        },
        "normal": {
            "timestamp_ms": int(datetime.now(timezone.utc).timestamp() * 1000),
            "person_count": 2,
            "water_level": 5.0,
            "fire_detected": False,
            "smoke_level": "none",
            "structural_damage": "none",
            "injured_detected": False,
            "disaster_type": None,
            "location_id": "zone-1",
            "objects": [],
        },
    }
    return {
        "message": "Mock Overshoot responses - use these to test the workflow",
        "scenarios": scenarios,
        "usage": {
            "fire": "POST /scenario2/process with scenarios.fire as overshoot_data",
            "flood": "POST /scenario2/process with scenarios.flood as overshoot_data",
            "normal": "POST /scenario2/process with scenarios.normal as overshoot_data",
        },
    }


@router.post("/test-workflow/{scenario}", summary="Test Scenario 2 workflow with mock data")
async def test_workflow_with_mock(scenario: str):
    """
    Test the Scenario 2 workflow with pre-defined mock Overshoot responses.
    
    Scenarios: fire, flood, normal
    """
    from app.core.scenario2_workflow import get_scenario2_workflow

    mock_data = {
        "fire": OvershootDisasterRecord(
            timestamp_ms=int(datetime.now(timezone.utc).timestamp() * 1000),
            person_count=3,
            water_level=0.0,
            fire_detected=True,
            smoke_level="dense",
            structural_damage="moderate",
            injured_detected=True,
            disaster_type="fire",
            location_id="zone-5",
        ),
        "flood": OvershootDisasterRecord(
            timestamp_ms=int(datetime.now(timezone.utc).timestamp() * 1000),
            person_count=8,
            water_level=75.0,
            fire_detected=False,
            smoke_level="none",
            structural_damage="moderate",
            injured_detected=False,
            disaster_type="flood",
            location_id="zone-3",
        ),
        "normal": OvershootDisasterRecord(
            timestamp_ms=int(datetime.now(timezone.utc).timestamp() * 1000),
            person_count=2,
            water_level=5.0,
            fire_detected=False,
            smoke_level="none",
            structural_damage="none",
            injured_detected=False,
            disaster_type=None,
            location_id="zone-1",
        ),
    }

    if scenario not in mock_data:
        return {"error": f"Unknown scenario: {scenario}. Available: {list(mock_data.keys())}"}

    workflow = get_scenario2_workflow()

    # Add mock server telemetry for contradiction testing
    mock_telemetry = {
        "temperature_sensor": 45.0,  # Low temp (contradicts fire)
        "pressure_sensor_a": 80.0,   # Low pressure (contradicts flood)
    }

    try:
        result = await workflow.process_video_and_telemetry(
            overshoot_record=mock_data[scenario],
            server_telemetry=mock_telemetry,
        )
        return {
            "scenario": scenario,
            "overshoot_input": mock_data[scenario].model_dump(),
            "server_telemetry": mock_telemetry,
            "workflow_result": result,
        }
    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "scenario": scenario,
            "traceback": traceback.format_exc(),
        }


@router.get("/test-example", summary="Example cURL commands for testing")
async def get_test_examples():
    """Returns example cURL commands to test the endpoints"""
    return {
        "examples": {
            "1_get_mock_response": {
                "command": "curl http://localhost:8000/overshoot-test/mock-response",
                "description": "Get mock Overshoot response data",
            },
            "2_test_fire_scenario": {
                "command": 'curl -X POST "http://localhost:8000/overshoot-test/test-workflow/fire"',
                "description": "Test workflow with fire scenario",
            },
            "3_test_with_real_data": {
                "command": '''curl -X POST "http://localhost:8000/scenario2/process" \\
  -H "Content-Type: application/json" \\
  -d '{
    "overshoot_data": {
      "timestamp_ms": 1700000000000,
      "person_count": 5,
      "water_level": 0.0,
      "fire_detected": true,
      "smoke_level": "dense",
      "structural_damage": "none",
      "injured_detected": false
    },
    "server_telemetry": {
      "temperature_sensor": 45.0,
      "pressure_sensor_a": 100.0
    }
  }' ''',
                "description": "Test workflow with custom data",
            },
            "4_ingest_and_process": {
                "command": '''curl -X POST "http://localhost:8000/scenario2/ingest-and-process" \\
  -H "Content-Type: application/json" \\
  -d '{
    "overshoot_data": {
      "timestamp_ms": 1700000000000,
      "person_count": 3,
      "fire_detected": true,
      "smoke_level": "dense"
    }
  }' ''',
                "description": "Ingest to CSV and process workflow",
            },
        },
    }
