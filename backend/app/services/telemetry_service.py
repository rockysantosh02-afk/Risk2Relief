"""Telemetry ingestion, validation, deduplication, aggregation, and intelligence domain service."""

import time
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Sequence, Tuple, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.telemetry import (
    TelemetrySource,
    TelemetryBatch,
    TelemetryReading,
    TelemetryQualityRecord,
)
from app.repositories.telemetry_repository import TelemetryRepository
from app.schemas.telemetry import (
    TelemetrySourceCreate,
    TelemetryReadingCreate,
    TelemetryBatchCreate,
    QualityEnum,
    IngestionStatisticsResponse,
)
from app.telemetry.validation import TelemetryValidationEngine, ValidationResult
from app.telemetry.aggregation import TelemetryAggregator, AggregationBucket, AggregationResult
from app.telemetry.source_health import SourceHealthEngine, SourceHealthMetrics


class TelemetryService:
    """Comprehensive domain service for telemetry lifecycle, validation, aggregation, and intelligence."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = TelemetryRepository(session)

    async def register_source(self, data: TelemetrySourceCreate) -> TelemetrySource:
        """Register a new telemetry sensor or virtual feed."""
        existing = await self.repo.get_source_by_identifier(data.source_identifier)
        if existing:
            raise ValueError(f"TelemetrySource '{data.source_identifier}' already registered")

        source = TelemetrySource(
            source_identifier=data.source_identifier,
            name=data.name,
            source_type=data.source_type.value,
            building_id=data.building_id,
            zone_id=data.zone_id,
            structural_node_id=data.structural_node_id,
            status=data.status,
            reliability_score=data.reliability_score,
            sampling_rate_hz=data.sampling_rate_hz,
            metadata_json=data.metadata_json or {},
        )
        return await self.repo.add_source(source)

    async def ingest_reading(
        self, data: TelemetryReadingCreate, now: Optional[datetime] = None
    ) -> Tuple[TelemetryReading, Optional[TelemetryQualityRecord], IngestionStatisticsResponse]:
        """Ingest a single reading through the deterministic validation pipeline.

        Returns (saved_reading, quality_record, stats).
        """
        stats = IngestionStatisticsResponse(total_received=1)
        current_time = now or datetime.now(timezone.utc)

        # 1. Source check
        source = await self.repo.get_source_by_id(data.source_id)
        source_is_known = source is not None
        source_is_active = source is not None and source.status.upper() in ("ONLINE", "CALIBRATING")

        # 2. Duplicate check
        existing_reading = await self.repo.find_reading_by_source_and_event(data.source_id, data.event_id)
        is_duplicate = existing_reading is not None

        # 3. Deterministic validation
        val_res = TelemetryValidationEngine.validate_reading(
            metric=data.metric,
            value=data.value,
            unit=data.unit,
            timestamp=data.timestamp,
            event_id=data.event_id,
            source_is_known=source_is_known,
            source_is_active=source_is_active,
            is_duplicate=is_duplicate,
            now=current_time,
        )

        # Handle duplicate event
        if is_duplicate:
            stats.duplicate += 1
            stats.rejected += 1
            stats.errors.append({
                "event_id": data.event_id,
                "error_code": val_res.error_code,
                "reason": val_res.reason,
            })
            quality_record = TelemetryQualityRecord(
                reading_id=existing_reading.id,
                source_id=data.source_id,
                flagged_quality=QualityEnum.DUPLICATE.value,
                anomaly_score=1.0,
                reason=val_res.reason or "Duplicate event_id detected",
                detected_at=current_time,
            )
            await self.repo.add_quality_record(quality_record)
            return existing_reading, quality_record, stats

        # Handle unknown source
        if not source_is_known:
            stats.rejected += 1
            stats.invalid += 1
            stats.errors.append({
                "event_id": data.event_id,
                "error_code": val_res.error_code,
                "reason": val_res.reason,
            })
            raise ValueError(f"TelemetrySource {data.source_id} not found")

        # Track quality counts
        if val_res.quality == QualityEnum.VALID:
            stats.accepted += 1
        elif val_res.quality == QualityEnum.ANOMALOUS:
            stats.anomalous += 1
            stats.accepted += 1  # Persisted as anomalous for investigation
        elif val_res.quality == QualityEnum.STALE:
            stats.stale += 1
            stats.accepted += 1  # Persisted as stale for audit
        else:
            stats.invalid += 1
            stats.rejected += 1
            stats.errors.append({
                "event_id": data.event_id,
                "error_code": val_res.error_code,
                "reason": val_res.reason,
            })

        # Persist reading
        reading_time = data.timestamp if data.timestamp.tzinfo else data.timestamp.replace(tzinfo=timezone.utc)
        reading = TelemetryReading(
            source_id=data.source_id,
            building_id=data.building_id,
            zone_id=data.zone_id,
            batch_id=data.batch_id,
            metric=data.metric,
            value=data.value,
            unit=data.unit,
            timestamp=reading_time,
            event_id=data.event_id,
            quality=val_res.quality.value,
            metadata_json=data.metadata_json or {},
        )
        saved_reading = await self.repo.add_reading(reading)

        # Record quality incident if not strictly VALID
        quality_record = None
        if not val_res.is_valid or val_res.quality != QualityEnum.VALID:
            quality_record = TelemetryQualityRecord(
                reading_id=saved_reading.id,
                source_id=data.source_id,
                flagged_quality=val_res.quality.value,
                anomaly_score=val_res.anomaly_score,
                reason=val_res.reason or "Validation rule triggered",
                detected_at=current_time,
            )
            await self.repo.add_quality_record(quality_record)

        # Update source last seen
        await self.repo.update_source_last_seen(data.source_id, reading_time)

        return saved_reading, quality_record, stats

    async def ingest_batch(
        self, data: TelemetryBatchCreate, now: Optional[datetime] = None
    ) -> Tuple[TelemetryBatch, IngestionStatisticsResponse]:
        """Ingest a batch of readings through deterministic validation with aggregated statistics."""
        start_time = time.perf_counter()
        current_time = now or datetime.now(timezone.utc)

        existing_batch = await self.repo.get_batch_by_identifier(data.batch_identifier)
        if existing_batch:
            raise ValueError(f"TelemetryBatch '{data.batch_identifier}' already processed")

        batch = TelemetryBatch(
            batch_identifier=data.batch_identifier,
            building_id=data.building_id,
            source_count=len({r.metric for r in data.readings}) or 1,
            readings_count=len(data.readings),
            status="INGESTED",
            metadata_json=data.metadata_json or {},
        )
        saved_batch = await self.repo.add_batch(batch)

        batch_stats = IngestionStatisticsResponse()

        # Find registered sources for the building
        sources = await self.repo.list_sources(data.building_id)
        default_source_id = sources[0].id if sources else None

        for r_base in data.readings:
            batch_stats.total_received += 1
            # Check if source_id is specified in reading metadata or use default
            source_id = uuid.UUID(r_base.metadata_json.get("source_id")) if (r_base.metadata_json and "source_id" in r_base.metadata_json) else default_source_id

            if not source_id:
                batch_stats.rejected += 1
                batch_stats.invalid += 1
                batch_stats.errors.append({
                    "event_id": r_base.event_id,
                    "error_code": "ERR_UNKNOWN_SOURCE",
                    "reason": f"No telemetry source available for reading {r_base.event_id}",
                })
                continue

            reading_create = TelemetryReadingCreate(
                source_id=source_id,
                building_id=data.building_id,
                batch_id=saved_batch.id,
                metric=r_base.metric,
                value=r_base.value,
                unit=r_base.unit,
                timestamp=r_base.timestamp,
                event_id=r_base.event_id,
                quality=r_base.quality,
                metadata_json=r_base.metadata_json or {},
            )

            try:
                _, _, r_stats = await self.ingest_reading(reading_create, now=current_time)
                batch_stats.accepted += r_stats.accepted
                batch_stats.rejected += r_stats.rejected
                batch_stats.duplicate += r_stats.duplicate
                batch_stats.stale += r_stats.stale
                batch_stats.invalid += r_stats.invalid
                batch_stats.anomalous += r_stats.anomalous
                batch_stats.errors.extend(r_stats.errors)
            except Exception as exc:
                batch_stats.rejected += 1
                batch_stats.invalid += 1
                batch_stats.errors.append({
                    "event_id": r_base.event_id,
                    "error_code": "ERR_INGESTION_EXCEPTION",
                    "reason": str(exc),
                })

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        saved_batch.processing_duration_ms = elapsed_ms
        saved_batch.status = "PROCESSED" if batch_stats.rejected == 0 else "PARTIAL"
        await self.session.flush()

        return saved_batch, batch_stats

    async def get_aggregated_telemetry(
        self,
        building_id: uuid.UUID,
        metric: str,
        bucket: AggregationBucket = AggregationBucket.ONE_MINUTE,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        baseline_value: Optional[float] = None,
    ) -> List[AggregationResult]:
        """Fetch observations and calculate multi-resolution aggregations and analytics."""
        readings = await self.repo.get_readings_for_aggregation(
            building_id=building_id,
            metric=metric,
            start_time=start_time,
            end_time=end_time,
        )
        return TelemetryAggregator.aggregate_readings(
            readings=readings,
            bucket=bucket,
            metric=metric,
            baseline_value=baseline_value,
        )

    async def get_source_health(
        self,
        source_id: uuid.UUID,
        window_seconds: float = 3600.0,
        now: Optional[datetime] = None,
    ) -> SourceHealthMetrics:
        """Inspect source observations and calculate explainable reliability metrics."""
        source = await self.repo.get_source_by_id(source_id)
        if not source:
            raise ValueError(f"TelemetrySource {source_id} not found")

        readings = await self.repo.get_source_readings_window(
            source_id=source_id,
            window_seconds=window_seconds,
            now=now,
        )

        return SourceHealthEngine.calculate_health(
            source_id=source.id,
            source_identifier=source.source_identifier,
            status=source.status,
            sampling_rate_hz=source.sampling_rate_hz,
            readings=readings,
            now=now,
            evaluation_window_seconds=window_seconds,
        )

    async def get_source(self, source_id: uuid.UUID) -> Optional[TelemetrySource]:
        """Fetch telemetry source by unique ID."""
        return await self.repo.get_source_by_id(source_id)

    async def list_sources_filtered(
        self,
        building_id: Optional[uuid.UUID] = None,
        source_type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Sequence[TelemetrySource]:
        """List telemetry sources with optional filters."""
        return await self.repo.list_sources_filtered(
            building_id=building_id, source_type=source_type, status=status
        )

    async def query_readings(
        self,
        building_id: Optional[uuid.UUID] = None,
        metric: Optional[str] = None,
        source_id: Optional[uuid.UUID] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        quality: Optional[str] = None,
        page: int = 1,
        limit: int = 50,
        order_by: str = "timestamp",
        order_dir: str = "desc",
    ) -> Tuple[Sequence[TelemetryReading], int]:
        """Query telemetry readings with pagination and total count."""
        offset = (page - 1) * limit
        return await self.repo.query_readings_with_count(
            building_id=building_id,
            metric=metric,
            source_id=source_id,
            start_time=start_time,
            end_time=end_time,
            quality=quality,
            limit=limit,
            offset=offset,
            order_by=order_by,
            order_dir=order_dir,
        )

    async def query_quality_records(
        self,
        source_id: Optional[uuid.UUID] = None,
        flagged_quality: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        page: int = 1,
        limit: int = 50,
    ) -> Tuple[Sequence[TelemetryQualityRecord], int]:
        """Query quality audit records with pagination and total count."""
        offset = (page - 1) * limit
        return await self.repo.query_quality_records(
            source_id=source_id,
            flagged_quality=flagged_quality,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
            offset=offset,
        )

