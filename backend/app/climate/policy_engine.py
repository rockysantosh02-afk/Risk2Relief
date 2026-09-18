"""Deterministic Parametric Insurance Policy and Trigger Evaluation Engine.

Evaluates verified consensus observations against deterministic policy rules.

ARCHITECTURAL PRINCIPLE:
ML anomaly detection is an advisory filter that informs consensus.
The final trigger decision is 100% deterministic, explainable, and rule-based.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from app.climate.consensus import ConsensusOutcome


@dataclass
class PolicyTriggerResult:
    """Outcome of deterministic policy evaluation."""
    policy_id: str
    policy_number: str
    event_identifier: str
    metric: str
    observed_value: float
    threshold: float
    operator: str
    triggered: bool
    difference: float
    payout_amount: float
    currency: str
    wallet_id: str
    reason: str
    evaluated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ParametricPolicyEngine:
    """Evaluates policies against consensus evidence."""

    @classmethod
    def evaluate_policy_trigger(
        cls,
        policy: Dict[str, Any],
        consensus: ConsensusOutcome,
        event_identifier: str,
    ) -> PolicyTriggerResult:
        """Evaluate deterministic policy trigger condition against verified consensus."""
        now = datetime.now(timezone.utc)
        pol_id = str(policy.get("id", "UNKNOWN"))
        pol_num = str(policy.get("policy_number", "R2R-POL-001"))
        wallet_id = str(policy.get("wallet_id", "SIM-WALLET-001"))
        metric = str(policy.get("metric", "rainfall_24h"))
        op = str(policy.get("operator", ">=")).strip()
        threshold = float(policy.get("threshold", 150.0))
        payout = float(policy.get("payout_amount", 25000.0))
        currency = str(policy.get("currency", "INR"))
        is_active = bool(policy.get("active", True))

        # Check 1: Policy active status
        if not is_active:
            return PolicyTriggerResult(
                policy_id=pol_id,
                policy_number=pol_num,
                event_identifier=event_identifier,
                metric=metric,
                observed_value=consensus.consensus_value or 0.0,
                threshold=threshold,
                operator=op,
                triggered=False,
                difference=0.0,
                payout_amount=0.0,
                currency=currency,
                wallet_id=wallet_id,
                reason=f"Policy '{pol_num}' is currently INACTIVE. Trigger evaluation aborted.",
                evaluated_at=now,
            )

        # Check 2: Consensus reliability gate
        if consensus.status != "CONSENSUS_REACHED" or consensus.consensus_value is None:
            return PolicyTriggerResult(
                policy_id=pol_id,
                policy_number=pol_num,
                event_identifier=event_identifier,
                metric=metric,
                observed_value=consensus.consensus_value or 0.0,
                threshold=threshold,
                operator=op,
                triggered=False,
                difference=0.0,
                payout_amount=0.0,
                currency=currency,
                wallet_id=wallet_id,
                reason=(
                    f"Trigger blocked: Multi-source consensus status is '{consensus.status}'. "
                    f"Explanation: {consensus.explanation}"
                ),
                evaluated_at=now,
            )

        observed = float(consensus.consensus_value)
        diff = round(observed - threshold, 2)

        # Check 3: Deterministic Operator Evaluation
        triggered = False
        if op == ">=":
            triggered = (observed >= threshold)
        elif op == ">":
            triggered = (observed > threshold)
        elif op == "<=":
            triggered = (observed <= threshold)
        elif op == "<":
            triggered = (observed < threshold)
        elif op == "==":
            triggered = (abs(observed - threshold) < 1e-4)
        else:
            triggered = (observed >= threshold)

        if triggered:
            reason = (
                f"Parametric trigger ACTIVATED: Observed consensus value {observed:.1f} {consensus.unit} "
                f"satisfies contract rule ({op} {threshold:.1f} {consensus.unit}). "
                f"Instant simulated payout of {payout:,.2f} {currency} authorized for wallet '{wallet_id}'."
            )
            actual_payout = payout
        else:
            reason = (
                f"Parametric trigger NOT REACHED: Observed consensus value {observed:.1f} {consensus.unit} "
                f"did not breach threshold ({op} {threshold:.1f} {consensus.unit}). "
                f"Margin below trigger: {abs(diff):.1f} {consensus.unit}."
            )
            actual_payout = 0.0

        return PolicyTriggerResult(
            policy_id=pol_id,
            policy_number=pol_num,
            event_identifier=event_identifier,
            metric=metric,
            observed_value=observed,
            threshold=threshold,
            operator=op,
            triggered=triggered,
            difference=diff,
            payout_amount=actual_payout,
            currency=currency,
            wallet_id=wallet_id,
            reason=reason,
            evaluated_at=now,
        )
