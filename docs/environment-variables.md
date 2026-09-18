# Risk2Relief: Environment Variables Specification

This document provides a reference matrix for all configuration variables supported across the Risk2Relief platform.

---

## 1. General Application Settings

| Variable | Type | Default | Description |
|---|---|---|---|
| `ENVIRONMENT` | string | `development` | Runtime environment mode: `development`, `testing`, `production`. |
| `PROJECT_NAME` | string | `Risk2Relief Building-Management Digital-Twin` | Platform human-readable title. |
| `APP_VERSION` | string | `0.1.0` | Semantic version string. |
| `DEBUG` | boolean | `true` | Enables verbose error handling and reload behaviors. |
| `LOG_LEVEL` | string | `INFO` | Logging threshold: `DEBUG`, `INFO`, `WARNING`, `ERROR`. |

---

## 2. Backend & Networking

| Variable | Type | Default | Description |
|---|---|---|---|
| `BACKEND_HOST` | string | `0.0.0.0` | Bind host for FastAPI server. |
| `BACKEND_PORT` | integer | `8000` | Bind port for FastAPI server. |
| `ALLOWED_CORS_ORIGINS` | JSON list | `["http://localhost:3000","http://localhost:5173"]` | Authorized CORS client origins. |

---

## 3. PostgreSQL Database

| Variable | Type | Default | Description |
|---|---|---|---|
| `POSTGRES_SERVER` | string | `localhost` | Database host or container name. |
| `POSTGRES_PORT` | integer | `5432` | Database port. |
| `POSTGRES_DB` | string | `risk2relief_db` | Target PostgreSQL database name. |
| `POSTGRES_USER` | string | `risk2relief_user` | Database user account. |
| `POSTGRES_PASSWORD` | string | *(secret)* | Password for PostgreSQL user. |
| `DATABASE_URL` | string | *(derived)* | Async connection string (`postgresql+asyncpg://...`). |
| `DB_POOL_SIZE` | integer | `10` | SQLAlchemy connection pool size. |
| `DB_MAX_OVERFLOW` | integer | `20` | Max overflow connections above pool size. |

---

## 4. Redis & Celery

| Variable | Type | Default | Description |
|---|---|---|---|
| `REDIS_HOST` | string | `localhost` | Redis server hostname. |
| `REDIS_PORT` | integer | `6379` | Redis server port. |
| `REDIS_PASSWORD` | string | *(empty)* | Optional Redis authentication token. |
| `REDIS_DB` | integer | `0` | Default cache database index. |
| `CELERY_BROKER_URL` | string | `redis://localhost:6379/1` | Message queue broker for Celery workers. |
| `CELERY_RESULT_BACKEND` | string | `redis://localhost:6379/2` | Asynchronous task result backend. |

---

## 5. Digital-Twin & Safety Boundaries

| Variable | Type | Default | Description |
|---|---|---|---|
| `SIMULATION_MODE` | boolean | `true` | Enforces in-silico simulation isolation. |
| `ENABLE_HARDWARE_ACTUATION` | boolean | `false` | **CRITICAL SAFETY INVARIANT:** Must remain `false`. Hardware command dispatch is permanently disabled. |
| `SIMULATION_TICK_RATE_HZ` | integer | `10` | Hertz frequency for physics simulation iterations. |
| `MAX_STRUCTURAL_STRESS_TOLERANCE_MPA` | float | `450.0` | Maximum tensile/compressive structural safety margin. |
| `CRITICAL_DEFLECTION_THRESHOLD_MM` | float | `15.0` | Structural deflection limit tripping the simulation interlock. |

---

## 6. Frontend Environment Variables

| Variable | Type | Default | Description |
|---|---|---|---|
| `VITE_API_BASE_URL` | string | `http://localhost:8000` | Backend API root for fetch clients. |
| `VITE_SIMULATION_MODE` | boolean | `true` | Frontend flag asserting digital-twin mode. |
| `VITE_APP_TITLE` | string | `Risk2Relief Digital-Twin` | Window title banner. |
