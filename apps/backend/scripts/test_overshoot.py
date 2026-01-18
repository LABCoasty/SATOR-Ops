#!/usr/bin/env python3
"""
Test script for Overshoot.ai integration and Scenario 2 workflow.

This script tests the backend API endpoints with mock Overshoot data.
Run: python scripts/test_overshoot.py
"""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from datetime import datetime, timezone


BASE_URL = "http://localhost:8000"


def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


def test_mock_response():
    """Test getting mock Overshoot response"""
    print_section("1. Get Mock Overshoot Response")
    with httpx.Client() as client:
        resp = client.get(f"{BASE_URL}/overshoot-test/mock-response")
        print(f"Status: {resp.status_code}")
        
        if resp.status_code != 200:
            print(f"❌ Error: {resp.status_code}")
            print(f"   Response: {resp.text}")
            print("\n💡 Tip: Make sure the backend server is running and the endpoint exists.")
            print("   Check: curl http://localhost:8000/docs to see available endpoints")
            return
        
        data = resp.json()
        if "scenarios" not in data:
            print(f"❌ Unexpected response format: {data}")
            return
            
        print("\nMock Scenarios Available:")
        for scenario_name, scenario_data in data.get("scenarios", {}).items():
            print(f"\n  {scenario_name.upper()}:")
            for key, value in scenario_data.items():
                print(f"    {key}: {value}")


def test_workflow(scenario: str):
    """Test Scenario 2 workflow with a specific scenario"""
    print_section(f"2. Test Workflow: {scenario.upper()}")
    with httpx.Client(timeout=30.0) as client:
        resp = client.post(f"{BASE_URL}/overshoot-test/test-workflow/{scenario}")
        print(f"Status: {resp.status_code}")
        
        if resp.status_code != 200:
            print(f"❌ Error: {resp.status_code}")
            print(f"   Response: {resp.text}")
            if resp.status_code == 404:
                print("\n💡 Endpoint not found. Make sure the server was restarted after adding the router.")
                print("   Check available endpoints: curl http://localhost:8000/docs")
            return
        
        data = resp.json()
        
        if "error" in data:
            print(f"Error: {data['error']}")
            return
        
        if "overshoot_input" not in data:
            print(f"⚠️  Unexpected response format: {list(data.keys())}")
            print(f"   Response: {json.dumps(data, indent=2, default=str)}")
            return
        
        print("\n📥 INPUT (Overshoot Data):")
        print(json.dumps(data["overshoot_input"], indent=2, default=str))
        
        print("\n📊 OUTPUT (Workflow Result):")
        workflow = data["workflow_result"]
        
        print(f"\n  Decision Card:")
        card = workflow["decision_card"]
        print(f"    ID: {card['id']}")
        print(f"    Mode: {card['mode']}")
        print(f"    Allowed Actions: {card['allowed_actions']}")
        print(f"    Uncertainty Score: {card['uncertainty_score']:.2f}")
        print(f"    Timebox: {card.get('timebox_seconds', 'N/A')} seconds")
        print(f"    Summary: {card.get('summary', 'N/A')}")
        
        print(f"\n  Contradictions ({len(workflow['contradictions'])}):")
        for c in workflow["contradictions"]:
            print(f"    - {c.get('reason_code', 'N/A')}: {c.get('description', 'N/A')}")
        
        print(f"\n  Predictions:")
        pred = workflow["predictions"]
        print(f"    Risk: {pred.get('immediate_risk', 'N/A')}")
        print(f"    Escalation Likelihood: {pred.get('escalation_likelihood', 0):.2f}")
        print(f"    Impact: {pred.get('estimated_impact', 'N/A')}")
        
        print(f"\n  Recommendations ({len(workflow['action_recommendations'])}):")
        for r in workflow["action_recommendations"]:
            print(f"    [{r.get('priority', 'N/A').upper()}] {r.get('action', 'N/A')}")
            print(f"      {r.get('description', 'N/A')}")
            if r.get('timebox_seconds'):
                print(f"      ⏱️  Timebox: {r['timebox_seconds']}s")


def test_custom_workflow():
    """Test workflow with custom data"""
    print_section("3. Test Workflow with Custom Data")
    
    custom_data = {
        "overshoot_data": {
            "timestamp_ms": int(datetime.now(timezone.utc).timestamp() * 1000),
            "person_count": 5,
            "water_level": 85.0,  # High water
            "fire_detected": False,
            "smoke_level": "none",
            "structural_damage": "severe",
            "injured_detected": True,
            "disaster_type": "flood",
        },
        "server_telemetry": {
            "temperature_sensor": 25.0,
            "pressure_sensor_a": 70.0,  # Low pressure (contradicts high water)
        },
    }
    
    with httpx.Client(timeout=30.0) as client:
        resp = client.post(
            f"{BASE_URL}/scenario2/process",
            json=custom_data,
        )
        print(f"Status: {resp.status_code}")
        
        if resp.status_code != 200:
            print(f"Error: {resp.text}")
            return
        
        data = resp.json()
        print("\n📥 Custom Input:")
        print(json.dumps(custom_data["overshoot_data"], indent=2))
        
        print("\n📊 Decision Card Summary:")
        card = data["decision_card"]
        print(f"  Mode: {card['mode']}")
        print(f"  Uncertainty: {card['uncertainty_score']:.2f}")
        print(f"  Summary: {card.get('summary', 'N/A')}")
        print(f"  Contradictions: {len(data['contradictions'])}")
        print(f"  Recommendations: {len(data['action_recommendations'])}")


def main():
    """Run all tests"""
    print("\n🧪 Overshoot.ai API Test Suite")
    print(f"Testing against: {BASE_URL}")
    
    # First, check if server is up
    try:
        with httpx.Client() as client:
            health_resp = client.get(f"{BASE_URL}/health", timeout=2.0)
            if health_resp.status_code != 200:
                print(f"\n⚠️  Server responded with {health_resp.status_code}")
    except httpx.ConnectError:
        print(f"\n❌ Error: Could not connect to {BASE_URL}")
        print("   Make sure the backend server is running:")
        print("   cd apps/backend && python main.py")
        print("\n   Or check if it's running on a different port.")
        sys.exit(1)
    
    try:
        # Test 1: Get mock responses
        test_mock_response()
        
        # Test 2: Test workflow with different scenarios
        for scenario in ["fire", "flood", "normal"]:
            test_workflow(scenario)
        
        # Test 3: Custom data
        test_custom_workflow()
        
        print_section("✅ All Tests Complete")
        print("\n💡 Next Steps:")
        print("  - Test with real Overshoot.ai API (requires API key)")
        print("  - Use POST /scenario2/ingest-and-process to save to CSV")
        print("  - Connect decision cards to frontend Decision Mode UI")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
