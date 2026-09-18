"""Unit and Integration Tests for Risk2Relief Climate Insurance Pipeline.

Validates multi-source ingestion, data validation, ML anomaly detection, source independence,
configurable consensus, parametric trigger evaluation, settlement idempotency, and demo scenarios.
"""

import pytest
import uuid
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.climate.validation import ClimateValidationEngine, ClimateQualityEnum
from app.climate.anomaly import ClimateAnomalyEngine
from app.climate.consensus import ClimateConsensusEngine, ConsensusPolicy
from app.climate.policy_engine import ParametricPolicyEngine
from app.climate.settlement_engine import SimulatedSettlementEngine
from app.climate.audit_trail import ClimateAuditTrailService
from app.climate.simulator import Risk2ReliefSimulator


@pytest.fixture(autouse=True)
def reset_climate_state():
    """Reset simulation ledger, caches, and audit trails before each test."""
    ClimateValidationEngine.reset_cache()
    SimulatedSettlementEngine.reset_ledger()
    ClimateAuditTrailService.reset_audit_log()
    yield


# ============================================================================
# 1. VALIDATION ENGINE TESTS
# ============================================================================

def test_climate_validation_nominal():
    """Verify valid climate observation passes with VALID quality."""
    res = ClimateValidationEngine.validate_observation(
        source_id="SRC-SAT-001",
        event_id="OBS-TEST-001",
        metric="rainfall_24h",
        value=158.0,
        unit="mm",
        timestamp=datetime.now(timezone.utc),
    )
    assert res.is_valid is True
    assert res.quality == ClimateQualityEnum.VALID
    assert res.error_code is None


def test_climate_validation_future_timestamp_rejected():
    """Verify future timestamp exceeding clock skew is rejected."""
    future_time = datetime.now(timezone.utc) + timedelta(minutes=10)
    res = ClimateValidationEngine.validate_observation(
        source_id="SRC-SAT-001",
        event_id="OBS-FUTURE-001",
        metric="rainfall_24h",
        value=158.0,
        unit="mm",
        timestamp=future_time,
    )
    assert res.is_valid is False
    assert res.quality == ClimateQualityEnum.INVALID
    assert res.error_code == "ERR_FUTURE_TIMESTAMP"


def test_climate_validation_stale_timestamp():
    """Verify timestamp older than freshness window is tagged STALE."""
    stale_time = datetime.now(timezone.utc) - timedelta(hours=5)
    res = ClimateValidationEngine.validate_observation(
        source_id="SRC-SAT-001",
        event_id="OBS-STALE-001",
        metric="rainfall_24h",
        value=158.0,
        unit="mm",
        timestamp=stale_time,
    )
    assert res.is_valid is True  # Stale data is ingestible for historical audit
    assert res.quality == ClimateQualityEnum.STALE
    assert res.error_code == "ERR_STALE_OBSERVATION"


def test_climate_validation_physical_bounds():
    """Verify unphysical values (e.g. 5000mm rainfall) are rejected."""
    res = ClimateValidationEngine.validate_observation(
        source_id="SRC-SAT-001",
        event_id="OBS-BOUNDS-001",
        metric="rainfall_24h",
        value=5000.0,  # Exceeds world record bounds
        unit="mm",
        timestamp=datetime.now(timezone.utc),
    )
    assert res.is_valid is False
    assert res.quality == ClimateQualityEnum.INVALID
    assert res.error_code == "ERR_OUT_OF_BOUNDS"


def test_climate_validation_duplicate_detection():
    """Verify duplicate observation ID from the same source is rejected."""
    now = datetime.now(timezone.utc)
    res1 = ClimateValidationEngine.validate_observation(
        source_id="SRC-GROUND-002",
        event_id="OBS-DUP-001",
        metric="rainfall_24h",
        value=154.0,
        unit="mm",
        timestamp=now,
    )
    assert res1.is_valid is True

    # Immediate resubmission
    res2 = ClimateValidationEngine.validate_observation(
        source_id="SRC-GROUND-002",
        event_id="OBS-DUP-001",
        metric="rainfall_24h",
        value=154.0,
        unit="mm",
        timestamp=now,
    )
    assert res2.is_valid is False
    assert res2.quality == ClimateQualityEnum.DUPLICATE
    assert res2.error_code == "ERR_DUPLICATE_OBSERVATION"


# ============================================================================
# 2. ML ANOMALY DETECTION TESTS
# ============================================================================

def test_climate_anomaly_peer_cluster_clean():
    """Verify consistent peer readings (158, 154, 156 mm) have low anomaly scores."""
    obs = [
        {"source_id": "S1", "value": 158.0, "quality": "VALID"},
        {"source_id": "S2", "value": 154.0, "quality": "VALID"},
        {"source_id": "S3", "value": 156.0, "quality": "VALID"},
    ]
    results = ClimateAnomalyEngine.evaluate_peer_observations(obs)
    for _, sig in results:
        assert sig.is_anomaly is False
        assert sig.anomaly_score < 0.40


def test_climate_anomaly_peer_cluster_outlier_flagged():
    """Verify spoofed/outlier reading (17 mm vs ~157 mm) is flagged with high anomaly score."""
    obs = [
        {"source_id": "S1", "value": 158.0, "quality": "VALID"},
        {"source_id": "S2", "value": 156.0, "quality": "VALID"},
        {"source_id": "S3", "value": 17.0, "quality": "VALID"},  # Severe outlier
    ]
    results = ClimateAnomalyEngine.evaluate_peer_observations(obs)
    outlier_sig = [sig for o, sig in results if o["source_id"] == "S3"][0]
    normal_sigs = [sig for o, sig in results if o["source_id"] != "S3"]

    assert outlier_sig.is_anomaly is True
    assert outlier_sig.anomaly_score >= 0.60
    assert "significantly deviates from peer-source cluster" in outlier_sig.reason

    for sig in normal_sigs:
        assert sig.is_anomaly is False


# ============================================================================
# 3. SOURCE INDEPENDENCE & CONSENSUS TESTS
# ============================================================================

def test_source_independence_consensus_success():
    """Verify 3 independent source groups reaching tight agreement succeed."""
    obs = [
        {"source_id": "S1", "value": 158.0, "independence_group": "GROUP_A", "reliability_score": 0.98, "quality": "VALID"},
        {"source_id": "S2", "value": 154.0, "independence_group": "GROUP_B", "reliability_score": 0.96, "quality": "VALID"},
        {"source_id": "S3", "value": 156.0, "independence_group": "GROUP_C", "reliability_score": 0.94, "quality": "VALID"},
    ]
    obs_with_sig = ClimateAnomalyEngine.evaluate_peer_observations(obs)
    consensus = ClimateConsensusEngine.evaluate_consensus(obs_with_sig, ConsensusPolicy(min_independent_sources=2))

    assert consensus.status == "CONSENSUS_REACHED"
    assert consensus.consensus_value is not None
    assert 154.0 <= consensus.consensus_value <= 158.0
    assert consensus.independent_source_count == 3
    assert consensus.agreement_score > 0.90


def test_source_independence_correlated_group_rejection():
    """Verify multiple sources from the same single independence group fail quorum."""
    obs = [
        {"source_id": "S1", "value": 158.0, "independence_group": "SAME_PROVIDER", "reliability_score": 0.98, "quality": "VALID"},
        {"source_id": "S2", "value": 156.0, "independence_group": "SAME_PROVIDER", "reliability_score": 0.96, "quality": "VALID"},
    ]
    obs_with_sig = ClimateAnomalyEngine.evaluate_peer_observations(obs)
    consensus = ClimateConsensusEngine.evaluate_consensus(obs_with_sig, ConsensusPolicy(min_independent_sources=2))

    assert consensus.status == "CONSENSUS_FAILED"
    assert "Only 1 independent source group" in consensus.explanation


# ============================================================================
# 4. POLICY TRIGGER & SETTLEMENT IDEMPOTENCY TESTS
# ============================================================================

def test_parametric_policy_trigger_and_settlement_idempotency():
    """Verify deterministic trigger activates and duplicate request returns identical settlement."""
    policy = {
        "id": "POL-TEST-001",
        "policy_number": "R2R-POL-TEST-001",
        "wallet_id": "SIM-WALLET-001",
        "metric": "rainfall_24h",
        "operator": ">=",
        "threshold": 150.0,
        "payout_amount": 25000.0,
        "currency": "INR",
        "active": True,
    }

    obs = [
        {"source_id": "S1", "value": 158.0, "independence_group": "GRP_A", "reliability_score": 0.98, "quality": "VALID"},
        {"source_id": "S2", "value": 154.0, "independence_group": "GRP_B", "reliability_score": 0.96, "quality": "VALID"},
    ]
    consensus = ClimateConsensusEngine.evaluate_consensus(ClimateAnomalyEngine.evaluate_peer_observations(obs))
    trigger_res = ParametricPolicyEngine.evaluate_policy_trigger(policy, consensus, "EVT-TEST-001")

    assert trigger_res.triggered is True
    assert trigger_res.payout_amount == 25000.0

    # 1st Settlement Execution
    settlement1 = SimulatedSettlementEngine.execute_settlement(trigger_res)
    assert settlement1.status == "COMPLETED"
    assert settlement1.amount == 25000.0
    assert settlement1.is_idempotent_retry is False
    txn_id_1 = settlement1.transaction_id

    # 2nd Settlement Execution (Idempotent Retry)
    settlement2 = SimulatedSettlementEngine.execute_settlement(trigger_res)
    assert settlement2.status == "COMPLETED"
    assert settlement2.transaction_id == txn_id_1  # Exact same transaction ID preserved
    assert settlement2.is_idempotent_retry is True

    # Confirm ledger has exactly 1 entry (Zero double payouts)
    assert len(SimulatedSettlementEngine.get_all_settlements()) == 1


# ============================================================================
# 5. END-TO-END DEMO SCENARIO TESTS
# ============================================================================

def test_e2e_scenario_1_success():
    """Verify Scenario 1 (158 / 154 / 156 mm) executes complete pipeline with ₹25k payout."""
    res = Risk2ReliefSimulator.run_scenario_1_success()
    assert res.scenario_id == "SCENARIO_1_SUCCESS"
    assert res.validation_status == "VALID"
    assert res.anomaly_detection["is_clean"] is True
    assert res.consensus.status == "CONSENSUS_REACHED"
    assert res.trigger_evaluation is not None and res.trigger_evaluation.triggered is True
    assert res.settlement is not None and res.settlement.status == "COMPLETED"
    assert res.settlement.amount == 25000.0
    assert len(res.pipeline_stages) >= 6
    assert len(res.audit_trail) >= 6


def test_e2e_scenario_2_disagreement():
    """Verify Scenario 2 (158 / 156 / 17 mm) flags outlier and suppresses payout."""
    res = Risk2ReliefSimulator.run_scenario_2_disagreement()
    assert res.scenario_id == "SCENARIO_2_DISAGREEMENT"
    assert res.anomaly_detection["flagged_count"] >= 1
    # Payout must be blocked safely
    assert res.settlement is not None
    assert res.settlement.status in ("BLOCKED", "FAILED")
    assert res.settlement.amount == 0.0


def test_e2e_scenario_3_no_trigger():
    """Verify Scenario 3 (120 / 118 / 121 mm) consensus reached but sub-threshold produces zero payout."""
    res = Risk2ReliefSimulator.run_scenario_3_no_trigger()
    assert res.scenario_id == "SCENARIO_3_NO_TRIGGER"
    assert res.consensus.status == "CONSENSUS_REACHED"
    assert res.trigger_evaluation is not None and res.trigger_evaluation.triggered is False
    assert res.settlement is not None and res.settlement.amount == 0.0


def test_e2e_scenario_4_idempotency():
    """Verify Scenario 4 retry returns existing transaction without duplicate settlement."""
    # First run Scenario 1
    Risk2ReliefSimulator.run_scenario_1_success()
    initial_count = len(SimulatedSettlementEngine.get_all_settlements())

    # Now run Scenario 4 (retry)
    res_retry = Risk2ReliefSimulator.run_scenario_4_idempotency()
    final_count = len(SimulatedSettlementEngine.get_all_settlements())

    assert res_retry.settlement is not None
    assert res_retry.settlement.status == "COMPLETED"
    assert final_count == initial_count  # No second record added


# ============================================================================
# 6. API GATEWAY INTEGRATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_api_endpoints():
    """Verify REST API v1 endpoints for dashboard, sources, policies, and demo scenarios."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Dashboard summary
        resp = await client.get("/api/v1/dashboard/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert data["system_status"] == "OPERATIONAL"
        assert data["simulation_mode"] is True

        # 2. Climate sources list
        resp = await client.get("/api/v1/climate/sources")
        assert resp.status_code == 200
        sources = resp.json()
        assert len(sources) >= 3
        assert any(s["source_type"] == "SATELLITE" for s in sources)

        # 3. Policies list
        resp = await client.get("/api/v1/policies")
        assert resp.status_code == 200
        policies = resp.json()
        assert len(policies) >= 1

        # 4. Trigger Demo Scenario 1 via API
        resp = await client.post("/api/v1/demo/scenario/success")
        assert resp.status_code == 200
        scenario_res = resp.json()
        assert scenario_res["scenario_id"] == "SCENARIO_1_SUCCESS"
        assert scenario_res["settlement"]["status"] == "COMPLETED"
        assert scenario_res["settlement"]["amount"] == 25000.0

        # 5. Audit trail endpoint
        resp = await client.get("/api/v1/climate/audit")
        assert resp.status_code == 200
        audit_logs = resp.json()
        assert len(audit_logs) >= 5
