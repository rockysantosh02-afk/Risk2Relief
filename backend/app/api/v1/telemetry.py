"""API v1 Telemetry Ingestion, Querying, Source Health, Quality & Aggregations."""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.telemetry_service import TelemetryService
from app.schemas.telemetry import (
    TelemetrySourceCreate,
    TelemetrySourceResponse,
    TelemetryReadingCreate,
    TelemetryReadingResponse,
    TelemetryBatchCreate,
    TelemetryBatchResponse,
    TelemetryQualityResponse,
    IngestionStatisticsResponse,
)
from app.schemas.common import PaginatedResponse
from app.telemetry.aggregation import AggregationBucket

router = APIRouter(prefix="/telemetry", tags=["Telemetry Pipeline"])


# ==========================================
# 1. Ingestion Endpoints
# ==========================================

@router.post(
    "/ingest",
    status_code=status.HTTP_201_CREATED,
    summary="Ingest Single Telemetry Reading",
    description="Deterministic ingestion pipeline validating units, timestamps, physical bounds, and idempotency.",
)
async def ingest_reading(
    data: TelemetryReadingCreate,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    service = TelemetryService(db)
    try:
        reading, quality_record, stats = await service.ingest_reading(data)
        return {
            "reading": TelemetryReadingResponse.model_validate(reading),
            "quality_record": TelemetryQualityResponse.model_validate(quality_record) if quality_record else None,
            "statistics": stats.model_dump(),
        }
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post(
    "/batch",
    status_code=status.HTTP_201_CREATED,
    summary="Ingest Telemetry Batch",
    description="High-throughput batch ingestion pipeline with deterministic validation and processing duration tracking.",
)
async def ingest_batch(
    data: TelemetryBatchCreate,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    service = TelemetryService(db)
    try:
        batch, stats = await service.ingest_batch(data)
        return {
            "batch": TelemetryBatchResponse.model_validate(batch),
            "statistics": stats.model_dump(),
        }
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


# ==========================================
# 2. Reading Queries & Aggregations
# ==========================================

@router.get(
    "/readings",
    response_model=PaginatedResponse[TelemetryReadingResponse],
    summary="Query Telemetry Readings",
    description="Retrieve paginated time-series observations filtered by building, sensor, metric, quality, and time bounds.",
)
async def query_readings(
    building_id: Optional[uuid.UUID] = Query(default=None),
    source_id: Optional[uuid.UUID] = Query(default=None),
    metric: Optional[str] = Query(default=None),
    quality: Optional[str] = Query(default=None),
    start_time: Optional[datetime] = Query(default=None),
    end_time: Optional[datetime] = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=500),
    order_by: str = Query(default="timestamp"),
    order_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[TelemetryReadingResponse]:
    service = TelemetryService(db)
    readings, total = await service.query_readings(
        building_id=building_id,
        source_id=source_id,
        metric=metric,
        quality=quality,
        start_time=start_time,
        end_time=end_time,
        page=page,
        limit=limit,
        order_by=order_by,
        order_dir=order_dir,
    )
    return PaginatedResponse.create(
        items=[TelemetryReadingResponse.model_validate(r) for r in readings],
        total=total,
        page=page,
        limit=limit,
    )


@router.get(
    "/aggregations",
    summary="Query Multi-Resolution Telemetry Aggregations",
    description="Calculate statistical summary windows (1s, 10s, 1m, 5m, 15m) including rate-of-change and baseline deviations.",
)
async def query_aggregations(
    building_id: uuid.UUID = Query(...),
    metric: str = Query(...),
    bucket: str = Query(default="1m"),
    start_time: Optional[datetime] = Query(default=None),
    end_time: Optional[datetime] = Query(default=None),
    baseline_value: Optional[float] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    service = TelemetryService(db)
    try:
        bucket_enum = AggregationBucket(bucket)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid aggregation bucket '{bucket}'. Choose from: {[b.value for b in AggregationBucket]}",
        )

    results = await service.get_aggregated_telemetry(
        building_id=building_id,
        metric=metric,
        bucket=bucket_enum,
        start_time=start_time,
        end_time=end_time,
        baseline_value=baseline_value,
    )
    return [
        {
            "bucket_start": r.bucket_start.isoformat(),
            "bucket_end": r.bucket_end.isoformat(),
            "metric": r.metric,
            "sample_count": r.sample_count,
            "min_value": r.min_value,
            "max_value": r.max_value,
            "mean_value": r.mean_value,
            "median_value": r.median_value,
            "stddev_value": r.stddev_value,
            "valid_samples": r.valid_samples,
            "anomalous_samples": r.anomalous_samples,
            "stale_samples": r.stale_samples,
            "moving_average": r.moving_average,
            "rate_of_change": r.rate_of_change,
            "baseline_deviation_percentage": r.baseline_deviation_percentage,
        }
        for r in results
    ]


# ==========================================
# 3. Telemetry Sources & Health
# ==========================================

@router.get(
    "/sources",
    response_model=List[TelemetrySourceResponse],
    summary="List Telemetry Sources",
)
async def list_sources(
    building_id: Optional[uuid.UUID] = Query(default=None),
    source_type: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> List[TelemetrySourceResponse]:
    service = TelemetryService(db)
    sources = await service.list_sources_filtered(building_id=building_id, source_type=source_type, status=status)
    return [TelemetrySourceResponse.model_validate(s) for s in sources]


@router.post(
    "/sources",
    response_model=TelemetrySourceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register Telemetry Source",
)
async def register_source(
    data: TelemetrySourceCreate,
    db: AsyncSession = Depends(get_db),
) -> TelemetrySourceResponse:
    service = TelemetryService(db)
    try:
        created = await service.register_source(data)
        return TelemetrySourceResponse.model_validate(created)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get(
    "/sources/{source_id}",
    response_model=TelemetrySourceResponse,
    summary="Get Telemetry Source",
)
async def get_source(
    source_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> TelemetrySourceResponse:
    service = TelemetryService(db)
    src = await service.get_source(source_id)
    if not src:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"TelemetrySource {source_id} not found")
    return TelemetrySourceResponse.model_validate(src)


@router.get(
    "/sources/{source_id}/health",
    summary="Get Telemetry Source Health & Explainable Reliability Score",
)
async def get_source_health(
    source_id: uuid.UUID,
    window_seconds: float = Query(default=3600.0, ge=60.0, le=86400.0),
    db: AsyncSession = Depends(get_db),
):
    service = TelemetryService(db)
    try:
        health = await service.get_source_health(source_id=source_id, window_seconds=window_seconds)
        return {
            "source_id": str(health.source_id),
            "source_identifier": health.source_identifier,
            "overall_reliability_score": health.overall_reliability_score,
            "status": health.status,
            "availability_score": health.availability_score,
            "accuracy_score": health.accuracy_score,
            "anomaly_penalty": health.anomaly_penalty,
            "latency_freshness_score": health.latency_freshness_score,
            "total_samples": health.total_samples,
            "valid_samples": health.valid_samples,
            "anomalous_samples": health.anomalous_samples,
            "stale_samples": health.stale_samples,
            "evaluation_window_seconds": health.evaluation_window_seconds,
            "calculated_at": health.calculated_at.isoformat(),
            "explanation": health.explanation,
        }
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


# ==========================================
# 4. Telemetry Quality Audit Records
# ==========================================

@router.get(
    "/quality-records",
    response_model=PaginatedResponse[TelemetryQualityResponse],
    summary="Query Telemetry Quality Audit Records",
    description="Retrieve validation failure and anomaly flags across telemetry sources.",
)
async def query_quality_records(
    source_id: Optional[uuid.UUID] = Query(default=None),
    flagged_quality: Optional[str] = Query(default=None),
    start_time: Optional[datetime] = Query(default=None),
    end_time: Optional[datetime] = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[TelemetryQualityResponse]:
    service = TelemetryService(db)
    records, total = await service.query_quality_records(
        source_id=source_id,
        flagged_quality=flagged_quality,
        start_time=start_time,
        end_time=end_time,
        page=page,
        limit=limit,
    )
    return PaginatedResponse.create(
        items=[TelemetryQualityResponse.model_validate(r) for r in records],
        total=total,
        page=page,
        limit=limit,
    )
