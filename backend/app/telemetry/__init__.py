"""Telemetry intelligence, validation, simulation, and aggregation modules."""

from app.telemetry.validation import (
    TelemetryValidationEngine,
    ValidationResult,
    METRIC_SPECIFICATIONS,
)
from app.telemetry.aggregation import (
    AggregationBucket,
    AggregationResult,
    TelemetryAggregator,
)
from app.telemetry.source_health import (
    SourceHealthMetrics,
    SourceHealthEngine,
)
from app.telemetry.simulator import (
    TelemetrySimulator,
    SimulatorScenarioEnum,
)

__all__ = [
    "TelemetryValidationEngine",
    "ValidationResult",
    "METRIC_SPECIFICATIONS",
    "AggregationBucket",
    "AggregationResult",
    "TelemetryAggregator",
    "SourceHealthMetrics",
    "SourceHealthEngine",
    "TelemetrySimulator",
    "SimulatorScenarioEnum",
]
