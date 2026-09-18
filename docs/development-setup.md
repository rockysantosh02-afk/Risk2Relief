# Risk2Relief: Development Setup Guide

This guide details the step-by-step procedure to configure, run, and develop on the Risk2Relief monorepo locally.

---

## 1. System Prerequisites

Ensure the following runtimes are installed on your host system:
- **Python:** 3.12 or higher (`python --version`)
- **Node.js:** 20.x or higher (`node -v`)
- **npm:** 10.x or higher (`npm -v`)
- **Docker Desktop & Docker Compose:** Version 24+ (`docker compose version`)

---

## 2. Environment Configuration

1. Copy the environment configuration template:
   ```bash
   cp .env.example .env
   ```
2. Review `.env` and configure local ports or test passwords as needed. Default values work out of the box with Docker Compose.

---

## 3. Option A: Full-Stack Containerized Setup (Recommended)

To run the complete platform including PostgreSQL, Redis, Backend, Frontend, and Celery worker:

```bash
docker compose up --build
```

### Accessing Endpoints:
- **Frontend Dashboard:** [http://localhost:5173](http://localhost:5173)
- **FastAPI OpenAPI Swagger:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Root Health Check:** [http://localhost:8000/health](http://localhost:8000/health)
- **API v1 Health Check:** [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
- **Simulation Status:** [http://localhost:8000/api/v1/simulation/status](http://localhost:8000/api/v1/simulation/status)

---

## 4. Option B: Independent Local Setup

If you prefer running services outside of Docker for active development:

### 4.1 Running the Backend

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux / macOS:
   source .venv/bin/activate
   ```
3. Install dependencies in editable mode:
   ```bash
   pip install -e ".[dev]"
   ```
4. Start the FastAPI development server:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

### 4.2 Running the Frontend

1. Open a new terminal and navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install npm dependencies:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```

---

## 5. Running Verification Checks

Run the automated verification suite:

```bash
# Windows:
.\scripts\run-checks.ps1

# Linux / macOS:
./scripts/run-checks.sh
```

This verifies:
1. Backend unit and contract tests via `pytest`.
2. Frontend typecheck and production build via `npm run build`.
3. Docker Compose YAML configuration syntax via `docker compose config`.
