# Risk2Relief: System Safety Boundaries & Physics Simulation Invariants

## 1. Architectural System Boundary

Risk2Relief models structural loads and hazard mitigation through a real-time digital-twin architecture. Within this system, the "anti-gravity" compensation model represents a theoretical physics simulation designed to calculate ideal load redistributions across building structural members.

### Invariant Definitions:
1. **IN-SILICO ISOLATION:**
   The anti-gravity component exists strictly as mathematical models running inside the backend simulation engine. It produces virtual load matrices, deflection estimates, and stress curves.
2. **NO HARDWARE RECEPTORS:**
   The platform neither contains nor provides drivers, protocols, or connection interfaces for real gravity-modifying hardware.
3. **READ-ONLY TELEMETRY INTEGRATION:**
   Physical building integrations are restricted to read-only observational data:
   - Strain gauges (measuring microstrain on structural columns)
   - Accelerometers and seismometers (measuring peak ground acceleration)
   - Temperature sensors (measuring thermal expansion)
   - Laser inclinometers (measuring angular building deflection)
4. **SAFETY INTERLOCK AUTOMATION:**
   If simulation calculations or physical sensor telemetry detect stress exceeding tolerance thresholds (`MAX_STRUCTURAL_STRESS_TOLERANCE_MPA > 450.0`), the system triggers an emergency interlock trip (`TRIPPED`), dispatching operator alerts while guaranteeing no physical actuators can be commanded.

---

## 2. Hard Architectural Safeguards

In `backend/app/core/config.py` and `backend/app/services/simulation_engine.py`, the following runtime safeguards are actively enforced:

```python
# System safety barrier
ENABLE_HARDWARE_ACTUATION = False

if settings.ENABLE_HARDWARE_ACTUATION:
    logger.critical("SAFETY VIOLATION DETECTED: Hardware actuation flag was enabled!")
    raise RuntimeError("Safety invariant breached: Hardware actuation is forbidden.")
```

---

## 3. Threat Model & Prohibited Capabilities

The following mechanisms are categorically forbidden from implementation:
- Actuator-control endpoints or RPC protocols.
- Force-generating hardware drivers.
- Direct building control or automated structural manipulation.
- Remote control override bypassing safety interlocks.
- Unauthenticated simulation overrides.

Any change attempting to bypass these barriers violates core system integrity.
