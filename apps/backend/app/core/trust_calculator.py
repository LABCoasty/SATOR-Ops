"""
Trust Calculator - Evidence trust scoring and conflict detection.

Implements the core trust scoring algorithm for SATOR-Ops:
- Source reliability weighting
- Recency decay
- Corroboration bonus
- Contradiction detection and penalty
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from enum import Enum
import math


class TrustLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    CONFLICTING = "conflicting"


@dataclass
class EvidenceInput:
    """Input evidence for trust calculation."""
    id: str
    source: str
    value: float
    timestamp: datetime
    source_reliability: float = 0.8  # 0-1 scale
    metadata: Optional[dict] = None


@dataclass
class TrustResult:
    """Result of trust calculation for a single evidence piece."""
    evidence_id: str
    raw_score: float
    adjusted_score: float
    trust_level: TrustLevel
    factors: dict


@dataclass
class Conflict:
    """Detected conflict between evidence pieces."""
    evidence_ids: List[str]
    conflict_type: str
    description: str
    severity: float  # 0-1 scale
    resolution: Optional[str] = None


class TrustCalculator:
    """
    Calculates trust scores for evidence and detects conflicts.
    
    Trust Score Formula:
    T = (R * W_r) * (F * W_f) * (C * W_c) - (P * W_p)
    
    Where:
    - R = Source reliability (0-1)
    - F = Freshness decay (0-1, based on age)
    - C = Corroboration bonus (1.0 - 1.3)
    - P = Contradiction penalty (0-0.3)
    - W_* = Weights for each factor
    """
    
    # Configuration weights
    RELIABILITY_WEIGHT = 0.4
    FRESHNESS_WEIGHT = 0.25
    CORROBORATION_WEIGHT = 0.2
    CONTRADICTION_WEIGHT = 0.15
    
    # Thresholds
    FRESHNESS_HALF_LIFE_MINUTES = 30  # Score halves every 30 minutes
    CONFLICT_THRESHOLD = 0.15  # 15% deviation = conflict
    HIGH_TRUST_THRESHOLD = 0.85
    MEDIUM_TRUST_THRESHOLD = 0.70
    
    def __init__(self, source_reliability_map: Optional[dict] = None):
        """
        Initialize with optional source reliability overrides.
        
        Args:
            source_reliability_map: Dict mapping source names to reliability scores
        """
        self.source_reliability = source_reliability_map or {
            "primary_sensor_array": 0.98,
            "backup_telemetry": 0.95,
            "external_feed_alpha": 0.87,
            "external_feed_beta": 0.72,
            "legacy_system_link": 0.65,
            "remote_station_c": 0.0,  # Offline
            "operator_manual": 0.90,
        }
    
    def get_source_reliability(self, source: str) -> float:
        """Get reliability score for a source."""
        # Normalize source name
        normalized = source.lower().replace(" ", "_").replace("-", "_")
        return self.source_reliability.get(normalized, 0.75)  # Default 0.75
    
    def calculate_freshness(self, timestamp: datetime, now: Optional[datetime] = None) -> float:
        """
        Calculate freshness decay based on evidence age.
        Uses exponential decay with configurable half-life.
        """
        now = now or datetime.utcnow()
        age_minutes = (now - timestamp).total_seconds() / 60
        
        # Exponential decay: score = 2^(-age/half_life)
        decay = math.pow(2, -age_minutes / self.FRESHNESS_HALF_LIFE_MINUTES)
        return max(0.1, min(1.0, decay))  # Clamp between 0.1 and 1.0
    
    def calculate_corroboration(
        self, 
        evidence: EvidenceInput, 
        all_evidence: List[EvidenceInput]
    ) -> Tuple[float, List[str]]:
        """
        Calculate corroboration bonus based on supporting evidence.
        
        Returns:
            Tuple of (corroboration_score, list of corroborating evidence IDs)
        """
        corroborating_ids = []
        
        for other in all_evidence:
            if other.id == evidence.id:
                continue
            
            # Check if values are within acceptable range (not conflicting)
            if evidence.value != 0:
                deviation = abs(other.value - evidence.value) / abs(evidence.value)
                if deviation < self.CONFLICT_THRESHOLD:
                    corroborating_ids.append(other.id)
        
        # Corroboration bonus: 1.0 base + 0.05 per corroborating source (max 1.3)
        bonus = 1.0 + (len(corroborating_ids) * 0.05)
        return min(1.3, bonus), corroborating_ids
    
    def calculate_trust(
        self, 
        evidence: EvidenceInput,
        all_evidence: Optional[List[EvidenceInput]] = None,
        now: Optional[datetime] = None
    ) -> TrustResult:
        """
        Calculate trust score for a single piece of evidence.
        
        Args:
            evidence: The evidence to score
            all_evidence: All evidence for corroboration calculation
            now: Current time (for testing)
        
        Returns:
            TrustResult with detailed scoring breakdown
        """
        all_evidence = all_evidence or [evidence]
        now = now or datetime.utcnow()
        
        # Calculate individual factors
        reliability = self.get_source_reliability(evidence.source)
        freshness = self.calculate_freshness(evidence.timestamp, now)
        corroboration, corroborating_ids = self.calculate_corroboration(evidence, all_evidence)
        
        # Check for contradictions
        conflicts = self.detect_conflicts([evidence] + [e for e in all_evidence if e.id != evidence.id])
        contradiction_penalty = 0.0
        for conflict in conflicts:
            if evidence.id in conflict.evidence_ids:
                contradiction_penalty = max(contradiction_penalty, conflict.severity * 0.3)
        
        # Calculate raw score (before weighting)
        raw_score = reliability * freshness * corroboration
        
        # Calculate weighted final score
        weighted_score = (
            (reliability * self.RELIABILITY_WEIGHT) +
            (freshness * self.FRESHNESS_WEIGHT) +
            ((corroboration - 1.0) * 3 * self.CORROBORATION_WEIGHT) +  # Normalize corroboration
            (1.0 - contradiction_penalty) * self.CONTRADICTION_WEIGHT
        )
        
        # Normalize to 0-1
        adjusted_score = max(0.0, min(1.0, weighted_score + 0.3))  # Base offset
        
        # Determine trust level
        if contradiction_penalty > 0.1:
            trust_level = TrustLevel.CONFLICTING
        elif adjusted_score >= self.HIGH_TRUST_THRESHOLD:
            trust_level = TrustLevel.HIGH
        elif adjusted_score >= self.MEDIUM_TRUST_THRESHOLD:
            trust_level = TrustLevel.MEDIUM
        else:
            trust_level = TrustLevel.LOW
        
        return TrustResult(
            evidence_id=evidence.id,
            raw_score=round(raw_score, 4),
            adjusted_score=round(adjusted_score, 4),
            trust_level=trust_level,
            factors={
                "reliability": round(reliability, 4),
                "freshness": round(freshness, 4),
                "corroboration": round(corroboration, 4),
                "corroborating_evidence": corroborating_ids,
                "contradiction_penalty": round(contradiction_penalty, 4),
            }
        )
    
    def detect_conflicts(self, evidence_list: List[EvidenceInput]) -> List[Conflict]:
        """
        Detect conflicts between evidence pieces.
        
        Groups evidence by source type and checks for value deviations.
        """
        conflicts = []
        
        # Group by similar metrics (simplified: just compare all)
        for i, ev1 in enumerate(evidence_list):
            for ev2 in evidence_list[i+1:]:
                if ev1.value == 0 or ev2.value == 0:
                    continue
                
                deviation = abs(ev1.value - ev2.value) / max(abs(ev1.value), abs(ev2.value))
                
                if deviation > self.CONFLICT_THRESHOLD:
                    severity = min(1.0, deviation / 0.5)  # Normalize to 0-1
                    
                    # Determine resolution based on reliability
                    r1 = self.get_source_reliability(ev1.source)
                    r2 = self.get_source_reliability(ev2.source)
                    
                    if r1 > r2:
                        resolution = f"Using {ev1.source} (reliability: {r1:.2f})"
                    elif r2 > r1:
                        resolution = f"Using {ev2.source} (reliability: {r2:.2f})"
                    else:
                        resolution = "Using weighted average"
                    
                    conflicts.append(Conflict(
                        evidence_ids=[ev1.id, ev2.id],
                        conflict_type="value_deviation",
                        description=f"{ev1.source} ({ev1.value}) vs {ev2.source} ({ev2.value})",
                        severity=round(severity, 4),
                        resolution=resolution,
                    ))
        
        return conflicts
    
    def aggregate_trust(self, results: List[TrustResult]) -> dict:
        """
        Aggregate multiple trust results into a composite score.
        
        Returns:
            Dict with composite score, confidence, and breakdown
        """
        if not results:
            return {
                "composite_score": 0.0,
                "confidence": 0.0,
                "num_sources": 0,
                "trust_level": TrustLevel.LOW,
            }
        
        # Weighted average by individual scores
        total_weight = sum(r.adjusted_score for r in results)
        if total_weight == 0:
            composite = 0.0
        else:
            composite = sum(r.adjusted_score ** 2 for r in results) / total_weight
        
        # Confidence based on number of sources and agreement
        num_sources = len(results)
        score_variance = sum((r.adjusted_score - composite) ** 2 for r in results) / num_sources
        confidence = min(1.0, (num_sources / 5) * (1 - score_variance))
        
        # Determine overall trust level
        conflicting_count = sum(1 for r in results if r.trust_level == TrustLevel.CONFLICTING)
        if conflicting_count > len(results) / 3:
            trust_level = TrustLevel.CONFLICTING
        elif composite >= self.HIGH_TRUST_THRESHOLD:
            trust_level = TrustLevel.HIGH
        elif composite >= self.MEDIUM_TRUST_THRESHOLD:
            trust_level = TrustLevel.MEDIUM
        else:
            trust_level = TrustLevel.LOW
        
        return {
            "composite_score": round(composite, 4),
            "confidence": round(confidence, 4),
            "num_sources": num_sources,
            "trust_level": trust_level,
            "individual_scores": [
                {"id": r.evidence_id, "score": r.adjusted_score, "level": r.trust_level}
                for r in results
            ],
        }


# Singleton instance for app-wide use
trust_calculator = TrustCalculator()
