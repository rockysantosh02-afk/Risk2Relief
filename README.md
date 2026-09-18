# Risk2Relief: Building-Management Digital-Twin Platform

[![Backend CI](https://github.com/risk2relief/risk2relief/actions/workflows/backend-ci.yml/badge.svg)](.github/workflows/backend-ci.yml)
[![Frontend CI](https://github.com/risk2relief/risk2relief/actions/workflows/frontend-ci.yml/badge.svg)](.github/workflows/frontend-ci.yml)

Risk2Relief is a production-oriented full-stack building-management digital-twin platform that ingests real-time sensor telemetry, calculates structural stresses and deflections, and simulates dynamic hazard mitigation strategies within an isolated in-silico environment.

---

## CRITICAL SYSTEM SAFETY BOUNDARY

> ### HARDWARE ISOLATION INVARIANT
> **The gravitational mitigation / "anti-gravity" functionality is strictly an in-silico mathematical and physics simulation subsystem.**
>
> 1. **No Real Anti-Gravity Technology**: The platform does not assume, model, or operate hypothetical gravity-generating physical hardware.
> 2. **Zero Actuator Controls**: No direct hardware command dispatch, pulse controls, or actuator interfaces exist.
> 3. **Strictly In-Silico**: All compensation calculations remain inside the digital-twin simulator.
> 4. **Safe Building Integrations**: Real-world building integrations are strictly limited to sensor telemetry ingestion (strain gauges, accelerometers, temperature), structural load modeling, and fail-safe safety interlocks.

---

## Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 18, TypeScript, Vite, TanStack React Query, Zustand, Lucide Icons, Modern Responsive CSS |
| **Backend** | Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2.x (async), Alembic, Celery, Redis |
| **Database** | PostgreSQL 16 (UUID & pgcrypto enabled) |
| **Broker / Cache** | Redis 7 (dual-channel broker + caching) |
| **Infrastructure** | Docker, Docker Compose, Kubernetes manifests, Terraform |
| **CI / CD** | GitHub Actions workflows |

---

## Monorepo Directory Architecture

```
Risk2Relief/
├── .github/                      # CI/CD pipelines
│   └── workflows/
│       ├── backend-ci.yml        # Python 3.12, linting & pytest
│       └── frontend-ci.yml       # Node 20, typecheck & build
├── backend/                      # FastAPI Python service
│   ├── app/
│   │   ├── api/v1/               # Versioned REST controllers (/health, /simulation)
│   │   ├── core/                 # Config (Pydantic v2), DB, Redis, Celery setup
│   │   ├── models/               # SQLAlchemy 2.x Declarative Models
│   │   ├── repositories/         # Data access layer (Route -> Service -> Repo -> DB)
│   │   ├── schemas/              # Pydantic v2 validation & response schemas
│   │   ├── services/             # Domain logic & simulation engine service
│   │   └── main.py               # Application entrypoint & CORS middleware
│   ├── tests/                    # Pytest test suite (health checks & contracts)
│   ├── Dockerfile                # Multi-stage container definition
│   └── pyproject.toml            # Python package & dependency manifest
├── frontend/                     # React + TypeScript + Vite web app
│   ├── src/
│   │   ├── api/                  # Native fetch API client & TanStack Query hooks
│   │   ├── components/           # Header, HealthMonitor, SimulationBanner, SafetyIndicator
│   │   ├── store/                # Zustand system status store
│   │   ├── types/                # TypeScript contract definitions
│   │   ├── App.tsx               # Main layout & dashboard shell
│   │   ├── index.css             # Glassmorphic CSS design system
│   │   └── main.tsx              # Application mount point
│   ├── index.html                # HTML entrypoint
│   ├── package.json              # Node.js dependencies & build scripts
│   ├── tsconfig.json             # TypeScript compiler configuration
│   └── vite.config.ts            # Vite bundler & API proxy configuration
├── shared/                       # Cross-boundary schemas & contracts
│   ├── schemas/                  # JSON Schemas (telemetry, safety limits)
│   └── types/                    # Cross-platform TypeScript interfaces
├── database/                     # Migrations & database initialization
│   ├── alembic.ini               # Alembic configuration
│   ├── migrations/               # Database revision scripts (asyncpg)
│   └── init/01_init_db.sql       # PostgreSQL initial database seed & extensions
├── docker/                       # Dockerfiles and ignore rules
│   ├── Dockerfile.backend        # Python FastAPI container
│   ├── Dockerfile.frontend       # Node/Nginx production build
│   ├── Dockerfile.celery         # Background worker container
│   └── .dockerignore             # Global docker ignore rules
├── config/                       # Central application configuration
│   ├── default.yaml              # Default system parameters
│   └── safety_boundaries.json    # Strict digital-twin safety boundary definitions
├── docs/                         # In-depth architectural & developer guides
│   ├── architecture.md           # Structural design, layers, and data flows
│   ├── development-setup.md      # Local developer setup guide
│   ├── environment-variables.md  # Comprehensive env-var matrix
│   ├── safety-boundaries.md      # Formal safety boundaries and invariant documentation
│   ├── contributing.md           # Contribution standards & Git workflow
│   └── phase1-existing-implementation-audit.md # Repository audit record
├── infrastructure/               # Production deployment blueprints
│   ├── k8s/                      # Kubernetes Deployment, Service, ConfigMap manifests
│   └── terraform/                # Terraform cloud provisioning scaffold
├── scripts/                      # Developer automation scripts
│   ├── dev-setup.ps1 / .sh       # Environment initialization scripts
│   └── run-checks.ps1 / .sh      # Lint, test, and build validation scripts
├── tests/                        # Monorepo-level integration test suite
│   └── integration/              # End-to-end service contracts
├── .env.example                  # Documented environment variable template
├── .gitignore                    # Production gitignore
├── .gitattributes                # Consistent LF line-ending definitions
└── docker-compose.yml            # Local development orchestration
```

---

## Quick Start

### 1. Prerequisites
- **Python 3.12+**
- **Node.js 20+** and **npm**
- **Docker** and **Docker Compose** (for containerized stack)

### 2. Automated Developer Setup
Clone the repository and run the setup script:

```bash
# On Windows (PowerShell):
.\scripts\dev-setup.ps1

# On Linux / macOS:
chmod +x scripts/dev-setup.sh
./scripts/dev-setup.sh
```

### 3. Running with Docker Compose (Recommended)
Launch the entire stack (PostgreSQL, Redis, Backend, Frontend, Celery worker) with health-monitored orchestration:

```bash
docker compose up --build
```

- **Frontend Dashboard:** [http://localhost:5173](http://localhost:5173)
- **FastAPI Documentation (Swagger UI):** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Root Health Check:** [http://localhost:8000/health](http://localhost:8000/health)

---

## Independent Local Execution

### Backend Execution
```bash
cd backend

# Create & activate virtual environment (optional)
python -m venv .venv
# On Windows: .venv\Scripts\activate
# On Unix: source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Run FastAPI with live reload
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Execution
```bash
cd frontend

# Install packages
npm install

# Start Vite dev server
npm run dev
```

---

## Health Check API Specification

The backend provides structured health-check endpoints:

- `GET /health` (Root health endpoint)
- `GET /api/v1/health` (API v1 health endpoint)

### Response Payload Sample
```json
{
  "status": "ok",
  "service": "risk2relief-api",
  "version": "0.1.0",
  "timestamp": "2026-09-18T10:00:00.000000+00:00",
  "dependencies": {
    "database": "connected",
    "redis": "connected"
  }
}
```
*Note: Health endpoints never leak database credentials, connection strings, or environment secrets.*

---

## Verification & Automated Testing

Run the full verification suite across backend, frontend, and Docker Compose:

```bash
# On Windows (PowerShell):
.\scripts\run-checks.ps1

# On Linux / macOS:
./scripts/run-checks.sh
```

Or run test suites independently:

```bash
# Run backend unit and integration tests
python -m pytest backend/tests tests/integration

# Run frontend typecheck and production build
cd frontend && npm run lint && npm run build
```
