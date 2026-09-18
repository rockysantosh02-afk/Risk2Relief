"""Telemetry Time-Series Aggregation & Derived Analytics Engine.

Calculates multi-resolution statistical windows:
- 1 second (1s)
- 10 seconds (10s)
- 1 minute (1m)
- 5 minutes (5m)
- 15 minutes (15m)

Computes statistical distribution (min, max, mean, median, stddev, count, valid/invalid counts)
and derived analytical metrics (moving average, rate of change, baseline deviation).
"""

from __future__ import annotations
import math
import statistics
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import List, Dict, Optional, Sequence, Any, Tuple

Tuple_Window = Tuple[datetime, datetime]
from pydantic import BaseModel, Field


class AggregationBucket(str, Enum):
    ONE_SECOND = "1s"
    TEN_SECONDS = "10s"
    ONE_MINUTE = "1m"
    FIVE_MINUTES = "5m"
    FIFTEEN_MINUTES = "15m"


BUCKET_SECONDS_MAP = {
    AggregationBucket.ONE_SECOND: 1,
    AggregationBucket.TEN_SECONDS: 10,
    AggregationBucket.ONE_MINUTE: 60,
    AggregationBucket.FIVE_MINUTES: 300,
    AggregationBucket.FIFTEEN_MINUTES: 900,
}


class AggregationResult(BaseModel):
    """Statistical summary for an aggregation time window."""
    bucket: AggregationBucket
    start_time: datetime
    end_time: datetime
    metric: str
    count: int = 0
    valid_count: int = 0
    invalid_count: int = 0
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    mean_value: Optional[float] = None
    median_value: Optional[float] = None
    stddev: Optional[float] = None
    moving_average: Optional[float] = None
    rate_of_change: Optional[float] = None
    baseline_deviation_percentage: Optional[float] = None


class TelemetryAggregator:
    """Engine computing temporal aggregations and derived metrics."""

    @staticmethod
    def get_bucket_window(ts: datetime, bucket: AggregationBucket) -> Tuple_Window:
        """Align timestamp to the start and end of its bucket window."""
        window_secs = BUCKET_SECONDS_MAP[bucket]
        epoch = int(ts.timestamp())
        bucket_start_epoch = (epoch // window_secs) * window_secs
        start_time = datetime.fromtimestamp(bucket_start_epoch, tz=timezone.utc)
        end_time = start_time + timedelta(seconds=window_secs)
        return start_time, end_time

    @classmethod
    def aggregate_readings(
        cls,
        readings: Sequence[Any],
        bucket: AggregationBucket,
        metric: str,
        baseline_value: Optional[float] = None,
        previous_mean: Optional[float] = None,
    ) -> List[AggregationResult]:
        """Aggregate a sequence of telemetry readings into discrete temporal windows."""
        if not readings:
            return []

        window_secs = BUCKET_SECONDS_MAP[bucket]

        # Group readings by window start
        grouped: Dict[datetime, List[Any]] = {}
        for r in readings:
            ts = r.timestamp if r.timestamp.tzinfo else r.timestamp.replace(tzinfo=timezone.utc)
            epoch = int(ts.timestamp())
            start_epoch = (epoch // window_secs) * window_secs
            window_start = datetime.fromtimestamp(start_epoch, tz=timezone.utc)
            if window_start not in grouped:
                grouped[window_start] = []
            grouped[window_start].append(r)

        results: List[AggregationResult] = []
        sorted_windows = sorted(grouped.keys())

        prior_mean = previous_mean
        rolling_values: List[float] = []

        for window_start in sorted_windows:
            window_end = window_start + timedelta(seconds=window_secs)
            items = grouped[window_start]

            total_count = len(items)
            valid_values = [item.value for item in items if getattr(item, "quality", "VALID") == "VALID"]
            valid_count = len(valid_values)
            invalid_count = total_count - valid_count

            min_val = min(valid_values) if valid_values else None
            max_val = max(valid_values) if valid_values else None
            mean_val = (sum(valid_values) / valid_count) if valid_count > 0 else None
            median_val = statistics.median(valid_values) if valid_count > 0 else None
            stddev_val = (statistics.stdev(valid_values) if valid_count > 1 else 0.0) if valid_count > 0 else None

            # Moving average calculation
            if mean_val is not None:
                rolling_values.append(mean_val)
                # 5-period rolling window
                if len(rolling_values) > 5:
                    rolling_values.pop(0)
                moving_avg = sum(rolling_values) / len(rolling_values)
            else:
                moving_avg = None

            # Rate of change: delta_mean / window_secs
            if mean_val is not None and prior_mean is not None and window_secs > 0:
                rate_of_change = (mean_val - prior_mean) / float(window_secs)
            else:
                rate_of_change = 0.0

            # Baseline deviation percentage
            if mean_val is not None and baseline_value is not None and baseline_value != 0:
                baseline_dev = ((mean_val - baseline_value) / abs(baseline_value)) * 100.0
            else:
                baseline_dev = None

            prior_mean = mean_val if mean_val is not None else prior_mean

            results.append(
                AggregationResult(
                    bucket=bucket,
                    start_time=window_start,
                    end_time=window_end,
                    metric=metric,
                    count=total_count,
                    valid_count=valid_count,
                    invalid_count=invalid_count,
                    min_value=min_val,
                    max_value=max_val,
                    mean_value=mean_val,
                    median_value=median_val,
                    stddev=stddev_val,
                    moving_average=moving_avg,
                    rate_of_change=rate_of_change,
                    baseline_deviation_percentage=baseline_dev,
                )
            )

        return results
