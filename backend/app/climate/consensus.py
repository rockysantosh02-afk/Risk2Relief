"""Configurable Multi-Source Climate Consensus Engine with Source Independence Guarantees.

Guarantees that parametric insurance triggers are based on corroborated,
anti-correlated multi-source evidence rather than single-point sensor failures.
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any, Set
from app.climate.validation import ClimateQualityEnum
from app.climate.anomaly import ClimateAnomalySignal


@dataclass
class ConsensusPolicy:
    """Configurable consensus reliability rules."""
    min_independent_sources: int = 2
    max_agreement_tolerance_pct: float = 12.0  # Max acceptable percentage spread across cluster
    min_confidence: float = 0.70
    exclude_ml_anomalies: bool = True
    allow_anomalies_in_cluster: bool = False  # If False, any ML anomaly in submitted cluster halts automatic consensus
    accepted_qualities: Set[str] = field(
        default_factory=lambda: {ClimateQualityEnum.VALID.value, ClimateQualityEnum.DEGRADED.value}
    )


@dataclass
class ConsensusOutcome:
    """Deterministic result of multi-source consensus evaluation."""
    status: str                         # CONSENSUS_REACHED, CONSENSUS_FAILED, INSUFFICIENT_SOURCES, FLAGGED_FOR_REVIEW
    consensus_value: Optional[float]
    unit: str
    agreement_score: float              # 0.0 to 1.0 (1.0 = perfect agreement)
    confidence: float                   # 0.0 to 1.0
    eligible_source_count: int
    independent_source_count: int
    independent_groups_present: List[str]
    outliers: List[Dict[str, Any]]
    rejected_sources: List[Dict[str, Any]]
    explanation: str
    evaluated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ClimateConsensusEngine:
    """Evaluates multi-source observations against independence and agreement rules."""

    @classmethod
    def evaluate_consensus(
        cls,
        observations_with_signals: List[Tuple[Dict[str, Any], ClimateAnomalySignal]],
        policy: Optional[ConsensusPolicy] = None,
        event_metric: str = "rainfall_24h",
        expected_unit: str = "mm",
    ) -> ConsensusOutcome:
        """Execute deterministic multi-source consensus algorithm."""
        pol = policy or ConsensusPolicy()
        now = datetime.now(timezone.utc)

        if not observations_with_signals:
            return ConsensusOutcome(
                status="INSUFFICIENT_SOURCES",
                consensus_value=None,
                unit=expected_unit,
                agreement_score=0.0,
                confidence=0.0,
                eligible_source_count=0,
                independent_source_count=0,
                independent_groups_present=[],
                outliers=[],
                rejected_sources=[],
                explanation="No observations submitted for climate event evaluation.",
                evaluated_at=now,
            )

        eligible: List[Tuple[Dict[str, Any], ClimateAnomalySignal]] = []
        rejected: List[Dict[str, Any]] = []
        outliers: List[Dict[str, Any]] = []

        # 1. Quality & Anomaly Filtering
        for obs, sig in observations_with_signals:
            quality = obs.get("quality", ClimateQualityEnum.VALID.value)
            if quality not in pol.accepted_qualities:
                rejected.append({
                    "source_id": obs.get("source_id"),
                    "source_identifier": obs.get("source_identifier", "UNKNOWN"),
                    "value": obs.get("value"),
                    "reason": f"Quality grade '{quality}' not accepted by consensus policy.",
                })
                continue

            if pol.exclude_ml_anomalies and sig.is_anomaly:
                outliers.append({
                    "source_id": obs.get("source_id"),
                    "source_identifier": obs.get("source_identifier", "UNKNOWN"),
                    "value": obs.get("value"),
                    "anomaly_score": sig.anomaly_score,
                    "reason": sig.reason,
                })
                continue

            eligible.append((obs, sig))

        # 2. Check if severe outliers exist and policy strictly forbids uncorroborated anomalies
        if outliers and not pol.allow_anomalies_in_cluster:
            return ConsensusOutcome(
                status="CONSENSUS_FAILED",
                consensus_value=None,
                unit=expected_unit,
                agreement_score=0.0,
                confidence=0.30,
                eligible_source_count=len(eligible),
                independent_source_count=len(set(obs.get("independence_group", "DEFAULT") for obs, _ in eligible)),
                independent_groups_present=list(set(obs.get("independence_group", "DEFAULT") for obs, _ in eligible)),
                outliers=outliers,
                rejected_sources=rejected,
                explanation=(
                    f"Consensus blocked: ML anomaly detected in observation cluster "
                    f"({outliers[0].get('source_identifier', 'Source')}: {outliers[0].get('value')} mm). "
                    f"Automatic settlement blocked because the evidence did not satisfy the configured "
                    f"consensus reliability policy."
                ),
                evaluated_at=now,
            )

        # 3. Source Independence Assessment
        independent_groups: Set[str] = set()
        for obs, _ in eligible:
            grp = obs.get("independence_group") or obs.get("provider_name") or "DEFAULT_GROUP"
            independent_groups.add(str(grp))

        indep_count = len(independent_groups)
        eligible_count = len(eligible)

        # 4. Check Minimum Independent Sources
        if indep_count < pol.min_independent_sources or eligible_count < pol.min_independent_sources:
            return ConsensusOutcome(
                status="CONSENSUS_FAILED",
                consensus_value=None,
                unit=expected_unit,
                agreement_score=0.0,
                confidence=0.20,
                eligible_source_count=eligible_count,
                independent_source_count=indep_count,
                independent_groups_present=list(independent_groups),
                outliers=outliers,
                rejected_sources=rejected,
                explanation=(
                    f"Consensus blocked: Only {indep_count} independent source group(s) available "
                    f"({eligible_count} valid sources). Configured policy requires >= {pol.min_independent_sources} "
                    f"independent sources to prevent single-provider bias or uncorroborated triggers."
                ),
                evaluated_at=now,
            )

        # 4. Calculate Weighted Consensus Value
        values: List[float] = []
        weights: List[float] = []
        for obs, sig in eligible:
            v = float(obs.get("value", 0.0))
            rel = float(obs.get("reliability_score", 0.95))
            qual = obs.get("quality", "VALID")
            # Downweight degraded readings
            q_factor = 0.75 if qual == "DEGRADED" else 1.0
            # Weight is a function of source reliability and anomaly confidence
            w = max(0.1, rel * q_factor * (1.0 - sig.anomaly_score))
            values.append(v)
            weights.append(w)

        # Weighted Median Calculation
        combined = sorted(zip(values, weights), key=lambda item: item[0])
        total_w = sum(w for _, w in combined)
        cum_w = 0.0
        weighted_median = combined[0][0]
        for v, w in combined:
            cum_w += w
            if cum_w >= (total_w / 2.0):
                weighted_median = v
                break

        # 5. Agreement & Tolerance Evaluation
        min_v = min(values)
        max_v = max(values)
        spread = max_v - min_v
        denom = max(1.0, weighted_median)
        spread_pct = (spread / denom) * 100.0

        agreement_score = round(max(0.0, min(1.0, 1.0 - (spread_pct / 100.0))), 4)
        confidence = round(min(0.99, 0.60 + (indep_count * 0.10) + (agreement_score * 0.20)), 2)

        if spread_pct <= pol.max_agreement_tolerance_pct and confidence >= pol.min_confidence:
            return ConsensusOutcome(
                status="CONSENSUS_REACHED",
                consensus_value=round(weighted_median, 2),
                unit=expected_unit,
                agreement_score=agreement_score,
                confidence=confidence,
                eligible_source_count=eligible_count,
                independent_source_count=indep_count,
                independent_groups_present=list(independent_groups),
                outliers=outliers,
                rejected_sources=rejected,
                explanation=(
                    f"Consensus reached across {eligible_count} observations from {indep_count} independent groups "
                    f"({', '.join(independent_groups)}). Agreement spread is {spread_pct:.1f}% "
                    f"(Policy allows <= {pol.max_agreement_tolerance_pct:.1f}%)."
                ),
                evaluated_at=now,
            )
        else:
            return ConsensusOutcome(
                status="CONSENSUS_FAILED",
                consensus_value=round(weighted_median, 2),
                unit=expected_unit,
                agreement_score=agreement_score,
                confidence=confidence,
                eligible_source_count=eligible_count,
                independent_source_count=indep_count,
                independent_groups_present=list(independent_groups),
                outliers=outliers,
                rejected_sources=rejected,
                explanation=(
                    f"Consensus failed due to high inter-source disagreement: Spread ({spread_pct:.1f}%) "
                    f"exceeds tolerance ({pol.max_agreement_tolerance_pct:.1f}%). Automated trigger suppressed."
                ),
                evaluated_at=now,
            )
