#!/usr/bin/env python3
"""
Quick test to verify scenario functionality without API.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_scenario_flow():
    """Test the scenario flow directly"""
    print("Testing scenario flow...")
    
    try:
        from app.services.data_loader import get_data_loader
        from app.services.incident_manager import get_incident_manager
        from app.core.decision_engine import get_decision_engine
        
        # Load data
        print("1. Loading scenario data...")
        loader = get_data_loader()
        scenario_data = loader.load_fixed_scenario()
        print(f"   ✅ Loaded {len(scenario_data.telemetry)} telemetry readings")
        print(f"   ✅ Loaded {len(scenario_data.contradictions)} contradictions")
        
        # Create incident
        print("\n2. Creating incident...")
        incident_manager = get_incident_manager()
        incident = incident_manager.create_incident(
            scenario_id="fixed-valve-incident",
            title="Sensor Contradiction Detected",
            description=scenario_data.contradictions[0].description,
            severity="CRITICAL",
            contradiction_ids=[c.contradiction_id for c in scenario_data.contradictions]
        )
        print(f"   ✅ Incident created: {incident.incident_id}")
        
        # Get telemetry at time
        print("\n3. Getting telemetry at t=60s...")
        telemetry_at_time = loader.get_telemetry_at_time(scenario_data.telemetry, 60.0)
        print(f"   ✅ Found {len(telemetry_at_time)} sensor readings")
        
        # Evaluate evidence
        print("\n4. Evaluating evidence...")
        decision_engine = get_decision_engine()
        evaluation = decision_engine.evaluate_evidence(
            telemetry=telemetry_at_time,
            events=[e for e in scenario_data.events if e.time_sec <= 60],
            contradictions=scenario_data.contradictions
        )
        print(f"   ✅ Evidence evaluated: {evaluation.uncertainty_level}")
        
        # Create decision card
        print("\n5. Creating decision card...")
        card = decision_engine.create_decision(
            evaluation=evaluation,
            telemetry_snapshot=telemetry_at_time,
            title=f"Decision Required: {incident.title}",
            summary=incident.description,
            severity="critical",
            scenario_id="fixed-valve-incident",
            incident_id=incident.incident_id
        )
        print(f"   ✅ Decision card created: {card.card_id}")
        
        print("\n✅ All tests passed! Scenario flow is working.")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_scenario_flow()
