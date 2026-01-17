"""
Temporal Reasoning API Routes.

Provides endpoints for advanced temporal analysis:
- Trust evolution analysis
- Audit chain verification
- Contradiction pattern analysis
- Decision provenance
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Query

from app.core.temporal_reasoning import temporal_reasoning_engine


router = APIRouter()


@router.get("/summary")
async def get_summary(run_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Get summary statistics for temporal reasoning data.
    
    Returns counts of trust updates, contradictions, receipts, audit events, etc.
    """
    return temporal_reasoning_engine.get_summary(run_id)


@router.get("/trust-evolution/{tag_id}")
async def analyze_trust_evolution(
    tag_id: str,
    run_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Analyze trust evolution for a specific sensor.
    
    Returns:
    - Start/end scores
    - Total degradation
    - Degradation rate (per second)
    - Time to quarantine
    - Significant drops
    - Evolution curve
    """
    analysis = temporal_reasoning_engine.analyze_trust_evolution(tag_id, run_id)
    
    return {
        "tag_id": analysis.tag_id,
        "start_score": analysis.start_score,
        "end_score": analysis.end_score,
        "total_degradation": analysis.total_degradation,
        "degradation_rate": round(analysis.degradation_rate, 4),
        "time_to_quarantine": analysis.time_to_quarantine,
        "significant_drops": [
            {
                "time_sec": p.time_sec,
                "trust_score": p.trust_score,
                "trust_state": p.trust_state,
                "reason_codes": p.reason_codes,
                "delta": p.delta,
            }
            for p in analysis.significant_drops
        ],
        "evolution_curve": [
            {
                "time_sec": p.time_sec,
                "trust_score": p.trust_score,
                "trust_state": p.trust_state,
            }
            for p in analysis.evolution_curve
        ],
    }


@router.get("/audit-chains")
async def verify_audit_chains(
    chain_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Verify integrity of audit event chains.
    
    Returns verification results for each chain, including:
    - Is valid (all hashes link correctly)
    - Total events
    - Broken links if any
    """
    results = temporal_reasoning_engine.verify_audit_chain(chain_id)
    
    return [
        {
            "chain_id": r.chain_id,
            "run_id": r.run_id,
            "total_events": r.total_events,
            "is_valid": r.is_valid,
            "broken_links_count": len(r.broken_links),
            "first_event_time": r.first_event.timestamp.isoformat() if r.first_event else None,
            "last_event_time": r.last_event.timestamp.isoformat() if r.last_event else None,
        }
        for r in results
    ]


@router.get("/contradiction-patterns")
async def analyze_contradiction_patterns(
    run_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Analyze patterns in contradictions.
    
    Returns:
    - Count per reason code
    - First occurrence time
    - Affected sensors
    - Whether it cascaded to other contradictions
    """
    patterns = temporal_reasoning_engine.analyze_contradiction_patterns(run_id)
    
    return [
        {
            "reason_code": p.reason_code,
            "count": p.count,
            "first_occurrence_sec": p.first_occurrence,
            "affected_sensors": p.affected_sensors,
            "average_gap_sec": round(p.average_gap, 2),
            "cascading": p.cascading,
        }
        for p in patterns
    ]


@router.get("/decision-provenance")
async def get_decision_provenance(
    receipt_id: Optional[str] = None,
    time_sec: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """
    Get decision provenance - the evidence chain that led to a decision.
    
    Returns receipts with their related:
    - Contradictions that were active
    - Trust degradations that occurred
    """
    return temporal_reasoning_engine.get_decision_provenance(receipt_id, time_sec)
