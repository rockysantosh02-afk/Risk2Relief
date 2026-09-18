# Risk2Relief: Platform Architecture & Domain Model (Phase 2)

## 1. System Overview

Risk2Relief is a building-management digital-twin platform engineered to ingest high-frequency sensor telemetry, model structural behaviors under environmental loads, and calculate optimal risk mitigation scenarios within an isolated in-silico simulation environment.

```
+-----------------------------------------------------------------------------------+
|                              Risk2Relief Platform                                 |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  [ Frontend (React + TS + Vite) ]  <--- HTTP / WebSockets --->  [ FastAPI Core ]  |
|         │                                                              │          |
|         ▼                                                              ▼          |
|  [ Zustand State / React Query ]                              [ Layered Services ]|
|                                                                        │          |
|                                       ┌────────────────────────────────┴───────┐  |
|                                       ▼                                        ▼  |
|                            [ Health & Core Services ]             [ In-Silico Engine ]
|                                       │                                        │  |
|                                       ▼                                        │  |
|                            [ Repositories / DAOs ]                             │  |
|                                       │                                        │  |
|                                       ▼                                        │  |
|                       [ PostgreSQL 16 ] & [ Redis 7 ]                          │  |
|                                                                                │  |
|  =========================== SYSTEM SAFETY BARRIER =========================== │  |
|  [ Physical Sensor Ingestion (Read-Only) ]  ───►  [ Digital-Twin Telemetry ]   │  |
|  [ Physical Actuator Command Pipeline ]     ───X  [ HARDWARE CONTROL FORBIDDEN ]  |
+-----------------------------------------------------------------------------------+
```

---

## 2. Layered Architecture

All platform functionality strictly adheres to the clean four-tier flow:

```
Client / Ingestion Request
            │
            ▼
API Layer (`app/api/v1/`)
            │  - Pydantic v2 validation & error formatting
            │  - Authentication & HTTP status handling
            ▼
Domain Service Layer (`app/services/`)
            │  - Business rules, deduplication, & threshold validation
            │  - Safety boundary assertions (rejection of hardware actuation)
            │  - Orchestration across multiple repositories
            ▼
Repository Layer (`app/repositories/`)
            │  - Data access patterns & query optimization
            │  - Eager loading (selectinload) to eliminate N+1 queries
            ▼
Persistence Layer (PostgreSQL 16 & Redis 7)
```

---

## 3. Entity-Relationship & Domain Model (Phase 2)

The platform persistence model is organized across three primary domains:

```
                              [ Building ]
                             /     │      \
                            /      │       \
            1:N (Cascading)/   1:N │        \ 1:N (Cascading)
                          ▼        │         ▼
          [ BuildingFloor ]        │   [ AntiGravityNode ]
                 │                 │    (In-Silico Simulated Only)
             1:N │                 │
                 ▼                 │
          [ BuildingZone ]         │
                 │                 │
             1:N │                 │
                 ▼                 │
        [ StructuralNode ]         │
                 ▲                 │
             N:1 │                 ▼
        [ TelemetrySource ] ◄──────┘
                 │
             1:N │
                 ▼
        [ TelemetryReading ] ── (1:N) ──► [ TelemetryQualityRecord ]
                 ▲
             N:1 │
        [ TelemetryBatch ]
```

### 3.1 Building Domain
- **`Building`**: Primary facility record (`id`, `code`, `name`, `status`, `number_of_floors`, `location`, `metadata_json`).
- **`BuildingFloor`**: Elevation levels within a building (`floor_number`, `elevation_meters`). Enforces `UNIQUE(building_id, floor_number)`.
- **`BuildingZone`**: Spatial subdivisions (`zone_code`, `zone_type`, `area_sqm`). Enforces `UNIQUE(floor_id, zone_code)`.
- **`StructuralNode`**: Structural points (`COLUMN`, `BEAM`, `SLAB`, `FOUNDATION`, `SENSOR_NODE`). Positioned via 3D coordinates `(x, y, z)`.
- **`AntiGravityNode`**: Digital-twin simulated compensation nodes. **Strict invariant**: `is_simulated="true"`. Represents mathematical load redistribution points without hardware controllers.

### 3.2 Telemetry Domain
- **`TelemetrySource`**: Sensor identities (`STRAIN_GAUGE`, `ACCELEROMETER`, `TEMPERATURE`, `LOAD_SENSOR`, `INCLINOMETER`, `PRESSURE`, `AIR_QUALITY`, `SIMULATOR`).
- **`TelemetryReading`**: Observations (`metric`, `value`, `unit`, `timestamp`, `event_id`, `quality`).
  - **Idempotency & Deduplication**: Enforces `UNIQUE(source_id, event_id)`.
  - **Composite Indexes**: `(building_id, metric, timestamp)`, `(source_id, timestamp)`, `(quality, timestamp)` for high-throughput time-series aggregation.
- **`TelemetryBatch`**: High-throughput packet envelopes with processing metrics.
- **`TelemetryQualityRecord`**: Audit trail capturing validation incidents (`VALID`, `INVALID`, `STALE`, `DUPLICATE`, `ANOMALOUS`, `MISSING`).

### 3.3 Configuration & Simulation Scenario Domain
- **`BuildingConfiguration`**: Operational retention, buffer sizes, and timezones. Versioned per building.
- **`GravityConfiguration`**: In-silico simulation parameters (`target_gravity_offset_percentage`, `max_compensation_kn`, `field_distribution_algorithm`). Enforces `in_silico_only=True` and `hardware_actuation_enabled=False`.
- **`SafetyThresholdConfiguration`**: Tensile/compressive stress, deflection, and vibration thresholds. Requires `warning_threshold_percentage < interlock_trip_threshold_percentage`.
- **`EnvironmentalConfiguration`**: Thermal expansion, ambient bounds, and seismic codes.
- **`SimulationScenario`**: Dynamic disturbance scenarios (`NORMAL`, `NODE_FAILURE`, `FIELD_IMBALANCE`, `STRUCTURAL_OVERLOAD`, `TELEMETRY_FAILURE`, `POWER_FAILURE`, `EMERGENCY`).

---

## 4. Digital-Twin System Safety Boundary

### Non-Negotiable Invariants:
1. **Mathematical Isolation**: All anti-gravity and gravitational mitigation calculations are strictly software simulations running on in-memory tensors.
2. **Zero Actuation**: The platform neither contains, allows, nor exposes interfaces or commands to operate real hardware actuators.
3. **Read-Only Telemetry**: Real-world integrations are restricted to telemetry sensor ingestion and read-only interlock trip alerts.
4. **Independent Architecture**: No foreign architectures (Flutter, Firebase/Firestore, mobile app frameworks) are permitted.

---

## 5. Telemetry Processing & Intelligence Subsystem (Phase 3)

### 5.1 Deterministic Validation Engine (`app/telemetry/validation.py`)
Deterministic, rule-based validation enforcing metric specifications, unit compatibility, physical boundaries, and clock skew limits without black-box ML models. Rejection errors output machine-readable codes (`ERR_MISSING_FIELD`, `ERR_UNKNOWN_METRIC`, `ERR_INVALID_UNIT`, `ERR_FUTURE_TIMESTAMP`, `ERR_STALE_TIMESTAMP`, `ERR_PHYSICAL_RANGE_EXCEEDED`, `ERR_DUPLICATE_EVENT`, `ERR_UNKNOWN_SOURCE`).

### 5.2 Multi-Resolution Aggregator (`app/telemetry/aggregation.py`)
Computes temporal statistical windows across 5 resolution buckets (`1s`, `10s`, `1m`, `5m`, `15m`). Evaluates min, max, mean, median, standard deviation, and sample counts, alongside derived indicators including 5-period moving averages, rate of change (first derivative), and baseline deviation percentages.

### 5.3 Source Health & Explainable Reliability Engine (`app/telemetry/source_health.py`)
Calculates source-level operational reliability scores $[0.0, 1.0]$ based on availability, accuracy, anomaly rate, and timestamp freshness, incorporating status penalties for offline or faulted sensors. Every score provides a detailed mathematical component explanation.

### 5.4 Seeded Synthetic Telemetry Simulator (`app/telemetry/simulator.py`)
Generates reproducible sensor streams across 8 disturbance scenarios (`NORMAL`, `INCREASING_LOAD`, `STRUCTURAL_STRESS`, `SENSOR_FAILURE`, `NOISY_SENSOR`, `STALE_SENSOR`, `DUPLICATE_SENSOR`, `SUDDEN_EVENT`). Feeds into the standard ingestion pipeline identically to physical telemetry.

For comprehensive architectural specifications and diagrams, see [telemetry-pipeline.md](file:///c:/Users/rocky/OneDrive/vs%20code%20project/Risk2Relief/docs/telemetry-pipeline.md).

---

## 6. Digital-Twin Physics & Structural Risk Subsystem (Phase 4)

### 6.1 Pure Gravity Computational Core (`app/physics/gravity_engine.py`)
Pure Python module independent of web or database frameworks. Computes 3D rational quadratic spatial attenuation $w(r) = 1 / (1 + (r / R_0)^2)$, active nodal force capacities, field superposition, target offset deviations, and spatial uniformity.

### 6.2 Gravity Stability Evaluator (`app/physics/stability.py`)
Assesses field stability across spatial and temporal dimensions (`NORMAL`, `WARNING`, `CRITICAL`, `UNSTABLE`). Monitors field deviation, uniformity, active node ratios, and convergence divergence to detect simulated excursions and generate `SafetyEvent` records.

### 6.3 Structural Load & Response Engine (`app/physics/structural_load.py`)
Simulation-oriented structural member load redistribution engine. Calculates member utilization ratios, estimated axial stress ($\text{MPa}$), elastic strain ($\mu\epsilon$), and safety margins under simulated gravitational relief. Explicitly tracks data provenance (`MEASURED`, `SIMULATED`, `ESTIMATED`).

### 6.4 Deterministic Structural Risk Engine (`app/physics/structural_risk.py`)
Combines utilization ($30\%$), strain ($20\%$), vibration ($15\%$), deflection ($15\%$), thermal gradient ($10\%$), and stability ($10\%$) with telemetry fidelity scaling into an explainable composite risk score $[0, 100]$ categorized as `LOW`, `MODERATE`, `HIGH`, or `CRITICAL`. Enforces non-dilutable safety floors for structural overloads.

### 6.5 Simulation Runner & Disturbance Scenarios (`app/simulation/`)
`ScenarioExecutor` and `SimulationRunner` supporting 7 disturbance scenarios (`NORMAL`, `NODE_FAILURE`, `FIELD_IMBALANCE`, `STRUCTURAL_OVERLOAD`, `TELEMETRY_FAILURE`, `POWER_FAILURE`, `EMERGENCY`). Multi-step executions and safety events are persisted via `SimulationResultService`.

For complete mathematical formulations and specifications, see [physics-simulation-engine.md](file:///c:/Users/rocky/OneDrive/vs%20code%20project/Risk2Relief/docs/physics-simulation-engine.md).

---

## 7. Safety State Machine, Anomaly Detection & Resilience Subsystem (Phase 5)

### 7.1 Deterministic Safety State Machine (`app/safety/state_machine.py`)
Deterministic finite state machine governing building operational safety across 6 states (`NORMAL`, `WARNING`, `DEGRADED`, `EMERGENCY`, `RECOVERY`, `MAINTENANCE`). Evaluates multi-modal observation vectors (gravity stability, structural risk, telemetry quality, power state, communication link, and seismic acceleration). Transitions are strictly auditable and persisted in `SafetyStateTransitionRecord`. Transition from `EMERGENCY` requires progression through `RECOVERY`.

### 7.2 Incident & Alert Subsystem (`app/safety/incidents.py`)
Manages incident lifecycle (`OPEN`, `INVESTIGATING`, `MITIGATED`, `RESOLVED`, `CLOSED`) with automatic incident creation upon escalation to `DEGRADED` or `EMERGENCY`. Generates deterministic simulated containment recommendations (e.g. simulated load rebalancing, zone egress alarms) and dispatches real-time `AlertNotification` envelopes via `AlertService`.

### 7.3 Advisory Anomaly Detection Engine (`app/safety/anomaly.py`)
Features rolling statistical Z-Score detection ($z \ge 3.0$) and a pure Python, deterministic Isolation Forest ($s(x, n) = 2^{-E(h(x))/c(n)}$) with no C-extension dependencies. Includes a benchmark evaluator for Precision, Recall, FPR, FNR, and F1. All model outputs are strictly **ADVISORY ONLY** and never trigger hardware actuators.

### 7.4 Controlled Failure Injection Framework (`app/safety/failure_injection.py`)
Resilience test harness executing 15 software, sensor, and infrastructure fault modes (including sensor flatline, duplicate streams, corrupted telemetry, stale data, source outages, network timeouts, Redis/DB/Celery fallbacks, gravity node failures, structural overloads, and seismic shocks). Verifies detection latency, safety response appropriateness, data integrity preservation, and recovery success in-silico.

For detailed transition rules and failure scenario matrices, see [safety-state-machine-and-resilience.md](file:///c:/Users/rocky/OneDrive/vs%20code%20project/Risk2Relief/docs/safety-state-machine-and-resilience.md).

