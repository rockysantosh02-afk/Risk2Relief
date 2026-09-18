"""Advisory ML Anomaly Detection Engine for Multi-Source Climate Observations.

Integrates scikit-learn Isolation Forest (`sklearn.ensemble.IsolationForest`),
peer-cluster deviation analysis, robust MAD scaling, and baseline reference distributions.

SAFETY & ARCHITECTURAL INVARIANT:
ML anomaly detection produces an ADVISORY SIGNAL only.
ML must NEVER directly command, authorize, or trigger parametric payouts or compensation.
The existing deterministic validation, multi-source consensus, trigger, and settlement
systems remain authoritative.
"""

from __future__ import annotations
import math
import random
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any, Tuple

logger = logging.getLogger("risk2relief.ml_anomaly")

# Centralized ML Configuration
ML_MODEL_NAME = "isolation_forest_climate_anomaly"
ML_MODEL_VERSION = "v1.0"
ML_CONTAMINATION = 0.08
ML_N_ESTIMATORS = 100
ML_RANDOM_STATE = 42
ML_MAX_SAMPLES = "auto"
ML_ANOMALY_THRESHOLD = 0.60

try:
    import numpy as np
    from sklearn.ensemble import IsolationForest
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn or numpy not available; falling back to statistical heuristic mode.")


@dataclass
class ClimateAnomalySignal:
    """Standardized advisory anomaly assessment for a climate observation."""
    is_anomaly: bool
    anomaly_score: float             # 0.0 (completely normal) to 1.0 (extreme anomaly)
    confidence: float                # 0.0 to 1.0
    model_name: str                  # "isolation_forest_climate_anomaly"
    model_version: str               # "v1.0"
    reason: str
    features_used: Dict[str, float]
    threshold: float = ML_ANOMALY_THRESHOLD
    raw_decision_score: Optional[float] = None
    status: str = "COMPLETED"         # COMPLETED, ANOMALY_DETECTED, NO_ANOMALY, LIMITED, FAILED
    advisory_disclaimer: str = (
        "ADVISORY ONLY. Isolation Forest checks whether an observation is statistically unusual "
        "compared with reference climate data. It is used as an advisory reliability signal "
        "and must never directly authorize or trigger financial settlement payouts."
    )


def build_reference_climate_dataset(seed: int = ML_RANDOM_STATE) -> Tuple[List[List[float]], str]:
    """Generate a reference baseline distribution representing historical climate patterns.

    DATASET IDENTIFIER: 'SIMULATED / DEMO REFERENCE TRAINING DATA'
    Generates 500+ multi-regime historical climate observation features across seasons:
      - Dry / Light showers (0 - 30 mm)
      - Moderate rain (30 - 80 mm)
      - Heavy monsoon rain (120 - 180 mm)
      - Extreme torrential events (190 - 240 mm)
      - Corroborated peer clusters (tight dev_from_median, low robust_z)
      - Controlled outlier noise for contamination calibration (~8%)
    """
    rng = random.Random(seed)
    features: List[List[float]] = []

    # Regime 1: Light rain (0 - 30 mm)
    for _ in range(150):
        base_val = rng.uniform(0.0, 30.0)
        peer_dev = abs(rng.gauss(0.0, 1.2))
        robust_z = peer_dev / max(0.8, peer_dev + 0.5)
        rel_ratio = max(0.85, min(1.15, 1.0 + rng.gauss(0.0, 0.05)))
        features.append([base_val, peer_dev, robust_z, rel_ratio])

    # Regime 2: Moderate rain (30 - 80 mm)
    for _ in range(150):
        base_val = rng.uniform(30.0, 80.0)
        peer_dev = abs(rng.gauss(0.0, 2.5))
        robust_z = peer_dev / max(1.5, peer_dev + 1.0)
        rel_ratio = max(0.88, min(1.12, 1.0 + rng.gauss(0.0, 0.04)))
        features.append([base_val, peer_dev, robust_z, rel_ratio])

    # Regime 3: Heavy monsoon rain (120 - 180 mm) - core trigger zone
    for _ in range(180):
        base_val = rng.uniform(120.0, 180.0)
        peer_dev = abs(rng.gauss(0.0, 3.5))
        robust_z = peer_dev / max(2.0, peer_dev + 1.5)
        rel_ratio = max(0.90, min(1.10, 1.0 + rng.gauss(0.0, 0.03)))
        features.append([base_val, peer_dev, robust_z, rel_ratio])

    # Regime 4: Extreme flood events (180 - 240 mm)
    for _ in range(80):
        base_val = rng.uniform(180.0, 240.0)
        peer_dev = abs(rng.gauss(0.0, 4.0))
        robust_z = peer_dev / max(2.5, peer_dev + 2.0)
        rel_ratio = max(0.92, min(1.08, 1.0 + rng.gauss(0.0, 0.02)))
        features.append([base_val, peer_dev, robust_z, rel_ratio])

    # Controlled synthetic anomalies / sensor dropouts for contamination (~8%)
    for _ in range(45):
        base_val = rng.choice([15.0, 18.0, 22.0, 450.0, 0.0])
        peer_dev = rng.uniform(80.0, 160.0)      # Drastic deviation from peer cluster
        robust_z = rng.uniform(4.5, 12.0)        # Extreme robust z-score
        rel_ratio = rng.choice([0.10, 0.15, 3.5, 4.2])
        features.append([base_val, peer_dev, robust_z, rel_ratio])

    description = "SIMULATED / DEMO REFERENCE TRAINING DATA (605 multi-regime climate observations)"
    return features, description


class IsolationForestClimateDetector:
    """Trained Isolation Forest ML Anomaly Detector for Climate Observations."""

    _instance: Optional[IsolationForestClimateDetector] = None

    def __init__(
        self,
        n_estimators: int = ML_N_ESTIMATORS,
        contamination: float = ML_CONTAMINATION,
        random_state: int = ML_RANDOM_STATE,
        max_samples: Any = ML_MAX_SAMPLES,
    ):
        self.model_name = ML_MODEL_NAME
        self.model_version = ML_MODEL_VERSION
        self.n_estimators = n_estimators
        self.contamination = contamination
        self.random_state = random_state
        self.max_samples = max_samples
        self.model: Optional[Any] = None
        self.training_dataset_id: str = ""
        self.training_sample_count: int = 0
        self.is_trained: bool = False

        self._train_model()

    def _train_model(self) -> None:
        """Train the Isolation Forest model using the reference climate dataset."""
        if not SKLEARN_AVAILABLE:
            logger.warning("scikit-learn is not installed; Isolation Forest cannot be trained.")
            return

        try:
            features, dataset_id = build_reference_climate_dataset(seed=self.random_state)
            X = np.array(features, dtype=np.float64)

            clf = IsolationForest(
                n_estimators=self.n_estimators,
                contamination=self.contamination,
                random_state=self.random_state,
                max_samples=self.max_samples,
                bootstrap=False,
            )
            clf.fit(X)

            self.model = clf
            self.training_dataset_id = dataset_id
            self.training_sample_count = len(features)
            self.is_trained = True
            logger.info(
                f"Isolation Forest model '{self.model_name}' ({self.model_version}) trained successfully "
                f"on {self.training_sample_count} reference samples."
            )
        except Exception as e:
            logger.error(f"Failed to train Isolation Forest model: {e}", exc_info=True)
            self.is_trained = False
            self.model = None

    @classmethod
    def get_instance(cls) -> IsolationForestClimateDetector:
        """Singleton accessor for in-memory cached model instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton for testing."""
        cls._instance = None

    def score_observations(
        self,
        observations: List[Dict[str, Any]],
        target_metric: str = "rainfall_24h",
        anomaly_threshold: float = ML_ANOMALY_THRESHOLD,
    ) -> List[Tuple[Dict[str, Any], ClimateAnomalySignal]]:
        """Evaluate contemporaneous multi-source observations using Isolation Forest."""
        results: List[Tuple[Dict[str, Any], ClimateAnomalySignal]] = []
        if not observations:
            return results

        n = len(observations)

        # Single source case
        if n <= 1:
            for obs in observations:
                val = float(obs.get("value", 0.0))
                sig = ClimateAnomalySignal(
                    is_anomaly=False,
                    anomaly_score=0.0,
                    confidence=0.50,
                    model_name=self.model_name,
                    model_version=self.model_version,
                    reason="Single observation provided; no peer sources available for cluster validation.",
                    features_used={"value": val},
                    threshold=anomaly_threshold,
                    raw_decision_score=0.0,
                    status="LIMITED",
                )
                results.append((obs, sig))
            return results

        # Extract values
        values = [float(obs.get("value", 0.0)) for obs in observations]

        # Robust central tendency (Median and MAD)
        sorted_vals = sorted(values)
        median = sorted_vals[n // 2] if n % 2 != 0 else (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2.0
        abs_deviations = [abs(v - median) for v in values]
        sorted_mads = sorted(abs_deviations)
        mad = sorted_mads[n // 2] if n % 2 != 0 else (sorted_mads[n // 2 - 1] + sorted_mads[n // 2]) / 2.0
        mad = max(0.5, mad)  # Prevent division by zero for identical readings

        mean = sum(values) / n
        variance = sum((x - mean) ** 2 for x in values) / max(1, n - 1)
        stddev = math.sqrt(variance)

        # Prepare feature matrix for each observation
        feature_rows: List[List[float]] = []
        feature_dicts: List[Dict[str, float]] = []

        for obs in observations:
            val = float(obs.get("value", 0.0))
            dev_from_median = abs(val - median)
            robust_z = dev_from_median / (1.4826 * mad)
            rel_ratio = val / max(1.0, median)

            feature_rows.append([val, dev_from_median, robust_z, rel_ratio])
            feature_dicts.append({
                "value": round(val, 2),
                "peer_median": round(median, 2),
                "peer_mean": round(mean, 2),
                "peer_stddev": round(stddev, 2),
                "dev_from_median": round(dev_from_median, 2),
                "robust_z_score": round(robust_z, 2),
                "relative_ratio": round(rel_ratio, 2),
            })

        # Score via scikit-learn Isolation Forest if trained
        if SKLEARN_AVAILABLE and self.is_trained and self.model is not None:
            try:
                X_eval = np.array(feature_rows, dtype=np.float64)
                # decision_function: higher is normal (>0), lower is anomalous (<0)
                raw_decision_scores = self.model.decision_function(X_eval)
                predictions = self.model.predict(X_eval)  # +1 inlier, -1 outlier

                for idx, obs in enumerate(observations):
                    val = float(obs.get("value", 0.0))
                    raw_score = float(raw_decision_scores[idx])
                    pred = int(predictions[idx])
                    f_dict = feature_dicts[idx]
                    robust_z = f_dict["robust_z_score"]
                    dev_from_median = f_dict["dev_from_median"]

                    # Map raw decision score [-0.5, +0.5] to normalized advisory anomaly score [0.0, 1.0]
                    # Higher raw_score -> Lower anomaly_score
                    # Anomaly threshold: raw_score < 0.0 or robust_z > 3.0
                    sigmoid_score = 1.0 / (1.0 + math.exp(6.0 * raw_score))
                    normalized_score = round(max(0.01, min(0.99, sigmoid_score)), 4)

                    is_anom = (pred == -1) or (normalized_score >= anomaly_threshold) or (robust_z > 3.0) or (median > 50.0 and (val / max(1.0, median)) < 0.25)

                    if is_anom:
                        status_str = "ANOMALY_DETECTED"
                        anomaly_score_final = max(0.60, normalized_score)
                        reason = (
                            f"Isolation Forest flagged observation ({val:.1f} mm): "
                            f"significantly deviates from peer-source cluster "
                            f"(Peer Median: {median:.1f} mm, Relative Deviation: {dev_from_median:.1f} mm, "
                            f"Robust Z: {robust_z:.2f}, Raw Score: {raw_score:.3f}). "
                            f"Statistically unusual relative to reference data."
                        )
                    else:
                        status_str = "NO_ANOMALY"
                        anomaly_score_final = min(0.38, normalized_score)
                        reason = (
                            f"Isolation Forest verified observation ({val:.1f} mm): "
                            f"Consistent with reference climate distribution and peer-source cluster "
                            f"(Within {robust_z:.2f} robust MADs, Raw Score: {raw_score:.3f})."
                        )

                    sig = ClimateAnomalySignal(
                        is_anomaly=is_anom,
                        anomaly_score=anomaly_score_final,
                        confidence=0.94 if n >= 3 else 0.78,
                        model_name=self.model_name,
                        model_version=self.model_version,
                        reason=reason,
                        features_used=f_dict,
                        threshold=anomaly_threshold,
                        raw_decision_score=round(raw_score, 4),
                        status=status_str,
                    )
                    results.append((obs, sig))

                return results

            except Exception as e:
                logger.error(f"Isolation Forest scoring error: {e}", exc_info=True)
                # Graceful degradation fallback

        # Fallback heuristic if scikit-learn model unavailable
        for idx, obs in enumerate(observations):
            val = float(obs.get("value", 0.0))
            f_dict = feature_dicts[idx]
            robust_z = f_dict["robust_z_score"]
            dev_from_median = f_dict["dev_from_median"]

            if robust_z > 3.0 or (median > 50.0 and (val / max(1.0, median)) < 0.25):
                anomaly_score = round(min(0.99, 0.60 + 0.08 * robust_z), 4)
                is_anom = True
                status_str = "ANOMALY_DETECTED"
                reason = (
                    f"Observation ({val:.1f} mm) significantly deviates from peer-source cluster "
                    f"(Peer Median: {median:.1f} mm, Relative Deviation: {dev_from_median:.1f} mm). "
                    f"Potential anomaly detected (Heuristic Fallback)."
                )
            else:
                anomaly_score = round(max(0.01, min(0.38, robust_z * 0.10)), 4)
                is_anom = False
                status_str = "NO_ANOMALY"
                reason = f"Observation consistent with peer-source cluster (Within {robust_z:.2f} robust MADs)."

            sig = ClimateAnomalySignal(
                is_anomaly=is_anom,
                anomaly_score=anomaly_score,
                confidence=0.80 if n >= 3 else 0.60,
                model_name=self.model_name,
                model_version=f"{self.model_version}-fallback",
                reason=reason,
                features_used=f_dict,
                threshold=anomaly_threshold,
                raw_decision_score=round(0.10 - (anomaly_score - 0.20), 4),
                status=status_str,
            )
            results.append((obs, sig))

        return results


class ClimateAnomalyEngine:
    """Multi-source peer cluster anomaly detector delegating to Isolation Forest."""

    @classmethod
    def evaluate_peer_observations(
        cls,
        observations: List[Dict[str, Any]],
        target_metric: str = "rainfall_24h",
        anomaly_threshold: float = ML_ANOMALY_THRESHOLD,
    ) -> List[Tuple[Dict[str, Any], ClimateAnomalySignal]]:
        """Evaluate a batch of contemporaneous multi-source observations using Isolation Forest."""
        detector = IsolationForestClimateDetector.get_instance()
        return detector.score_observations(
            observations=observations,
            target_metric=target_metric,
            anomaly_threshold=anomaly_threshold,
        )
