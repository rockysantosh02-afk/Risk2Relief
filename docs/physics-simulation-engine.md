# Risk2Relief: Physics Simulation, Anti-Gravity Digital-Twin & Structural Risk Engine

## 1. System Safety Boundary & Invariants

```
============================== SYSTEM SAFETY BOUNDARY ==============================
Risk2Relief is an IN-SILICO DIGITAL-TWIN SIMULATION PLATFORM.
1. All anti-gravity and gravitational mitigation calculations are strictly software simulations running on in-memory numerical arrays.
2. The platform DOES NOT operate, connect to, or issue commands to physical gravity actuators.
3. Real-world physical building integrations are restricted to telemetry sensor ingestion and read-only emergency notifications.
4. Calculations explicitly distinguish between MEASURED, SIMULATED, and ESTIMATED data.
5. Outputs are diagnostic simulation estimates and DO NOT constitute certified civil or structural engineering sign-offs.
====================================================================================
```

---

## 2. Architecture Overview

The Phase 4 subsystem consists of a pure computational physics core, a stability evaluator, a structural load and response engine, an explainable structural risk engine, a scenario disturbance executor, a multi-step simulation runner, and a persistence service.

```
+----------------------------------------------------------------------------------------------------+
|                                    PHASE 4 SIMULATION ARCHITECTURE                                 |
+----------------------------------------------------------------------------------------------------+
|                                                                                                    |
|  [ Scenario Executor (NORMAL, NODE_FAILURE, FIELD_IMBALANCE, OVERLOAD, etc.) ]                     |
|                                    │                                                               |
|                                    ▼                                                               |
|  [ Pure Gravity Engine: app/physics/gravity_engine.py ]                                            |
|        ├── GravityNodeState, GravityFieldState, GravitySimulationState                             |
|        ├── Spatial Influence w(r), Node Contribution, Combined Field Superposition                 |
|        └── Target Deviation, Spatial Uniformity, Temporal Stability                                |
|                                    │                                                               |
|                                    ▼                                                               |
|  [ Gravity Stability Evaluator: app/physics/stability.py ]                                        |
|        ├── Statuses: NORMAL, WARNING, CRITICAL, UNSTABLE                                           |
|        └── Deterministic Threshold Checks & SafetyEvent Generation                                 |
|                                    │                                                               |
|                                    ▼                                                               |
|  [ Structural Load Engine: app/physics/structural_load.py ]                                        |
|        ├── Dead/Live Loads (Gk, Qk) - Simulated Gravity Relief (F_relief) = Net Effective Load    |
|        ├── Structural Utilization, Estimated Stress (MPa), Estimated Strain (ue), Safety Margin     |
|        └── Explicit Data Provenance: MEASURED vs. SIMULATED vs. ESTIMATED                          |
|                                    │                                                               |
|                                    ▼                                                               |
|  [ Structural Risk Engine: app/physics/structural_risk.py ]                                        |
|        ├── Risk Levels: LOW, MODERATE, HIGH, CRITICAL                                              |
|        ├── Weighted Multi-Factor Composite Scoring (Stress, Strain, Vib, Incl, Temp, Stability)   |
|        └── Fully Explainable Factor Contributors & Safety Boundary Disclaimers                     |
|                                    │                                                               |
|                                    ▼                                                               |
|  [ Simulation Runner & Result Service: app/simulation/runner.py & app/services/simulation_service ]|
|        ├── Multi-Step Simulation Orchestration & Step Aggregation                                  |
|        └── Persistence to PostgreSQL: SimulationRun & SafetyEvent Records                          |
+----------------------------------------------------------------------------------------------------+
```

---

## 3. Pure Gravity Engine (`backend/app/physics/gravity_engine.py`)

The pure gravity engine is an independent computational module decoupled from FastAPI, PostgreSQL, Redis, Celery, and frontend dependencies.

### 3.1 Spatial Influence & Attenuation Model
Simulated anti-gravity compensation fields decay with distance according to a rational quadratic attenuation function:

$$w(r) = \frac{1}{1 + \left(\frac{r}{R_0}\right)^2}$$

Where:
- $r = \|\mathbf{x} - \mathbf{x}_{\text{node}}\| = \sqrt{(x - x_0)^2 + (y - y_0)^2 + (z - z_0)^2}$ is the 3D Euclidean distance in meters.
- $R_0$ is the characteristic influence radius (default $20.0\,\text{m}$).
- Hard cutoff boundary: $w(r) = 0$ for $r > 5 R_0$.

### 3.2 Active Nodal Force Output
Each simulated node computes active load offset capacity based on its operating state, efficiency, and health:

$$F_{\text{active}} = F_{\text{nominal}} \times \eta \times \left(\frac{H}{100}\right) \quad \text{if } \text{state} \in \{\text{"ACTIVE"}, \text{"SIMULATED"}\} \text{ else } 0.0\,\text{kN}$$

Where:
- $F_{\text{nominal}}$: Nominal rated load relief capacity in kiloNewtons ($\text{kN}$).
- $\eta \in [0.0, 1.0]$: Operational efficiency factor.
- $H \in [0.0, 100.0]$: Nodal health score.

### 3.3 Field Superposition & Spatial Metrics
At each evaluation point $\mathbf{x}$:

$$F_{\text{total}}(\mathbf{x}) = \sum_{i=1}^{N} F_{\text{active}, i} \cdot w_i(\|\mathbf{x} - \mathbf{x}_i\|)$$

$$\text{Offset}(\mathbf{x}) = \left(\frac{F_{\text{total}}(\mathbf{x})}{L_{\text{dead}}(\mathbf{x})}\right) \times 100\%$$

Spatial Uniformity is computed from the Coefficient of Variation ($\text{CoV} = \frac{\sigma}{\mu}$) of the offset percentage across all evaluation points:

$$\text{Uniformity} = \max\left(0.0, \min\left(1.0, 1.0 - \frac{\sigma}{\mu}\right)\right)$$

Target deviation measures deviation from configured baseline offset:

$$\text{Deviation} = |\mu_{\text{offset}} - \text{Target Offset}|$$

---

## 4. Gravity Stability Evaluator (`backend/app/physics/stability.py`)

The stability evaluator monitors spatial balance, nodal availability, and temporal convergence to detect simulated field instabilities.

### 4.1 Stability Classification Matrix

| Status | Deviation Threshold | Uniformity Threshold | Node Availability | Step Convergence Delta |
| :--- | :--- | :--- | :--- | :--- |
| **`NORMAL`** | $\le 3.0\%$ | $\ge 0.75$ | $\ge 90\%$ | $\le 2.0\%$ |
| **`WARNING`** | $\le 8.0\%$ | $\ge 0.50$ | $\ge 75\%$ | $\le 5.0\%$ |
| **`CRITICAL`** | $> 8.0\%$ | $< 0.50$ | $< 75\%$ | $\le 5.0\%$ |
| **`UNSTABLE`** | Any | Any | $< 50\%$ | $> 5.0\%$ (Divergence) |

### 4.2 Threshold Violations & Safety Events
When thresholds are breached, the evaluator emits machine-readable `ThresholdViolation` and `SafetyEvent` records:
- `CRITICAL_NODE_LOSS`: Triggered when active nodes drop below $50\%$.
- `FIELD_TARGET_DEVIATION_EXCEEDED`: Triggered when deviation exceeds warning limits.
- `FIELD_IMBALANCE_CRITICAL`: Triggered when spatial uniformity drops below $0.50$.
- `FIELD_DIVERGENCE_DETECTED`: Triggered when step-to-step mean offset delta exceeds $5.0\%$.

---

## 5. Structural Load & Response Engine (`backend/app/physics/structural_load.py`)

The structural engine calculates load redistribution, utilization ratios, and axial stresses across structural members under simulated gravitational compensation.

### 5.1 Formulation
1. **Net Effective Axial Load**:
   $$N_{\text{eff}} = \max(0.0, (G_k + Q_k) - F_{\text{relief}})$$
   Where $G_k$ is dead load ($\text{kN}$), $Q_k$ is live load ($\text{kN}$), and $F_{\text{relief}}$ is simulated gravity compensation ($\text{kN}$).

2. **Utilization Ratio**:
   $$U = \frac{N_{\text{eff}}}{N_{\text{capacity}}}$$

3. **Estimated Axial Stress**:
   $$\sigma = \frac{N_{\text{eff}} \times 10^{-3}}{A_{\text{cross}}} \quad (\text{MPa})$$

4. **Estimated Elastic Strain**:
   $$\epsilon = \left(\frac{\sigma}{E}\right) \times 10^{3} \quad (\mu\epsilon)$$

5. **Safety Margin**:
   $$\text{Margin} = (1.0 - U) \times 100\%$$

### 5.2 Explicit Data Provenance
Every output metric explicitly records its origin:
- `MEASURED`: Physical sensor readings (strain gauges, accelerometers, inclinometers, temperature probes).
- `SIMULATED`: Digital-twin simulated gravity compensation force ($F_{\text{relief}}$).
- `ESTIMATED`: Derived structural calculations ($N_{\text{eff}}$, $U$, $\sigma$, $\epsilon$).

---

## 6. Structural Risk Engine (`backend/app/physics/structural_risk.py`)

Combines structural responses, ambient factors, simulated field stability, and telemetry fidelity using an explainable, deterministic multi-factor model.

### 6.1 Composite Weighting Model

$$\text{Risk Score} = \sum_{j} w_j \cdot S_j + P_{\text{telemetry}}$$

| Factor | Weight ($w_j$) | Normal Range ($S \le 20$) | Elevated ($S \le 65$) | High ($S \le 90$) | Critical ($S = 100$) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Utilization Ratio** | $30\%$ | $U < 0.60$ | $0.60 \le U < 0.85$ | $0.85 \le U < 1.00$ | $U \ge 1.00$ |
| **Material Strain** | $20\%$ | $< 300\,\mu\epsilon$ | $300 - 800\,\mu\epsilon$ | $800 - 1500\,\mu\epsilon$ | $\ge 1500\,\mu\epsilon$ |
| **Dynamic Vibration** | $15\%$ | $< 15\,\text{Hz}$ | $15 - 35\,\text{Hz}$ | $35 - 60\,\text{Hz}$ | $\ge 60\,\text{Hz}$ |
| **Inclination Deflection** | $15\%$ | $< 0.05^\circ$ | $0.05 - 0.20^\circ$ | $0.20 - 0.50^\circ$ | $\ge 0.50^\circ$ |
| **Thermal Differential** | $10\%$ | $\Delta T < 15^\circ\text{C}$ | $15 - 35^\circ\text{C}$ | $> 35^\circ\text{C}$ | $> 50^\circ\text{C}$ |
| **Simulated Stability** | $10\%$ | `NORMAL` ($0$) | `WARNING` ($45$) | `CRITICAL` ($80$) | `UNSTABLE` ($100$) |

### 6.2 Limiting Condition Safety Floors
To prevent catastrophic single-point failures from being diluted by normal sensors, limiting condition floors are enforced:
- If peak member utilization $U \ge 1.00$: Risk Score is floored at $\ge 90.0$ (`CRITICAL`).
- If peak member utilization $U \ge 0.85$: Risk Score is floored at $\ge 70.0$ (`HIGH`).
- If gravity stability is `UNSTABLE`: Risk Score is floored at $\ge 90.0$ (`CRITICAL`).

### 6.3 Risk Classification Matrix
- **`LOW`** ($0.0 - 39.9$): Nominal operating condition. Continue standard monitoring.
- **`MODERATE`** ($40.0 - 69.9$): Elevated stress. Increase telemetry sampling rate to 20 Hz.
- **`HIGH`** ($70.0 - 89.9$): High stress warning. Redistribute simulated nodal offload and schedule physical NDT inspection.
- **`CRITICAL`** ($90.0 - 100.0$): Structural overload or instability. Initiate emergency zone evacuation protocol simulation.

---

## 7. Scenario Disturbance Catalog (`backend/app/simulation/scenarios.py`)

The platform implements 7 deterministic disturbance scenarios:

1. **`NORMAL`**: Baseline quiescent operation; nominal nodal outputs and design loads.
2. **`NODE_FAILURE`**: Simulated hardware failure on designated primary anti-gravity nodes ($F_{\text{active}} = 0\,\text{kN}$).
3. **`FIELD_IMBALANCE`**: Asymmetric efficiency drops ($10\%$ efficiency on selected structural wings) inducing spatial field asymmetry.
4. **`STRUCTURAL_OVERLOAD`**: Massive live load spike ($250\% - 300\%$ live load) applied across members.
5. **`TELEMETRY_FAILURE`**: Sensor corruption and high noise injection; telemetry reliability drops to $25\%$.
6. **`POWER_FAILURE`**: Widespread electrical tripping taking $75\%$ of simulated anti-gravity nodes offline.
7. **`EMERGENCY`**: Compound structural emergency: severe overload, partial nodal tripping, high vibration ($65\,\text{Hz}$), and excessive angular deflection ($0.55^\circ$).

---

## 8. Persistence Architecture

Simulation runs and safety incidents are persisted using SQLAlchemy 2.x models managed via Alembic migration `002_phase4_simulation`:
- **`simulation_runs`**: Records run metadata, duration, peak/final risk scores, stability statuses, summary metrics, and serialized time-series step snapshots.
- **`safety_events`**: Detailed audit log of every safety threshold violation, excursion severity, and trigger source.
