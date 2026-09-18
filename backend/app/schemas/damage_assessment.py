"""Pydantic v2 schemas for Damage Assessment & Dynamic Filter Engine.

Validates reason for applying, occupation, dynamic occupation-specific parameters,
unit conversions, and compensation rule responses.
"""

from __future__ import annotations
import uuid
from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict, Field, model_validator


class ReasonForApplying(str, Enum):
    FLOOD = "FLOOD"
    CYCLONE = "CYCLONE"
    EXTREME_RAINFALL = "EXTREME_RAINFALL"
    EXTREME_HEAT = "EXTREME_HEAT"
    DROUGHT = "DROUGHT"
    OTHER = "OTHER"


class Occupation(str, Enum):
    FARMER = "FARMER"
    SHOPKEEPER = "SHOPKEEPER"
    SMALL_BUSINESS = "SMALL_BUSINESS"
    DAILY_WAGE_WORKER = "DAILY_WAGE_WORKER"
    STREET_VENDOR = "STREET_VENDOR"
    FISHER = "FISHER"
    TRANSPORT_WORKER = "TRANSPORT_WORKER"
    OTHER = "OTHER"


class FarmerCropType(str, Enum):
    PADDY = "PADDY"
    WHEAT = "WHEAT"
    SUGARCANE = "SUGARCANE"
    MAIZE = "MAIZE"
    COTTON = "COTTON"
    PULSES = "PULSES"
    VEGETABLES = "VEGETABLES"
    OTHER = "OTHER"


class LandAreaUnit(str, Enum):
    ACRES = "ACRES"
    CENTS = "CENTS"


class DamageSeverity(str, Enum):
    PARTIAL = "PARTIAL"
    MAJOR = "MAJOR"
    COMPLETE = "COMPLETE"


class ShopStoreType(str, Enum):
    GROCERY_STORE = "GROCERY_STORE"
    CLOTHING_STORE = "CLOTHING_STORE"
    ELECTRONICS_STORE = "ELECTRONICS_STORE"
    HARDWARE_STORE = "HARDWARE_STORE"
    PHARMACY = "PHARMACY"
    RESTAURANT_FOOD = "RESTAURANT_FOOD"
    STATIONERY_STORE = "STATIONERY_STORE"
    MOBILE_ACCESSORIES = "MOBILE_ACCESSORIES"
    AGRI_INPUT_STORE = "AGRI_INPUT_STORE"
    OTHER = "OTHER"


class ShopDamageCategory(str, Enum):
    INVENTORY_DAMAGE = "INVENTORY_DAMAGE"
    PREMISES_DAMAGE = "PREMISES_DAMAGE"
    EQUIPMENT_DAMAGE = "EQUIPMENT_DAMAGE"
    COMPLETE_STORE_LOSS = "COMPLETE_STORE_LOSS"


class InventoryDamageBand(str, Enum):
    BELOW_25K = "BELOW_25K"
    BAND_25K_50K = "BAND_25K_50K"
    BAND_50K_100K = "BAND_50K_100K"
    ABOVE_100K = "ABOVE_100K"


# Base DTO for calculations and submissions
class DamageAssessmentBase(BaseModel):
    model_config = ConfigDict(extra="ignore", from_attributes=True)

    reason_for_applying: ReasonForApplying = Field(..., description="Root cause climate event for relief")
    occupation: Occupation = Field(..., description="Primary occupation category (parent dynamic filter)")
    applicant_name: str = Field(default="Anonymous Applicant", min_length=2, max_length=128)
    location_name: str = Field(default="Monitored District", min_length=2, max_length=255)
    damage_severity: DamageSeverity = Field(default=DamageSeverity.MAJOR, description="Severity tier")

    # Farmer dynamic fields
    crop_type: Optional[FarmerCropType] = Field(None, description="Crop variety (required if occupation=FARMER)")
    damaged_area: Optional[float] = Field(None, description="Numerical damaged area (acres or cents)")
    damaged_area_unit: Optional[LandAreaUnit] = Field(None, description="Land area unit (ACRES or CENTS)")
    affected_percentage: Optional[float] = Field(default=100.0, ge=0.0, le=100.0)

    # Shopkeeper dynamic fields
    store_type: Optional[ShopStoreType] = Field(None, description="Store category (required if occupation=SHOPKEEPER)")
    damage_category: Optional[ShopDamageCategory] = Field(None, description="Damage type category")
    inventory_damage_band: Optional[InventoryDamageBand] = Field(None, description="Estimated damage value band")

    # Generic dynamic fields
    work_type: Optional[str] = Field(None, max_length=64, description="Specific trade or work description")
    loss_quantity: Optional[float] = Field(None, ge=0.0, description="Quantity / days of lost work")

    @model_validator(mode="after")
    def validate_occupation_specific_fields(self) -> "DamageAssessmentBase":
        # 1. Farmer Validation
        if self.occupation == Occupation.FARMER:
            if not self.crop_type:
                raise ValueError("Crop type is required for Farmer damage assessments.")
            if self.damaged_area is None:
                raise ValueError("Damaged land area is required for Farmer damage assessments.")
            if self.damaged_area <= 0.0:
                raise ValueError("Damaged land area must be strictly greater than zero.")
            if self.damaged_area > 10000.0:
                raise ValueError("Damaged land area exceeds realistic bounds (> 10,000).")
            if not self.damaged_area_unit:
                raise ValueError("Damaged area unit (ACRES or CENTS) is required.")

        # 2. Shopkeeper Validation
        elif self.occupation == Occupation.SHOPKEEPER:
            if not self.store_type:
                raise ValueError("Store type is required for Shopkeeper damage assessments.")
            if not self.damage_category:
                raise ValueError("Damage category is required for Shopkeeper damage assessments.")

        return self


class DamageAssessmentCalculateRequest(DamageAssessmentBase):
    """Payload for calculating deterministic compensation without persisting."""
    pass


class DamageAssessmentCreate(DamageAssessmentBase):
    """Payload for creating and persisting a damage assessment."""
    policy_id: Optional[uuid.UUID] = Field(None, description="Optional associated policy ID")


class CalculationBreakdown(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rule_code: str
    rule_version: str
    reason: str
    occupation: str
    target_subtype: Optional[str] = None
    damage_severity: str
    original_quantity: Optional[float] = None
    original_unit: Optional[str] = None
    normalized_quantity: float
    normalized_unit: str
    rate_per_unit: float
    formula_string: str
    raw_calculated_amount: float
    max_payout_cap: float
    cap_applied: bool
    final_compensation_amount: float
    currency: str = "INR"
    explanation: str


class DamageAssessmentCalculationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: str = "SUCCESS"
    breakdown: CalculationBreakdown
    is_simulation: bool = True
    disclaimer: str = "SIMULATION MODE — NO REAL MONEY MOVED"


class DamageAssessmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    assessment_number: str
    policy_id: Optional[uuid.UUID] = None
    applicant_name: str
    location_name: str
    reason_for_applying: str
    occupation: str
    crop_type: Optional[str] = None
    damaged_area: Optional[float] = None
    damaged_area_unit: Optional[str] = None
    normalized_area_acres: Optional[float] = None
    store_type: Optional[str] = None
    damage_category: Optional[str] = None
    inventory_damage_band: Optional[str] = None
    work_type: Optional[str] = None
    damage_severity: str
    affected_percentage: Optional[float] = None
    rule_code: str
    rule_version: str
    rate_applied: float
    calculation_formula: str
    calculated_amount: float
    max_cap_applied: bool
    currency: str
    explanation: str
    status: str
    created_at: datetime
    is_simulation: bool = True


class DamageCompensationRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    rule_code: str
    rule_version: str
    reason_for_applying: str
    occupation: str
    damage_category: str
    target_subtype: Optional[str] = None
    damage_severity: str
    calculation_type: str
    rate_per_unit: float
    unit_name: str
    max_payout_amount: float
    currency: str
    active: bool
    explanation_template: str
