# ==============================================================================
# Sovereign AI Workbench (SIH26117) — Windows Master Pipeline Launcher
# Native Windows Execution Engine with Robust Error Capture & Recovery
# ==============================================================================

$ErrorActionPreference = "Continue"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$RootDir = Split-Path -Parent $ScriptDir
Set-Location $RootDir

$LogDir = Join-Path $RootDir "logs"
if (!(Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir | Out-Null
}

$LogFile = Join-Path $LogDir "windows_pipeline.log"
$ErrorLogFile = Join-Path $LogDir "windows_errors.log"

function Log-Header {
    param([string]$title)
    Write-Host "`n========================================================================" -ForegroundColor Cyan
    Write-Host "  $title" -ForegroundColor Cyan
    Write-Host "========================================================================" -ForegroundColor Cyan
}

Log-Header "Sovereign AI Workbench — Native Windows Engine Initialization"
Write-Host "Project Root: $RootDir" -ForegroundColor Yellow
Write-Host "Logs Location: $LogDir" -ForegroundColor Yellow

# 1. Verify Python Availability
Write-Host "`n[1/4] Checking Python environment..." -ForegroundColor Green
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "❌ CRITICAL: Python is not installed or not in system PATH!" -ForegroundColor Red
    "[{0}] CRITICAL: Python binary not found in PATH" -f (Get-Date -Format "o") | Out-File -FilePath $ErrorLogFile -Append
    Exit 1
}

$pythonVersion = & python --version 2>&1
Write-Host "Detected: $pythonVersion" -ForegroundColor Green

# 2. Virtual Environment Setup
$VenvDir = Join-Path $RootDir ".venv"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Host "`n[2/4] Creating Python Virtual Environment (.venv)..." -ForegroundColor Green
    try {
        & python -m venv $VenvDir
        Write-Host "✅ Virtual environment created at $VenvDir" -ForegroundColor Green
    } catch {
        $err = $_
        Write-Host "❌ Failed to create virtual environment: $err" -ForegroundColor Red
        "[{0}] ERROR creating venv: {1}" -f (Get-Date -Format "o"), $err | Out-File -FilePath $ErrorLogFile -Append
        Exit 1
    }
} else {
    Write-Host "`n[2/4] Virtual Environment already exists." -ForegroundColor Green
}

# 3. Install & Update Dependencies with Retries
Write-Host "`n[3/4] Checking and installing Python dependencies..." -ForegroundColor Green
$pipPackages = @(
    "pip", "setuptools", "wheel",
    "torch", "transformers", "ultralytics",
    "qdrant-client", "sentence-transformers",
    "fastapi", "uvicorn", "onnxruntime",
    "pydantic", "requests", "roboflow",
    "peft", "trl", "bitsandbytes", "datasets",
    "accelerate", "pillow", "pyyaml"
)

$maxRetries = 3
$installSuccess = $false

for ($attempt = 1; $attempt -le $maxRetries; $attempt++) {
    Write-Host "Installing packages (Attempt $attempt of $maxRetries)..." -ForegroundColor Yellow
    try {
        & $VenvPython -m pip install --upgrade --quiet @pipPackages
        $installSuccess = $true
        Write-Host "✅ Dependencies installed successfully!" -ForegroundColor Green
        break
    } catch {
        $err = $_
        Write-Host "⚠️ Warning on package installation attempt $attempt: $err" -ForegroundColor Yellow
        "[{0}] WARNING (Pip Attempt {1}): {2}" -f (Get-Date -Format "o"), $attempt, $err | Out-File -FilePath $ErrorLogFile -Append
        Start-Sleep -Seconds 3
    }
}

if (-not $installSuccess) {
    Write-Host "⚠️ Package installation had warnings, proceeding with existing environment..." -ForegroundColor Yellow
}

# 4. Execute Full Pipeline with Error Capture
Log-Header "Launching Model Pipeline (Track A: YOLOv11s & Track B: Qwen2.5-VL)"

$startTime = Get-Date

try {
    Write-Host "Pipeline execution started at $startTime" -ForegroundColor Green
    Write-Host "Streaming logs to console and $LogFile..." -ForegroundColor Green
    
    & $VenvPython "$RootDir\scripts\run_full_pipeline.py" --full 2>&1 | Tee-Object -FilePath $LogFile
    
    $endTime = Get-Date
    $elapsed = $endTime - $startTime
    Write-Host "`n========================================================================" -ForegroundColor Green
    Write-Host "  ✅ PIPELINE EXECUTED SUCCESSFULLY!" -ForegroundColor Green
    Write-Host "  Total Execution Time: $($elapsed.Hours)h $($elapsed.Minutes)m $($elapsed.Seconds)s" -ForegroundColor Green
    Write-Host "  Full Log: $LogFile" -ForegroundColor Green
    Write-Host "========================================================================" -ForegroundColor Green

} catch {
    $err = $_
    $endTime = Get-Date
    Write-Host "`n========================================================================" -ForegroundColor Red
    Write-Host "  ❌ PIPELINE FAILED WITH EXCEPTION!" -ForegroundColor Red
    Write-Host "  Error Details: $err" -ForegroundColor Red
    Write-Host "  Error log written to: $ErrorLogFile" -ForegroundColor Red
    Write-Host "========================================================================" -ForegroundColor Red

    "[{0}] CRITICAL PIPELINE FAILURE:`n{1}`nTraceback:`n{2}" -f (Get-Date -Format "o"), $err, $_.ScriptStackTrace | Out-File -FilePath $ErrorLogFile -Append
    Exit 1
}
