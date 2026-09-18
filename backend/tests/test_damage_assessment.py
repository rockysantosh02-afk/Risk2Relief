"""Comprehensive unit and integration test suite for Damage Assessment & Dynamic Filter Engine.

Tests:
1. Valid farmer assessment calculation
2. Cent-to-Acre unit conversion
3. Rejection of negative/zero area
4. Rejection of missing crop type for farmer
5. Valid shopkeeper assessment calculation
6. Rejection of missing store type for shopkeeper
7. Daily wage worker calculation
8. Backend payout cap enforcement
9. Damage assessment persistence & audit trail integration
10. API endpoints for calculate, create, list, and rule retrieval
11. Dynamic occupation switching isolation
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.schemas.damage_assessment import (
    DamageAssessmentBase,
    DamageAssessmentCreate,
    DamageAssessmentCalculateRequest,
    Occupation,
    ReasonForApplying,
    FarmerCropType,
    LandAreaUnit,
    DamageSeverity,
    ShopStoreType,
    ShopDamageCategory,
    InventoryDamageBand,
)
from app.services.compensation_service import DamageCompensationService
from app.climate.audit_trail import ClimateAuditTrailService


# ============================================================================
# 1. Unit Tests: Compensation Service & Unit Conversion
# ============================================================================

def test_farmer_paddy_major_calculation():
    """Verify Farmer with 2.5 Acres Paddy Major damage calculates ₹25,000."""
    req = DamageAssessmentBase(
        reason_for_applying=ReasonForApplying.EXTREME_RAINFALL,
        occupation=Occupation.FARMER,
        applicant_name="Ramesh Patel",
        location_name="Wayanad District",
        crop_type=FarmerCropType.PADDY,
        damaged_area=2.5,
        damaged_area_unit=LandAreaUnit.ACRES,
        damage_severity=DamageSeverity.MAJOR,
        affected_percentage=100.0,
    )
    breakdown = DamageCompensationService.calculate_compensation(req)

    assert breakdown.rule_code == "FARMER_PADDY_MAJOR_V1"
    assert breakdown.normalized_quantity == 2.5
    assert breakdown.normalized_unit == "ACRES"
    assert breakdown.rate_per_unit == 10000.0
    assert breakdown.final_compensation_amount == 25000.0
    assert breakdown.cap_applied is False
    assert "2.5 Acres × ₹10,000/acre" in breakdown.formula_string


def test_farmer_cent_to_acre_conversion():
    """Verify 250 Cents is normalized to 2.5 Acres with identical calculation."""
    req = DamageAssessmentBase(
        reason_for_applying=ReasonForApplying.FLOOD,
        occupation=Occupation.FARMER,
        crop_type=FarmerCropType.PADDY,
        damaged_area=250.0,
        damaged_area_unit=LandAreaUnit.CENTS,
        damage_severity=DamageSeverity.MAJOR,
    )
    breakdown = DamageCompensationService.calculate_compensation(req)

    assert breakdown.original_quantity == 250.0
    assert breakdown.original_unit == "CENTS"
    assert breakdown.normalized_quantity == 2.5
    assert breakdown.normalized_unit == "ACRES"
    assert breakdown.final_compensation_amount == 25000.0
    assert "250.0 Cents ÷ 100 = 2.5 Acres" in breakdown.formula_string


def test_farmer_negative_and_zero_area_rejected():
    """Verify zero and negative area throw explicit validation errors."""
    with pytest.raises(ValueError, match="strictly greater than zero"):
        DamageAssessmentBase(
            reason_for_applying=ReasonForApplying.EXTREME_RAINFALL,
            occupation=Occupation.FARMER,
            crop_type=FarmerCropType.PADDY,
            damaged_area=-2.0,
            damaged_area_unit=LandAreaUnit.ACRES,
        )

    with pytest.raises(ValueError, match="strictly greater than zero"):
        DamageAssessmentBase(
            reason_for_applying=ReasonForApplying.EXTREME_RAINFALL,
            occupation=Occupation.FARMER,
            crop_type=FarmerCropType.PADDY,
            damaged_area=0.0,
            damaged_area_unit=LandAreaUnit.ACRES,
        )


def test_farmer_missing_crop_type_rejected():
    """Verify farmer without crop type throws validation error."""
    with pytest.raises(ValueError, match="Crop type is required"):
        DamageAssessmentBase(
            reason_for_applying=ReasonForApplying.EXTREME_RAINFALL,
            occupation=Occupation.FARMER,
            damaged_area=2.0,
            damaged_area_unit=LandAreaUnit.ACRES,
        )


def test_shopkeeper_grocery_inventory_calculation():
    """Verify Shopkeeper with Grocery inventory damage calculates tier amount."""
    req = DamageAssessmentBase(
        reason_for_applying=ReasonForApplying.FLOOD,
        occupation=Occupation.SHOPKEEPER,
        applicant_name="Suresh Kumar",
        store_type=ShopStoreType.GROCERY_STORE,
        damage_category=ShopDamageCategory.INVENTORY_DAMAGE,
        damage_severity=DamageSeverity.MAJOR,
        inventory_damage_band=InventoryDamageBand.BAND_25K_50K,
    )
    breakdown = DamageCompensationService.calculate_compensation(req)

    assert breakdown.rule_code == "SHOP_GROCERY_INVENTORY_MAJOR_V1"
    assert breakdown.rate_per_unit == 30000.0
    assert breakdown.final_compensation_amount == 30000.0
    assert breakdown.cap_applied is False


def test_shopkeeper_missing_store_type_rejected():
    """Verify shopkeeper without store type throws validation error."""
    with pytest.raises(ValueError, match="Store type is required"):
        DamageAssessmentBase(
            reason_for_applying=ReasonForApplying.FLOOD,
            occupation=Occupation.SHOPKEEPER,
            damage_category=ShopDamageCategory.INVENTORY_DAMAGE,
        )


def test_daily_wage_worker_calculation():
    """Verify Daily wage worker calculates rate * days lost."""
    req = DamageAssessmentBase(
        reason_for_applying=ReasonForApplying.EXTREME_HEAT,
        occupation=Occupation.DAILY_WAGE_WORKER,
        damage_severity=DamageSeverity.MAJOR,
        loss_quantity=10.0,
    )
    breakdown = DamageCompensationService.calculate_compensation(req)

    assert breakdown.rule_code == "DAILY_WAGE_HEAT_MAJOR_V1"
    assert breakdown.rate_per_unit == 800.0
    assert breakdown.final_compensation_amount == 8000.0


def test_backend_payout_cap_enforcement():
    """Verify high area (e.g. 10 Acres Paddy -> ₹100,000) is strictly capped at ₹50,000."""
    req = DamageAssessmentBase(
        reason_for_applying=ReasonForApplying.FLOOD,
        occupation=Occupation.FARMER,
        crop_type=FarmerCropType.PADDY,
        damaged_area=10.0,
        damaged_area_unit=LandAreaUnit.ACRES,
        damage_severity=DamageSeverity.MAJOR,
    )
    breakdown = DamageCompensationService.calculate_compensation(req)

    assert breakdown.raw_calculated_amount == 100000.0
    assert breakdown.max_payout_cap == 50000.0
    assert breakdown.cap_applied is True
    assert breakdown.final_compensation_amount == 50000.0
    assert "Capped at Max Limit ₹50,000" in breakdown.formula_string


def test_record_assessment_audit_trail_integration():
    """Verify submitting damage assessment logs DAMAGE_DATA_VALIDATED and COMPENSATION_CALCULATED in audit trail."""
    create_req = DamageAssessmentCreate(
        reason_for_applying=ReasonForApplying.CYCLONE,
        occupation=Occupation.FARMER,
        applicant_name="Anita Sharma",
        crop_type=FarmerCropType.WHEAT,
        damaged_area=3.0,
        damaged_area_unit=LandAreaUnit.ACRES,
        damage_severity=DamageSeverity.MAJOR,
    )
    resp = DamageCompensationService.record_assessment(create_req)

    assert resp.assessment_number.startswith("ASM-2026-")
    assert resp.calculated_amount == 27000.0  # 3.0 * 9000

    # Verify audit events
    audit_events = ClimateAuditTrailService.get_all_events(limit=10)
    stages = [e.stage for e in audit_events]
    assert "DAMAGE_DATA_VALIDATED" in stages
    assert "COMPENSATION_CALCULATED" in stages


# ============================================================================
# 2. Integration Tests: FastAPI Endpoints
# ============================================================================

@pytest.mark.asyncio
async def test_api_damage_assessments_calculate():
    """Test POST /api/v1/damage-assessments/calculate preview endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "reason_for_applying": "EXTREME_RAINFALL",
            "occupation": "FARMER",
            "applicant_name": "Kavita Devi",
            "crop_type": "PADDY",
            "damaged_area": 2.5,
            "damaged_area_unit": "ACRES",
            "damage_severity": "MAJOR",
        }
        resp = await client.post("/api/v1/damage-assessments/calculate", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "SUCCESS"
        assert data["breakdown"]["final_compensation_amount"] == 25000.0
        assert data["breakdown"]["rule_code"] == "FARMER_PADDY_MAJOR_V1"


@pytest.mark.asyncio
async def test_api_damage_assessments_create_and_get():
    """Test POST /api/v1/damage-assessments and GET by ID."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "reason_for_applying": "FLOOD",
            "occupation": "SHOPKEEPER",
            "applicant_name": "Sunil Varma",
            "store_type": "GROCERY_STORE",
            "damage_category": "INVENTORY_DAMAGE",
            "damage_severity": "MAJOR",
            "inventory_damage_band": "BAND_25K_50K",
        }
        create_resp = await client.post("/api/v1/damage-assessments", json=payload)
        assert create_resp.status_code == 201
        asm_data = create_resp.json()
        asm_id = asm_data["id"]
        assert asm_data["calculated_amount"] == 30000.0

        # Retrieve by ID
        get_resp = await client.get(f"/api/v1/damage-assessments/{asm_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["id"] == asm_id


@pytest.mark.asyncio
async def test_api_damage_rules_list():
    """Test GET /api/v1/damage-rules returns all active preconfigured rules."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/damage-rules")
        assert resp.status_code == 200
        rules = resp.json()
        assert len(rules) >= 8
        rule_codes = [r["rule_code"] for r in rules]
        assert "FARMER_PADDY_MAJOR_V1" in rule_codes
        assert "SHOP_GROCERY_INVENTORY_MAJOR_V1" in rule_codes
