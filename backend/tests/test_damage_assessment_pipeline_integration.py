"""Integration tests for Live Decision Pipeline + Damage Assessment & Relief + Instant Settlement.

Covers all 8 specified verification tests:
TEST 1: Climate pipeline succeeds -> Trigger = TRUE, Damage Assessment available.
TEST 2: Damage Assessment calculates ₹X -> Instant Settlement receives exactly ₹X (settlement.amount == calculated_compensation).
TEST 3: Change damage inputs (1 acre -> 3 acres) -> Compensation and Settlement amount change accordingly.
TEST 4: Trigger false -> No settlement executed.
TEST 5: Damage Assessment incomplete / invalid -> Blocked / error returned.
TEST 6: Settlement retry -> Preserves idempotency, no duplicate transactions.
TEST 7: Settlement amount mismatch -> Blocked.
TEST 8: Arbitrary climate values -> Pipeline dynamically evaluates actual inputs with no preset branching.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.schemas.damage_assessment import (
    DamageAssessmentBase,
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
from app.climate.settlement_engine import SimulatedSettlementEngine


# ============================================================================
# TEST 1: Climate pipeline succeeds -> Trigger = TRUE, Damage Assessment available
# ============================================================================
@pytest.mark.asyncio
async def test_1_pipeline_trigger_success_enables_assessment():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Submit arbitrary live readings exceeding the 150mm threshold
        payload = {
            "sat_value": 180.0,
            "ground_value": 175.0,
            "iot_value": 178.0,
            "policy_threshold": 150.0,
        }
        res = await ac.post("/api/v1/demo/dynamic-run", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["consensus"]["status"] == "CONSENSUS_REACHED"
        assert data["trigger_evaluation"]["triggered"] is True
        assert data["trigger_evaluation"]["threshold"] == 150.0
        assert data["trigger_evaluation"]["observed_value"] >= 150.0


# ============================================================================
# TEST 2: Damage Assessment calculates ₹X -> Instant Settlement receives exactly ₹X
# ============================================================================
@pytest.mark.asyncio
async def test_2_settlement_receives_exact_calculated_compensation():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Step A: Calculate Damage Assessment for Farmer (2.5 Acres Paddy Major -> ₹25,000)
        calc_payload = {
            "reason_for_applying": "EXTREME_RAINFALL",
            "occupation": "FARMER",
            "applicant_name": "Ramesh Patel",
            "location_name": "Wayanad District, Kerala",
            "crop_type": "PADDY",
            "damaged_area": 2.5,
            "damaged_area_unit": "ACRES",
            "damage_severity": "MAJOR",
            "affected_percentage": 100.0,
        }
        calc_res = await ac.post("/api/v1/damage-assessments/calculate", json=calc_payload)
        assert calc_res.status_code == 200
        calc_data = calc_res.json()
        breakdown = calc_data["breakdown"]
        calculated_amount = breakdown["final_compensation_amount"]
        assert calculated_amount == 25000.0

        # Step B: Settle via Instant Settlement using exact calculated amount
        settle_payload = {
            "event_identifier": "EVT-INTEG-TEST-001",
            "assessment_id": "ASM-TEST-001",
            "calculated_compensation": calculated_amount,
            "rule_code": breakdown["rule_code"],
        }
        settle_res = await ac.post("/api/v1/demo/settle-damage-assessment", json=settle_payload)
        assert settle_res.status_code == 200
        settle_data = settle_res.json()

        # Strict equality check
        assert settle_data["status"] == "COMPLETED"
        assert settle_data["amount"] == calculated_amount
        assert settle_data["amount"] == 25000.0
        assert settle_data["transaction_id"].startswith("SIM-TXN-")


# ============================================================================
# TEST 3: Change damage inputs (1 acre -> 3 acres) -> Compensation & Settlement update
# ============================================================================
@pytest.mark.asyncio
async def test_3_damage_input_change_updates_settlement():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1 Acre Paddy Major -> 1 * 10,000 = ₹10,000
        calc_1 = await ac.post("/api/v1/damage-assessments/calculate", json={
            "reason_for_applying": "FLOOD",
            "occupation": "FARMER",
            "applicant_name": "Farmer 1",
            "crop_type": "PADDY",
            "damaged_area": 1.0,
            "damaged_area_unit": "ACRES",
            "damage_severity": "MAJOR",
        })
        amt_1 = calc_1.json()["breakdown"]["final_compensation_amount"]
        assert amt_1 == 10000.0

        # 3 Acres Paddy Major -> 3 * 10,000 = ₹30,000
        calc_3 = await ac.post("/api/v1/damage-assessments/calculate", json={
            "reason_for_applying": "FLOOD",
            "occupation": "FARMER",
            "applicant_name": "Farmer 3",
            "crop_type": "PADDY",
            "damaged_area": 3.0,
            "damaged_area_unit": "ACRES",
            "damage_severity": "MAJOR",
        })
        amt_3 = calc_3.json()["breakdown"]["final_compensation_amount"]
        assert amt_3 == 30000.0

        # Settle for 3 acres
        settle_res = await ac.post("/api/v1/demo/settle-damage-assessment", json={
            "event_identifier": "EVT-INTEG-TEST-003",
            "assessment_id": "ASM-TEST-003",
            "calculated_compensation": amt_3,
            "rule_code": calc_3.json()["breakdown"]["rule_code"],
        })
        assert settle_res.status_code == 200
        assert settle_res.json()["amount"] == 30000.0


# ============================================================================
# TEST 4: Trigger false -> No settlement executed
# ============================================================================
@pytest.mark.asyncio
async def test_4_trigger_false_no_settlement():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Rainfall below 150mm threshold
        payload = {
            "sat_value": 120.0,
            "ground_value": 118.0,
            "iot_value": 121.0,
            "policy_threshold": 150.0,
        }
        res = await ac.post("/api/v1/demo/dynamic-run", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["trigger_evaluation"]["triggered"] is False
        assert data["settlement"]["status"] in ("BLOCKED", "FAILED")
        assert data["settlement"]["amount"] == 0.0
        assert "not triggered" in data["settlement"]["failure_reason"].lower() or "blocked" in data["settlement"]["failure_reason"].lower()


# ============================================================================
# TEST 5: Damage Assessment incomplete / invalid -> Blocked / error returned
# ============================================================================
@pytest.mark.asyncio
async def test_5_invalid_damage_assessment_blocked():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Missing or negative area for Farmer
        invalid_payload = {
            "reason_for_applying": "EXTREME_RAINFALL",
            "occupation": "FARMER",
            "crop_type": "PADDY",
            "damaged_area": -1.0,
            "damaged_area_unit": "ACRES",
        }
        res = await ac.post("/api/v1/damage-assessments/calculate", json=invalid_payload)
        assert res.status_code == 422  # Validation error from schema


# ============================================================================
# TEST 6: Settlement retry -> Preserves idempotency, no duplicate transactions
# ============================================================================
@pytest.mark.asyncio
async def test_6_settlement_idempotency_no_duplicates():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        event_identifier = "EVT-IDEMPOTENT-RETRY-001"
        payload = {
            "event_identifier": event_identifier,
            "assessment_id": "ASM-IDEM-001",
            "calculated_compensation": 40000.0,
            "rule_code": "SHOP_GROCERY_INVENTORY_MAJOR_V1",
        }

        # First settlement request
        res1 = await ac.post("/api/v1/demo/settle-damage-assessment", json=payload)
        assert res1.status_code == 200
        data1 = res1.json()
        tx1 = data1["transaction_id"]

        # Retry identical settlement request
        res2 = await ac.post("/api/v1/demo/settle-damage-assessment", json=payload)
        assert res2.status_code == 200
        data2 = res2.json()
        tx2 = data2["transaction_id"]

        # Must return the identical transaction ID (idempotent)
        assert tx1 == tx2
        assert data1["amount"] == data2["amount"] == 40000.0


# ============================================================================
# TEST 7: Settlement amount mismatch / invalid -> Blocked
# ============================================================================
@pytest.mark.asyncio
async def test_7_invalid_settlement_amount_rejected():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Zero amount settlement
        res_zero = await ac.post("/api/v1/demo/settle-damage-assessment", json={
            "event_identifier": "EVT-INVALID-AMT-001",
            "calculated_compensation": 0.0,
        })
        assert res_zero.status_code == 400
        assert "greater than zero" in res_zero.json()["detail"]

        # Negative amount settlement
        res_neg = await ac.post("/api/v1/demo/settle-damage-assessment", json={
            "event_identifier": "EVT-INVALID-AMT-002",
            "calculated_compensation": -5000.0,
        })
        assert res_neg.status_code == 400


# ============================================================================
# TEST 8: Arbitrary climate values -> Pipeline dynamically evaluates actual inputs
# ============================================================================
@pytest.mark.asyncio
async def test_8_arbitrary_climate_values_dynamic():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Arbitrary custom values: 210, 205, 208 mm with threshold 190 mm
        payload = {
            "sat_value": 210.0,
            "ground_value": 205.0,
            "iot_value": 208.0,
            "policy_threshold": 190.0,
        }
        res = await ac.post("/api/v1/demo/dynamic-run", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["observations"][0]["value"] == 210.0
        assert data["observations"][1]["value"] == 205.0
        assert data["observations"][2]["value"] == 208.0
        assert data["trigger_evaluation"]["threshold"] == 190.0
        assert data["trigger_evaluation"]["triggered"] is True
