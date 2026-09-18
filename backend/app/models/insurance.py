"""Parametric Insurance domain SQLAlchemy 2.x models for Risk2Relief.

Defines InsurancePolicy, ConsensusDecision, TriggerEvaluation, and Settlement.
Guarantees deterministic parametric rules, consensus provenance, and strict settlement idempotency.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy import (
    String,
    Integer,
    Float,
    Boolean,
    ForeignKey,
    UniqueConstraint,
    Index,
    JSON,
    Uuid,
    DateTime,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class InsurancePolicy(Base, TimestampMixin):
    """Parametric climate insurance policy contract with deterministic trigger threshold."""

    __tablename__ = "insurance_policies"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    policy_number: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )  # e.g., R2R-POL-2026-001
    policyholder_name: Mapped[str] = mapped_column(String(128), nullable=False)
    policyholder_type: Mapped[str] = mapped_column(
        String(32), default="FARMER", nullable=False, index=True
    )  # FARMER, GIG_WORKER, COOPERATIVE, MUNICIPALITY
    location_name: Mapped[str] = mapped_column(String(255), nullable=False)
    covered_event: Mapped[str] = mapped_column(
        String(64), default="FLASH_FLOOD", nullable=False, index=True
    )  # FLASH_FLOOD, EXTREME_RAINFALL, HEATWAVE, DROUGHT
    metric: Mapped[str] = mapped_column(
        String(64), default="rainfall_24h", nullable=False, index=True
    )  # rainfall_24h, temperature_max
    operator: Mapped[str] = mapped_column(
        String(8), default=">=", nullable=False
    )  # >=, >, <=, <, ==
    threshold: Mapped[float] = mapped_column(Float, default=150.0, nullable=False)
    payout_amount: Mapped[float] = mapped_column(Float, default=25000.0, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="INR", nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    effective_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    effective_to: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    wallet_id: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )  # Simulated wallet ID: SIM-WALLET-FARMER-001
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict, nullable=True)

    # Relationships
    evaluations: Mapped[List["TriggerEvaluation"]] = relationship(
        "TriggerEvaluation", back_populates="policy", cascade="all, delete-orphan"
    )
    settlements: Mapped[List["Settlement"]] = relationship(
        "Settlement", back_populates="policy", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_policies_event_metric", "covered_event", "metric", "active"),
    )

    def __repr__(self) -> str:
        return f"<InsurancePolicy(number='{self.policy_number}', holder='{self.policyholder_name}', payout={self.payout_amount} {self.currency})>"


class ConsensusDecision(Base, TimestampMixin):
    """Auditable multi-source consensus decision record for a climate observation event."""

    __tablename__ = "consensus_decisions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    event_identifier: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )  # e.g., EVT-2026-FLOOD-001
    metric: Mapped[str] = mapped_column(String(64), default="rainfall_24h", nullable=False)
    eligible_source_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    independent_source_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    consensus_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    consensus_method: Mapped[str] = mapped_column(
        String(64), default="WEIGHTED_MEDIAN", nullable=False
    )  # WEIGHTED_MEDIAN, TRIMMED_MEAN, TOLERANCE_CLUSTER
    agreement_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)  # 0.0 to 1.0 (e.g. 0.98)
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default="CONSENSUS_REACHED", nullable=False, index=True
    )  # CONSENSUS_REACHED, CONSENSUS_FAILED, INSUFFICIENT_SOURCES, FLAGGED_FOR_REVIEW
    outliers_json: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, default=list, nullable=True)
    rejected_sources_json: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, default=list, nullable=True)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        Index("ix_consensus_event_status", "event_identifier", "status"),
    )

    def __repr__(self) -> str:
        return f"<ConsensusDecision(event='{self.event_identifier}', value={self.consensus_value}, status='{self.status}')>"


class TriggerEvaluation(Base, TimestampMixin):
    """Deterministic policy trigger evaluation record against verified consensus evidence."""

    __tablename__ = "trigger_evaluations"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    policy_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("insurance_policies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_identifier: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )
    observed_value: Mapped[float] = mapped_column(Float, nullable=False)
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    operator: Mapped[str] = mapped_column(String(8), nullable=False)
    triggered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    difference: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    policy: Mapped["InsurancePolicy"] = relationship("InsurancePolicy", back_populates="evaluations")

    __table_args__ = (
        Index("ix_trigger_policy_triggered", "policy_id", "triggered"),
    )

    def __repr__(self) -> str:
        return f"<TriggerEvaluation(policy='{self.policy_id}', triggered={self.triggered}, diff={self.difference})>"


class Settlement(Base, TimestampMixin):
    """Simulated instantaneous payout settlement with strict deterministic idempotency."""

    __tablename__ = "settlements"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    settlement_id: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )  # e.g., SET-2026-0001
    policy_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("insurance_policies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_identifier: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )
    settlement_key: Mapped[str] = mapped_column(
        String(128), unique=True, nullable=False, index=True
    )  # Deterministic unique idempotency key: hash(policy_id + event_identifier)
    wallet_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="INR", nullable=False)
    transaction_id: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )  # Simulated transaction hash: SIM-TXN-8F31A9
    status: Mapped[str] = mapped_column(
        String(32), default="COMPLETED", nullable=False, index=True
    )  # COMPLETED, PENDING, FAILED, DUPLICATE_BLOCKED
    failure_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_simulation: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=True
    )

    # Relationships
    policy: Mapped["InsurancePolicy"] = relationship("InsurancePolicy", back_populates="settlements")

    __table_args__ = (
        Index("ix_settlements_wallet_status", "wallet_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<Settlement(id='{self.settlement_id}', txn='{self.transaction_id}', amount={self.amount} {self.currency}, status='{self.status}')>"
