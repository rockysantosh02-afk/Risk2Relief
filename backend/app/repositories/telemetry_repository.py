"""Repository for TelemetrySource, TelemetryReading, TelemetryBatch, and Quality Records.

Optimized for time-series filtering and idempotent deduplication.
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Sequence, List, Tuple
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.telemetry import (
    TelemetrySource,
    TelemetryBatch,
    TelemetryReading,
    TelemetryQualityRecord,
)
from app.repositories.base import BaseRepository


class TelemetryRepository(BaseRepository[TelemetryReading]):
    """Data access repository for telemetry streams and quality auditing."""

    def __init__(self, session: AsyncSession):
        super().__init__(TelemetryReading, session)

    # Telemetry Source operations
    async def add_source(self, source: TelemetrySource) -> TelemetrySource:
        self.session.add(source)
        await self.session.flush()
        await self.session.refresh(source)
        return source

    async def get_source_by_identifier(self, identifier: str) -> Optional[TelemetrySource]:
        result = await self.session.execute(
            select(TelemetrySource).where(TelemetrySource.source_identifier == identifier)
        )
        return result.scalar_one_or_none()

    async def get_source_by_id(self, source_id: uuid.UUID) -> Optional[TelemetrySource]:
        result = await self.session.execute(
            select(TelemetrySource).where(TelemetrySource.id == source_id)
        )
        return result.scalar_one_or_none()

    async def list_sources(self, building_id: uuid.UUID) -> Sequence[TelemetrySource]:
        result = await self.session.execute(
            select(TelemetrySource).where(TelemetrySource.building_id == building_id)
        )
        return result.scalars().all()

    async def update_source_last_seen(self, source_id: uuid.UUID, last_seen: datetime) -> None:
        source = await self.get_source_by_id(source_id)
        if source:
            source.last_seen = last_seen
            await self.session.flush()

    # Telemetry Reading operations
    async def add_reading(self, reading: TelemetryReading) -> TelemetryReading:
        self.session.add(reading)
        await self.session.flush()
        await self.session.refresh(reading)
        return reading

    async def bulk_add_readings(self, readings: List[TelemetryReading]) -> Sequence[TelemetryReading]:
        self.session.add_all(readings)
        await self.session.flush()
        return readings

    async def find_reading_by_source_and_event(
        self, source_id: uuid.UUID, event_id: str
    ) -> Optional[TelemetryReading]:
        """Check for existing reading by source_id and event_id for duplicate detection."""
        result = await self.session.execute(
            select(TelemetryReading).where(
                TelemetryReading.source_id == source_id,
                TelemetryReading.event_id == event_id,
            )
        )
        return result.scalar_one_or_none()

    async def query_readings(
        self,
        building_id: uuid.UUID,
        metric: Optional[str] = None,
        source_id: Optional[uuid.UUID] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        quality: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[TelemetryReading]:
        """Perform indexed time-series filtering on telemetry observations."""
        filters = [TelemetryReading.building_id == building_id]

        if metric:
            filters.append(TelemetryReading.metric == metric)
        if source_id:
            filters.append(TelemetryReading.source_id == source_id)
        if start_time:
            filters.append(TelemetryReading.timestamp >= start_time)
        if end_time:
            filters.append(TelemetryReading.timestamp <= end_time)
        if quality:
            filters.append(TelemetryReading.quality == quality)

        stmt = (
            select(TelemetryReading)
            .where(and_(*filters))
            .order_by(TelemetryReading.timestamp.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def query_readings_with_count(
        self,
        building_id: Optional[uuid.UUID] = None,
        metric: Optional[str] = None,
        source_id: Optional[uuid.UUID] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        quality: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        order_by: str = "timestamp",
        order_dir: str = "desc",
    ) -> Tuple[Sequence[TelemetryReading], int]:
        """Query readings with total matching count for pagination."""
        from sqlalchemy import func
        filters = []
        if building_id:
            filters.append(TelemetryReading.building_id == building_id)
        if metric:
            filters.append(TelemetryReading.metric == metric)
        if source_id:
            filters.append(TelemetryReading.source_id == source_id)
        if start_time:
            filters.append(TelemetryReading.timestamp >= start_time)
        if end_time:
            filters.append(TelemetryReading.timestamp <= end_time)
        if quality:
            filters.append(TelemetryReading.quality == quality.upper())

        where_clause = and_(*filters) if filters else True

        count_stmt = select(func.count(TelemetryReading.id)).where(where_clause)
        total_res = await self.session.execute(count_stmt)
        total = total_res.scalar_one()

        order_col = getattr(TelemetryReading, order_by, TelemetryReading.timestamp)
        order_expr = order_col.desc() if order_dir.lower() == "desc" else order_col.asc()

        stmt = select(TelemetryReading).where(where_clause).order_by(order_expr).limit(limit).offset(offset)
        res = await self.session.execute(stmt)
        return res.scalars().all(), total

    async def list_sources_filtered(
        self,
        building_id: Optional[uuid.UUID] = None,
        source_type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Sequence[TelemetrySource]:
        filters = []
        if building_id:
            filters.append(TelemetrySource.building_id == building_id)
        if source_type:
            filters.append(TelemetrySource.source_type == source_type.upper())
        if status:
            filters.append(TelemetrySource.status == status.upper())

        where_clause = and_(*filters) if filters else True
        stmt = select(TelemetrySource).where(where_clause).order_by(TelemetrySource.name)
        res = await self.session.execute(stmt)
        return res.scalars().all()

    # Telemetry Batch operations
    async def add_batch(self, batch: TelemetryBatch) -> TelemetryBatch:
        self.session.add(batch)
        await self.session.flush()
        await self.session.refresh(batch)
        return batch

    async def get_batch_by_identifier(self, identifier: str) -> Optional[TelemetryBatch]:
        result = await self.session.execute(
            select(TelemetryBatch).where(TelemetryBatch.batch_identifier == identifier)
        )
        return result.scalar_one_or_none()

    # Quality Record operations
    async def add_quality_record(self, record: TelemetryQualityRecord) -> TelemetryQualityRecord:
        self.session.add(record)
        await self.session.flush()
        await self.session.refresh(record)
        return record

    async def list_quality_records_by_source(
        self, source_id: uuid.UUID, limit: int = 50
    ) -> Sequence[TelemetryQualityRecord]:
        result = await self.session.execute(
            select(TelemetryQualityRecord)
            .where(TelemetryQualityRecord.source_id == source_id)
            .order_by(TelemetryQualityRecord.detected_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def query_quality_records(
        self,
        source_id: Optional[uuid.UUID] = None,
        flagged_quality: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[Sequence[TelemetryQualityRecord], int]:
        from sqlalchemy import func
        filters = []
        if source_id:
            filters.append(TelemetryQualityRecord.source_id == source_id)
        if flagged_quality:
            filters.append(TelemetryQualityRecord.flagged_quality == flagged_quality.upper())
        if start_time:
            filters.append(TelemetryQualityRecord.detected_at >= start_time)
        if end_time:
            filters.append(TelemetryQualityRecord.detected_at <= end_time)

        where_clause = and_(*filters) if filters else True
        count_stmt = select(func.count(TelemetryQualityRecord.id)).where(where_clause)
        total_res = await self.session.execute(count_stmt)
        total = total_res.scalar_one()

        stmt = (
            select(TelemetryQualityRecord)
            .where(where_clause)
            .order_by(TelemetryQualityRecord.detected_at.desc())
            .limit(limit)
            .offset(offset)
        )
        res = await self.session.execute(stmt)
        return res.scalars().all(), total


    async def get_readings_for_aggregation(
        self,
        building_id: uuid.UUID,
        metric: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 10000,
    ) -> Sequence[TelemetryReading]:
        """Fetch readings ordered by timestamp ascending for windowed aggregation."""
        filters = [
            TelemetryReading.building_id == building_id,
            TelemetryReading.metric == metric,
        ]
        if start_time:
            filters.append(TelemetryReading.timestamp >= start_time)
        if end_time:
            filters.append(TelemetryReading.timestamp <= end_time)

        stmt = (
            select(TelemetryReading)
            .where(and_(*filters))
            .order_by(TelemetryReading.timestamp.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_source_readings_window(
        self,
        source_id: uuid.UUID,
        window_seconds: float = 3600.0,
        now: Optional[datetime] = None,
    ) -> Sequence[TelemetryReading]:
        """Fetch observations for a specific sensor source over an evaluation time window."""
        current_time = now or datetime.now(timezone.utc)
        start_time = current_time - timedelta(seconds=window_seconds)

        stmt = (
            select(TelemetryReading)
            .where(
                and_(
                    TelemetryReading.source_id == source_id,
                    TelemetryReading.timestamp >= start_time,
                )
            )
            .order_by(TelemetryReading.timestamp.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

