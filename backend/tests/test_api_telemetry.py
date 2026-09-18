"""API tests for Telemetry Ingestion, Queries, Source Health, Quality & Aggregations."""

import uuid
from datetime import datetime, timezone
from starlette.testclient import TestClient


def test_telemetry_pipeline_api(client: TestClient):
    """Verify complete end-to-end telemetry lifecycle via REST API."""
    # 1. Create Building
    bld_code = f"BLD-{uuid.uuid4().hex[:6].upper()}"
    bld_resp = client.post("/api/v1/buildings", json={"name": "Telemetry Hub", "code": bld_code, "number_of_floors": 5})
    assert bld_resp.status_code == 201
    bld_id = bld_resp.json()["id"]

    # 2. Register Telemetry Source
    src_ident = f"SRC-{uuid.uuid4().hex[:6].upper()}"
    src_payload = {
        "source_identifier": src_ident,
        "name": "Base Column Strain Sensor",
        "source_type": "STRAIN_GAUGE",
        "building_id": bld_id,
        "status": "ONLINE",
        "reliability_score": 1.0,
        "sampling_rate_hz": 50.0,
    }
    src_resp = client.post("/api/v1/telemetry/sources", json=src_payload)
    assert src_resp.status_code == 201
    src_id = src_resp.json()["id"]

    # 3. Source Details & Health
    health_resp = client.get(f"/api/v1/telemetry/sources/{src_id}/health")
    assert health_resp.status_code == 200
    assert health_resp.json()["status"] == "ONLINE"

    # 4. Ingest Single Telemetry Reading
    event_id_1 = f"EVT-{uuid.uuid4().hex[:8].upper()}"
    reading_payload = {
        "source_id": src_id,
        "building_id": bld_id,
        "metric": "strain",
        "value": 450.5,
        "unit": "microstrain",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_id": event_id_1,
        "quality": "VALID",
    }
    ingest_resp = client.post("/api/v1/telemetry/ingest", json=reading_payload)
    assert ingest_resp.status_code == 201
    res_data = ingest_resp.json()
    assert res_data["reading"]["event_id"] == event_id_1
    assert res_data["statistics"]["accepted"] == 1

    # 5. Duplicate Event Ingestion (Deterministic duplicate prevention)
    dup_resp = client.post("/api/v1/telemetry/ingest", json=reading_payload)
    assert dup_resp.status_code == 201
    dup_data = dup_resp.json()
    assert dup_data["statistics"]["duplicate"] == 1
    assert dup_data["quality_record"] is not None
    assert dup_data["quality_record"]["flagged_quality"] == "DUPLICATE"

    # 6. Ingest Telemetry Batch
    batch_ident = f"BATCH-{uuid.uuid4().hex[:6].upper()}"
    batch_payload = {
        "batch_identifier": batch_ident,
        "building_id": bld_id,
        "readings": [
            {
                "metric": "strain",
                "value": 460.0,
                "unit": "microstrain",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event_id": f"EVT-B1-{uuid.uuid4().hex[:6]}",
                "quality": "VALID",
            },
            {
                "metric": "strain",
                "value": 470.0,
                "unit": "microstrain",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event_id": f"EVT-B2-{uuid.uuid4().hex[:6]}",
                "quality": "VALID",
            },
        ],
    }
    batch_resp = client.post("/api/v1/telemetry/batch", json=batch_payload)
    assert batch_resp.status_code == 201
    batch_data = batch_resp.json()
    assert batch_data["statistics"]["accepted"] == 2

    # 7. Query Readings with Pagination & Filter
    readings_resp = client.get(f"/api/v1/telemetry/readings?building_id={bld_id}&metric=strain&limit=10")
    assert readings_resp.status_code == 200
    paged = readings_resp.json()
    assert paged["total"] >= 3
    assert len(paged["items"]) >= 3

    # 8. Query Quality Records
    quality_resp = client.get(f"/api/v1/telemetry/quality-records?source_id={src_id}")
    assert quality_resp.status_code == 200
    q_paged = quality_resp.json()
    assert q_paged["total"] >= 1

    # 9. Query Aggregations
    aggr_resp = client.get(f"/api/v1/telemetry/aggregations?building_id={bld_id}&metric=strain&bucket=1m")
    assert aggr_resp.status_code == 200
    aggr_data = aggr_resp.json()
    assert isinstance(aggr_data, list)
