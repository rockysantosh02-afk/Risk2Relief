# Risk2Relief Local Development Environment Setup (PowerShell)
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " Risk2Relief: Initializing Developer Environment   " -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# 1. Check Python
Write-Host "`n[1/4] Checking Python 3.12+..." -ForegroundColor Yellow
$pythonVersion = python --version
Write-Host "Detected: $pythonVersion" -ForegroundColor Green

# 2. Check Node
Write-Host "`n[2/4] Checking Node.js & npm..." -ForegroundColor Yellow
$nodeVersion = node -v
$npmVersion = npm -v
Write-Host "Detected Node: $nodeVersion, npm: $npmVersion" -ForegroundColor Green

# 3. Setup Frontend dependencies
Write-Host "`n[3/4] Installing Frontend Dependencies..." -ForegroundColor Yellow
Push-Location -Path "./frontend"
npm install
Pop-Location

# 4. Copy environment template if not exists
Write-Host "`n[4/4] Configuring Environment..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example" -ForegroundColor Green
} else {
    Write-Host ".env already exists, skipping." -ForegroundColor Gray
}

Write-Host "`n==================================================" -ForegroundColor Green
Write-Host " Environment initialized successfully!           " -ForegroundColor Green
Write-Host " Run 'docker compose up' or local dev servers.   " -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
