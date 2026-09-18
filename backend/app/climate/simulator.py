"""Deterministic Climate Scenario Simulator and Pipeline Orchestrator.

Implements all primary hackathon demo scenarios and dynamic arbitrary inputs end-to-end:
  - Scenario 1: Successful Trigger (158 / 154 / 156 mm -> Consensus -> ₹25k Payout)
  - Scenario 2: Data Disagreement (158 / 156 / 17 mm -> Isolation Forest ML Anomaly -> Payout Blocked)
  - Scenario 3: Threshold Not Reached (120 / 118 / 121 mm -> No Trigger)
  - Scenario 4: Idempotency Retry (Same event resubmitted -> 1 Payout, Zero Duplicate)
  - Dynamic Live Pipeline: Arbitrary user-submitted multi-source telemetry evaluated live.
"""

from __future__ import annotations
import time
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

from app.climate.validation import ClimateValidationEngine
from app.climate.anomaly import ClimateAnomalyEngine, ML_MODEL_NAME, ML_MODEL_VERSION
from app.climate.consensus import ClimateConsensusEngine, ConsensusPolicy
from app.climate.policy_engine import ParametricPolicyEngine
from app.climate.settlement_engine import SimulatedSettlementEngine
from app.climate.audit_trail import ClimateAuditTrailService
from app.schemas.insurance import (
    DemoScenarioResponse,
    PipelineStageResult,
    ConsensusDecisionResponse,
    TriggerEvaluationResponse,
    SettlementResponse,
)


class Risk2ReliefSimulator:
    """End-to-End Climate Insurance Pipeline Orchestrator for Demos & Dynamic Inputs."""

    # Default Demo Policy
    DEFAULT_POLICY = {
        "id": "POL-2026-FLOOD-001",
        "policy_number": "R2R-POL-2026-001",
        "policyholder_name": "Rajesh Kumar (Smallholder Farmer)",
        "policyholder_type": "FARMER",
        "location_name": "Vellore Agro District, Zone 4",
        "covered_event": "FLASH_FLOOD",
        "metric": "rainfall_24h",
        "operator": ">=",
        "threshold": 150.0,
        "payout_amount": 25000.0,
        "currency": "INR",
        "active": True,
        "wallet_id": "SIM-WALLET-FARMER-001",
    }

    # Standard Demo Sources
    SOURCES = {
        "SAT": {
            "source_id": "SRC-SAT-001",
            "source_identifier": "SRC-SAT-001",
            "source_name": "Copernicus Sentinel-1 Radar Satellite",
            "provider_name": "Copernicus_EU",
            "source_type": "SATELLITE",
            "independence_group": "GROUP_COPERNICUS",
            "reliability_score": 0.98,
        },
        "GROUND": {
            "source_id": "SRC-GROUND-002",
            "source_identifier": "SRC-GROUND-002",
            "source_name": "IMD Automated Weather Station (Vellore)",
            "provider_name": "IMD_Ground_Network",
            "source_type": "GROUND_STATION",
            "independence_group": "GROUP_IMD",
            "reliability_score": 0.96,
        },
        "IOT": {
            "source_id": "SRC-IOT-003",
            "source_identifier": "SRC-IOT-003",
            "source_name": "AgriSense Community IoT Rain Gauge",
            "provider_name": "Community_IoT",
            "source_type": "IOT_SENSOR",
            "independence_group": "GROUP_COMMUNITY_IOT",
            "reliability_score": 0.94,
        },
    }

    @classmethod
    def run_pipeline(
        cls,
        scenario_id: str,
        scenario_name: str,
        description: str,
        event_identifier: str,
        raw_readings: List[Dict[str, Any]],
        policy_data: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> DemoScenarioResponse:
        """Execute the complete Risk2Relief pipeline across all 8 stages."""
        t_start = time.perf_counter()
        now = datetime.now(timezone.utc)
        corr_id = correlation_id or f"CORR-{uuid.uuid4().hex[:8].upper()}"
        active_policy = policy_data or cls.DEFAULT_POLICY
        pipeline_stages: List[PipelineStageResult] = []

        # --------------------------------------------------------------------
        # STAGE 1: DATA INGESTION
        # --------------------------------------------------------------------
        ingested_observations: List[Dict[str, Any]] = []
        for r in raw_readings:
            src_info = cls.SOURCES.get(r.get("source_key", "SAT"), cls.SOURCES["SAT"])
            obs = {
                "source_id": src_info["source_id"],
                "source_identifier": src_info["source_identifier"],
                "source_name": src_info["source_name"],
                "provider_name": src_info["provider_name"],
                "source_type": src_info["source_type"],
                "independence_group": src_info["independence_group"],
                "reliability_score": src_info["reliability_score"],
                "event_id": r.get("event_id", f"OBS-{uuid.uuid4().hex[:6].upper()}"),
                "event_identifier": event_identifier,
                "metric": "rainfall_24h",
                "value": float(r.get("value", 0.0)),
                "unit": "mm",
                "timestamp": r.get("timestamp", now),
            }
            ingested_observations.append(obs)

        ClimateAuditTrailService.record_stage(
            event_identifier=event_identifier,
            stage="DATA_RECEIVED",
            status="SUCCESS",
            title="Multi-Source Climate Telemetry Ingested",
            message=f"Received {len(ingested_observations)} multi-source observations for event '{event_identifier}'.",
            policy_id=active_policy.get("id"),
            correlation_id=corr_id,
            metadata={"readings": [f"{o['source_name']}: {o['value']} mm" for o in ingested_observations]},
        )
        pipeline_stages.append(PipelineStageResult(
            stage="DATA_RECEIVED",
            status="SUCCESS",
            title="Multi-Source Telemetry Ingestion",
            message=f"Received {len(ingested_observations)} observations across independent provider groups.",
            details={"sources": [f"{o['source_identifier']} ({o['value']} mm)" for o in ingested_observations]},
        ))

        # --------------------------------------------------------------------
        # STAGE 2: VALIDATION ENGINE
        # --------------------------------------------------------------------
        validated_obs: List[Dict[str, Any]] = []
        all_valid = True
        for o in ingested_observations:
            val = ClimateValidationEngine.validate_observation(
                source_id=o["source_id"],
                event_id=o["event_id"],
                metric=o["metric"],
                value=o["value"],
                unit=o["unit"],
                timestamp=o["timestamp"],
            )
            o["quality"] = val.quality.value
            o["validation_status"] = "PASSED" if val.is_valid else "REJECTED"
            o["validation_error"] = val.error_code
            o["validation_reason"] = val.reason
            if not val.is_valid:
                all_valid = False
            validated_obs.append(o)

        ClimateAuditTrailService.record_stage(
            event_identifier=event_identifier,
            stage="VALIDATION",
            status="SUCCESS" if all_valid else "WARNING",
            title="Deterministic Telemetry Validation",
            message=f"Validated {len(validated_obs)} observations against physical reality bounds and freshness.",
            policy_id=active_policy.get("id"),
            correlation_id=corr_id,
            metadata={"validation_results": [f"{o['source_identifier']}: {o['quality']}" for o in validated_obs]},
        )
        pipeline_stages.append(PipelineStageResult(
            stage="VALIDATION",
            status="SUCCESS" if all_valid else "WARNING",
            title="Deterministic Data Validation",
            message="Verified engineering units, timestamps, physical bounds, and duplicate suppression.",
            details={"qualities": {o["source_identifier"]: o["quality"] for o in validated_obs}},
        ))

        # --------------------------------------------------------------------
        # STAGE 3: ISOLATION FOREST ML ANOMALY DETECTION (ADVISORY)
        # --------------------------------------------------------------------
        obs_with_signals = ClimateAnomalyEngine.evaluate_peer_observations(validated_obs, target_metric="rainfall_24h")
        anomalies_found = [sig for _, sig in obs_with_signals if sig.is_anomaly]
        limited_signals = [sig for _, sig in obs_with_signals if sig.status in ("LIMITED", "FAILED")]

        for obs, sig in obs_with_signals:
            obs["anomaly_score"] = sig.anomaly_score
            obs["is_anomaly"] = sig.is_anomaly
            obs["anomaly_reason"] = sig.reason
            obs["raw_decision_score"] = sig.raw_decision_score
            obs["features_used"] = sig.features_used
            obs["model_name"] = sig.model_name
            obs["model_version"] = sig.model_version
            obs["ml_status"] = sig.status

        ml_stage_name = "ML_ANOMALY_CHECK_UNAVAILABLE" if limited_signals else "ML_ANOMALY_CHECK_COMPLETED"
        ml_audit_status = "WARNING" if anomalies_found else "SUCCESS"

        ClimateAuditTrailService.record_stage(
            event_identifier=event_identifier,
            stage=ml_stage_name,
            status=ml_audit_status,
            title="Isolation Forest ML Anomaly Detection (Advisory)",
            message=(
                f"Isolation Forest flagged {len(anomalies_found)} suspicious observation(s) out of {len(validated_obs)}."
                if anomalies_found else f"Isolation Forest verified all {len(validated_obs)} observations within normal reference cluster."
            ),
            policy_id=active_policy.get("id"),
            correlation_id=corr_id,
            metadata={
                "model_name": ML_MODEL_NAME,
                "model_version": ML_MODEL_VERSION,
                "flagged_count": len(anomalies_found),
                "total_observations": len(validated_obs),
                "observations": [
                    {
                        "source_identifier": o["source_identifier"],
                        "value": o["value"],
                        "is_anomaly": o["is_anomaly"],
                        "anomaly_score": o["anomaly_score"],
                        "raw_decision_score": o.get("raw_decision_score"),
                    }
                    for o in validated_obs
                ],
            },
        )
        pipeline_stages.append(PipelineStageResult(
            stage="ML_ANOMALY_CHECK",
            status="WARNING" if anomalies_found else "SUCCESS",
            title="Isolation Forest ML Anomaly Detection",
            message=f"Isolation Forest (scikit-learn) evaluated peer clusters (Flagged: {len(anomalies_found)} anomalies).",
            details={
                "model": f"{ML_MODEL_NAME}:{ML_MODEL_VERSION}",
                "anomalies": [sig.reason for sig in anomalies_found],
                "all_scores": {o["source_identifier"]: o["anomaly_score"] for o in validated_obs},
            },
        ))

        # --------------------------------------------------------------------
        # STAGE 4: SOURCE INDEPENDENCE & CONSENSUS
        # --------------------------------------------------------------------
        consensus_policy = ConsensusPolicy(min_independent_sources=2, max_agreement_tolerance_pct=12.0)
        consensus = ClimateConsensusEngine.evaluate_consensus(
            observations_with_signals=obs_with_signals,
            policy=consensus_policy,
            event_metric="rainfall_24h",
            expected_unit="mm",
        )

        ClimateAuditTrailService.record_stage(
            event_identifier=event_identifier,
            stage="CONSENSUS",
            status="SUCCESS" if consensus.status == "CONSENSUS_REACHED" else "FAILED",
            title="Source Independence & Multi-Source Consensus",
            message=consensus.explanation,
            policy_id=active_policy.get("id"),
            correlation_id=corr_id,
            metadata={
                "status": consensus.status,
                "consensus_value": consensus.consensus_value,
                "independent_groups": consensus.independent_groups_present,
                "agreement_score": consensus.agreement_score,
            },
        )
        pipeline_stages.append(PipelineStageResult(
            stage="CONSENSUS",
            status="SUCCESS" if consensus.status == "CONSENSUS_REACHED" else "FAILED",
            title="Multi-Source Consensus Evaluation",
            message=consensus.explanation,
            details={
                "status": consensus.status,
                "consensus_value": consensus.consensus_value,
                "agreement_score": f"{consensus.agreement_score * 100:.1f}%",
                "independent_sources": consensus.independent_source_count,
            },
        ))

        # --------------------------------------------------------------------
        # STAGE 5: DETERMINISTIC PARAMETRIC TRIGGER
        # --------------------------------------------------------------------
        trigger_res = ParametricPolicyEngine.evaluate_policy_trigger(
            policy=active_policy,
            consensus=consensus,
            event_identifier=event_identifier,
        )

        ClimateAuditTrailService.record_stage(
            event_identifier=event_identifier,
            stage="TRIGGER_EVALUATION",
            status="SUCCESS" if trigger_res.triggered else "NORMAL",
            title="Deterministic Parametric Trigger Evaluation",
            message=trigger_res.reason,
            policy_id=active_policy.get("id"),
            correlation_id=corr_id,
            metadata={
                "triggered": trigger_res.triggered,
                "observed_value": trigger_res.observed_value,
                "threshold": trigger_res.threshold,
                "payout_amount": trigger_res.payout_amount,
            },
        )
        pipeline_stages.append(PipelineStageResult(
            stage="TRIGGER_EVALUATION",
            status="SUCCESS" if trigger_res.triggered else "NORMAL",
            title="Parametric Policy Trigger",
            message=trigger_res.reason,
            details={
                "triggered": trigger_res.triggered,
                "policy_number": trigger_res.policy_number,
                "threshold": f"{trigger_res.threshold} mm",
                "observed": f"{trigger_res.observed_value} mm",
            },
        ))

        # --------------------------------------------------------------------
        # STAGE 6: SIMULATED INSTANT SETTLEMENT & IDEMPOTENCY
        # --------------------------------------------------------------------
        settlement_record = SimulatedSettlementEngine.execute_settlement(trigger_res)

        ClimateAuditTrailService.record_stage(
            event_identifier=event_identifier,
            stage="SETTLEMENT_COMPLETED" if settlement_record.status == "COMPLETED" else "SETTLEMENT_BLOCKED",
            status="SUCCESS" if settlement_record.status == "COMPLETED" else "FAILED",
            title="Simulated Instant Settlement Execution",
            message=(
                f"Simulated payout of {settlement_record.amount:,.2f} {settlement_record.currency} "
                f"dispatched to wallet '{settlement_record.wallet_id}'. Txn ID: {settlement_record.transaction_id}."
                if settlement_record.status == "COMPLETED" else settlement_record.failure_reason or "Settlement suppressed."
            ),
            policy_id=active_policy.get("id"),
            correlation_id=corr_id,
            metadata={
                "settlement_id": settlement_record.settlement_id,
                "transaction_id": settlement_record.transaction_id,
                "is_idempotent_retry": settlement_record.is_idempotent_retry,
            },
        )
        pipeline_stages.append(PipelineStageResult(
            stage="SETTLEMENT",
            status="SUCCESS" if settlement_record.status == "COMPLETED" else "BLOCKED",
            title="Simulated Instant Settlement",
            message=(
                f"Simulated payment of ₹{settlement_record.amount:,.2f} completed."
                if settlement_record.status == "COMPLETED" else "No settlement created."
            ),
            details={
                "settlement_id": settlement_record.settlement_id,
                "transaction_id": settlement_record.transaction_id,
                "wallet": settlement_record.wallet_id,
                "idempotent_retry": settlement_record.is_idempotent_retry,
            },
        ))

        # --------------------------------------------------------------------
        # STAGE 7: AUDIT TRAIL LOGGING & SUMMARY
        # --------------------------------------------------------------------
        duration_ms = (time.perf_counter() - t_start) * 1000.0
        all_audit = ClimateAuditTrailService.get_events_for_climate_event(event_identifier)

        consensus_dto = ConsensusDecisionResponse(
            event_identifier=consensus.event_identifier if hasattr(consensus, "event_identifier") else event_identifier,
            metric="rainfall_24h",
            eligible_source_count=consensus.eligible_source_count,
            independent_source_count=consensus.independent_source_count,
            consensus_value=consensus.consensus_value,
            consensus_method="WEIGHTED_MEDIAN",
            agreement_score=consensus.agreement_score,
            confidence=consensus.confidence,
            status=consensus.status,
            outliers=consensus.outliers,
            rejected_sources=consensus.rejected_sources,
            explanation=consensus.explanation,
        )

        trigger_dto = TriggerEvaluationResponse(
            policy_id=uuid.UUID(active_policy.get("id", "00000000-0000-0000-0000-000000000001")) if isinstance(active_policy.get("id"), str) and len(active_policy.get("id")) == 36 else uuid.uuid4(),
            policy_number=trigger_res.policy_number,
            event_identifier=event_identifier,
            observed_value=trigger_res.observed_value,
            threshold=trigger_res.threshold,
            operator=trigger_res.operator,
            triggered=trigger_res.triggered,
            difference=trigger_res.difference,
            reason=trigger_res.reason,
            payout_amount=trigger_res.payout_amount,
            currency=trigger_res.currency,
        )

        settlement_dto = SettlementResponse(
            settlement_id=settlement_record.settlement_id,
            policy_id=trigger_dto.policy_id,
            policy_number=trigger_res.policy_number,
            event_identifier=event_identifier,
            settlement_key=settlement_record.settlement_key,
            wallet_id=settlement_record.wallet_id,
            amount=settlement_record.amount,
            currency=settlement_record.currency,
            transaction_id=settlement_record.transaction_id,
            status=settlement_record.status,
            failure_reason=settlement_record.failure_reason,
            is_simulation=True,
            created_at=settlement_record.created_at,
            completed_at=settlement_record.completed_at,
        )

        return DemoScenarioResponse(
            scenario_name=scenario_name,
            scenario_id=scenario_id,
            description=description,
            event_identifier=event_identifier,
            observations=validated_obs,
            validation_status="VALID" if all_valid else "WARNING",
            anomaly_detection={
                "model_name": ML_MODEL_NAME,
                "model_version": ML_MODEL_VERSION,
                "algorithm": "Isolation Forest (scikit-learn)",
                "advisory_role": "Advisory Reliability Signal — Non-Authoritative",
                "status": "ANOMALY_DETECTED" if anomalies_found else "NO_ANOMALY",
                "flagged_count": len(anomalies_found),
                "is_clean": len(anomalies_found) == 0,
                "details": [sig.reason for sig in anomalies_found],
                "observations": [
                    {
                        "source_id": o["source_identifier"],
                        "value": o["value"],
                        "is_anomaly": o["is_anomaly"],
                        "anomaly_score": o["anomaly_score"],
                        "raw_decision_score": o.get("raw_decision_score"),
                    }
                    for o in validated_obs
                ],
            },
            source_independence={
                "independent_groups_count": consensus.independent_source_count,
                "groups": consensus.independent_groups_present,
                "quorum_satisfied": consensus.independent_source_count >= consensus_policy.min_independent_sources,
            },
            consensus=consensus_dto,
            trigger_evaluation=trigger_dto,
            settlement=settlement_dto,
            pipeline_stages=pipeline_stages,
            audit_trail=[
                {
                    "stage": e.stage,
                    "status": e.status,
                    "title": e.title,
                    "message": e.message,
                    "timestamp": e.timestamp.isoformat(),
                }
                for e in all_audit
            ],
            execution_duration_ms=round(duration_ms, 2),
            is_simulation=True,
            summary_message=(
                f"Pipeline completed in {duration_ms:.2f}ms: "
                + (f"Instant simulated payout of ₹{settlement_record.amount:,.2f} completed." if settlement_record.status == "COMPLETED" else "Payout suppressed safely.")
            ),
        )

    # ------------------------------------------------------------------------
    # DYNAMIC LIVE PIPELINE RUNNER
    # ------------------------------------------------------------------------

    @classmethod
    def run_dynamic_pipeline(
        cls,
        sat_value: float,
        ground_value: float,
        iot_value: float,
        policy_threshold: float = 150.0,
        payout_amount: float = 25000.0,
        event_identifier: Optional[str] = None,
    ) -> DemoScenarioResponse:
        """Run arbitrary multi-source telemetry dynamically through the entire 8-stage pipeline."""
        evt_id = event_identifier or f"EVT-DYN-{uuid.uuid4().hex[:6].upper()}"
        readings = [
            {"source_key": "SAT", "value": float(sat_value), "event_id": f"OBS-DYN-SAT-{uuid.uuid4().hex[:4]}"},
            {"source_key": "GROUND", "value": float(ground_value), "event_id": f"OBS-DYN-GRD-{uuid.uuid4().hex[:4]}"},
            {"source_key": "IOT", "value": float(iot_value), "event_id": f"OBS-DYN-IOT-{uuid.uuid4().hex[:4]}"},
        ]
        custom_policy = {
            **cls.DEFAULT_POLICY,
            "threshold": float(policy_threshold),
            "payout_amount": float(payout_amount),
        }
        return cls.run_pipeline(
            scenario_id="DYNAMIC_LIVE_EVALUATION",
            scenario_name=f"Dynamic Telemetry ({sat_value:.1f} / {ground_value:.1f} / {iot_value:.1f} mm)",
            description=f"Arbitrary multi-source climate telemetry evaluated live by Isolation Forest, Consensus, & Parametric Trigger.",
            event_identifier=evt_id,
            raw_readings=readings,
            policy_data=custom_policy,
        )

    # ------------------------------------------------------------------------
    # SCENARIO RUNNERS
    # ------------------------------------------------------------------------

    @classmethod
    def run_scenario_1_success(cls) -> DemoScenarioResponse:
        """Scenario 1: Successful Trigger (158 / 154 / 156 mm -> Consensus 156mm -> ₹25,000 Payout)."""
        readings = [
            {"source_key": "SAT", "value": 158.0, "event_id": f"OBS-SC1-SAT-{uuid.uuid4().hex[:4]}"},
            {"source_key": "GROUND", "value": 154.0, "event_id": f"OBS-SC1-GRD-{uuid.uuid4().hex[:4]}"},
            {"source_key": "IOT", "value": 156.0, "event_id": f"OBS-SC1-IOT-{uuid.uuid4().hex[:4]}"},
        ]
        return cls.run_pipeline(
            scenario_id="SCENARIO_1_SUCCESS",
            scenario_name="Corroborated Extreme Rainfall -> Instant Settlement",
            description="Satellite, Ground Station, and Community IoT sensors all corroborate 24h rainfall > 150mm.",
            event_identifier="EVT-2026-FLOOD-001",
            raw_readings=readings,
        )

    @classmethod
    def run_scenario_2_disagreement(cls) -> DemoScenarioResponse:
        """Scenario 2: Data Disagreement (158 / 156 / 17 mm -> Isolation Forest ML Anomaly -> Payout Blocked)."""
        readings = [
            {"source_key": "SAT", "value": 158.0, "event_id": f"OBS-SC2-SAT-{uuid.uuid4().hex[:4]}"},
            {"source_key": "GROUND", "value": 156.0, "event_id": f"OBS-SC2-GRD-{uuid.uuid4().hex[:4]}"},
            {"source_key": "IOT", "value": 17.0, "event_id": f"OBS-SC2-IOT-{uuid.uuid4().hex[:4]}"},  # Outlier reading
        ]
        return cls.run_pipeline(
            scenario_id="SCENARIO_2_DISAGREEMENT",
            scenario_name="Sensor Disagreement / Anomaly Detected",
            description="Community IoT sensor reports 17mm while Satellite and Ground report ~157mm; Isolation Forest ML flags outlier and consensus suppresses payout.",
            event_identifier="EVT-2026-DISPUTE-002",
            raw_readings=readings,
        )

    @classmethod
    def run_scenario_3_no_trigger(cls) -> DemoScenarioResponse:
        """Scenario 3: Sub-Threshold Rainfall (120 / 118 / 121 mm -> Consensus Reached -> No Trigger)."""
        readings = [
            {"source_key": "SAT", "value": 120.0, "event_id": f"OBS-SC3-SAT-{uuid.uuid4().hex[:4]}"},
            {"source_key": "GROUND", "value": 118.0, "event_id": f"OBS-SC3-GRD-{uuid.uuid4().hex[:4]}"},
            {"source_key": "IOT", "value": 121.0, "event_id": f"OBS-SC3-IOT-{uuid.uuid4().hex[:4]}"},
        ]
        return cls.run_pipeline(
            scenario_id="SCENARIO_3_NO_TRIGGER",
            scenario_name="Normal Monsoon Rainfall (Sub-Threshold)",
            description="Multi-source consensus reaches 120mm nominal rainfall. Trigger threshold (150mm) is not breached; zero payout dispatched.",
            event_identifier="EVT-2026-NOMINAL-003",
            raw_readings=readings,
        )

    @classmethod
    def run_scenario_4_idempotency(cls) -> DemoScenarioResponse:
        """Scenario 4: Idempotent Retry Test (Re-submitting Scenario 1 event -> Duplicate suppressed, original payout preserved)."""
        readings = [
            {"source_key": "SAT", "value": 158.0, "event_id": f"OBS-SC4-SAT-RETRY"},
            {"source_key": "GROUND", "value": 154.0, "event_id": f"OBS-SC4-GRD-RETRY"},
            {"source_key": "IOT", "value": 156.0, "event_id": f"OBS-SC4-IOT-RETRY"},
        ]
        return cls.run_pipeline(
            scenario_id="SCENARIO_4_IDEMPOTENCY",
            scenario_name="Idempotent Duplicate Retry Protection",
            description="Resubmits identical event. Idempotency guard prevents duplicate financial payout and returns existing completed transaction.",
            event_identifier="EVT-2026-FLOOD-001",  # Same event ID as Scenario 1
            raw_readings=readings,
        )
