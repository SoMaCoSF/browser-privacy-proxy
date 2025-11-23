# ==============================================================================
# file_id: SOM-SCR-0008-v1.0.0
# name: setup.ps1
# description: Setup script for Privacy Proxy
# project_id: BROWSER-MIXER-ANON
# category: script
# tags: [setup, installation]
# created: 2025-01-22
# modified: 2025-01-22
# version: 1.0.0
# agent_id: AGENT-PRIME-001
# execution: .\setup.ps1
# ==============================================================================

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 69) -ForegroundColor Cyan
Write-Host "  PRIVACY PROXY - Setup Script" -ForegroundColor Yellow
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 69) -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
Write-Host "[1/6] Checking Python installation..." -ForegroundColor Green
try {
    $pythonVersion = python --version 2>&1
    Write-Host "      Found: $pythonVersion" -ForegroundColor Gray
} catch {
    Write-Host "      ERROR: Python not found. Please install Python 3.12+" -ForegroundColor Red
    exit 1
}

# Check if uv is installed
Write-Host "[2/6] Checking uv package manager..." -ForegroundColor Green
try {
    $uvVersion = uv --version 2>&1
    Write-Host "      Found: $uvVersion" -ForegroundColor Gray
} catch {
    Write-Host "      ERROR: uv not found. Install from: https://github.com/astral-sh/uv" -ForegroundColor Red
    exit 1
}

# Create virtual environment
Write-Host "[3/6] Creating virtual environment..." -ForegroundColor Green
if (Test-Path ".venv") {
    Write-Host "      Virtual environment already exists" -ForegroundColor Gray
} else {
    uv venv .venv
    Write-Host "      Virtual environment created" -ForegroundColor Gray
}

# Activate virtual environment and install packages
Write-Host "[4/6] Installing dependencies..." -ForegroundColor Green
.venv\Scripts\activate.ps1
uv pip install mitmproxy fake-useragent requests pyyaml
Write-Host "      Dependencies installed" -ForegroundColor Gray

# Create directories
Write-Host "[5/6] Creating directory structure..." -ForegroundColor Green
$directories = @("database", "logs", "config", "tests")
foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir | Out-Null
        Write-Host "      Created: $dir/" -ForegroundColor Gray
    } else {
        Write-Host "      Exists: $dir/" -ForegroundColor Gray
    }
}

# Initialize database
Write-Host "[6/6] Initializing database..." -ForegroundColor Green
if (Test-Path "database\schema.sql") {
    python -c "from database_handler import DatabaseHandler; db = DatabaseHandler('database/browser_privacy.db'); print('Database initialized')"
    Write-Host "      Database initialized" -ForegroundColor Gray
} else {
    Write-Host "      WARNING: schema.sql not found, skipping" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 69) -ForegroundColor Cyan
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 69) -ForegroundColor Cyan
Write-Host ""
Write-Host "Quick Start:" -ForegroundColor Yellow
Write-Host "  1. Activate virtual environment:" -ForegroundColor White
Write-Host "     .venv\Scripts\activate.ps1" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. Start the proxy:" -ForegroundColor White
Write-Host "     python start_proxy.py" -ForegroundColor Gray
Write-Host ""
Write-Host "  3. Configure your browser to use proxy:" -ForegroundColor White
Write-Host "     HTTP/HTTPS Proxy: 127.0.0.1:8080" -ForegroundColor Gray
Write-Host ""
Write-Host "  4. View statistics:" -ForegroundColor White
Write-Host "     python manage.py stats" -ForegroundColor Gray
Write-Host ""
Write-Host "See README.md for full documentation" -ForegroundColor Cyan
Write-Host ""
