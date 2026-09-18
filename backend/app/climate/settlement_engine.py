"""Simulated Instant Settlement Engine with Deterministic Idempotency.

Executes synthetic wallet payouts and guarantees zero duplicate payouts on retries.

SAFETY INVARIANT & HACKATHON DISCLAIMER:
This engine operates strictly in SIMULATION MODE.
No real money, fiat currency, bank APIs, or blockchain contracts are invoked.
"""

from __future__ import annotations
import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from app.climate.policy_engine import PolicyTriggerResult


@dataclass
class SettlementRecord:
    """Outcome of simulated financial settlement."""
    settlement_id: str
    policy_id: str
    policy_number: str
    event_identifier: str
    settlement_key: str
    wallet_id: str
    amount: float
    currency: str
    transaction_id: str
    status: str                         # COMPLETED, DUPLICATE_PREVENTED, BLOCKED, FAILED
    is_simulation: bool = True
    is_idempotent_retry: bool = False
    failure_reason: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None


class SimulatedSettlementEngine:
    """Simulated instantaneous settlement executor."""

    # In-memory store of completed settlements for instant idempotency checks
    _settlement_ledger: Dict[str, SettlementRecord] = {}

    @classmethod
    def generate_settlement_key(cls, policy_id: str, event_identifier: str) -> str:
        """Create a deterministic unique idempotency key from policy and event context."""
        raw_key = f"{policy_id}:{event_identifier}"
        return f"SETTLE-{hashlib.sha256(raw_key.encode('utf-8')).hexdigest()[:16].upper()}"

    @classmethod
    def execute_settlement(
        cls,
        trigger_result: PolicyTriggerResult,
    ) -> SettlementRecord:
        """Execute simulated instant settlement with deterministic deduplication."""
        now = datetime.now(timezone.utc)
        settlement_key = cls.generate_settlement_key(trigger_result.policy_id, trigger_result.event_identifier)

        # 1. Idempotency Check: Prevent duplicate payouts for the same event and policy
        if settlement_key in cls._settlement_ledger:
            existing = cls._settlement_ledger[settlement_key]
            return SettlementRecord(
                settlement_id=existing.settlement_id,
                policy_id=existing.policy_id,
                policy_number=existing.policy_number,
                event_identifier=existing.event_identifier,
                settlement_key=settlement_key,
                wallet_id=existing.wallet_id,
                amount=existing.amount,
                currency=existing.currency,
                transaction_id=existing.transaction_id,
                status="COMPLETED",
                is_simulation=True,
                is_idempotent_retry=True,
                failure_reason="Duplicate settlement request suppressed by idempotency guard. Original payout preserved.",
                created_at=existing.created_at,
                completed_at=existing.completed_at,
            )

        # 2. Check if trigger actually occurred
        if not trigger_result.triggered:
            return SettlementRecord(
                settlement_id=f"SET-REJ-{uuid.uuid4().hex[:6].upper()}",
                policy_id=trigger_result.policy_id,
                policy_number=trigger_result.policy_number,
                event_identifier=trigger_result.event_identifier,
                settlement_key=settlement_key,
                wallet_id=trigger_result.wallet_id,
                amount=0.0,
                currency=trigger_result.currency,
                transaction_id="NONE",
                status="BLOCKED",
                is_simulation=True,
                is_idempotent_retry=False,
                failure_reason=f"Settlement blocked: Policy was not triggered ({trigger_result.reason})",
                created_at=now,
                completed_at=None,
            )

        # 3. Create Simulated Settlement
        settlement_id = f"SET-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        txn_id = f"SIM-TXN-{uuid.uuid4().hex[:8].upper()}"

        record = SettlementRecord(
            settlement_id=settlement_id,
            policy_id=trigger_result.policy_id,
            policy_number=trigger_result.policy_number,
            event_identifier=trigger_result.event_identifier,
            settlement_key=settlement_key,
            wallet_id=trigger_result.wallet_id,
            amount=trigger_result.payout_amount,
            currency=trigger_result.currency,
            transaction_id=txn_id,
            status="COMPLETED",
            is_simulation=True,
            is_idempotent_retry=False,
            failure_reason=None,
            created_at=now,
            completed_at=now,
        )

        # Store in ledger
        cls._settlement_ledger[settlement_key] = record
        return record

    @classmethod
    def execute_settlement_for_assessment(
        cls,
        event_identifier: str,
        policy_id: str,
        policy_number: str,
        wallet_id: str,
        amount: float,
        currency: str = "INR",
        assessment_id: Optional[str] = None,
    ) -> SettlementRecord:
        """Execute simulated settlement explicitly calculated from a verified damage assessment."""
        now = datetime.now(timezone.utc)
        settlement_key = cls.generate_settlement_key(policy_id, event_identifier)

        # 1. Idempotency Check
        if settlement_key in cls._settlement_ledger:
            existing = cls._settlement_ledger[settlement_key]
            return SettlementRecord(
                settlement_id=existing.settlement_id,
                policy_id=existing.policy_id,
                policy_number=existing.policy_number,
                event_identifier=existing.event_identifier,
                settlement_key=settlement_key,
                wallet_id=existing.wallet_id,
                amount=existing.amount,
                currency=existing.currency,
                transaction_id=existing.transaction_id,
                status="COMPLETED",
                is_simulation=True,
                is_idempotent_retry=True,
                failure_reason="Duplicate settlement request suppressed by idempotency guard. Original payout preserved.",
                created_at=existing.created_at,
                completed_at=existing.completed_at,
            )

        if amount <= 0:
            return SettlementRecord(
                settlement_id=f"SET-REJ-{uuid.uuid4().hex[:6].upper()}",
                policy_id=policy_id,
                policy_number=policy_number,
                event_identifier=event_identifier,
                settlement_key=settlement_key,
                wallet_id=wallet_id,
                amount=0.0,
                currency=currency,
                transaction_id="NONE",
                status="BLOCKED",
                is_simulation=True,
                is_idempotent_retry=False,
                failure_reason="Settlement blocked: Calculated compensation amount must be strictly greater than zero.",
                created_at=now,
                completed_at=None,
            )

        settlement_id = f"SET-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        txn_id = f"SIM-TXN-{uuid.uuid4().hex[:8].upper()}"

        record = SettlementRecord(
            settlement_id=settlement_id,
            policy_id=policy_id,
            policy_number=policy_number,
            event_identifier=event_identifier,
            settlement_key=settlement_key,
            wallet_id=wallet_id,
            amount=amount,
            currency=currency,
            transaction_id=txn_id,
            status="COMPLETED",
            is_simulation=True,
            is_idempotent_retry=False,
            failure_reason=None,
            created_at=now,
            completed_at=now,
        )

        cls._settlement_ledger[settlement_key] = record
        return record

    @classmethod
    def get_all_settlements(cls) -> List[SettlementRecord]:
        """Return all simulated settlements in chronological order."""
        return list(cls._settlement_ledger.values())

    @classmethod
    def reset_ledger(cls) -> None:
        """Clear ledger for demo resets."""
        cls._settlement_ledger.clear()
