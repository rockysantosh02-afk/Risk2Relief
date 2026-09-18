"""Unit tests for Telemetry domain models, time-series indexing, and deduplication."""

import uuid
from datetime import datetime, timezone, timedelta
import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.building import Building
from app.models.telemetry import (
    TelemetrySource,
    TelemetryBatch,
    TelemetryReading,
    TelemetryQualityRecord,
)
from app.repositories.telemetry_repository import TelemetryRepository


@pytest.mark.asyncio
async def test_telemetry_source_and_reading_lifecycle(db_session):
    """Test creating a telemetry source and recording observations."""
    building = Building(name="Telemetry Tower", code="BLD-TEL-01")
    db_session.add(building)
    await db_session.flush()

    source = TelemetrySource(
        source_identifier="SRC-STR-001",
        name="Foundation Strain Sensor A",
        source_type="STRAIN_GAUGE",
        building_id=building.id,
        status="ONLINE",
    )
    db_session.add(source)
    await db_session.flush()

    now = datetime.now(timezone.utc)
    reading = TelemetryReading(
        source_id=source.id,
        building_id=building.id,
        metric="strain_microstrain",
        value=145.2,
        unit="um/m",
        timestamp=now,
        event_id="EVT-001-ALPHA",
        quality="VALID",
    )
    db_session.add(reading)
    await db_session.flush()

    assert reading.id is not None
    assert reading.metric == "strain_microstrain"


@pytest.mark.asyncio
async def test_telemetry_idempotency_duplicate_constraint(db_session):
    """Verify that duplicate (source_id, event_id) combinations violate unique constraint."""
    building = Building(name="Idempotency Lab", code="BLD-IDEM-01")
    db_session.add(building)
    await db_session.flush()

    source = TelemetrySource(
        source_identifier="SRC-IDEM-01",
        name="Test Sensor",
        source_type="ACCELEROMETER",
        building_id=building.id,
    )
    db_session.add(source)
    await db_session.flush()

    now = datetime.now(timezone.utc)
    r1 = TelemetryReading(
        source_id=source.id,
        building_id=building.id,
        metric="vibration_hz",
        value=12.4,
        unit="Hz",
        timestamp=now,
        event_id="EVT-UNIQUE-101",
    )
    db_session.add(r1)
    await db_session.flush()

    # Second reading with identical event_id for the same source
    r2 = TelemetryReading(
        source_id=source.id,
        building_id=building.id,
        metric="vibration_hz",
        value=12.4,
        unit="Hz",
        timestamp=now,
        event_id="EVT-UNIQUE-101",
    )
    db_session.add(r2)
    with pytest.raises(IntegrityError):
        await db_session.flush()


@pytest.mark.asyncio
async def test_telemetry_time_series_repository_queries(db_session):
    """Verify repository methods for time-series filtering and ordering."""
    building = Building(name="TimeSeries Hub", code="BLD-TS-01")
    db_session.add(building)
    await db_session.flush()

    source = TelemetrySource(
        source_identifier="SRC-TS-01",
        name="Temperature Probe",
        source_type="TEMPERATURE",
        building_id=building.id,
    )
    db_session.add(source)
    await db_session.flush()

    repo = TelemetryRepository(db_session)
    now = datetime.now(timezone.utc)

    # Insert sequential readings
    readings = []
    for i in range(5):
        r = TelemetryReading(
            source_id=source.id,
            building_id=building.id,
            metric="temperature_celsius",
            value=20.0 + i,
            unit="C",
            timestamp=now + timedelta(seconds=i * 10),
            event_id=f"EVT-TS-{i}",
            quality="VALID",
        )
        readings.append(r)

    await repo.bulk_add_readings(readings)

    # Query with filter
    results = await repo.query_readings(
        building_id=building.id,
        metric="temperature_celsius",
        limit=10,
    )

    assert len(results) == 5
    # Should be ordered desc by timestamp
    assert results[0].value == 24.0
    assert results[-1].value == 20.0
