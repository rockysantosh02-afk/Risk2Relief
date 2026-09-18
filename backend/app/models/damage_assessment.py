"""Damage Assessment and Compensation Rule SQLAlchemy 2.x ORM models for Risk2Relief.

Defines DamageCompensationRule and DamageAssessment entities.
Supports deterministic, explainable compensation calculation, multi-crop/land normalization,
shopkeeper inventory damage bands, and backend-enforced payout caps.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy import (
    String,
    Float,
    Boolean,
    ForeignKey,
    Index,
    JSON,
    Uuid,
    DateTime,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class DamageCompensationRule(Base, TimestampMixin):
    """Centralized, auditable compensation rule definition for dynamic damage assessment."""

    __tablename__ = "damage_compensation_rules"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    rule_code: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )  # e.g., FARMER_PADDY_MAJOR_V1
    rule_version: Mapped[str] = mapped_column(String(16), default="1.0", nullable=False)
    reason_for_applying: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )  # FLOOD, CYCLONE, EXTREME_RAINFALL, EXTREME_HEAT, DROUGHT, OTHER, ALL
    occupation: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )  # FARMER, SHOPKEEPER, SMALL_BUSINESS, DAILY_WAGE_WORKER, STREET_VENDOR, FISHER, TRANSPORT_WORKER, OTHER
    damage_category: Mapped[str] = mapped_column(
        String(64), default="GENERAL", nullable=False
    )  # CROP_DAMAGE, INVENTORY_DAMAGE, PREMISES_DAMAGE, EQUIPMENT_DAMAGE, WAGE_LOSS, etc.
    target_subtype: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True
    )  # e.g., PADDY, WHEAT, GROCERY_STORE, etc.
    damage_severity: Mapped[str] = mapped_column(
        String(32), default="MAJOR", nullable=False
    )  # PARTIAL, MAJOR, COMPLETE
    calculation_type: Mapped[str] = mapped_column(
        String(32), default="PER_UNIT", nullable=False
    )  # PER_UNIT (rate * quantity), FIXED_BAND, FIXED_TIER
    rate_per_unit: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    unit_name: Mapped[str] = mapped_column(String(32), default="ACRES", nullable=False)
    max_payout_amount: Mapped[float] = mapped_column(Float, default=50000.0, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="INR", nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    explanation_template: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict, nullable=True)

    __table_args__ = (
        Index("ix_rules_occ_reason_severity", "occupation", "reason_for_applying", "damage_severity", "active"),
    )

    def __repr__(self) -> str:
        return f"<DamageCompensationRule(code='{self.rule_code}', occ='{self.occupation}', rate={self.rate_per_unit}/{self.unit_name}, cap={self.max_payout_amount})>"


class DamageAssessment(Base, TimestampMixin):
    """Structured victim damage assessment record linked to policies and audit history."""

    __tablename__ = "damage_assessments"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    assessment_number: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )  # e.g., ASM-2026-0001
    policy_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("insurance_policies.id", ondelete="SET NULL"), nullable=True, index=True
    )
    applicant_name: Mapped[str] = mapped_column(String(128), default="Anonymous Applicant", nullable=False)
    location_name: Mapped[str] = mapped_column(String(255), default="Monitored District", nullable=False)
    reason_for_applying: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    occupation: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    # Farmer specific fields (nullable for non-farmers)
    crop_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    damaged_area: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    damaged_area_unit: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)  # ACRES, CENTS
    normalized_area_acres: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Shopkeeper specific fields
    store_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    damage_category: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    inventory_damage_band: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # Generic & Shared fields
    work_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    damage_severity: Mapped[str] = mapped_column(String(32), default="MAJOR", nullable=False)
    affected_percentage: Mapped[Optional[float]] = mapped_column(Float, default=100.0, nullable=True)
    loss_quantity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Calculated outputs
    rule_code: Mapped[str] = mapped_column(String(64), nullable=False)
    rule_version: Mapped[str] = mapped_column(String(16), default="1.0", nullable=False)
    rate_applied: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    calculation_formula: Mapped[str] = mapped_column(String(255), nullable=False)
    calculated_amount: Mapped[float] = mapped_column(Float, nullable=False)
    max_cap_applied: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="INR", nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[str] = mapped_column(
        String(32), default="SUBMITTED", nullable=False, index=True
    )  # SUBMITTED, VERIFIED, LINKED_TO_POLICY, SETTLED, REJECTED
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict, nullable=True)

    __table_args__ = (
        Index("ix_assessments_occ_reason", "occupation", "reason_for_applying", "status"),
    )

    def __repr__(self) -> str:
        return f"<DamageAssessment(number='{self.assessment_number}', occ='{self.occupation}', amount={self.calculated_amount} {self.currency})>"
