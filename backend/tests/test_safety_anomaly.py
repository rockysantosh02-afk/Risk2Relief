"""Unit tests for Advisory Anomaly Detection Engine & Benchmark Evaluator."""

import pytest
import random
from app.safety.anomaly import (
    StatisticalZScoreDetector,
    IsolationForestDetector,
    AnomalyBenchmarkEvaluator,
    AnomalyBenchmarkMetrics,
)


def test_statistical_zscore_detector_normal_and_spike():
    """Z-score detector should establish a baseline and flag extreme spikes as anomalies."""
    detector = StatisticalZScoreDetector(window_size=20, z_threshold=3.0)

    # Feed steady baseline data around 10.0 with small noise
    rng = random.Random(42)
    for _ in range(15):
        val = 10.0 + rng.uniform(-0.1, 0.1)
        res = detector.detect(val, feature_name="strain_microstrain")
        assert not res.is_anomaly
        assert "ADVISORY ONLY" in res.advisory_disclaimer

    # Feed an extreme outlier spike (z > 3.0)
    spike_val = 25.0
    spike_res = detector.detect(spike_val, feature_name="strain_microstrain")
    assert spike_res.is_anomaly
    assert spike_res.anomaly_score > 0.50
    assert spike_res.features["z_score"] >= 3.0
    assert spike_res.method == "Z_SCORE"


def test_isolation_forest_detector_fit_and_detect():
    """Isolation Forest should train deterministically and isolate synthetic outliers."""
    detector = IsolationForestDetector(n_trees=25, subsample_size=32, seed=123)

    # Generate synthetic 3D normal baseline vectors clustered around (100.0, 50.0, 0.5)
    rng = random.Random(123)
    train_data = [
        [
            100.0 + rng.uniform(-2.0, 2.0),
            50.0 + rng.uniform(-1.0, 1.0),
            0.5 + rng.uniform(-0.05, 0.05),
        ]
        for _ in range(80)
    ]
    feature_names = ["temperature", "humidity", "vibration"]
    detector.fit(train_data, feature_names=feature_names)

    # Test an in-distribution nominal point
    normal_obs = {"temperature": 100.2, "humidity": 50.1, "vibration": 0.51}
    normal_result = detector.detect(normal_obs, threshold=0.60)
    assert not normal_result.is_anomaly
    assert normal_result.anomaly_score < 0.60
    assert "ADVISORY ONLY" in normal_result.advisory_disclaimer

    # Test an extreme outlier point
    outlier_obs = {"temperature": 350.0, "humidity": 5.0, "vibration": 15.0}
    outlier_result = detector.detect(outlier_obs, threshold=0.60)
    assert outlier_result.is_anomaly
    assert outlier_result.anomaly_score >= 0.60
    assert outlier_result.method == "ISOLATION_FOREST"


def test_isolation_forest_determinism():
    """Two Isolation Forest instances with the same seed and data must produce identical scores."""
    train_data = [[10.0, 20.0], [10.2, 19.8], [9.9, 20.1], [10.1, 20.0]] * 10
    test_vec = {"f0": 10.05, "f1": 19.95}

    model1 = IsolationForestDetector(n_trees=20, seed=999)
    model1.fit(train_data)
    res1 = model1.detect(test_vec)

    model2 = IsolationForestDetector(n_trees=20, seed=999)
    model2.fit(train_data)
    res2 = model2.detect(test_vec)

    assert res1.anomaly_score == res2.anomaly_score
    assert res1.is_anomaly == res2.is_anomaly


def test_anomaly_benchmark_evaluator():
    """Benchmark evaluator should correctly compute Precision, Recall, FPR, FNR, and F1."""
    # 10 samples: 4 true anomalies (indices 0, 1, 2, 3), 6 normal (indices 4..9)
    ground_truth = [1, 1, 1, 1, 0, 0, 0, 0, 0, 0]
    # Predictions:
    # index 0: TP, index 1: TP, index 2: TP, index 3: FN (predicted 0)
    # index 4: FP (predicted 1), indices 5..9: TN (predicted 0)
    predictions  = [1, 1, 1, 0, 1, 0, 0, 0, 0, 0]

    metrics: AnomalyBenchmarkMetrics = AnomalyBenchmarkEvaluator.evaluate(
        ground_truth=ground_truth,
        predictions=predictions,
    )

    assert metrics.total_samples == 10
    assert metrics.true_positives == 3
    assert metrics.false_positives == 1
    assert metrics.true_negatives == 5
    assert metrics.false_negatives == 1

    # Precision = 3 / (3 + 1) = 0.75
    assert metrics.precision == 0.75
    # Recall = 3 / (3 + 1) = 0.75
    assert metrics.recall == 0.75
    # FPR = FP / (FP + TN) = 1 / (1 + 5) = 1/6 ~= 0.1667
    assert metrics.false_positive_rate == pytest.approx(0.1667, abs=1e-3)
    # FNR = FN / (FN + TP) = 1 / (1 + 3) = 0.25
    assert metrics.false_negative_rate == 0.25
    # F1 = 2 * (0.75 * 0.75) / (0.75 + 0.75) = 0.75
    assert metrics.f1_score == 0.75
