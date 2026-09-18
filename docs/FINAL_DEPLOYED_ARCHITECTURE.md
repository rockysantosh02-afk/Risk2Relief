# Risk2Relief Final Deployed Architecture

**System**: Risk2Relief Autonomous Parametric Climate Insurance Platform  
**Target Infrastructure**: Render Cloud (Web Service + Static Site + Managed PostgreSQL) + Firebase Auth  
**Runtime**: Python 3.12 (Backend) / Node 20+ & React 18 (Frontend)

---

## 1. Physical Infrastructure Architecture

```
[ Beneficiary Browser / Mobile Device ]
                  │
                  ▼ HTTPS
     ┌─────────────────────────────┐
     │   RENDER STATIC SITE HOST   │
     │   (React 18 + Vite SPA)     │
     │   risk2relief-frontend      │
     └──────────────┬──────────────┘
                    │
                    │ 1. User Authenticates
                    ▼
     ┌─────────────────────────────┐
     │   FIREBASE AUTHENTICATION   │
     │   Identity Provider (OAuth) │
     └──────────────┬──────────────┘
                    │
                    │ 2. Obtains JWT ID Token
                    ▼
     ┌─────────────────────────────┐
     │   RENDER FASTAPI SERVICE    │
     │   (Python 3.12 Web Service) │
     │   risk2relief-backend       │
     │                             │
     │  - Security Middlewares     │
     │  - Firebase Admin Verifier  │
     │  - Live Telemetry Pipeline  │
     │  - Isolation Forest ML      │
     │  - Dynamic Damage Engine    │
     │  - Instant Settlement       │
     └──────────────┬──────────────┘
                    │
                    │ 3. Read/Write State
                    ▼
     ┌─────────────────────────────┐
     │     RENDER POSTGRESQL       │
     │     Managed Database        │
     │     risk2relief-postgres    │
     └─────────────────────────────┘
```

---

## 2. Logical Decision Flow & Data Lifecycles

```
+-----------------------------------------------------------------------------------+
| 1. MULTI-SOURCE TELEMETRY INGESTION                                               |
|    Source A (AWS Station) | Source B (IoT Ground Radar) | Source C (Satellite IR)  |
+-----------------------------------------┬-----------------------------------------+
                                          ▼
+-----------------------------------------------------------------------------------+
| 2. VALIDATION & SANITIZATION LAYER                                                |
|    - Range Check (0 to 500 mm/h)                                                  |
|    - Calibration Drift Tolerance Check                                            |
|    - Timestamp & Coordinate Freshness                                             |
+-----------------------------------------┬-----------------------------------------+
                                          ▼
+-----------------------------------------------------------------------------------+
| 3. ADVISORY ISOLATION FOREST ML ANOMALY DETECTOR                                  |
|    - Evaluates multidimensional anomaly score                                     |
|    - Identifies potential sensor spoofing / malicious telemetry tampering        |
|    - Informs audit trail without blocking deterministic consensus                 |
+-----------------------------------------┬-----------------------------------------+
                                          ▼
+-----------------------------------------------------------------------------------+
| 4. CONFIGURABLE CONSENSUS ENGINE                                                  |
|    - Quorum Rule: Minimum 2-of-3 sensors must agree within tolerance              |
|    - Fault-Isolation: Outliers dynamically pruned from final mean calculation     |
+-----------------------------------------┬-----------------------------------------+
                                          ▼
+-----------------------------------------------------------------------------------+
| 5. PARAMETRIC TRIGGER EVALUATION                                                  |
|    - Trigger Rule: Consensus Intensity >= Policy Trigger Threshold (150.0 mm/h)  |
|    - Status: TRIGGERED vs NORMAL                                                  |
+-----------------------------------------┬-----------------------------------------+
                                          ▼
+-----------------------------------------------------------------------------------+
| 6. OCCUPATION-SPECIFIC DAMAGE ASSESSMENT                                          |
|    - Dynamic Filter: Farmer | Street Vendor | Laborer | Shopkeeper                |
|    - Calculates verifiable loss using backend-authoritative compensation formula   |
+-----------------------------------------┬-----------------------------------------+
                                          ▼
+-----------------------------------------------------------------------------------+
| 7. INSTANT RELIEF SETTLEMENT (IN-SILICO SIMULATION)                               |
|    - Integrity Assertion: Settlement Amount == Calculated Compensation            |
|    - Idempotent Transaction Execution & Synthetic Wallet Credit                   |
+-----------------------------------------┬-----------------------------------------+
                                          ▼
+-----------------------------------------------------------------------------------+
| 8. CRYPTOGRAPHIC AUDIT TRAIL                                                      |
|    - SHA-256 State Fingerprinting & Chronological Immutable Log                  |
+-----------------------------------------------------------------------------------+
```

---

## 3. Financial Safety & Simulation Guarantees

> [!NOTE]
> Risk2Relief operates with an absolute structural barrier separating simulated digital-twin calculations from external financial rails. All disbursements are executed strictly in-silico with synthetic cryptographic transaction IDs to showcase autonomous sub-second settlement reliability safely.
