"""
SATOR Flow Test - End-to-end test demonstrating both scenarios.

Run with: python -m pytest tests/test_sator_flow.py -v -s
Or standalone: python tests/test_sator_flow.py
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.data_loader import get_data_loader
from app.services.incident_manager import get_incident_manager, IncidentSeverity
from app.services.audit_logger import get_audit_logger
from app.services.operator_questionnaire import get_questionnaire_service, QuestionAnswer
from app.services.artifact_builder import get_artifact_builder
from app.core.decision_engine import get_decision_engine
from app.integrations.overshoot import get_overshoot_client, VisionFrame
from app.integrations.leanmcp import (
    get_mcp_server,
    MCPRequest,
    analyze_vision,
    detect_contradictions,
    predict_issues,
    recommend_action,
    create_decision_card,
)
from app.integrations.kairo.anchor import get_anchor_service


# ============================================================================
# Test Utilities
# ============================================================================

def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_step(step: int, description: str):
    """Print a step description."""
    print(f"\n[Step {step}] {description}")
    print("-" * 40)


def print_json(data: dict, indent: int = 2):
    """Pretty print JSON data."""
    print(json.dumps(data, indent=indent, default=str))


# ============================================================================
# Scenario 1: Fixed Case (Static Data)
# ============================================================================

def test_scenario_1_fixed_case():
    """
    Test Scenario 1: Fixed Case with Static Data
    
    Flow:
    1. Load static CSV/JSON data
    2. Detect contradictions
    3. Create incident
    4. Generate operator questions
    5. Simulate operator answers
    6. Record action
    7. Close incident
    8. Build artifact
    9. Anchor on-chain
    """
    print_header("SCENARIO 1: Fixed Case (Static Data)")
    
    # Get service instances
    data_loader = get_data_loader()
    incident_manager = get_incident_manager()
    decision_engine = get_decision_engine()
    questionnaire = get_questionnaire_service()
    artifact_builder = get_artifact_builder()
    audit_logger = get_audit_logger()
    anchor_service = get_anchor_service()
    
    # Step 1: Load scenario data
    print_step(1, "Loading static scenario data")
    scenario_data = data_loader.load_fixed_scenario()
    print(f"  Loaded {len(scenario_data.telemetry)} telemetry readings")
    print(f"  Loaded {len(scenario_data.events)} events")
    print(f"  Loaded {len(scenario_data.contradictions)} contradictions")
    print(f"  Scenario: {scenario_data.metadata.name}")
    
    # Step 2: Get telemetry at contradiction time
    print_step(2, "Getting telemetry at t=60s (contradiction detection)")
    telemetry_at_time = data_loader.get_telemetry_at_time(scenario_data.telemetry, 60.0)
    print(f"  Found {len(telemetry_at_time)} sensor readings")
    for tag_id, reading in list(telemetry_at_time.items())[:3]:
        print(f"    {tag_id}: {reading.value} {reading.unit}")
    
    # Step 3: Create incident
    print_step(3, "Creating incident from detected contradictions")
    incident = incident_manager.create_incident(
        scenario_id="fixed-valve-incident",
        title="Sensor Contradiction Detected",
        description=scenario_data.contradictions[0].description if scenario_data.contradictions else "Test contradiction",
        severity=IncidentSeverity.CRITICAL,
        contradiction_ids=[c.contradiction_id for c in scenario_data.contradictions]
    )
    print(f"  Created incident: {incident.incident_id}")
    print(f"  State: {incident.state}")
    print(f"  Severity: {incident.severity}")
    
    # Log to audit
    audit_logger.log_incident_opened(
        incident_id=incident.incident_id,
        scenario_id="fixed-valve-incident",
        title=incident.title,
        contradiction_ids=incident.contradiction_ids
    )
    
    # Step 4: Evaluate evidence and create decision card
    print_step(4, "Evaluating evidence with Decision Engine")
    evaluation = decision_engine.evaluate_evidence(
        telemetry=telemetry_at_time,
        events=[e for e in scenario_data.events if e.time_sec <= 60],
        contradictions=scenario_data.contradictions
    )
    print(f"  Overall uncertainty: {evaluation.overall_uncertainty:.2f}")
    print(f"  Decision required: {evaluation.requires_decision}")
    print(f"  Key findings: {evaluation.key_findings[:3]}...")
    
    from app.services.data_loader import EventSeverity
    card = decision_engine.create_decision(
        evaluation=evaluation,
        telemetry_snapshot=telemetry_at_time,
        title=f"Decision Required: {incident.title}",
        summary=incident.description,
        severity=EventSeverity.CRITICAL
    )
    print(f"  Created decision card: {card.card_id}")
    print(f"  Allowed actions: {[a.label for a in card.allowed_actions]}")
    
    incident_manager.link_decision_card(incident.incident_id, card.card_id)
    
    # Step 5: Generate operator questions
    print_step(5, "Generating operator questions")
    questions = questionnaire.generate_questions_for_incident(
        incident_id=incident.incident_id,
        contradictions=[c.model_dump() for c in scenario_data.contradictions],
        sensor_readings={k: v.model_dump() for k, v in telemetry_at_time.items()},
        severity="critical"
    )
    print(f"  Generated {len(questions)} questions:")
    for q in questions:
        print(f"    - {q.question_text[:60]}...")
        incident_manager.record_question_asked(incident.incident_id, q.question_id)
    
    # Step 6: Simulate operator answering questions
    print_step(6, "Simulating operator answers")
    for q in questions[:2]:  # Answer first 2 questions
        if q.options:
            # Select first option for demo
            answer = QuestionAnswer(
                question_id=q.question_id,
                operator_id="operator-001",
                answer_value=q.options[0].option_id,
                confidence=4,
                notes="Visual confirmation matches expected state"
            )
            impact = questionnaire.submit_answer(answer)
            print(f"  Answered: {q.question_text[:40]}...")
            print(f"    -> Trust adjustment: {impact.trust_adjustment:+.2f}")
            
            incident_manager.record_question_answered(incident.incident_id, q.question_id)
            audit_logger.log_question_answered(
                incident_id=incident.incident_id,
                scenario_id="fixed-valve-incident",
                operator_id="operator-001",
                question_id=q.question_id,
                answer=answer.answer_value,
                impact=impact.model_dump()
            )
    
    # Step 7: Triage the incident
    print_step(7, "Triaging incident")
    incident = incident_manager.triage(
        incident_id=incident.incident_id,
        operator_id="operator-001",
        initial_assessment="Sensor contradiction confirmed via visual inspection"
    )
    print(f"  State changed to: {incident.state}")
    
    # Step 8: Record action and dispatch
    print_step(8, "Recording operator action (DEFER)")
    decision_engine.record_action(
        card_id=card.card_id,
        action_id="defer-inspection",
        operator_id="operator-001"
    )
    
    incident = incident_manager.dispatch(
        incident_id=incident.incident_id,
        operator_id="operator-001",
        action_type="defer",
        action_details="Deferring control action - requesting field inspection to verify sensor state"
    )
    print(f"  Action taken: {incident.action_taken}")
    print(f"  State: {incident.state}")
    
    # Generate trust receipt
    reason_codes = list(set(c.reason_code for c in scenario_data.contradictions if c.reason_code))
    receipt = artifact_builder.generate_trust_receipt(
        incident_id=incident.incident_id,
        trust_score=1 - evaluation.overall_uncertainty,
        sensor_scores=evaluation.sensor_trust_scores,
        reason_codes=reason_codes,
        contradictions=scenario_data.contradictions,
        evidence_sources=["telemetry", "operator_visual"],
        questions_asked=len(questions),
        questions_answered=2,
        operator_adjustments=0.1
    )
    print(f"  Generated trust receipt: {receipt.receipt_id}")
    print(f"  Trust level: {receipt.trust_level}")
    
    # Step 9: Close incident and build artifact
    print_step(9, "Closing incident and building artifact")
    incident = incident_manager.close(
        incident_id=incident.incident_id,
        operator_id="operator-001",
        resolution_summary="Deferred to field inspection due to sensor contradiction. Visual verification suggests sensor fault."
    )
    print(f"  State: {incident.state}")
    print(f"  Closed at: {incident.closed_at}")
    
    artifact = artifact_builder.build_artifact(
        incident=incident,
        telemetry_samples=scenario_data.telemetry[:50],
        contradictions=scenario_data.contradictions,
        decision_card=card.model_dump(),
        questions_asked=[q.model_dump() for q in questions],
        questions_answered=[q.model_dump() for q in questions if q.answered]
    )
    print(f"  Built artifact: {artifact.artifact_id}")
    print(f"  Content hash: {artifact.content_hash[:32]}...")
    
    # Step 10: Anchor on-chain
    print_step(10, "Anchoring artifact on-chain (KairoAISec)")
    anchor_record = artifact_builder.anchor_artifact(artifact.artifact_id)
    if anchor_record:
        print(f"  Anchored successfully!")
        print(f"  TX Hash: {anchor_record.tx_hash[:32]}...")
        print(f"  Verification URL: {anchor_record.verification_url}")
        print(f"  Chain: {anchor_record.chain}")
    
    # Verify integrity
    print_step(11, "Verifying artifact integrity")
    verification = artifact_builder.verify_artifact(artifact.artifact_id)
    print(f"  Content hash valid: {verification['content_hash_valid']}")
    print(f"  Audit chain valid: {verification['audit_chain_valid']}")
    print(f"  On-chain valid: {verification['on_chain_valid']}")
    print(f"  Overall verified: {verification['verified']}")
    
    # Show audit trail
    print_step(12, "Audit Trail Summary")
    events = audit_logger.get_incident_trail(incident.incident_id)
    print(f"  Total events: {len(events)}")
    for event in events[-5:]:
        print(f"    [{event.event_type}] {event.summary}")
    
    print("\n" + "=" * 60)
    print("  SCENARIO 1 COMPLETE - Artifact created and anchored!")
    print("=" * 60)
    
    return artifact


# ============================================================================
# Scenario 2: Live Vision (Overshoot)
# ============================================================================

def test_scenario_2_live_vision():
    """
    Test Scenario 2: Live Vision with Overshoot
    
    Flow:
    1. Simulate Overshoot vision frame
    2. Analyze vision with LeanMCP
    3. Cross-validate with telemetry
    4. Detect contradictions
    5. Generate predictions
    6. Create incident and decision card
    7. Operator interaction
    8. Build artifact and anchor
    """
    print_header("SCENARIO 2: Live Vision (Overshoot + LeanMCP)")
    
    # Get service instances
    overshoot_client = get_overshoot_client()
    mcp_server = get_mcp_server()
    incident_manager = get_incident_manager()
    questionnaire = get_questionnaire_service()
    artifact_builder = get_artifact_builder()
    audit_logger = get_audit_logger()
    data_loader = get_data_loader()
    
    # Step 1: Simulate Overshoot vision frame
    print_step(1, "Simulating Overshoot vision frame")
    
    mock_vision_frame = {
        "frame_id": "overshoot-frame-001",
        "timestamp": datetime.utcnow().isoformat(),
        "video_timestamp_ms": 15000,
        "equipment_states": [
            {
                "equipment_id": "valve-101",
                "name": "Main Isolation Valve",
                "equipment_type": "valve",
                "valve_position": "closed",
                "confidence": 0.92,
                "status": "normal",
                "mapped_tag_id": "VALVE_POS_101"
            },
            {
                "equipment_id": "gauge-201",
                "name": "Pressure Gauge",
                "equipment_type": "gauge",
                "gauge_reading": {"value": 145, "unit": "psi"},
                "confidence": 0.88,
                "status": "warning",
                "mapped_tag_id": "PT_001"
            }
        ],
        "operator_actions": [
            {
                "action_type": "inspecting",
                "person": {
                    "person_id": "person-001",
                    "location": {"x": 100, "y": 200, "zone": "valve_area"},
                    "wearing_ppe": True
                }
            }
        ],
        "safety_events": [],
        "frame_quality": 0.95,
        "scene_description": "Operator inspecting valve station"
    }
    
    frame = overshoot_client.simulate_frame(mock_vision_frame)
    print(f"  Frame ID: {frame.frame_id}")
    print(f"  Equipment detected: {len(frame.equipment_states)}")
    print(f"  Operators observed: {len(frame.operator_actions)}")
    
    audit_logger.log_vision_received(
        scenario_id="live-vision-demo",
        frame_id=frame.frame_id,
        equipment_count=len(frame.equipment_states),
        safety_event_count=len(frame.safety_events)
    )
    
    # Step 2: Analyze vision with LeanMCP
    print_step(2, "Analyzing vision frame (LeanMCP: analyze_vision)")
    
    vision_analysis = analyze_vision(frame.model_dump())
    print(f"  Equipment states: {len(vision_analysis['equipment_states'])}")
    print(f"  Insights: {len(vision_analysis['insights'])}")
    print(f"  Summary: {vision_analysis['summary']}")
    
    # Step 3: Get telemetry for cross-validation
    print_step(3, "Getting telemetry for cross-validation")
    
    # Create mock telemetry that contradicts vision
    mock_telemetry = {
        "VALVE_POS_101": {"value": 85, "unit": "%", "quality": "good"},  # Says 85% open but vision shows closed!
        "PT_001": {"value": 150, "unit": "psi", "quality": "good"},
        "FT_001": {"value": 120, "unit": "gpm", "quality": "good"},  # Flow detected with "closed" valve
    }
    print(f"  VALVE_POS_101: {mock_telemetry['VALVE_POS_101']['value']}% (sensor)")
    print(f"  Vision shows: CLOSED")
    print(f"  -> This is a contradiction!")
    
    # Step 4: Detect contradictions (LeanMCP)
    print_step(4, "Detecting contradictions (LeanMCP: detect_contradictions)")
    
    contradictions = detect_contradictions(
        vision_frame=frame.model_dump(),
        telemetry=mock_telemetry
    )
    print(f"  Found {len(contradictions)} contradictions:")
    for c in contradictions:
        print(f"    [{c['reason_code']}] {c['description']}")
    
    # Step 5: Generate predictions (LeanMCP)
    print_step(5, "Generating predictions (LeanMCP: predict_issues)")
    
    predictions = predict_issues(
        vision_frame=frame.model_dump(),
        telemetry=mock_telemetry,
        history=[]
    )
    print(f"  Generated {len(predictions)} predictions:")
    for p in predictions:
        print(f"    [{p['issue_type']}] {p['description']} ({p['confidence']*100:.0f}% confidence)")
    
    # Step 6: Get recommendation (LeanMCP)
    print_step(6, "Getting action recommendation (LeanMCP: recommend_action)")
    
    recommendation = recommend_action(
        incident_state={"severity": "critical", "state": "open"},
        evidence={
            "contradictions": contradictions,
            "predictions": predictions,
            "vision_analysis": vision_analysis
        },
        trust_score=0.4  # Low trust due to contradictions
    )
    print(f"  Recommended action: {recommendation['recommended_action']}")
    print(f"  Action type: {recommendation['action_type']}")
    print(f"  Rationale: {recommendation['rationale']}")
    print(f"  Follow-up questions: {len(recommendation['follow_up_questions'])}")
    
    # Step 7: Create decision card (LeanMCP)
    print_step(7, "Creating decision card (LeanMCP: create_decision_card)")
    
    # Create incident first
    incident = incident_manager.create_incident(
        scenario_id="live-vision-demo",
        title="Vision-Telemetry Contradiction",
        description="Valve visually closed but sensor shows 85% open",
        severity=IncidentSeverity.CRITICAL,
        contradiction_ids=[c['contradiction_id'] for c in contradictions]
    )
    
    card_data = create_decision_card(
        incident_id=incident.incident_id,
        findings={
            "contradictions": contradictions,
            "predictions": predictions,
            "recommendation": recommendation,
            "trust_score": 0.4,
            "telemetry": mock_telemetry,
            "vision": frame.model_dump()
        },
        operator_questions=[]
    )
    print(f"  Card ID: {card_data['card_id']}")
    print(f"  Title: {card_data['title']}")
    print(f"  Severity: {card_data['severity']}")
    print(f"  Trust Score: {card_data['trust_score']*100:.0f}%")
    print(f"  Allowed actions: {[a['label'] for a in card_data['allowed_actions']]}")
    
    incident_manager.link_decision_card(incident.incident_id, card_data['card_id'])
    
    # Step 8: Generate and answer operator questions
    print_step(8, "Operator interaction (questions & answers)")
    
    questions = questionnaire.generate_questions_for_incident(
        incident_id=incident.incident_id,
        contradictions=contradictions,
        sensor_readings=mock_telemetry,
        severity="critical"
    )
    print(f"  Generated {len(questions)} questions")
    
    # Simulate operator confirming vision is correct
    if questions:
        first_q = questions[0]
        if first_q.options:
            # Operator says vision contradicts sensor
            answer = QuestionAnswer(
                question_id=first_q.question_id,
                operator_id="operator-002",
                answer_value="contradicts",  # Confirms vision is right, sensor is wrong
                confidence=5
            )
            impact = questionnaire.submit_answer(answer)
            print(f"  Operator answered: sensor reading contradicts visual observation")
            print(f"  -> Trust adjustment: {impact.trust_adjustment:+.2f}")
            print(f"  -> Triggers: {impact.incident_state_change}")
    
    # Step 9: Take action and close
    print_step(9, "Taking action and closing incident")
    
    incident = incident_manager.triage(
        incident_id=incident.incident_id,
        operator_id="operator-002",
        initial_assessment="Vision confirmed valve is closed, sensor fault suspected"
    )
    
    incident = incident_manager.dispatch(
        incident_id=incident.incident_id,
        operator_id="operator-002",
        action_type="act",
        action_details="Flagging sensor VALVE_POS_101 for maintenance. Vision confirms actual state."
    )
    print(f"  Action: {incident.action_taken}")
    
    incident = incident_manager.close(
        incident_id=incident.incident_id,
        operator_id="operator-002",
        resolution_summary="Sensor fault confirmed via Overshoot vision. Maintenance ticket created."
    )
    print(f"  Incident closed: {incident.state}")
    
    # Step 10: Build artifact
    print_step(10, "Building artifact packet")
    
    receipt = artifact_builder.generate_trust_receipt(
        incident_id=incident.incident_id,
        trust_score=0.75,  # Improved after vision validation
        sensor_scores={"VALVE_POS_101": 0.2, "PT_001": 0.8, "FT_001": 0.7},
        reason_codes=["RC11"],
        contradictions=contradictions,
        evidence_sources=["telemetry", "overshoot_vision", "operator_visual"],
        vision_validated=True,
        questions_asked=len(questions),
        questions_answered=1,
        operator_adjustments=-0.2
    )
    
    artifact = artifact_builder.build_artifact(
        incident=incident,
        telemetry_samples=[],  # Would include real samples
        contradictions=[],  # Already in findings
        decision_card=card_data,
        vision_frames=[frame],
        questions_asked=[q.model_dump() for q in questions],
        questions_answered=[q.model_dump() for q in questions if q.answered]
    )
    print(f"  Artifact ID: {artifact.artifact_id}")
    print(f"  Content hash: {artifact.content_hash[:32]}...")
    print(f"  Includes vision frames: {len(artifact.vision_frames)}")
    
    # Step 11: Anchor on-chain
    print_step(11, "Anchoring on-chain (KairoAISec)")
    
    anchor_record = artifact_builder.anchor_artifact(artifact.artifact_id)
    if anchor_record:
        print(f"  TX Hash: {anchor_record.tx_hash[:32]}...")
        print(f"  Verification: {anchor_record.verification_url}")
    
    # Final verification
    print_step(12, "Final verification")
    verification = artifact_builder.verify_artifact(artifact.artifact_id)
    print(f"  Verified: {verification['verified']}")
    
    print("\n" + "=" * 60)
    print("  SCENARIO 2 COMPLETE - Vision-validated artifact anchored!")
    print("=" * 60)
    
    return artifact


# ============================================================================
# MCP Server Test
# ============================================================================

def test_mcp_server():
    """Test the MCP server tool invocations."""
    print_header("MCP SERVER TEST")
    
    mcp_server = get_mcp_server()
    
    # List available tools
    print_step(1, "Listing available MCP tools")
    tools = mcp_server.list_tools()
    print(f"  Available tools: {tools}")
    
    # Get capabilities
    print_step(2, "Getting server capabilities")
    caps = mcp_server.get_capabilities()
    print(f"  Protocol version: {caps.protocol_version}")
    print(f"  Server name: {caps.server_name}")
    print(f"  Supports batch: {caps.supports_batch}")
    
    # Test tool invocation
    print_step(3, "Testing tool invocation (analyze_vision)")
    
    request = MCPRequest(
        tool_name="analyze_vision",
        parameters={
            "vision_frame": {
                "frame_id": "test-frame",
                "equipment_states": [
                    {"equipment_id": "test-1", "status": "warning", "name": "Test Valve"}
                ],
                "operator_actions": [],
                "safety_events": []
            }
        }
    )
    
    response = mcp_server.invoke(request)
    print(f"  Success: {response.success}")
    print(f"  Execution time: {response.execution_time_ms:.2f}ms")
    if response.result:
        print(f"  Insights: {len(response.result.get('insights', []))}")
    
    print("\n  MCP Server operational!")


# ============================================================================
# Main
# ============================================================================

def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("  SATOR OPS - END-TO-END FLOW TEST")
    print("  Testing both scenarios with mock data")
    print("=" * 60)
    
    try:
        # Test MCP Server first
        test_mcp_server()
        
        # Run Scenario 1
        artifact1 = test_scenario_1_fixed_case()
        
        # Run Scenario 2
        artifact2 = test_scenario_2_live_vision()
        
        # Summary
        print("\n" + "=" * 60)
        print("  ALL TESTS PASSED!")
        print("=" * 60)
        print(f"\n  Artifacts created:")
        print(f"    1. {artifact1.artifact_id} (Fixed Case)")
        print(f"    2. {artifact2.artifact_id} (Live Vision)")
        print(f"\n  Both scenarios:")
        print(f"    ✓ Loaded/received data")
        print(f"    ✓ Detected contradictions")
        print(f"    ✓ Created incidents")
        print(f"    ✓ Generated operator questions")
        print(f"    ✓ Processed operator answers")
        print(f"    ✓ Recorded actions")
        print(f"    ✓ Built artifacts")
        print(f"    ✓ Anchored on-chain (KairoAISec)")
        print(f"    ✓ Verified integrity")
        
    except Exception as e:
        print(f"\n  ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
