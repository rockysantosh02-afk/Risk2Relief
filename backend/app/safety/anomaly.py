"""Advisory Anomaly Detection Engine (Statistical & Machine Learning).

SYSTEM SAFETY BOUNDARY:
All anomaly detection outputs in this module are ADVISORY ONLY.
They provide predictive observability for digital-twin calibration and operator review.
They must NEVER directly command, authorize, or trigger physical actuators or hardware actions.
"""

from __future__ import annotations
import math
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any, Tuple


@dataclass
class AnomalyDetectionResult:
    """Standardized advisory anomaly detection output."""
    is_anomaly: bool
    anomaly_score: float             # 0.0 (strictly normal) to 1.0 (extreme anomaly)
    confidence: float                # 0.0 to 1.0
    method: str                      # "Z_SCORE" or "ISOLATION_FOREST"
    model_version: str
    features: Dict[str, float]
    threshold: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    advisory_disclaimer: str = (
        "ADVISORY ONLY. Model inference provides observational intelligence for the digital twin "
        "and must NEVER directly authorize or command physical hardware actions."
    )


class StatisticalZScoreDetector:
    """Rolling statistical anomaly detector using dynamic z-score thresholding."""

    def __init__(self, window_size: int = 30, z_threshold: float = 3.0):
        self.window_size = max(5, window_size)
        self.z_threshold = z_threshold
        self.history: List[float] = []
        self.model_version = "stat-zscore-v1.2"

    def update(self, value: float) -> None:
        """Add observation to rolling buffer."""
        self.history.append(value)
        if len(self.history) > self.window_size:
            self.history.pop(0)

    def detect(self, value: float, feature_name: str = "metric_value") -> AnomalyDetectionResult:
        """Compute rolling mean, standard deviation, and z-score."""
        n = len(self.history)
        if n < 5:
            # Insufficient history for robust statistical baseline
            self.update(value)
            return AnomalyDetectionResult(
                is_anomaly=False,
                anomaly_score=0.0,
                confidence=0.20,
                method="Z_SCORE",
                model_version=self.model_version,
                features={feature_name: value},
                threshold=self.z_threshold,
            )

        mean = sum(self.history) / n
        variance = sum((x - mean) ** 2 for x in self.history) / (n - 1)
        stddev = math.sqrt(variance)

        if stddev < 1e-6:
            # Constant signal; divergence is extreme
            z = 0.0 if abs(value - mean) < 1e-6 else 10.0
        else:
            z = abs(value - mean) / stddev

        is_anom = z >= self.z_threshold
        # Normalize score into [0.0, 1.0] sigmoid
        score = round(1.0 / (1.0 + math.exp(-0.8 * (z - self.z_threshold))), 4)
        confidence = round(min(1.0, 0.5 + (n / (2.0 * self.window_size))), 2)

        self.update(value)

        return AnomalyDetectionResult(
            is_anomaly=is_anom,
            anomaly_score=score,
            confidence=confidence,
            method="Z_SCORE",
            model_version=self.model_version,
            features={
                feature_name: value,
                "rolling_mean": round(mean, 4),
                "rolling_stddev": round(stddev, 4),
                "z_score": round(z, 4),
            },
            threshold=self.z_threshold,
        )


class _IsolationTreeNode:
    """Node in an isolation tree."""
    def __init__(
        self,
        left: Optional[_IsolationTreeNode] = None,
        right: Optional[_IsolationTreeNode] = None,
        split_feature: Optional[int] = None,
        split_value: Optional[float] = None,
        size: int = 0,
    ):
        self.left = left
        self.right = right
        self.split_feature = split_feature
        self.split_value = split_value
        self.size = size

    @property
    def is_leaf(self) -> bool:
        return self.left is None and self.right is None


class IsolationForestDetector:
    """Pure Python deterministic Isolation Forest for multidimensional telemetry anomalies."""

    def __init__(
        self,
        n_trees: int = 30,
        subsample_size: int = 64,
        contamination: float = 0.10,
        seed: int = 42,
    ):
        self.n_trees = n_trees
        self.subsample_size = subsample_size
        self.contamination = contamination
        self.seed = seed
        self._rng = random.Random(seed)
        self.trees: List[_IsolationTreeNode] = []
        self.feature_names: List[str] = []
        self.model_version = "iforest-pure-py-v2.0"
        self.trained_n_samples = 0

    @staticmethod
    def _c(n: int) -> float:
        """Average path length of unsuccessful search in Binary Search Tree."""
        if n <= 1:
            return 0.0
        if n == 2:
            return 1.0
        euler_mascheroni = 0.5772156649
        return 2.0 * (math.log(n - 1) + euler_mascheroni) - (2.0 * (n - 1) / n)

    def _build_tree(self, X: List[List[float]], current_depth: int, max_depth: int) -> _IsolationTreeNode:
        n_samples = len(X)
        if n_samples <= 1 or current_depth >= max_depth:
            return _IsolationTreeNode(size=n_samples)

        n_features = len(X[0])
        feat_idx = self._rng.randint(0, n_features - 1)
        feat_vals = [row[feat_idx] for row in X]
        min_v = min(feat_vals)
        max_v = max(feat_vals)

        if min_v == max_v:
            return _IsolationTreeNode(size=n_samples)

        split_v = self._rng.uniform(min_v, max_v)
        left_X = [row for row in X if row[feat_idx] < split_v]
        right_X = [row for row in X if row[feat_idx] >= split_v]

        left_node = self._build_tree(left_X, current_depth + 1, max_depth)
        right_node = self._build_tree(right_X, current_depth + 1, max_depth)

        return _IsolationTreeNode(
            left=left_node,
            right=right_node,
            split_feature=feat_idx,
            split_value=split_v,
            size=n_samples,
        )

    def fit(self, X: List[List[float]], feature_names: Optional[List[str]] = None) -> None:
        """Fit isolation forest on normal baseline calibration vectors."""
        if not X:
            return
        self.trained_n_samples = len(X)
        self.feature_names = feature_names or [f"f{i}" for i in range(len(X[0]))]
        self.trees = []
        max_depth = int(math.ceil(math.log2(max(2, self.subsample_size))))

        for _ in range(self.n_trees):
            if len(X) > self.subsample_size:
                sample_indices = self._rng.sample(range(len(X)), self.subsample_size)
                sample = [X[i] for i in sample_indices]
            else:
                sample = list(X)

            tree = self._build_tree(sample, 0, max_depth)
            self.trees.append(tree)

    def _path_length(self, x: List[float], node: _IsolationTreeNode, current_depth: int) -> float:
        if node.is_leaf:
            return current_depth + self._c(node.size)
        if x[node.split_feature] < node.split_value:
            return self._path_length(x, node.left, current_depth + 1)
        return self._path_length(x, node.right, current_depth + 1)

    def score(self, x: List[float]) -> float:
        """Compute anomaly score s in [0.0, 1.0]. Score > 0.60 indicates anomaly."""
        if not self.trees:
            return 0.0
        avg_path = sum(self._path_length(x, t, 0) for t in self.trees) / len(self.trees)
        c_val = self._c(self.subsample_size)
        if c_val <= 0:
            return 0.0
        exponent = -1.0 * (avg_path / c_val)
        return round(math.pow(2.0, exponent), 4)

    def detect(self, features: Dict[str, float], threshold: float = 0.60) -> AnomalyDetectionResult:
        """Evaluate observation vector and return standardized result."""
        vec = [features.get(name, 0.0) for name in self.feature_names]
        anomaly_score = self.score(vec)
        is_anom = anomaly_score >= threshold

        return AnomalyDetectionResult(
            is_anomaly=is_anom,
            anomaly_score=anomaly_score,
            confidence=0.85,
            method="ISOLATION_FOREST",
            model_version=self.model_version,
            features=features,
            threshold=threshold,
        )


@dataclass
class AnomalyBenchmarkMetrics:
    """Benchmark evaluation metrics for anomaly detection algorithms."""
    total_samples: int
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int
    precision: float
    recall: float
    false_positive_rate: float
    false_negative_rate: float
    f1_score: float


class AnomalyBenchmarkEvaluator:
    """Calculates precision, recall, false-positive rate, and false-negative rate."""

    @staticmethod
    def evaluate(
        ground_truth: List[int],
        predictions: List[int],
    ) -> AnomalyBenchmarkMetrics:
        """Evaluate binary classification outputs against ground truth (1 = anomaly, 0 = normal)."""
        tp = 0
        fp = 0
        tn = 0
        fn = 0

        for true_label, pred_label in zip(ground_truth, predictions):
            if true_label == 1 and pred_label == 1:
                tp += 1
            elif true_label == 0 and pred_label == 1:
                fp += 1
            elif true_label == 0 and pred_label == 0:
                tn += 1
            elif true_label == 1 and pred_label == 0:
                fn += 1

        total = len(ground_truth)
        precision = round(tp / (tp + fp), 4) if (tp + fp) > 0 else 0.0
        recall = round(tp / (tp + fn), 4) if (tp + fn) > 0 else 0.0
        fpr = round(fp / (fp + tn), 4) if (fp + tn) > 0 else 0.0
        fnr = round(fn / (fn + tp), 4) if (fn + tp) > 0 else 0.0

        f1 = (
            round((2.0 * precision * recall) / (precision + recall), 4)
            if (precision + recall) > 0
            else 0.0
        )

        return AnomalyBenchmarkMetrics(
            total_samples=total,
            true_positives=tp,
            false_positives=fp,
            true_negatives=tn,
            false_negatives=fn,
            precision=precision,
            recall=recall,
            false_positive_rate=fpr,
            false_negative_rate=fnr,
            f1_score=f1,
        )
