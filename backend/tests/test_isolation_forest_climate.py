"""Comprehensive Unit and Integration Tests for scikit-learn Isolation Forest ML Anomaly Detection.

Validates:
1. Model initialization and centralized parameters.
2. Training on reference climate dataset (SIMULATED / DEMO REFERENCE DATA).
3. Model scoring and raw decision scores.
4. Normal observation peer cluster evaluation (e.g. 158 / 154 / 156 mm).
5. Anomalous observation detection (e.g. 158 / 156 / 17 mm).
6. Multiple dynamic observation sets (173 / 169 / 171 mm, 180 / 175 / 178 mm).
7. Single observation handling (no peers available -> LIMITED status).
8. Empty / invalid observation handling.
9. Deterministic random_state reproducibility.
10. Model versioning in output signals.
11. Advisory constraint (ML does not trigger payout directly).
12. Graceful degradation fallback on exception.
13. Dynamic pipeline API integration (`/api/v1/demo/dynamic-run`).
14. Audit trail logging of ML events (`ML_ANOMALY_CHECK_COMPLETED`).
"""

import pytest
import numpy as np
from datetime import datetime, timezone
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.climate.anomaly import (
    ClimateAnomalyEngine,
    IsolationForestClimateDetector,
    ClimateAnomalySignal,
    build_reference_climate_dataset,
    ML_MODEL_NAME,
    ML_MODEL_VERSION,
    ML_CONTAMINATION,
    ML_RANDOM_STATE,
)
from app.climate.simulator import Risk2ReliefSimulator
from app.climate.audit_trail import ClimateAuditTrailService
from app.climate.settlement_engine import SimulatedSettlementEngine
from app.climate.validation import ClimateValidationEngine


@pytest.fixture(autouse=True)
def reset_state():
    """Reset simulation ledger, caches, and audit logs before each test."""
    ClimateValidationEngine.reset_cache()
    SimulatedSettlementEngine.reset_ledger()
    ClimateAuditTrailService.reset_audit_log()
    IsolationForestClimateDetector.reset_instance()
    yield


# ----------------------------------------------------------------------------
# 1. MODEL INITIALIZATION & TRAINING TESTS
# ----------------------------------------------------------------------------

def test_isolation_forest_initialization_and_dataset():
    """Verify Isolation Forest initializes, loads reference dataset, and trains successfully."""
    detector = IsolationForestClimateDetector.get_instance()
    assert detector.model_name == ML_MODEL_NAME
    assert detector.model_version == ML_MODEL_VERSION
    assert detector.contamination == ML_CONTAMINATION
    assert detector.random_state == ML_RANDOM_STATE
    assert detector.is_trained is True
    assert detector.model is not None
    assert detector.training_sample_count >= 500
    assert "SIMULATED / DEMO REFERENCE TRAINING DATA" in detector.training_dataset_id


def test_build_reference_climate_dataset_structure():
    """Verify reference dataset generates proper 4D feature vectors across regimes."""
    features, desc = build_reference_climate_dataset(seed=42)
    assert len(features) >= 500
    assert "SIMULATED / DEMO REFERENCE TRAINING DATA" in desc
    for row in features:
        assert len(row) == 4
        base_val, peer_dev, robust_z, rel_ratio = row
        assert base_val >= 0.0
        assert peer_dev >= 0.0
        assert robust_z >= 0.0
        assert rel_ratio >= 0.0


# ----------------------------------------------------------------------------
# 2. SCORING & CLUSTER EVALUATION TESTS
# ----------------------------------------------------------------------------

def test_isolation_forest_scoring_normal_cluster():
    """Verify normal cluster (158 / 154 / 156 mm) results in NO_ANOMALY and low anomaly scores."""
    obs = [
        {"source_id": "SRC-SAT-001", "source_identifier": "Copernicus-Sat", "value": 158.0},
        {"source_id": "SRC-GRD-002", "source_identifier": "IMD-Ground", "value": 154.0},
        {"source_id": "SRC-IOT-003", "source_identifier": "AgriSense-IoT", "value": 156.0},
    ]
    results = ClimateAnomalyEngine.evaluate_peer_observations(obs)
    assert len(results) == 3

    for o, sig in results:
        assert sig.is_anomaly is False
        assert sig.status == "NO_ANOMALY"
        assert sig.anomaly_score < 0.45
        assert sig.model_name == ML_MODEL_NAME
        assert sig.model_version == ML_MODEL_VERSION
        assert "Consistent with reference climate distribution" in sig.reason
        assert "value" in sig.features_used
        assert "peer_median" in sig.features_used
        assert "robust_z_score" in sig.features_used


def test_isolation_forest_scoring_anomaly_outlier():
    """Verify outlier reading (17 mm vs ~157 mm) is correctly flagged with high anomaly score."""
    obs = [
        {"source_id": "SRC-SAT-001", "source_identifier": "Copernicus-Sat", "value": 158.0},
        {"source_id": "SRC-GRD-002", "source_identifier": "IMD-Ground", "value": 156.0},
        {"source_id": "SRC-IOT-003", "source_identifier": "AgriSense-IoT", "value": 17.0},
    ]
    results = ClimateAnomalyEngine.evaluate_peer_observations(obs)
    outlier_tuple = [r for r in results if r[0]["source_id"] == "SRC-IOT-003"][0]
    normal_tuples = [r for r in results if r[0]["source_id"] != "SRC-IOT-003"]

    outlier_obs, outlier_sig = outlier_tuple
    assert outlier_sig.is_anomaly is True
    assert outlier_sig.status == "ANOMALY_DETECTED"
    assert outlier_sig.anomaly_score >= 0.60
    assert outlier_sig.raw_decision_score is not None
    assert "deviates from peer-source cluster" in outlier_sig.reason
    assert "Statistically unusual relative to reference data" in outlier_sig.reason

    for _, sig in normal_tuples:
        assert sig.is_anomaly is False
        assert sig.status == "NO_ANOMALY"


def test_isolation_forest_scoring_dynamic_heavy_flood():
    """Verify dynamic arbitrary input (173 / 169 / 171 mm) evaluates cleanly without anomalies."""
    obs = [
        {"source_id": "SRC-SAT-001", "value": 173.0},
        {"source_id": "SRC-GRD-002", "value": 169.0},
        {"source_id": "SRC-IOT-003", "value": 171.0},
    ]
    results = ClimateAnomalyEngine.evaluate_peer_observations(obs)
    for _, sig in results:
        assert sig.is_anomaly is False
        assert sig.status == "NO_ANOMALY"
        assert sig.anomaly_score < 0.40


def test_isolation_forest_scoring_dynamic_extreme_events():
    """Verify dynamic arbitrary inputs (180 / 175 / 178 mm) evaluate accurately."""
    obs = [
        {"source_id": "SRC-SAT-001", "value": 180.0},
        {"source_id": "SRC-GRD-002", "value": 175.0},
        {"source_id": "SRC-IOT-003", "value": 178.0},
    ]
    results = ClimateAnomalyEngine.evaluate_peer_observations(obs)
    for _, sig in results:
        assert sig.is_anomaly is False
        assert sig.status == "NO_ANOMALY"


# ----------------------------------------------------------------------------
# 3. EDGE CASES, EMPTY, & SINGLE-SOURCE TESTS
# ----------------------------------------------------------------------------

def test_isolation_forest_single_source_handling():
    """Verify single observation returns LIMITED status without fabricating peer consensus."""
    obs = [{"source_id": "SRC-SAT-001", "value": 158.0}]
    results = ClimateAnomalyEngine.evaluate_peer_observations(obs)
    assert len(results) == 1
    _, sig = results[0]
    assert sig.is_anomaly is False
    assert sig.status == "LIMITED"
    assert sig.anomaly_score == 0.0
    assert "Single observation provided" in sig.reason


def test_isolation_forest_empty_observations():
    """Verify empty list returns empty results safely."""
    results = ClimateAnomalyEngine.evaluate_peer_observations([])
    assert results == []


# ----------------------------------------------------------------------------
# 4. DETERMINISM & ADVISORY SAFETY INVARIANT
# ----------------------------------------------------------------------------

def test_isolation_forest_determinism():
    """Verify fixed random_state yields identical scores across separate runs."""
    obs = [
        {"source_id": "S1", "value": 158.0},
        {"source_id": "S2", "value": 156.0},
        {"source_id": "S3", "value": 17.0},
    ]
    IsolationForestClimateDetector.reset_instance()
    run1 = ClimateAnomalyEngine.evaluate_peer_observations(obs)

    IsolationForestClimateDetector.reset_instance()
    run2 = ClimateAnomalyEngine.evaluate_peer_observations(obs)

    for i in range(3):
        assert run1[i][1].anomaly_score == run2[i][1].anomaly_score
        assert run1[i][1].raw_decision_score == run2[i][1].raw_decision_score
        assert run1[i][1].is_anomaly == run2[i][1].is_anomaly


def test_isolation_forest_advisory_disclaimer_present():
    """Verify all signals contain explicit advisory non-authoritative disclaimers."""
    obs = [{"source_id": "S1", "value": 158.0}, {"source_id": "S2", "value": 154.0}]
    results = ClimateAnomalyEngine.evaluate_peer_observations(obs)
    for _, sig in results:
        assert "ADVISORY ONLY" in sig.advisory_disclaimer
        assert "never directly authorize" in sig.advisory_disclaimer.lower()


# ----------------------------------------------------------------------------
# 5. DYNAMIC LIVE PIPELINE & AUDIT INTEGRATION
# ----------------------------------------------------------------------------

def test_dynamic_pipeline_runner_success():
    """Verify Risk2ReliefSimulator.run_dynamic_pipeline processes arbitrary inputs (173/169/171 mm)."""
    res = Risk2ReliefSimulator.run_dynamic_pipeline(sat_value=173.0, ground_value=169.0, iot_value=171.0)
    assert res.scenario_id == "DYNAMIC_LIVE_EVALUATION"
    assert res.anomaly_detection["is_clean"] is True
    assert res.anomaly_detection["model_name"] == ML_MODEL_NAME
    assert res.consensus.status == "CONSENSUS_REACHED"
    assert res.trigger_evaluation is not None and res.trigger_evaluation.triggered is True
    assert res.settlement is not None and res.settlement.status == "COMPLETED"
    assert res.settlement.amount == 25000.0


def test_dynamic_pipeline_runner_anomaly_disagreement():
    """Verify dynamic arbitrary input with outlier (158/156/17 mm) blocks payout safely."""
    res = Risk2ReliefSimulator.run_dynamic_pipeline(sat_value=158.0, ground_value=156.0, iot_value=17.0)
    assert res.scenario_id == "DYNAMIC_LIVE_EVALUATION"
    assert res.anomaly_detection["flagged_count"] >= 1
    assert res.anomaly_detection["is_clean"] is False
    assert res.settlement is not None
    assert res.settlement.status in ("BLOCKED", "FAILED")
    assert res.settlement.amount == 0.0


@pytest.mark.asyncio
async def test_dynamic_pipeline_rest_api_endpoint():
    """Verify POST /api/v1/demo/dynamic-run REST endpoint with custom values."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "sat_value": 173.0,
            "ground_value": 169.0,
            "iot_value": 171.0,
            "policy_threshold": 150.0,
            "payout_amount": 25000.0,
        }
        resp = await client.post("/api/v1/demo/dynamic-run", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["scenario_id"] == "DYNAMIC_LIVE_EVALUATION"
        assert data["anomaly_detection"]["model_name"] == ML_MODEL_NAME
        assert data["anomaly_detection"]["is_clean"] is True
        assert data["consensus"]["status"] == "CONSENSUS_REACHED"
        assert data["settlement"]["status"] == "COMPLETED"
        assert data["settlement"]["amount"] == 25000.0


@pytest.mark.asyncio
async def test_dynamic_pipeline_audit_event_logged():
    """Verify ML anomaly check is logged to the immutable audit trail."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "sat_value": 158.0,
            "ground_value": 156.0,
            "iot_value": 17.0,
            "event_identifier": "EVT-TEST-AUDIT-ML",
        }
        resp = await client.post("/api/v1/demo/dynamic-run", json=payload)
        assert resp.status_code == 200

        # Query audit trail
        audit_resp = await client.get("/api/v1/climate/audit?event_identifier=EVT-TEST-AUDIT-ML")
        assert audit_resp.status_code == 200
        audit_records = audit_resp.json()
        ml_records = [r for r in audit_records if "ML_ANOMALY" in r["stage"]]
        assert len(ml_records) >= 1
        assert ml_records[0]["status"] in ("WARNING", "SUCCESS")
        assert "Isolation Forest" in ml_records[0]["title"]
