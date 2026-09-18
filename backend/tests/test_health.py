"""Unit tests for Risk2Relief health and safety boundary endpoints."""

def test_root_health_endpoint(client):
    """Verify that GET /health returns 200 with structured status and dependencies."""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert data["status"] in ("ok", "degraded")
    assert data["service"] == "risk2relief-api"
    assert "version" in data
    assert "timestamp" in data
    assert "dependencies" in data

    deps = data["dependencies"]
    assert "database" in deps
    assert "redis" in deps

    # Ensure no secrets or connection strings are leaked
    raw_text = response.text.lower()
    assert "password" not in raw_text
    assert "postgresql://" not in raw_text
    assert "redis://" not in raw_text


def test_api_v1_health_endpoint(client):
    """Verify that GET /api/v1/health returns 200 with matching contract."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200

    data = response.json()
    assert data["service"] == "risk2relief-api"
    assert "dependencies" in data
    assert "database" in data["dependencies"]
    assert "redis" in data["dependencies"]


def test_simulation_safety_boundary_endpoint(client):
    """Verify that the digital-twin simulation enforces in-silico isolation."""
    response = client.get("/api/v1/simulation/status")
    assert response.status_code == 200

    data = response.json()
    assert data["mode"] == "in-silico-only"
    assert "safety_boundary" in data

    boundary = data["safety_boundary"]
    assert boundary["subsystem"] == "physics_simulation_digital_twin"
    assert boundary["simulation_only"] is True
    assert boundary["hardware_actuators_allowed"] is False
    assert boundary["gravity_modifying_hardware_allowed"] is False
    assert boundary["direct_control_commands_allowed"] is False


def test_service_discovery_root(client):
    """Verify GET / metadata discovery."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "risk2relief-api"
    assert data["health"] == "/health"
