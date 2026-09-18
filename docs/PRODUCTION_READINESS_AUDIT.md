# Risk2Relief Production Readiness Audit

**Platform**: Risk2Relief — Autonomous Parametric Climate Insurance & Instant Settlement Reliability Engine  
**Audit Type**: Full-Stack Technical, Security, Infrastructure, and Production Deployment Audit  
**Date**: September 2026  
**Status**: DEPLOYMENT READY (SIMULATED / HACKATHON FINANCIAL PROTOTYPE)

---

## 1. System Map & End-to-End Data Flow

```
USER / BENEFICIARY (Browser / Mobile)
        ↓
RENDER STATIC FRONTEND (React 18 + Vite + TypeScript + Glassmorphism UI)
        ↓
FIREBASE AUTHENTICATION (Client SDK: Google Sign-In & Email/Password Identity)
        ↓ [Bearer ID Token in Authorization Header]
RENDER FASTAPI BACKEND (/api/v1 + Security Middlewares + CORS + Health / Metrics)
        ↓
FIREBASE ADMIN SDK (Token Verification & UID Extraction)
        ↓
POSTGRESQL DATABASE (Policies, Telemetry, Damage Rules, Assessments, Settlements, Audit Logs)
        ↓
LIVE DECISION ENGINE
  ├── 1. Ingestion & Deterministic Validation (Range, Drift, Duplicate Check)
  ├── 2. Isolation Forest Anomaly Detection (Pure Python / scikit-learn Advisory Layer)
  ├── 3. Configurable Consensus Engine (2-of-3 Sensor Quorum, Fault Isolation)
  └── 4. Parametric Trigger Evaluation (Threshold >= 150.0 mm/h)
        ↓
DAMAGE ASSESSMENT & RELIEF COMPENSATION
  ├── Dynamic Occupation & Loss Reason Filter (Farmer, Street Vendor, Laborer, Shopkeeper)
  └── Backend-Authoritative Compensation Formula (Calculated strictly server-side)
        ↓
INSTANT RELIEF SETTLEMENT
  ├── In-Silico Synthetic Wallet Disbursement
  ├── Strict Idempotency & Duplicate Request Protection
  └── Exact Amount Integrity: Settlement Amount == Calculated Compensation
        ↓
IMMUTABLE AUDIT TRAIL
  └── Cryptographic Hash Chaining (SHA-256) & State Lifecycle Persistence
```

---

## 2. Component-by-Component Architectural Audit

### 2.1 Frontend Architecture (`frontend/`)
- **Framework & Tooling**: Vite 5.4 + React 18 + TypeScript 5.3.
- **Styling**: Native CSS tokens with dark-navy glassmorphism design system (`index.css`), responsive layouts, and zero heavy UI library overhead.
- **State Management**: Zustand store (`useAuthStore`) for user authentication status; TanStack React Query (`@tanstack/react-query`) for API caching and mutation state.
- **API Client**: Native fetch wrapper (`apiFetch`, `fetchJson`) with dynamic `VITE_API_BASE_URL` resolution and automatic Firebase Bearer token injection.
- **Branding**: Official Risk2Relief logo component (`Risk2ReliefLogo.tsx`) integrated in Header, AuthModal, Favicon (`index.html`), and metadata.

### 2.2 Backend Architecture (`backend/`)
- **Framework**: FastAPI 0.111 + Uvicorn 0.29 + Python 3.12.
- **Security Middlewares**:
  - `SecurityHeadersMiddleware`: Injects `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection: 1; mode=block`, `Referrer-Policy: strict-origin-when-cross-origin`.
  - `RequestSizeLimiterMiddleware`: Enforces 1 MB payload limits to prevent buffer overflow/DoS.
  - `RateLimiterMiddleware`: In-memory sliding-window rate limiting per client IP (60 req/min).
  - `CorrelationIdMiddleware`: Injects unique `X-Correlation-ID` for end-to-end tracing.
  - `CORSMiddleware`: Configured with `get_cors_origins()` supporting comma-separated `CORS_ORIGINS` for deployed Render frontend domains.
- **Endpoints**:
  - `GET /health`: System health (database, simulation, version, timestamp).
  - `GET /metrics`: Prometheus metric exposition.
  - `GET /api/v1/auth/firebase/me`: Authenticated user identity verification.
  - `POST /api/v1/climate/scenarios/run-live`: Dynamic 3-source telemetry pipeline execution.
  - `POST /api/v1/damage-assessments/calculate`: Authoritative relief compensation calculation.
  - `POST /api/v1/settlements/execute`: Idempotent instant settlement disbursement.

### 2.3 Database Architecture (`database/` & `backend/app/models/`)
- **Engine**: Async SQLAlchemy 2.0 with `asyncpg` connection pool (`pool_pre_ping=True`, `pool_size=10`).
- **Migrations**: Alembic (`alembic.ini`, `database/migrations/`) supporting automated schema upgrades (`alembic upgrade head`).
- **Connection Safety**: Handles both `postgres://` (Render default) and `postgresql://` formats dynamically converted to `postgresql+asyncpg://`.

### 2.4 ML Anomaly Detection Architecture (`backend/app/climate/ml/`)
- **Detector**: `IsolationForestAnomalyDetector` utilizing `sklearn.ensemble.IsolationForest` with deterministic fallback.
- **Safety Invariant**: ML output is strictly **advisory**. Anomaly scores and contamination flags inform audit trails but never directly authorize financial payouts or override consensus triggers.

---

## 3. Environment Variables Audit

| Variable | Target Service | Purpose | Production Example |
| :--- | :--- | :--- | :--- |
| `DATABASE_URL` | Backend | PostgreSQL connection string | `postgres://user:pass@host/risk2relief_db` |
| `CORS_ORIGINS` | Backend | Allowed frontend origin domains | `https://risk2relief-frontend.onrender.com` |
| `ENVIRONMENT` | Backend | Deployment environment | `production` |
| `DEBUG` | Backend | Disable debug mode / tracebacks | `false` |
| `LOG_LEVEL` | Backend | Logging verbosity | `INFO` |
| `FIREBASE_PROJECT_ID` | Backend | Firebase project for token verification | `risk2relief` |
| `VITE_API_BASE_URL` | Frontend | Target backend API base URL | `https://risk2relief-backend.onrender.com` |
| `VITE_FIREBASE_API_KEY` | Frontend | Firebase Web SDK API Key | `AIzaSy...` |
| `VITE_FIREBASE_AUTH_DOMAIN` | Frontend | Firebase Auth Domain | `risk2relief.firebaseapp.com` |
| `VITE_FIREBASE_PROJECT_ID` | Frontend | Firebase Project ID | `risk2relief` |
| `VITE_FIREBASE_APP_ID` | Frontend | Firebase App ID | `1:12345:web:abcde` |

---

## 4. Current Risks & Mitigation Strategies

1. **Render Free-Tier Cold Starts**: Free-tier Render instances sleep after inactivity.
   - *Mitigation*: The frontend includes loading spinners and graceful timeouts, clearly indicating live backend connection status to judges.
2. **CORS Misconfiguration on Initial Deploy**: Frontend domain is unknown before Render generates the URL.
   - *Mitigation*: Backend dynamically parses `CORS_ORIGINS` comma-separated list, allowing instantaneous update once the frontend URL is assigned.
3. **Financial Boundary Integrity**: Accidental confusion between real money and demo disbursements.
   - *Mitigation*: Explicit simulation banners, UI notices, and synthetic wallet hashes maintain strict in-silico compliance.
