# ============================================================
#  StudentSystem - One-click startup script
#  Run this in PowerShell as Administrator
# ============================================================

$ProjectRoot  = "C:\Users\Narmatha\Desktop\ICBT\project\StudentSystem"
$BackendDir   = "$ProjectRoot\backend"
$FrontendDir  = "$ProjectRoot\frontend"
$VenvActivate = "$ProjectRoot\.venv\Scripts\Activate.ps1"

# ── helper ──────────────────────────────────────────────────
function Write-Step($msg) {
    Write-Host "`n>>> $msg" -ForegroundColor Cyan
}
function Write-Ok($msg) {
    Write-Host "    [OK] $msg" -ForegroundColor Green
}
function Write-Warn($msg) {
    Write-Host "    [!!] $msg" -ForegroundColor Yellow
}
function Write-Err($msg) {
    Write-Host "    [ERROR] $msg" -ForegroundColor Red
}

# ── 1. Administrator check ───────────────────────────────────
Write-Step "Checking administrator privileges..."
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]"Administrator")
if (-not $isAdmin) {
    Write-Err "Please run this script as Administrator (right-click PowerShell > Run as administrator)."
    pause
    exit 1
}
Write-Ok "Running as administrator."

# ── 2. MySQL service ─────────────────────────────────────────
Write-Step "Checking MySQL80.0 service..."
$mysql = Get-Service -Name "MySQL80.0" -ErrorAction SilentlyContinue
if ($null -eq $mysql) {
    Write-Err "MySQL80.0 service not found. Please install MySQL 8.0 first."
    pause
    exit 1
}
if ($mysql.Status -ne "Running") {
    Write-Warn "MySQL80.0 is not running. Starting it..."
    Start-Service MySQL80.0
    Start-Sleep -Seconds 3
    $mysql = Get-Service -Name "MySQL80.0"
    if ($mysql.Status -eq "Running") {
        Write-Ok "MySQL80.0 started successfully."
    } else {
        Write-Err "Failed to start MySQL80.0. Check MySQL installation."
        pause
        exit 1
    }
} else {
    Write-Ok "MySQL80.0 is already running."
}

# ── 3. Virtual environment ───────────────────────────────────
Write-Step "Checking Python virtual environment..."
if (-not (Test-Path $VenvActivate)) {
    Write-Warn ".venv not found. Creating it now..."
    Set-Location $ProjectRoot
    python -m venv .venv
    if (-not (Test-Path $VenvActivate)) {
        Write-Err "Failed to create .venv. Make sure Python is installed and in PATH."
        pause
        exit 1
    }
    Write-Ok ".venv created."
} else {
    Write-Ok ".venv found."
}

# ── 4. Install Python requirements ──────────────────────────
Write-Step "Installing Python requirements..."
$pip = "$ProjectRoot\.venv\Scripts\pip.exe"
& $pip install -r "$BackendDir\requirements.txt" --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Warn "pip install reported issues - backend may still work if packages are already installed."
} else {
    Write-Ok "Requirements installed."
}

# ── 5. Start backend in a new window ────────────────────────
Write-Step "Starting backend server (port 8000)..."
$backendCmd = "Set-Location '$BackendDir'; & '$ProjectRoot\.venv\Scripts\Activate.ps1'; uvicorn server:app --reload --host 0.0.0.0 --port 8000"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd -Verb RunAs
Write-Ok "Backend window launched."

# Give backend a moment to initialise the database on first run
Write-Host "    Waiting 5 seconds for backend to initialise..." -ForegroundColor DarkGray
Start-Sleep -Seconds 5

# ── 6. Start frontend in a new window ───────────────────────
Write-Step "Starting frontend (port 3000)..."
$frontendCmd = "Set-Location '$FrontendDir'; npm start"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd
Write-Ok "Frontend window launched."

# ── 7. Open browser ─────────────────────────────────────────
Write-Step "Opening browser in 8 seconds..."
Start-Sleep -Seconds 8
Start-Process "http://localhost:3000"
Write-Ok "Browser opened."

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  StudentSystem is starting up!" -ForegroundColor Green
Write-Host "  Frontend : http://localhost:3000" -ForegroundColor White
Write-Host "  Backend  : http://localhost:8000" -ForegroundColor White
Write-Host "  API docs : http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "  Default login: admin@school.com / admin123" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Close the backend and frontend windows to stop the servers." -ForegroundColor DarkGray
Write-Host ""
