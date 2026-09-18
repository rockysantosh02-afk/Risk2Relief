# Risk2Relief: Safety State Machine, Anomaly Detection & Resilience Framework (Phase 5)

## 1. System Safety Boundary & Foundational Invariants

The Risk2Relief platform operates strictly as an **in-silico digital-twin simulation and monitoring system**.
All analytical models, state machine transitions, incident escalations, and failure injection scenarios adhere to the following safety invariants:

1. **In-Silico Simulation Only**: Simulated anti-gravity force vectors and structural risk mitigations exist purely as mathematical tensors within computational memory.
2. **Zero Actuator Hardware Control**: The platform contains no drivers, interfaces, or execution pathways capable of operating physical building actuators or gravity hardware.
3. **Advisory Analytics Boundary**: Machine learning and statistical anomaly detectors are strictly **ADVISORY ONLY**. Under no circumstances may an automated model output directly trigger or authorize physical interventions.
4. **Resilience Fault Envelopes**: All failure injection scenarios are software, network, and data simulation faults executed safely in-memory without impacting real-world infrastructure.

---

## 2. Deterministic Safety State Machine (`app/safety/state_machine.py`)

The safety state machine provides deterministic, auditable governance over building operational safety. It monitors multi-modal inputs and executes transitions based on explicit guard conditions.

```
       ┌───────────────────────────────┐
       │          MAINTENANCE          │
       └──────┬─────────────────▲──────┘
              │                 │
              ▼                 │
       ┌──────────────┐         │
       │    NORMAL    │─────────┤
       └──────┬───────┘         │
              │                 │
              ▼                 │
       ┌──────────────┐         │
       │   WARNING    │─────────┤
       └──────┬───────┘         │
              │                 │
              ▼                 │
       ┌──────────────┐         │
       │   DEGRADED   │─────────┤
       └──────┬───────┘         │
              │                 │
              ▼                 │
       ┌──────────────┐         │
       │  EMERGENCY   │         │
       └──────┬───────┘         │
              │                 │
              ▼                 │
       ┌──────────────┐         │
       │   RECOVERY   │─────────┘
       └──────┬───────┘
              │
              ▼
           NORMAL
```

### 2.1 State Matrix & Allowable Transitions

| From State | Permitted Target States | Transition Rules & Constraints |
|---|---|---|
| `NORMAL` | `WARNING`, `MAINTENANCE`, `EMERGENCY` (override) | Nominal baseline. Direct jump to `EMERGENCY` permitted only for catastrophic hazards (e.g. seismic PGA $\ge 0.40g$, sudden structural collapse). |
| `WARNING` | `NORMAL`, `DEGRADED`, `MAINTENANCE` | Moderate anomalies detected. Escalates to `DEGRADED` if metrics deteriorate, returns to `NORMAL` if resolved. |
| `DEGRADED` | `WARNING`, `EMERGENCY`, `RECOVERY`, `MAINTENANCE` | Critical subsystem fault. Escalates to `EMERGENCY` on instability, de-escalates to `WARNING` or enters `RECOVERY`. |
| `EMERGENCY` | `RECOVERY` | **Strict Invariant**: Direct transition from `EMERGENCY` to `NORMAL` or `WARNING` is strictly forbidden. The system must enter `RECOVERY` for structural verification. |
| `RECOVERY` | `NORMAL`, `DEGRADED`, `EMERGENCY`, `MAINTENANCE` | Diagnostic inspection phase. Transitions to `NORMAL` once all metrics verify nominal for a stable duration. |
| `MAINTENANCE` | `NORMAL`, `RECOVERY` | Manual operator isolation or scheduled calibration mode. |

### 2.2 Input Determinism & Multi-Modal Guards

The state machine evaluates a structured `SafetyInputs` payload across 6 dimensions:

```python
@dataclass
class SafetyInputs:
    gravity_stability: str = "NORMAL"         # NORMAL, WARNING, CRITICAL, UNSTABLE
    structural_risk: str = "LOW"               # LOW, MODERATE, HIGH, CRITICAL
    telemetry_reliability: float = 1.0         # 0.0 to 1.0
    power_state: str = "NOMINAL"               # NOMINAL, BACKUP, CRITICAL_LOW, OFFLINE
    communication_state: str = "CONNECTED"     # CONNECTED, DEGRADED, DISCONNECTED
    environmental_conditions: Dict[str, Any]   # e.g., {"seismic_pga_g": 0.55}
    is_maintenance_mode: bool = False
```

1. **Maintenance Priority**: If `is_maintenance_mode=True`, the target state is immediately `MAINTENANCE`.
2. **Emergency Guards**:
   - `gravity_stability == "UNSTABLE"` OR
   - `structural_risk == "CRITICAL"` (utilization $\ge 100\%$) OR
   - `power_state == "OFFLINE"` OR
   - `environmental_conditions.seismic_pga_g >= 0.40`
   $\implies$ Target: `EMERGENCY`.
3. **Degraded Guards**:
   - `gravity_stability == "CRITICAL"` OR
   - `structural_risk == "HIGH"` OR
   - `power_state == "CRITICAL_LOW"` OR
   - `communication_state == "DISCONNECTED"` OR
   - `telemetry_reliability < 0.40`
   $\implies$ Target: `DEGRADED` (or `RECOVERY` if coming from `EMERGENCY`).
4. **Warning Guards**:
   - `gravity_stability == "WARNING"` OR
   - `structural_risk == "MODERATE"` OR
   - `power_state == "BACKUP"` OR
   - `communication_state == "DEGRADED"` OR
   - `telemetry_reliability < 0.75`
   $\implies$ Target: `WARNING`.
5. **Recovery Progression**:
   - When all metrics return to baseline from `EMERGENCY`, target is `RECOVERY`.
   - When in `RECOVERY` with verified nominal inputs, target is `NORMAL`.

---

## 3. Incident & Alert Management Subsystem (`app/safety/incidents.py`)

### 3.1 Database Persistence (`app/models/safety.py`)
- **`SafetyStateTransitionRecord`**: Immutable log of every state transition containing `building_id`, `from_state`, `to_state`, `trigger_reason`, `inputs_snapshot_json`, `transitioned_at`, and `is_valid_transition`. Indexed on `(building_id, transitioned_at)`.
- **`Incident`**: Tracks safety lifecycle events (`OPEN`, `INVESTIGATING`, `MITIGATED`, `RESOLVED`, `CLOSED`) with `incident_code`, `severity` (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), `initial_safety_state`, `escalated_safety_state`, `root_cause`, `evidence_json`, and `recommended_simulated_response`. Indexed on `(building_id, status)` and `(severity, created_at)`.

### 3.2 Automatic Incident Escalation
When a building transitions into `DEGRADED` or `EMERGENCY`:
1. `SafetyService` automatically creates an `Incident` record with severity `HIGH` or `CRITICAL`.
2. `IncidentService.generate_containment_recommendation` deterministically drafts containment actions:
   - *Emergency*: Trigger simulated localized zone egress alarms; shed non-essential simulated live loads; transfer active anti-gravity nodal offload vectors to foundation-bearing columns.
   - *Degraded*: Increase sensor telemetry polling to 50 Hz; rebalance simulated anti-gravity force vectors away from degraded quadrants; schedule non-destructive ultrasonic column testing.
3. `AlertService` dispatches real-time `AlertNotification` envelopes for dashboard feeds and audit logs.

---

## 4. Advisory Anomaly Detection Engine (`app/safety/anomaly.py`)

### 4.1 Rolling Statistical Z-Score Detector
Maintains a moving window buffer ($N=30$) of scalar metric observations, computing sample mean $\mu$ and standard deviation $\sigma$:
$$z = \frac{|x - \mu|}{\sigma}$$
Anomalies trigger when $z \ge 3.0$. Scores are normalized using a sigmoid:
$$s(z) = \frac{1}{1 + e^{-0.8(z - z_{\text{thresh}})}}$$

### 4.2 Pure Python Deterministic Isolation Forest
Implemented without external C-extensions or scikit-learn dependencies. Uses seeded random partitioning over multidimensional telemetry vectors:
- Binary isolation trees recursively partition bounding hypercubes until sample isolation or max depth $d_{\text{max}} = \lceil\log_2(\text{subsample\_size})\rceil$.
- Average path length $c(n)$ of unsuccessful searches in binary search trees:
  $$c(n) = 2(\ln(n-1) + 0.5772156649) - \frac{2(n-1)}{n}$$
- Anomaly score calculation:
  $$s(x, n) = 2^{-\frac{E(h(x))}{c(n)}}$$
  Observations with $s(x, n) \ge 0.60$ are classified as anomalies.

### 4.3 Benchmark Evaluation Framework
Evaluates detector performance against labeled datasets, computing:
- $\text{Precision} = \frac{TP}{TP + FP}$
- $\text{Recall} = \frac{TP}{TP + FN}$
- $\text{False Positive Rate (FPR)} = \frac{FP}{FP + TN}$
- $\text{False Negative Rate (FNR)} = \frac{FN}{FN + TP}$
- $\text{F1-Score} = 2 \cdot \frac{\text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}}$

---

## 5. Controlled Failure Injection Framework (`app/safety/failure_injection.py`)

The platform includes an automated resilience harness executing 15 software, sensor, and infrastructure fault modes:

| Scenario | Fault Simulation Description | Safety State Response | Resilience Verification |
|---|---|---|---|
| `sensor_failure` | Flatline / zero values injected | Escalates to `WARNING` | Preserves data integrity; zero data loss |
| `duplicate_sensor` | Re-transmission of identical `event_id` | Maintains state | Caught by DB unique constraint; deduplicated |
| `corrupted_telemetry` | Out-of-bounds physical values | Escalates to `DEGRADED` | Invalid readings quarantined in quality audit |
| `stale_telemetry` | Latency skew $> 3600\text{s}$ | Escalates to `WARNING` | Flagged as STALE; rejected from time-series aggregates |
| `source_outage` | Sensor disconnection | Escalates to `DEGRADED` | Sensor marked OFFLINE; health score penalized |
| `network_timeout` | Gateway packet loss | Escalates to `WARNING` | Graceful timeout; automatic retry |
| `redis_failure` | Cache layer down | Maintains integrity | Direct DB query fallback |
| `database_failure` | Transient connection fault | Transaction rolled back | ACID atomicity; zero corruption |
| `celery_failure` | Worker pool outage | Synchronous fallback | Tasks buffered; zero message loss |
| `gravity_node_failure` | Single simulated node tripped | Escalates to `WARNING` | Remaining nodes rebalance simulated load |
| `multiple_node_failure` | 3 of 4 simulated nodes tripped | Escalates to `DEGRADED` | Gravity stability drops to CRITICAL |
| `structural_overload` | Member stress at $120\%$ capacity | Escalates to `EMERGENCY` | Direct emergency trip triggered |
| `environmental_emergency` | Seismic ground acceleration $\text{PGA} = 0.55g$ | Escalates to `EMERGENCY` | Emergency override triggered immediately |
| `websocket_disconnect` | Client socket dropped | Maintains server state | Client auto-reconnect handshake |
| `invalid_configuration` | `hardware_actuation_enabled=True` attempt | Rejection by Safety Barrier | Config rejected; safety invariant maintained |

---

## 6. Verification Suite Summary

The test suite provides comprehensive coverage across all Phase 5 capabilities:

- `backend/tests/test_safety_state_machine.py` (9 tests): Validates state transitions, invalid transition barriers, emergency overrides, and maintenance protocols.
- `backend/tests/test_safety_anomaly.py` (4 tests): Tests statistical z-score triggers, Isolation Forest training/inference determinism, and benchmark metric calculations.
- `backend/tests/test_safety_failure_injection.py` (18 tests): Evaluates all 15 failure injection scenarios, catastrophic emergency escalations, and tamper protection.
- `backend/tests/test_safety_service_integration.py` (3 tests): Validates end-to-end async SQLite persistence of state transition records, automatic incident creation, and incident CRUD.

**Total Repository Test Results**: 103 tests passing, 0 failed.
