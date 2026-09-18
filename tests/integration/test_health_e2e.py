"""Integration tests for Risk2Relief services.

Validates end-to-end contract compliance for the health and digital-twin simulation endpoints.
"""

import sys
from pathlib import Path
import pytest
from starlette.testclient import TestClient

# Add project root and backend to path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "backend"))

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_e2e_health_contract(client):
    """Ensure root and v1 health endpoints provide consistent, valid JSON payloads."""
    root_res = client.get("/health")
    assert root_res.status_code == 200
    root_data = root_res.json()

    v1_res = client.get("/api/v1/health")
    assert v1_res.status_code == 200
    v1_data = v1_res.json()

    assert root_data["service"] == v1_data["service"] == "risk2relief-api"
    assert "database" in root_data["dependencies"]
    assert "redis" in root_data["dependencies"]


def test_e2e_digital_twin_safety_guarantees(client):
    """Ensure digital-twin endpoint asserts strict hardware isolation invariants."""
    res = client.get("/api/v1/simulation/status")
    assert res.status_code == 200
    data = res.json()

    assert data["mode"] == "in-silico-only"
    assert data["safety_boundary"]["hardware_actuators_allowed"] is False
    assert data["safety_boundary"]["gravity_modifying_hardware_allowed"] is False
