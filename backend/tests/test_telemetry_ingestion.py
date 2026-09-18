"""Integration tests for Telemetry Ingestion Pipeline, Batch Statistics, and Quality Records."""

import uuid
import pytest
from datetime import datetime, timezone, timedelta

from app.models.building import Building
from app.schemas.telemetry import (
    SourceTypeEnum,
    TelemetrySourceCreate,
    TelemetryReadingCreate,
    TelemetryBatchCreate,
    TelemetryReadingBase,
    QualityEnum,
)
from app.telemetry.aggregation import AggregationBucket
from app.services.telemetry_service import TelemetryService


@pytest.mark.asyncio
async def test_telemetry_ingestion_single_valid_reading(db_session):
    """Verify single valid reading ingestion records telemetry reading accurately."""
    service = TelemetryService(db_session)
    now = datetime.now(timezone.utc)

    # 1. Create building and source
    bld = Building(name="Tower One", code="TW1-INGEST", number_of_floors=5)
    db_session.add(bld)
    await db_session.flush()

    source = await service.register_source(
        TelemetrySourceCreate(
            source_identifier="STR-INGEST-01",
            name="Strain Sensor 01",
            source_type=SourceTypeEnum.STRAIN_GAUGE,
            building_id=bld.id,
            sampling_rate_hz=10.0,
            status="ONLINE",
        )
    )

    # 2. Ingest valid reading
    reading_data = TelemetryReadingCreate(
        source_id=source.id,
        building_id=bld.id,
        metric="strain_microstrain",
        value=150.0,
        unit="um/m",
        timestamp=now,
        event_id="EVT-ING-001",
    )

    reading, quality_rec, stats = await service.ingest_reading(reading_data, now=now)

    assert reading.id is not None
    assert reading.quality == QualityEnum.VALID.value
    assert quality_rec is None  # No quality incident record for valid
    assert stats.total_received == 1
    assert stats.accepted == 1
    assert stats.rejected == 0
    assert stats.duplicate == 0


@pytest.mark.asyncio
async def test_telemetry_ingestion_duplicate_deduplication(db_session):
    """Verify duplicate event_id is rejected and flagged as DUPLICATE quality record."""
    service = TelemetryService(db_session)
    now = datetime.now(timezone.utc)

    bld = Building(name="Tower Two", code="TW2-INGEST", number_of_floors=5)
    db_session.add(bld)
    await db_session.flush()

    source = await service.register_source(
        TelemetrySourceCreate(
            source_identifier="TEMP-INGEST-01",
            name="Temp Sensor 01",
            source_type=SourceTypeEnum.TEMPERATURE,
            building_id=bld.id,
            sampling_rate_hz=1.0,
            status="ONLINE",
        )
    )

    reading_data = TelemetryReadingCreate(
        source_id=source.id,
        building_id=bld.id,
        metric="temperature_celsius",
        value=23.5,
        unit="C",
        timestamp=now,
        event_id="EVT-DUP-TEST",
    )

    # First ingestion succeeds
    _, _, stats1 = await service.ingest_reading(reading_data, now=now)
    assert stats1.accepted == 1

    # Second ingestion with same event_id is detected as duplicate
    existing_reading, quality_rec, stats2 = await service.ingest_reading(reading_data, now=now)

    assert stats2.total_received == 1
    assert stats2.accepted == 0
    assert stats2.rejected == 1
    assert stats2.duplicate == 1
    assert quality_rec is not None
    assert quality_rec.flagged_quality == QualityEnum.DUPLICATE.value
    assert quality_rec.anomaly_score == 1.0


@pytest.mark.asyncio
async def test_telemetry_ingestion_anomalous_reading(db_session):
    """Verify anomalous reading exceeding physical range is stored but flagged in quality record."""
    service = TelemetryService(db_session)
    now = datetime.now(timezone.utc)

    bld = Building(name="Tower Three", code="TW3-INGEST", number_of_floors=5)
    db_session.add(bld)
    await db_session.flush()

    source = await service.register_source(
        TelemetrySourceCreate(
            source_identifier="VIB-INGEST-01",
            name="Vibration Sensor 01",
            source_type=SourceTypeEnum.ACCELEROMETER,
            building_id=bld.id,
            sampling_rate_hz=50.0,
            status="ONLINE",
        )
    )

    # Vibration 5000 Hz exceeds max plausible range (1000 Hz)
    reading_data = TelemetryReadingCreate(
        source_id=source.id,
        building_id=bld.id,
        metric="vibration_hz",
        value=5000.0,
        unit="Hz",
        timestamp=now,
        event_id="EVT-ANOM-01",
    )

    reading, quality_rec, stats = await service.ingest_reading(reading_data, now=now)

    assert reading.quality == QualityEnum.ANOMALOUS.value
    assert stats.anomalous == 1
    assert quality_rec is not None
    assert quality_rec.flagged_quality == QualityEnum.ANOMALOUS.value
    assert quality_rec.anomaly_score >= 0.90


@pytest.mark.asyncio
async def test_telemetry_batch_ingestion(db_session):
    """Verify batch ingestion processes multiple readings and generates batch statistics."""
    service = TelemetryService(db_session)
    now = datetime.now(timezone.utc)

    bld = Building(name="Tower Four", code="TW4-INGEST", number_of_floors=5)
    db_session.add(bld)
    await db_session.flush()

    source = await service.register_source(
        TelemetrySourceCreate(
            source_identifier="BATCH-SRC-01",
            name="Batch Sensor 01",
            source_type=SourceTypeEnum.ACCELEROMETER,
            building_id=bld.id,
            sampling_rate_hz=10.0,
            status="ONLINE",
        )
    )

    # 3 readings: 2 valid, 1 anomalous
    readings = [
        TelemetryReadingBase(
            metric="vibration_hz",
            value=12.0,
            unit="Hz",
            timestamp=now - timedelta(seconds=2),
            event_id="EVT-B-01",
            metadata_json={"source_id": str(source.id)},
        ),
        TelemetryReadingBase(
            metric="vibration_hz",
            value=14.0,
            unit="Hz",
            timestamp=now - timedelta(seconds=1),
            event_id="EVT-B-02",
            metadata_json={"source_id": str(source.id)},
        ),
        TelemetryReadingBase(
            metric="vibration_hz",
            value=9999.0,  # Anomalous
            unit="Hz",
            timestamp=now,
            event_id="EVT-B-03",
            metadata_json={"source_id": str(source.id)},
        ),
    ]

    batch_data = TelemetryBatchCreate(
        batch_identifier="BATCH-20260918-01",
        building_id=bld.id,
        readings=readings,
    )

    batch, stats = await service.ingest_batch(batch_data, now=now)

    assert batch.id is not None
    assert batch.processing_duration_ms is not None
    assert stats.total_received == 3
    assert stats.accepted == 3  # 2 valid + 1 anomalous persisted
    assert stats.anomalous == 1
    assert stats.rejected == 0


@pytest.mark.asyncio
async def test_telemetry_service_aggregation_and_health(db_session):
    """Verify aggregated telemetry and source health service query methods."""
    service = TelemetryService(db_session)
    now = datetime.now(timezone.utc)

    bld = Building(name="Tower Five", code="TW5-INGEST", number_of_floors=5)
    db_session.add(bld)
    await db_session.flush()

    source = await service.register_source(
        TelemetrySourceCreate(
            source_identifier="HEALTH-SRC-01",
            name="Health Sensor 01",
            source_type=SourceTypeEnum.TEMPERATURE,
            building_id=bld.id,
            sampling_rate_hz=1.0,
            status="ONLINE",
        )
    )

    base_time = datetime(2026, 9, 18, 12, 0, 0, tzinfo=timezone.utc)
    # Ingest 5 readings all within the [12:00:00, 12:00:10) window
    for i in range(5):
        await service.ingest_reading(
            TelemetryReadingCreate(
                source_id=source.id,
                building_id=bld.id,
                metric="temperature_celsius",
                value=20.0 + i,
                unit="C",
                timestamp=base_time + timedelta(seconds=i),
                event_id=f"EVT-H-{i}",
            ),
            now=base_time + timedelta(seconds=i),
        )

    # Query aggregation
    aggs = await service.get_aggregated_telemetry(
        building_id=bld.id,
        metric="temperature_celsius",
        bucket=AggregationBucket.TEN_SECONDS,
        baseline_value=20.0,
    )
    assert len(aggs) == 1
    assert aggs[0].count == 5
    assert aggs[0].mean_value == 22.0

    # Query source health
    health = await service.get_source_health(source.id, window_seconds=60.0, now=base_time + timedelta(seconds=5))
    assert health.source_id == source.id
    assert health.total_readings == 5
    assert health.valid_readings == 5
    assert health.error_rate == 0.0
    assert health.is_healthy is True
