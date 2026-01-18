#!/usr/bin/env python3
"""
Test script to diagnose scenario issues.

This script tests:
1. Data loading
2. Scenario start
3. Service initialization
4. Common error conditions
"""

import sys
import os
import traceback

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_data_loader():
    """Test if data loader works"""
    print("\n" + "="*60)
    print("TEST 1: Data Loader")
    print("="*60)
    try:
        from app.services.data_loader import get_data_loader
        
        loader = get_data_loader()
        print(f"✅ Data loader initialized")
        print(f"   Data directory: {loader.data_dir}")
        print(f"   CSV directory: {loader.csv_dir}")
        
        # Check if files exist
        required_files = [
            "telemetry.csv",
            "events.csv",
            "contradictions.json"
        ]
        
        for filename in required_files:
            filepath = loader.csv_dir / filename
            if filepath.exists():
                print(f"   ✅ {filename} exists")
            else:
                print(f"   ❌ {filename} MISSING at {filepath}")
        
        # Try loading scenario
        print("\n   Attempting to load fixed scenario...")
        scenario_data = loader.load_fixed_scenario()
        print(f"   ✅ Scenario loaded successfully!")
        print(f"      - Telemetry readings: {len(scenario_data.telemetry)}")
        print(f"      - Events: {len(scenario_data.events)}")
        print(f"      - Contradictions: {len(scenario_data.contradictions)}")
        print(f"      - Scenario: {scenario_data.metadata.name}")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        traceback.print_exc()
        return False

def test_services():
    """Test if all services initialize"""
    print("\n" + "="*60)
    print("TEST 2: Service Initialization")
    print("="*60)
    
    services_to_test = [
        ("Incident Manager", "app.services.incident_manager", "get_incident_manager"),
        ("Decision Engine", "app.core.decision_engine", "get_decision_engine"),
        ("Audit Logger", "app.services.audit_logger", "get_audit_logger"),
        ("Questionnaire Service", "app.services.operator_questionnaire", "get_questionnaire_service"),
    ]
    
    all_ok = True
    for name, module_path, func_name in services_to_test:
        try:
            module = __import__(module_path, fromlist=[func_name])
            func = getattr(module, func_name)
            service = func()
            print(f"   ✅ {name} initialized")
        except Exception as e:
            print(f"   ❌ {name} failed: {e}")
            all_ok = False
    
    return all_ok

def test_scenario_start():
    """Test starting a scenario via API"""
    print("\n" + "="*60)
    print("TEST 3: Scenario Start (API)")
    print("="*60)
    
    try:
        import httpx
        
        base_url = "http://localhost:8000"
        
        # Check if server is running
        print("   Checking if server is running...")
        with httpx.Client(timeout=2.0) as client:
            health_resp = client.get(f"{base_url}/health")
            if health_resp.status_code != 200:
                print(f"   ❌ Server health check failed: {health_resp.status_code}")
                return False
            print("   ✅ Server is running")
        
        # List scenarios
        print("\n   Listing available scenarios...")
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(f"{base_url}/api/scenarios")
            if resp.status_code == 200:
                scenarios = resp.json()
                print(f"   ✅ Found {len(scenarios)} scenarios:")
                for s in scenarios:
                    print(f"      - {s['scenario_id']}: {s['name']}")
            else:
                print(f"   ❌ Failed to list scenarios: {resp.status_code}")
                print(f"      Response: {resp.text[:200]}")
                return False
        
        # Try to start a scenario
        print("\n   Attempting to start 'fixed-valve-incident'...")
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(
                f"{base_url}/api/scenarios/fixed-valve-incident/start",
                json={"operator_id": "test-operator"},
                timeout=10.0
            )
            if resp.status_code == 200:
                result = resp.json()
                print(f"   ✅ Scenario started successfully!")
                print(f"      Status: {result.get('status', {}).get('status')}")
                print(f"      Message: {result.get('message')}")
                return True
            else:
                print(f"   ❌ Failed to start scenario: {resp.status_code}")
                print(f"      Response: {resp.text[:500]}")
                return False
                
    except httpx.ConnectError:
        print("   ❌ Could not connect to server")
        print("      Make sure the server is running: cd apps/backend && python main.py")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        traceback.print_exc()
        return False

def main():
    print("\n" + "="*60)
    print("SATOR Ops - Scenario Diagnostic Test")
    print("="*60)
    
    results = []
    
    # Test 1: Data Loader
    results.append(("Data Loader", test_data_loader()))
    
    # Test 2: Services
    results.append(("Service Initialization", test_services()))
    
    # Test 3: API
    results.append(("Scenario Start API", test_scenario_start()))
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("✅ All tests passed! Your app should be working.")
    else:
        print("❌ Some tests failed. Check the errors above.")
        print("\nCommon fixes:")
        print("1. Make sure data files exist in app/data/csv/")
        print("2. Make sure server is running: python main.py")
        print("3. Check server logs for errors")
        print("4. Verify all dependencies are installed: pip install -r requirements.txt")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
