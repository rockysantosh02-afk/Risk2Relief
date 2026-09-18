"""Unit tests for Telemetry Aggregation and Derived Analytics Engine."""

import pytest
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
from typing import Optional

from app.telemetry.aggregation import (
    TelemetryAggregator,
    AggregationBucket,
    BUCKET_SECONDS_MAP,
)


@dataclass
class MockReading:
    timestamp: datetime
    value: float
    quality: str = "VALID"


def test_aggregation_bucket_windows():
    """Verify bucket alignment accurately rounds timestamps to epoch intervals."""
    # 2026-09-18 12:03:45 UTC
    ts = datetime(2026, 9, 18, 12, 3, 45, tzinfo=timezone.utc)

    # 1s bucket
    start_1s, end_1s = TelemetryAggregator.get_bucket_window(ts, AggregationBucket.ONE_SECOND)
    assert start_1s == datetime(2026, 9, 18, 12, 3, 45, tzinfo=timezone.utc)
    assert end_1s == datetime(2026, 9, 18, 12, 3, 46, tzinfo=timezone.utc)

    # 10s bucket
    start_10s, end_10s = TelemetryAggregator.get_bucket_window(ts, AggregationBucket.TEN_SECONDS)
    assert start_10s == datetime(2026, 9, 18, 12, 3, 40, tzinfo=timezone.utc)
    assert end_10s == datetime(2026, 9, 18, 12, 3, 50, tzinfo=timezone.utc)

    # 1m bucket
    start_1m, end_1m = TelemetryAggregator.get_bucket_window(ts, AggregationBucket.ONE_MINUTE)
    assert start_1m == datetime(2026, 9, 18, 12, 3, 0, tzinfo=timezone.utc)
    assert end_1m == datetime(2026, 9, 18, 12, 4, 0, tzinfo=timezone.utc)

    # 5m bucket
    start_5m, end_5m = TelemetryAggregator.get_bucket_window(ts, AggregationBucket.FIVE_MINUTES)
    assert start_5m == datetime(2026, 9, 18, 12, 0, 0, tzinfo=timezone.utc)
    assert end_5m == datetime(2026, 9, 18, 12, 5, 0, tzinfo=timezone.utc)

    # 15m bucket
    start_15m, end_15m = TelemetryAggregator.get_bucket_window(ts, AggregationBucket.FIFTEEN_MINUTES)
    assert start_15m == datetime(2026, 9, 18, 12, 0, 0, tzinfo=timezone.utc)
    assert end_15m == datetime(2026, 9, 18, 12, 15, 0, tzinfo=timezone.utc)


def test_aggregation_basic_statistics():
    """Verify min, max, mean, median, stddev, and counts are calculated accurately."""
    base_time = datetime(2026, 9, 18, 10, 0, 0, tzinfo=timezone.utc)
    readings = [
        MockReading(timestamp=base_time + timedelta(seconds=2), value=10.0),
        MockReading(timestamp=base_time + timedelta(seconds=4), value=20.0),
        MockReading(timestamp=base_time + timedelta(seconds=6), value=30.0),
        MockReading(timestamp=base_time + timedelta(seconds=7), value=40.0),
        MockReading(timestamp=base_time + timedelta(seconds=8), value=50.0),
    ]

    results = TelemetryAggregator.aggregate_readings(
        readings=readings,
        bucket=AggregationBucket.TEN_SECONDS,
        metric="temperature_celsius",
    )

    assert len(results) == 1
    res = results[0]
    assert res.bucket == AggregationBucket.TEN_SECONDS
    assert res.count == 5
    assert res.valid_count == 5
    assert res.invalid_count == 0
    assert res.min_value == 10.0
    assert res.max_value == 50.0
    assert res.mean_value == 30.0
    assert res.median_value == 30.0
    assert res.stddev is not None
    assert round(res.stddev, 2) == 15.81


def test_aggregation_quality_separation():
    """Verify invalid/anomalous readings do not contaminate statistics of valid readings."""
    base_time = datetime(2026, 9, 18, 10, 0, 0, tzinfo=timezone.utc)
    readings = [
        MockReading(timestamp=base_time + timedelta(seconds=1), value=100.0, quality="VALID"),
        MockReading(timestamp=base_time + timedelta(seconds=2), value=200.0, quality="VALID"),
        MockReading(timestamp=base_time + timedelta(seconds=3), value=99999.0, quality="ANOMALOUS"),
        MockReading(timestamp=base_time + timedelta(seconds=4), value=-9999.0, quality="INVALID"),
    ]

    results = TelemetryAggregator.aggregate_readings(
        readings=readings,
        bucket=AggregationBucket.TEN_SECONDS,
        metric="load_kn",
    )

    assert len(results) == 1
    res = results[0]
    assert res.count == 4
    assert res.valid_count == 2
    assert res.invalid_count == 2
    # Statistics computed only from 100.0 and 200.0
    assert res.min_value == 100.0
    assert res.max_value == 200.0
    assert res.mean_value == 150.0


def test_aggregation_baseline_deviation_and_rate_of_change():
    """Verify baseline deviation and rate of change between windows."""
    base_time = datetime(2026, 9, 18, 10, 0, 0, tzinfo=timezone.utc)
    readings = [
        # Window 1 (10:00:00 - 10:00:10): Mean = 100.0
        MockReading(timestamp=base_time + timedelta(seconds=2), value=100.0),
        # Window 2 (10:00:10 - 10:00:20): Mean = 150.0
        MockReading(timestamp=base_time + timedelta(seconds=12), value=150.0),
    ]

    results = TelemetryAggregator.aggregate_readings(
        readings=readings,
        bucket=AggregationBucket.TEN_SECONDS,
        metric="load_kn",
        baseline_value=100.0,
    )

    assert len(results) == 2
    # Window 1: Mean 100, baseline 100 -> dev 0%
    assert results[0].mean_value == 100.0
    assert results[0].baseline_deviation_percentage == 0.0
    assert results[0].rate_of_change == 0.0

    # Window 2: Mean 150, baseline 100 -> dev +50%
    assert results[1].mean_value == 150.0
    assert results[1].baseline_deviation_percentage == 50.0
    # Rate of change: (150 - 100) / 10s = 5.0 units/sec
    assert results[1].rate_of_change == 5.0


def test_aggregation_empty_list():
    """Verify empty readings input returns empty list."""
    results = TelemetryAggregator.aggregate_readings(
        readings=[],
        bucket=AggregationBucket.ONE_MINUTE,
        metric="vibration_hz",
    )
    assert results == []
