# Risk2Relief Quality & Verification Checks (PowerShell)
$ErrorActionPreference = "Stop"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " Risk2Relief: Running Verification Suite          " -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# 1. Backend Pytest
Write-Host "`n[1/3] Running Backend Tests (pytest)..." -ForegroundColor Yellow
python -m pytest backend/tests tests/integration
if ($LASTEXITCODE -ne 0) {
    Write-Error "Backend tests failed!"
}

# 2. Frontend Lint & Build
Write-Host "`n[2/3] Checking Frontend Typecheck & Build..." -ForegroundColor Yellow
Push-Location -Path "./frontend"
npm run build
if ($LASTEXITCODE -ne 0) {
    Pop-Location
    Write-Error "Frontend build failed!"
}
Pop-Location

# 3. Docker Compose Config Validation
Write-Host "`n[3/3] Validating Docker Compose Orchestration..." -ForegroundColor Yellow
docker compose config > $null
if ($LASTEXITCODE -ne 0) {
    Write-Error "Docker Compose validation failed!"
}

Write-Host "`n==================================================" -ForegroundColor Green
Write-Host " All verification checks passed successfully!     " -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
