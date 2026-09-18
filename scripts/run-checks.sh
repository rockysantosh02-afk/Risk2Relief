#!/usr/bin/env bash
set -e

echo "=================================================="
echo " Risk2Relief: Running Verification Suite          "
echo "=================================================="

# 1. Backend Pytest
echo -e "\n[1/3] Running Backend Tests (pytest)..."
python3 -m pytest backend/tests tests/integration || python -m pytest backend/tests tests/integration

# 2. Frontend Lint & Build
echo -e "\n[2/3] Checking Frontend Typecheck & Build..."
cd frontend
npm run build
cd ..

# 3. Docker Compose Config Validation
echo -e "\n[3/3] Validating Docker Compose Orchestration..."
docker compose config > /dev/null

echo -e "\n=================================================="
echo " All verification checks passed successfully!     "
echo "=================================================="
