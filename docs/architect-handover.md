# Risk2Relief: Complete AI Architect Handover & Technical Dossier

## 1. Executive Summary & Purpose

**Project Name:** Risk2Relief  
**Workspace Path:** `C:\Users\rocky\OneDrive\vs code project\Risk2Relief`  
**Current Milestone:** Phase 1 Foundation Completed & Verified  
**Next Milestone:** Phase 2 (Domain Modeling, Telemetry Ingestion, & Physics Digital-Twin Simulation)

Risk2Relief is a production-oriented, full-stack building-management digital-twin platform. It ingests high-frequency structural sensor telemetry (strain, vibration, temperature, load), computes structural deformation and stress distributions, and models hazard mitigation strategies within an isolated in-silico simulation environment.

---

## 2. Hard System Boundaries & Non-Negotiable Safety Invariants

> ### CRITICAL ARCHITECTURAL CONSTRAINTS:
> 1. **IN-SILICO SIMULATION ONLY**:
>    The "anti-gravity" / gravitational mitigation subsystem is strictly a mathematical digital-twin physics simulation. Real-world anti-gravity technology is not assumed to exist.
> 2. **NO HARDWARE ACTUATION**:
>    The platform **must never** implement, command, or expose interfaces for physical actuators or gravity-generating hardware.
> 3. **READ-ONLY TELEMETRY INTEGRATION**:
>    Physical building integrations are strictly limited to sensor telemetry ingestion (strain gauges, accelerometers, temperature sensors, inclinometers) and fail-safe safety interlocks.
> 4. **ISOLATION FROM UNRELATED PROJECTS**:
>    The repository is independent. Do NOT introduce Flutter, mobile app code, Firebase/Firestore SDKs, caregiver dashboards, or external codebases (such as SMIRITI-AI).
> 5. **LAYER SEPARATION**:
>    Maintain the pattern: `API Route (app/api/v1/) -> Domain Service (app/services/) -> Repository (app/repositories/) -> Database (PostgreSQL / Redis)`. Never put database queries or business logic in route handlers.

---

## 3. Technology Stack & Runtime Versions

- **Frontend:**
  - React 18.2.0 + TypeScript 5.2.2 + Vite 5.1.6
  - TanStack React Query 5.28.9 (data fetching & polling)
  - Zustand 4.5.2 (lightweight state)
  - Lucide React 0.363.0 (icons)
  - Pure Modern CSS design system (Plus Jakarta Sans + JetBrains Mono)
- **Backend:**
  - Python 3.12.10
  - FastAPI 0.111.0 + Starlette 0.37.2
  - Pydantic v2 (2.13.3) + Pydantic-Settings (2.14.2)
  - SQLAlchemy 2.0.25 (Async engine via asyncpg)
  - Alembic 1.20.0 (database migrations)
  - Redis 7 / redis-py (connection pool & caching)
  - Celery 5.3+ (asynchronous worker)
  - Pytest 7.4.4 + Pytest-Asyncio 0.23.3
- **Infrastructure & DevOps:**
  - Docker + Docker Compose (v2 syntax, multi-container dev environment)
  - Kubernetes (Deployment, Service, ConfigMap)
  - Terraform (AWS VPC, Subnet blueprints)
  - GitHub Actions CI (`backend-ci.yml`, `frontend-ci.yml`)

---

## 4. Complete File & Directory Inventory

```
Risk2Relief/
├── .github/
│   └── workflows/
│       ├── backend-ci.yml             # GitHub Actions: Python 3.12, Postgres/Redis services, Pytest
│       └── frontend-ci.yml            # GitHub Actions: Node 20, typecheck, production build
├── .env.example                       # Documented environment template with safety defaults
├── .gitattributes                     # Normalizes LF line endings and binary declarations
├── .gitignore                         # Comprehensive ignore rules (Python, Node, Docker, Terraform)
├── README.md                          # Master architectural overview, quickstart & endpoints
├── docker-compose.yml                 # Orchestration: postgres, redis, backend, celery_worker, frontend
├── PS_F03.pdf                         # Preserved original challenge problem statement specification
│
├── backend/                           # FastAPI Python Backend
│   ├── Dockerfile                     # Multi-stage Python 3.12-slim container
│   ├── pyproject.toml                 # Package manifest, dependencies, and pytest configuration
│   ├── app/
│   │   ├── __init__.py                # Package version 0.1.0
│   │   ├── main.py                    # App factory, CORS, lifespan, /health, /api/v1 router
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py              # Pydantic-settings v2 BaseSettings class
│   │   │   ├── database.py            # Async SQLAlchemy engine, AsyncSessionLocal, check_database_health()
│   │   │   ├── redis.py               # Async Redis client, connection pool, check_redis_health()
│   │   │   └── celery_app.py          # Celery worker configuration with Redis broker/backend
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── router.py          # API v1 aggregator router
│   │   │       ├── health.py          # GET /api/v1/health route
│   │   │       └── simulation.py      # GET /api/v1/simulation/status route
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── base.py                # SQLAlchemy 2.x DeclarativeBase & TimestampMixin
│   │   ├── repositories/
│   │   │   ├── __init__.py
│   │   │   ├── base.py                # BaseRepository generic class
│   │   │   └── health_repository.py   # HealthRepository database ping queries
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── health.py              # HealthResponse & DependencyHealth Pydantic models
│   │   │   └── simulation.py          # SimulationStatusResponse & SafetyBoundaryStatus models
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── health_service.py      # HealthService aggregating DB and Redis health
│   │       └── simulation_engine.py   # In-silico physics simulation service enforcing safety barriers
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py                # Pytest TestClient fixture
│       └── test_health.py             # 4 unit tests verifying health and safety boundary contracts
│
├── frontend/                          # React + TypeScript + Vite Frontend
│   ├── package.json                   # React, Vite, TS, TanStack Query, Zustand, Lucide
│   ├── tsconfig.json                  # Strict TypeScript compiler options
│   ├── tsconfig.node.json             # Bundler node configuration
│   ├── vite.config.ts                 # Dev server with reverse proxy for /api and /health
│   ├── index.html                     # HTML5 shell with Google Fonts
│   ├── public/
│   │   └── vite.svg                   # Brand icon
│   └── src/
│       ├── main.tsx                   # React root with QueryClientProvider
│       ├── App.tsx                    # Main shell: Header, SimulationBanner, HealthMonitor, SafetyIndicator
│       ├── index.css                  # Custom cyber-structural glassmorphic design system
│       ├── vite-env.d.ts              # Vite client environment types
│       ├── api/
│       │   ├── client.ts              # Native fetch wrapper with base URL handling
│       │   └── health.ts              # TanStack Query hooks (useHealthQuery, useSimulationQuery)
│       ├── store/
│       │   └── useSystemStore.ts      # Zustand system state store
│       ├── types/
│       │   └── index.ts               # Frontend interfaces matching backend contracts
│       └── components/
│           ├── Header.tsx             # Risk2Relief branding & status badges
│           ├── SimulationBanner.tsx   # Visual notice enforcing in-silico simulation isolation
│           ├── HealthMonitor.tsx      # Reactive health diagnostics and dependency status card
│           └── SafetyIndicator.tsx    # Safety interlock & permitted integration monitor card
│
├── shared/                            # Shared Cross-Boundary Contracts
│   ├── schemas/
│   │   ├── telemetry.json             # JSONSchema for building structural telemetry packets
│   │   └── safety_limits.json         # JSONSchema for structural stress & interlock thresholds
│   └── types/
│       └── index.ts                   # Universal TypeScript interfaces for cross-boundary contracts
│
├── database/                          # Database Layer
│   ├── alembic.ini                    # Alembic migration configuration
│   ├── migrations/
│   │   ├── env.py                     # Asyncpg migration runner wired to Base.metadata
│   │   ├── script.py.mako             # Revision template
│   │   └── versions/.gitkeep          # Revision version directory
│   └── init/
│       └── 01_init_db.sql             # PostgreSQL initialization: uuid-ossp, pgcrypto, system_heartbeat
│
├── docker/                            # Container Definitions
│   ├── Dockerfile.backend             # Multi-stage Python 3.12-slim backend container
│   ├── Dockerfile.frontend            # Multi-stage Node 20 / Nginx frontend container
│   ├── Dockerfile.celery              # Background task worker container
│   └── .dockerignore                  # Build context exclusion rules
│
├── config/                            # Central Configuration
│   ├── default.yaml                   # Default system settings, ports, pool sizes, simulation mode
│   └── safety_boundaries.json         # Formal JSON specification of in-silico invariants
│
├── docs/                              # Project Documentation
│   ├── architecture.md                # System layers, data flow, Celery/Redis architecture
│   ├── development-setup.md           # Step-by-step developer setup guide
│   ├── environment-variables.md       # Matrix of all environment variables and defaults
│   ├── contributing.md                # Git workflow, PR rules, and coding standards
│   ├── safety-boundaries.md           # In-silico simulation invariants & forbidden actuator controls
│   ├── phase1-existing-implementation-audit.md # Full audit of initial repository state
│   └── architect-handover.md          # Complete dossier for ongoing development
│
├── scripts/                           # Developer Automation
│   ├── dev-setup.ps1 / .sh            # Automated developer environment bootstrapper
│   └── run-checks.ps1 / .sh           # Unified testing, linting, and build validation runner
│
└── tests/                             # System Integration Suite
    └── integration/
        └── test_health_e2e.py         # End-to-end service contract and safety guarantee tests
```

---

## 5. Current Verified Test & Build Status

| Check | Tool / Command | Result |
|---|---|---|
| **Backend Unit Tests** | `pytest backend/tests` | **4 passed** (100% pass rate) |
| **Integration Tests** | `pytest tests/integration` | **2 passed** (100% pass rate) |
| **Frontend Typecheck** | `tsc --noEmit` (via `npm run lint`) | **0 errors** |
| **Frontend Build** | `tsc && vite build` (via `npm run build`) | **0 errors**, production bundle built in 2.74s |
| **Docker Compose** | `docker compose config --quiet` | **0 errors / 0 warnings** |
| **API /health** | HTTP GET `/health` | **200 OK**, structured JSON returned |
| **API /api/v1/health** | HTTP GET `/api/v1/health` | **200 OK**, structured JSON returned |
| **API /api/v1/simulation/status** | HTTP GET `/api/v1/simulation/status` | **200 OK**, `mode: "in-silico-only"` verified |

---

## 6. How Next Phases Should Build Upon This Foundation

When continuing development into Phase 2:
1. **Domain Models**: Create models in `backend/app/models/` (e.g. `building.py`, `sensor.py`, `telemetry.py`) extending `Base` from `app.models.base`.
2. **Migrations**: Generate Alembic migrations via `alembic revision --autogenerate -m "..."`.
3. **Services**: Implement simulation models in `backend/app/services/simulation_engine.py` using pure mathematical physics equations (finite element strain calculations, deflection vectors). Never connect to hardware actuators.
4. **API Endpoints**: Add new endpoints under `backend/app/api/v1/` and register them in `backend/app/api/v1/router.py`.
5. **Frontend Dashboard**: Expand `frontend/src/` by adding 2D/3D building digital-twin views (using Chart.js, D3, or Canvas), telemetry charts, and zone stress heatmaps.
