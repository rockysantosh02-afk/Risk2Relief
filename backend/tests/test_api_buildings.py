"""API tests for Buildings, Floors, Zones, and Nodes."""

import uuid
import pytest
from starlette.testclient import TestClient


def test_building_crud_and_hierarchy_api(client: TestClient):
    """Verify building creation, retrieval, update, hierarchy, and deletion via REST API."""
    unique_code = f"BLD-{uuid.uuid4().hex[:6].upper()}"

    # 1. Create Building
    create_payload = {
        "name": "Titan Center",
        "code": unique_code,
        "description": "High-rise digital-twin facility",
        "location": "Sector 4",
        "status": "OPERATIONAL",
        "number_of_floors": 12,
        "metadata_json": {"seismic_zone": "4"},
    }
    resp = client.post("/api/v1/buildings", json=create_payload)
    assert resp.status_code == 201, resp.text
    bld_data = resp.json()
    bld_id = bld_data["id"]
    assert bld_data["code"] == unique_code
    assert bld_data["number_of_floors"] == 12

    # 2. Get Building
    get_resp = client.get(f"/api/v1/buildings/{bld_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "Titan Center"

    # 3. List Buildings (paginated)
    list_resp = client.get("/api/v1/buildings?page=1&limit=10")
    assert list_resp.status_code == 200
    paged = list_resp.json()
    assert "items" in paged
    assert paged["total"] >= 1
    assert any(b["id"] == bld_id for b in paged["items"])

    # 4. Update Building
    update_payload = {"name": "Titan Center Tower", "status": "MAINTENANCE"}
    upd_resp = client.put(f"/api/v1/buildings/{bld_id}", json=update_payload)
    assert upd_resp.status_code == 200
    assert upd_resp.json()["name"] == "Titan Center Tower"
    assert upd_resp.json()["status"] == "MAINTENANCE"

    # 5. Add Floor
    floor_payload = {
        "floor_number": 1,
        "name": "Ground Level",
        "elevation_meters": 0.0,
    }
    floor_resp = client.post(f"/api/v1/buildings/{bld_id}/floors", json=floor_payload)
    assert floor_resp.status_code == 201, floor_resp.text
    floor_id = floor_resp.json()["id"]

    # 6. Add Zone
    zone_payload = {
        "zone_code": "Z-CORE",
        "name": "Central Core",
        "zone_type": "CORE",
        "area_sqm": 450.0,
    }
    zone_resp = client.post(f"/api/v1/floors/{floor_id}/zones", json=zone_payload)
    assert zone_resp.status_code == 201
    zone_id = zone_resp.json()["id"]

    # 7. Add Structural Node
    node_payload = {
        "building_id": bld_id,
        "floor_id": floor_id,
        "zone_id": zone_id,
        "node_code": "COL-01",
        "node_type": "COLUMN",
        "position_x": 5.0,
        "position_y": 5.0,
        "position_z": 0.0,
    }
    node_resp = client.post("/api/v1/structural-nodes", json=node_payload)
    assert node_resp.status_code == 201
    assert node_resp.json()["node_code"] == "COL-01"

    # 8. Add In-Silico Anti-Gravity Node (Testing strict simulation invariant)
    ag_identifier = f"AG-{uuid.uuid4().hex[:6].upper()}"
    ag_payload = {
        "building_id": bld_id,
        "zone_id": zone_id,
        "node_identifier": ag_identifier,
        "name": "Digital Twin Node 1",
        "position_x": 5.0,
        "position_y": 5.0,
        "position_z": 0.0,
        "nominal_field_strength_kn": 550.0,
        "operating_state": "SIMULATED",
    }
    ag_resp = client.post("/api/v1/antigravity-nodes", json=ag_payload)
    assert ag_resp.status_code == 201
    ag_data = ag_resp.json()
    assert ag_data["node_identifier"] == ag_identifier
    # Strict Digital-Twin Invariant Check:
    assert ag_data["is_simulated"] == "true"

    # 9. Get Building Hierarchy
    hier_resp = client.get(f"/api/v1/buildings/{bld_id}/hierarchy")
    assert hier_resp.status_code == 200
    hier = hier_resp.json()
    assert len(hier["floors"]) >= 1
    assert len(hier["floors"][0]["zones"]) >= 1

    # 10. Delete Building
    del_resp = client.delete(f"/api/v1/buildings/{bld_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["deleted"] is True
