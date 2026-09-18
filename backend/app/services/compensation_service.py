"""Damage Compensation Engine Service for Risk2Relief.

Implements deterministic rule selection, land unit normalization (cents <-> acres),
mathematical formula evaluation, backend payout cap enforcement, and audit integration.
Guarantees zero ML/LLM financial decision authority.
"""

from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Tuple

from app.schemas.damage_assessment import (
    DamageAssessmentBase,
    DamageAssessmentCreate,
    CalculationBreakdown,
    DamageAssessmentCalculationResponse,
    DamageAssessmentResponse,
    DamageCompensationRuleResponse,
    Occupation,
    LandAreaUnit,
    DamageSeverity,
    InventoryDamageBand,
)
from app.climate.audit_trail import ClimateAuditTrailService


# Centralized in-memory / pre-configured rule definitions (matches DB model schema)
_PRECONFIGURED_RULES: List[Dict[str, Any]] = [
    # ------------------ FARMER RULES ------------------
    {
        "id": uuid.UUID("11111111-1111-1111-1111-111111111101"),
        "rule_code": "FARMER_PADDY_MAJOR_V1",
        "rule_version": "1.0",
        "reason_for_applying": "ALL",
        "occupation": "FARMER",
        "damage_category": "CROP_DAMAGE",
        "target_subtype": "PADDY",
        "damage_severity": "MAJOR",
        "calculation_type": "PER_UNIT",
        "rate_per_unit": 10000.0,
        "unit_name": "ACRES",
        "max_payout_amount": 50000.0,
        "currency": "INR",
        "active": True,
        "explanation_template": "Major Paddy crop loss calculated at ₹10,000 per normalized acre (Max Cap: ₹50,000).",
    },
    {
        "id": uuid.UUID("11111111-1111-1111-1111-111111111102"),
        "rule_code": "FARMER_PADDY_COMPLETE_V1",
        "rule_version": "1.0",
        "reason_for_applying": "ALL",
        "occupation": "FARMER",
        "damage_category": "CROP_DAMAGE",
        "target_subtype": "PADDY",
        "damage_severity": "COMPLETE",
        "calculation_type": "PER_UNIT",
        "rate_per_unit": 15000.0,
        "unit_name": "ACRES",
        "max_payout_amount": 60000.0,
        "currency": "INR",
        "active": True,
        "explanation_template": "Complete Paddy crop destruction calculated at ₹15,000 per acre (Max Cap: ₹60,000).",
    },
    {
        "id": uuid.UUID("11111111-1111-1111-1111-111111111103"),
        "rule_code": "FARMER_PADDY_PARTIAL_V1",
        "rule_version": "1.0",
        "reason_for_applying": "ALL",
        "occupation": "FARMER",
        "damage_category": "CROP_DAMAGE",
        "target_subtype": "PADDY",
        "damage_severity": "PARTIAL",
        "calculation_type": "PER_UNIT",
        "rate_per_unit": 6000.0,
        "unit_name": "ACRES",
        "max_payout_amount": 30000.0,
        "currency": "INR",
        "active": True,
        "explanation_template": "Partial Paddy crop damage calculated at ₹6,000 per acre (Max Cap: ₹30,000).",
    },
    {
        "id": uuid.UUID("11111111-1111-1111-1111-111111111104"),
        "rule_code": "FARMER_WHEAT_MAJOR_V1",
        "rule_version": "1.0",
        "reason_for_applying": "ALL",
        "occupation": "FARMER",
        "damage_category": "CROP_DAMAGE",
        "target_subtype": "WHEAT",
        "damage_severity": "MAJOR",
        "calculation_type": "PER_UNIT",
        "rate_per_unit": 9000.0,
        "unit_name": "ACRES",
        "max_payout_amount": 45000.0,
        "currency": "INR",
        "active": True,
        "explanation_template": "Major Wheat crop loss calculated at ₹9,000 per acre (Max Cap: ₹45,000).",
    },
    {
        "id": uuid.UUID("11111111-1111-1111-1111-111111111105"),
        "rule_code": "FARMER_SUGARCANE_MAJOR_V1",
        "rule_version": "1.0",
        "reason_for_applying": "ALL",
        "occupation": "FARMER",
        "damage_category": "CROP_DAMAGE",
        "target_subtype": "SUGARCANE",
        "damage_severity": "MAJOR",
        "calculation_type": "PER_UNIT",
        "rate_per_unit": 12000.0,
        "unit_name": "ACRES",
        "max_payout_amount": 60000.0,
        "currency": "INR",
        "active": True,
        "explanation_template": "Major Sugarcane field loss calculated at ₹12,000 per acre (Max Cap: ₹60,000).",
    },
    {
        "id": uuid.UUID("11111111-1111-1111-1111-111111111106"),
        "rule_code": "FARMER_MAIZE_MAJOR_V1",
        "rule_version": "1.0",
        "reason_for_applying": "ALL",
        "occupation": "FARMER",
        "damage_category": "CROP_DAMAGE",
        "target_subtype": "MAIZE",
        "damage_severity": "MAJOR",
        "calculation_type": "PER_UNIT",
        "rate_per_unit": 8000.0,
        "unit_name": "ACRES",
        "max_payout_amount": 40000.0,
        "currency": "INR",
        "active": True,
        "explanation_template": "Major Maize crop loss calculated at ₹8,000 per acre (Max Cap: ₹40,000).",
    },
    {
        "id": uuid.UUID("11111111-1111-1111-1111-111111111107"),
        "rule_code": "FARMER_GENERIC_MAJOR_V1",
        "rule_version": "1.0",
        "reason_for_applying": "ALL",
        "occupation": "FARMER",
        "damage_category": "CROP_DAMAGE",
        "target_subtype": "OTHER",
        "damage_severity": "MAJOR",
        "calculation_type": "PER_UNIT",
        "rate_per_unit": 7500.0,
        "unit_name": "ACRES",
        "max_payout_amount": 35000.0,
        "currency": "INR",
        "active": True,
        "explanation_template": "General horticulture/crop loss calculated at ₹7,500 per acre (Max Cap: ₹35,000).",
    },

    # ------------------ SHOPKEEPER RULES ------------------
    {
        "id": uuid.UUID("11111111-1111-1111-1111-111111111201"),
        "rule_code": "SHOP_GROCERY_INVENTORY_MAJOR_V1",
        "rule_version": "1.0",
        "reason_for_applying": "ALL",
        "occupation": "SHOPKEEPER",
        "damage_category": "INVENTORY_DAMAGE",
        "target_subtype": "GROCERY_STORE",
        "damage_severity": "MAJOR",
        "calculation_type": "FIXED_TIER",
        "rate_per_unit": 30000.0,
        "unit_name": "STORE_UNIT",
        "max_payout_amount": 45000.0,
        "currency": "INR",
        "active": True,
        "explanation_template": "Grocery inventory inundation/spoilage base relief tier ₹30,000 (Max Cap: ₹45,000).",
    },
    {
        "id": uuid.UUID("11111111-1111-1111-1111-111111111202"),
        "rule_code": "SHOP_CLOTHING_INVENTORY_MAJOR_V1",
        "rule_version": "1.0",
        "reason_for_applying": "ALL",
        "occupation": "SHOPKEEPER",
        "damage_category": "INVENTORY_DAMAGE",
        "target_subtype": "CLOTHING_STORE",
        "damage_severity": "MAJOR",
        "calculation_type": "FIXED_TIER",
        "rate_per_unit": 35000.0,
        "unit_name": "STORE_UNIT",
        "max_payout_amount": 50000.0,
        "currency": "INR",
        "active": True,
        "explanation_template": "Apparel & textile flood damage base relief tier ₹35,000 (Max Cap: ₹50,000).",
    },
    {
        "id": uuid.UUID("11111111-1111-1111-1111-111111111203"),
        "rule_code": "SHOP_ELECTRONICS_INVENTORY_MAJOR_V1",
        "rule_version": "1.0",
        "reason_for_applying": "ALL",
        "occupation": "SHOPKEEPER",
        "damage_category": "INVENTORY_DAMAGE",
        "target_subtype": "ELECTRONICS_STORE",
        "damage_severity": "MAJOR",
        "calculation_type": "FIXED_TIER",
        "rate_per_unit": 45000.0,
        "unit_name": "STORE_UNIT",
        "max_payout_amount": 60000.0,
        "currency": "INR",
        "active": True,
        "explanation_template": "Electronics & hardware water ingress tier ₹45,000 (Max Cap: ₹60,000).",
    },
    {
        "id": uuid.UUID("11111111-1111-1111-1111-111111111204"),
        "rule_code": "SHOP_GENERIC_MAJOR_V1",
        "rule_version": "1.0",
        "reason_for_applying": "ALL",
        "occupation": "SHOPKEEPER",
        "damage_category": "INVENTORY_DAMAGE",
        "target_subtype": "OTHER",
        "damage_severity": "MAJOR",
        "calculation_type": "FIXED_TIER",
        "rate_per_unit": 25000.0,
        "unit_name": "STORE_UNIT",
        "max_payout_amount": 40000.0,
        "currency": "INR",
        "active": True,
        "explanation_template": "Commercial retail inventory damage base tier ₹25,000 (Max Cap: ₹40,000).",
    },

    # ------------------ OTHER OCCUPATION RULES ------------------
    {
        "id": uuid.UUID("11111111-1111-1111-1111-111111111301"),
        "rule_code": "DAILY_WAGE_HEAT_MAJOR_V1",
        "rule_version": "1.0",
        "reason_for_applying": "ALL",
        "occupation": "DAILY_WAGE_WORKER",
        "damage_category": "WAGE_LOSS",
        "target_subtype": "GENERAL",
        "damage_severity": "MAJOR",
        "calculation_type": "PER_UNIT",
        "rate_per_unit": 800.0,
        "unit_name": "DAYS",
        "max_payout_amount": 15000.0,
        "currency": "INR",
        "active": True,
        "explanation_template": "Extreme climate livelihood wage loss calculated at ₹800/day (Max Cap: ₹15,000).",
    },
    {
        "id": uuid.UUID("11111111-1111-1111-1111-111111111302"),
        "rule_code": "STREET_VENDOR_FLOOD_MAJOR_V1",
        "rule_version": "1.0",
        "reason_for_applying": "ALL",
        "occupation": "STREET_VENDOR",
        "damage_category": "EQUIPMENT_DAMAGE",
        "target_subtype": "GENERAL",
        "damage_severity": "MAJOR",
        "calculation_type": "FIXED_TIER",
        "rate_per_unit": 15000.0,
        "unit_name": "CART_UNIT",
        "max_payout_amount": 20000.0,
        "currency": "INR",
        "active": True,
        "explanation_template": "Micro-vendor kiosk/cart storm damage relief ₹15,000 (Max Cap: ₹20,000).",
    },
    {
        "id": uuid.UUID("11111111-1111-1111-1111-111111111303"),
        "rule_code": "FISHER_CYCLONE_MAJOR_V1",
        "rule_version": "1.0",
        "reason_for_applying": "ALL",
        "occupation": "FISHER",
        "damage_category": "EQUIPMENT_DAMAGE",
        "target_subtype": "GENERAL",
        "damage_severity": "MAJOR",
        "calculation_type": "FIXED_TIER",
        "rate_per_unit": 25000.0,
        "unit_name": "BOAT_NET_UNIT",
        "max_payout_amount": 40000.0,
        "currency": "INR",
        "active": True,
        "explanation_template": "Artisanal fishing boat/gear cyclone damage relief ₹25,000 (Max Cap: ₹40,000).",
    },
    {
        "id": uuid.UUID("11111111-1111-1111-1111-111111111304"),
        "rule_code": "GENERIC_RELIEF_MAJOR_V1",
        "rule_version": "1.0",
        "reason_for_applying": "ALL",
        "occupation": "OTHER",
        "damage_category": "GENERAL",
        "target_subtype": "GENERAL",
        "damage_severity": "MAJOR",
        "calculation_type": "FIXED_TIER",
        "rate_per_unit": 12000.0,
        "unit_name": "BENEFICIARY_UNIT",
        "max_payout_amount": 20000.0,
        "currency": "INR",
        "active": True,
        "explanation_template": "General informal worker catastrophic climate grant ₹12,000 (Max Cap: ₹20,000).",
    },
]


class DamageCompensationService:
    """Core calculation and validation engine for dynamic victim damage assessment."""

    _registered_assessments: List[Dict[str, Any]] = []

    @classmethod
    def get_all_rules(cls) -> List[DamageCompensationRuleResponse]:
        """Return all active compensation rules."""
        return [DamageCompensationRuleResponse(**r) for r in _PRECONFIGURED_RULES if r.get("active", True)]

    @classmethod
    def get_rule_by_code(cls, rule_code: str) -> Optional[Dict[str, Any]]:
        """Find a rule by unique rule_code."""
        for r in _PRECONFIGURED_RULES:
            if r["rule_code"] == rule_code:
                return r
        return None

    @classmethod
    def normalize_land_area(cls, area: float, unit: LandAreaUnit) -> Tuple[float, str]:
        """Deterministic Indian land unit conversion: 1 Acre = 100 Cents."""
        if unit == LandAreaUnit.CENTS:
            normalized_acres = round(area / 100.0, 4)
            return normalized_acres, "ACRES"
        return round(area, 4), "ACRES"

    @classmethod
    def select_best_rule(cls, assessment: DamageAssessmentBase) -> Dict[str, Any]:
        """Find matching rule based on occupation, crop/store subtype, and severity."""
        occ_str = str(assessment.occupation.value if hasattr(assessment.occupation, "value") else assessment.occupation).upper()
        severity_str = str(assessment.damage_severity.value if hasattr(assessment.damage_severity, "value") else assessment.damage_severity).upper()

        subtype = None
        if occ_str == "FARMER" and assessment.crop_type:
            subtype = str(assessment.crop_type.value if hasattr(assessment.crop_type, "value") else assessment.crop_type).upper()
        elif occ_str == "SHOPKEEPER" and assessment.store_type:
            subtype = str(assessment.store_type.value if hasattr(assessment.store_type, "value") else assessment.store_type).upper()

        # 1. Exact match (Occupation + Subtype + Severity)
        for r in _PRECONFIGURED_RULES:
            if not r["active"]:
                continue
            if r["occupation"] == occ_str and r.get("target_subtype") == subtype and r["damage_severity"] == severity_str:
                return r

        # 2. Subtype match with generic severity
        for r in _PRECONFIGURED_RULES:
            if not r["active"]:
                continue
            if r["occupation"] == occ_str and r.get("target_subtype") == subtype:
                return r

        # 3. Occupation match with generic subtype
        for r in _PRECONFIGURED_RULES:
            if not r["active"]:
                continue
            if r["occupation"] == occ_str and (r.get("target_subtype") in ["OTHER", "GENERAL", None]):
                return r

        # 4. Global fallback rule
        for r in _PRECONFIGURED_RULES:
            if r["rule_code"] == "GENERIC_RELIEF_MAJOR_V1":
                return r

        # Fallback safeguard
        return _PRECONFIGURED_RULES[0]

    @classmethod
    def calculate_compensation(cls, assessment: DamageAssessmentBase) -> CalculationBreakdown:
        """Deterministically calculate compensation breakdown with backend caps."""
        rule = cls.select_best_rule(assessment)
        occ_str = str(assessment.occupation.value if hasattr(assessment.occupation, "value") else assessment.occupation)
        reason_str = str(assessment.reason_for_applying.value if hasattr(assessment.reason_for_applying, "value") else assessment.reason_for_applying)
        severity_str = str(assessment.damage_severity.value if hasattr(assessment.damage_severity, "value") else assessment.damage_severity)

        raw_amount = 0.0
        formula_str = ""
        orig_qty = None
        orig_unit = None
        norm_qty = 1.0
        norm_unit = rule["unit_name"]

        rate = float(rule["rate_per_unit"])
        max_cap = float(rule["max_payout_amount"])

        # 1. Farmer calculation (Rate * Normalized Acres)
        if occ_str == "FARMER":
            orig_qty = assessment.damaged_area or 1.0
            orig_unit = str(assessment.damaged_area_unit.value if hasattr(assessment.damaged_area_unit, "value") else assessment.damaged_area_unit)
            unit_enum = assessment.damaged_area_unit or LandAreaUnit.ACRES
            norm_qty, norm_unit = cls.normalize_land_area(orig_qty, unit_enum)

            pct_mult = (assessment.affected_percentage or 100.0) / 100.0
            raw_amount = rate * norm_qty * pct_mult
            if unit_enum == LandAreaUnit.CENTS:
                formula_str = f"({orig_qty} Cents ÷ 100 = {norm_qty} Acres) × ₹{rate:,.0f}/acre"
            else:
                formula_str = f"{norm_qty} Acres × ₹{rate:,.0f}/acre"
            if pct_mult < 1.0:
                formula_str += f" × {assessment.affected_percentage}%"

        # 2. Shopkeeper calculation (Tier with Band multiplier)
        elif occ_str == "SHOPKEEPER":
            norm_qty = 1.0
            orig_qty = 1.0
            orig_unit = "STORE"
            band_mult = 1.0
            band_label = ""
            if assessment.inventory_damage_band:
                band_str = str(assessment.inventory_damage_band.value if hasattr(assessment.inventory_damage_band, "value") else assessment.inventory_damage_band)
                if band_str == InventoryDamageBand.BELOW_25K.value:
                    band_mult = 0.75
                    band_label = " (Band < ₹25k: 0.75x)"
                elif band_str == InventoryDamageBand.BAND_25K_50K.value:
                    band_mult = 1.0
                    band_label = " (Band ₹25k-₹50k: 1.0x)"
                elif band_str == InventoryDamageBand.BAND_50K_100K.value:
                    band_mult = 1.35
                    band_label = " (Band ₹50k-₹100k: 1.35x)"
                elif band_str == InventoryDamageBand.ABOVE_100K.value:
                    band_mult = 1.65
                    band_label = " (Band > ₹100k: 1.65x)"

            raw_amount = rate * band_mult
            formula_str = f"Base Tier ₹{rate:,.0f}{band_label}"

        # 3. Daily Wage Worker calculation (Rate * Lost Days)
        elif occ_str == "DAILY_WAGE_WORKER":
            norm_qty = assessment.loss_quantity or 5.0
            orig_qty = norm_qty
            orig_unit = "DAYS"
            raw_amount = rate * norm_qty
            formula_str = f"{norm_qty} Days × ₹{rate:,.0f}/day"

        # 4. Generic fallback
        else:
            norm_qty = 1.0
            orig_qty = 1.0
            orig_unit = "UNIT"
            raw_amount = rate
            formula_str = f"Fixed Relief Grant: ₹{rate:,.0f}"

        # Payout Cap Enforcement
        cap_applied = False
        final_amount = raw_amount
        if raw_amount > max_cap:
            final_amount = max_cap
            cap_applied = True
            formula_str += f" [Capped at Max Limit ₹{max_cap:,.0f}]"

        subtype_val = rule.get("target_subtype")
        explanation = rule["explanation_template"]

        return CalculationBreakdown(
            rule_code=rule["rule_code"],
            rule_version=rule["rule_version"],
            reason=reason_str,
            occupation=occ_str,
            target_subtype=subtype_val,
            damage_severity=severity_str,
            original_quantity=orig_qty,
            original_unit=orig_unit,
            normalized_quantity=norm_qty,
            normalized_unit=norm_unit,
            rate_per_unit=rate,
            formula_string=formula_str,
            raw_calculated_amount=round(raw_amount, 2),
            max_payout_cap=round(max_cap, 2),
            cap_applied=cap_applied,
            final_compensation_amount=round(final_amount, 2),
            currency=rule["currency"],
            explanation=explanation,
        )

    @classmethod
    def record_assessment(cls, create_in: DamageAssessmentCreate) -> DamageAssessmentResponse:
        """Calculate, log to audit trail, and persist damage assessment."""
        breakdown = cls.calculate_compensation(create_in)
        asm_id = uuid.uuid4()
        asm_number = f"ASM-2026-{uuid.uuid4().hex[:6].upper()}"
        now = datetime.now(timezone.utc)

        occ_str = str(create_in.occupation.value if hasattr(create_in.occupation, "value") else create_in.occupation)
        reason_str = str(create_in.reason_for_applying.value if hasattr(create_in.reason_for_applying, "value") else create_in.reason_for_applying)
        crop_str = str(create_in.crop_type.value if hasattr(create_in.crop_type, "value") else create_in.crop_type) if create_in.crop_type else None
        store_str = str(create_in.store_type.value if hasattr(create_in.store_type, "value") else create_in.store_type) if create_in.store_type else None
        cat_str = str(create_in.damage_category.value if hasattr(create_in.damage_category, "value") else create_in.damage_category) if create_in.damage_category else None
        band_str = str(create_in.inventory_damage_band.value if hasattr(create_in.inventory_damage_band, "value") else create_in.inventory_damage_band) if create_in.inventory_damage_band else None
        unit_str = str(create_in.damaged_area_unit.value if hasattr(create_in.damaged_area_unit, "value") else create_in.damaged_area_unit) if create_in.damaged_area_unit else None
        severity_str = str(create_in.damage_severity.value if hasattr(create_in.damage_severity, "value") else create_in.damage_severity)

        record = {
            "id": asm_id,
            "assessment_number": asm_number,
            "policy_id": create_in.policy_id,
            "applicant_name": create_in.applicant_name,
            "location_name": create_in.location_name,
            "reason_for_applying": reason_str,
            "occupation": occ_str,
            "crop_type": crop_str,
            "damaged_area": create_in.damaged_area,
            "damaged_area_unit": unit_str,
            "normalized_area_acres": breakdown.normalized_quantity if occ_str == "FARMER" else None,
            "store_type": store_str,
            "damage_category": cat_str,
            "inventory_damage_band": band_str,
            "work_type": create_in.work_type,
            "damage_severity": severity_str,
            "affected_percentage": create_in.affected_percentage,
            "rule_code": breakdown.rule_code,
            "rule_version": breakdown.rule_version,
            "rate_applied": breakdown.rate_per_unit,
            "calculation_formula": breakdown.formula_string,
            "calculated_amount": breakdown.final_compensation_amount,
            "max_cap_applied": breakdown.cap_applied,
            "currency": breakdown.currency,
            "explanation": breakdown.explanation,
            "status": "SUBMITTED",
            "created_at": now,
            "is_simulation": True,
        }
        cls._registered_assessments.append(record)

        # Audit Trail Integration
        ClimateAuditTrailService.record_stage(
            event_identifier=f"EVT-ASM-{asm_number}",
            stage="DAMAGE_DATA_VALIDATED",
            status="PASSED",
            title=f"Damage Assessment Validated: {asm_number}",
            message=f"Validated dynamic inputs for {occ_str} ({reason_str}). Formula: {breakdown.formula_string}",
            policy_id=str(create_in.policy_id) if create_in.policy_id else None,
            metadata={
                "assessment_number": asm_number,
                "occupation": occ_str,
                "reason": reason_str,
                "calculated_amount": breakdown.final_compensation_amount,
                "rule_code": breakdown.rule_code,
                "cap_applied": breakdown.cap_applied,
            },
        )

        ClimateAuditTrailService.record_stage(
            event_identifier=f"EVT-ASM-{asm_number}",
            stage="COMPENSATION_CALCULATED",
            status="SUCCESS",
            title=f"Compensation Determined: ₹{breakdown.final_compensation_amount:,.2f} INR",
            message=f"Applied rule {breakdown.rule_code} v{breakdown.rule_version}. Amount: ₹{breakdown.final_compensation_amount:,.2f}",
            policy_id=str(create_in.policy_id) if create_in.policy_id else None,
            metadata={
                "formula": breakdown.formula_string,
                "raw_amount": breakdown.raw_calculated_amount,
                "final_amount": breakdown.final_compensation_amount,
                "max_cap": breakdown.max_payout_cap,
            },
        )

        return DamageAssessmentResponse(**record)

    @classmethod
    def get_all_assessments(cls) -> List[DamageAssessmentResponse]:
        """Return all submitted assessments."""
        return [DamageAssessmentResponse(**r) for r in cls._registered_assessments]

    @classmethod
    def get_assessment_by_id(cls, assessment_id: uuid.UUID) -> Optional[DamageAssessmentResponse]:
        """Return a single assessment by UUID."""
        for r in cls._registered_assessments:
            if r["id"] == assessment_id:
                return DamageAssessmentResponse(**r)
        return None
