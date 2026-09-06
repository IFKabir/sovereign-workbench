# Sovereign AI Workbench (SIH26117) - one-click PowerShell launcher
[CmdletBinding()]
param([switch]$NoBrowser)

$ErrorActionPreference = 'Stop'
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$RepoRoot = (Resolve-Path (Join-Path $ScriptDir '..')).Path
$WebDir = Join-Path $RepoRoot 'apps\web'
$LogDir = Join-Path $RepoRoot 'runs\launcher'
$VenvPython = Join-Path $RepoRoot '.venv\Scripts\python.exe'

Write-Host '========================================================================' -ForegroundColor Cyan
Write-Host '  Starting Sovereign AI Workbench - SIH26117' -ForegroundColor Cyan
Write-Host '========================================================================' -ForegroundColor Cyan

if (-not (Test-Path -LiteralPath $VenvPython)) {
    throw "Virtual-environment Python was not found at: $VenvPython"
}
if (-not (Get-Command npm.cmd -ErrorAction SilentlyContinue)) {
    throw 'npm.cmd was not found. Install Node.js or add it to PATH.'
}

New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
Set-Location -LiteralPath $RepoRoot

# Load environment variables from .env if present
$EnvFile = Join-Path $RepoRoot '.env'
if (Test-Path -LiteralPath $EnvFile) {
    Get-Content -LiteralPath $EnvFile | Where-Object { $_ -match '^\s*[^#=]+\s*=' } | ForEach-Object {
        $parts = $_.Split('=', 2)
        $k = $parts[0].Trim()
        $v = $parts[1].Trim().Trim('"').Trim("'")
        if ($k -and -not [string]::IsNullOrWhiteSpace($k)) {
            [System.Environment]::SetEnvironmentVariable($k, $v)
        }
    }
}

# All child processes inherit these settings.
$env:PYTHONPATH = "$RepoRoot;$RepoRoot\packages\shared-schemas;$RepoRoot\packages\security-audit;$RepoRoot\packages\agent-core"
if (-not $env:VLLM_BASE_URL) { $env:VLLM_BASE_URL = 'http://127.0.0.1:8002/v1' }
if (-not $env:VLLM_MODEL_NAME) { $env:VLLM_MODEL_NAME = 'Qwen/Qwen2.5-0.5B-Instruct' }
if (-not $env:QDRANT_URL) { $env:QDRANT_URL = 'http://127.0.0.1:6333' }
if (-not $env:YOLO_SERVICE_URL) { $env:YOLO_SERVICE_URL = 'http://127.0.0.1:8001' }
if (-not $env:AUDIT_DB_PATH) { $env:AUDIT_DB_PATH = Join-Path $RepoRoot 'data\audit_ledger.db' }

function Stop-PortProcess {
    param([int[]]$Ports)
    $connections = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
        Where-Object { $_.LocalPort -in $Ports }
    foreach ($connection in $connections) {
        Write-Host "  Stopping PID $($connection.OwningProcess) on port $($connection.LocalPort)"
        Stop-Process -Id $connection.OwningProcess -Force -ErrorAction SilentlyContinue
    }
}

function Start-LoggedProcess {
    param(
        [string]$Name,
        [string]$FilePath,
        [string[]]$Arguments,
        [string]$WorkingDirectory
    )
    $stdout = Join-Path $LogDir "$Name.out.log"
    $stderr = Join-Path $LogDir "$Name.err.log"
    Remove-Item -LiteralPath $stdout, $stderr -Force -ErrorAction SilentlyContinue
    $process = Start-Process -FilePath $FilePath -ArgumentList $Arguments `
        -WorkingDirectory $WorkingDirectory -WindowStyle Hidden `
        -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
    Write-Host "  $Name started (PID $($process.Id)); error log: $stderr" -ForegroundColor DarkGray
    return $process
}

function Wait-ServiceHealth {
    param(
        [string]$Name,
        [string]$Url,
        [int]$TimeoutSeconds = 30,
        [int]$RequestTimeoutSeconds = 2
    )
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        try {
            Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec $RequestTimeoutSeconds | Out-Null
            Write-Host "  [READY] $Name" -ForegroundColor Green
            return $true
        } catch {
            Start-Sleep -Milliseconds 750
        }
    } while ((Get-Date) -lt $deadline)
    Write-Host "  [NOT READY] $Name - inspect runs\launcher logs" -ForegroundColor Red
    return $false
}

Write-Host "`nStopping stale application processes..." -ForegroundColor Yellow
# Qdrant (6333) is intentionally excluded because Docker may own it.
Stop-PortProcess -Ports @(3000, 8001, 8002, 8080)

Write-Host "`n[1/5] Checking Qdrant..." -ForegroundColor Green
$qdrantReady = $false
try {
    Invoke-WebRequest -Uri 'http://127.0.0.1:6333/healthz' -UseBasicParsing -TimeoutSec 2 | Out-Null
    $qdrantReady = $true
} catch {
    if (Get-Command docker -ErrorAction SilentlyContinue) {
        docker start sovereign-qdrant 2>$null | Out-Null
        if ($LASTEXITCODE -ne 0) {
            docker run -d --name sovereign-qdrant -p 6333:6333 qdrant/qdrant:latest | Out-Null
        }
        $qdrantReady = Wait-ServiceHealth -Name 'Qdrant' -Url 'http://127.0.0.1:6333/healthz' -TimeoutSeconds 20
    } else {
        Write-Host '  [OPTIONAL] Docker/Qdrant unavailable; local fixture retrieval will be used.' -ForegroundColor Yellow
    }
}
if ($qdrantReady) { Write-Host '  [READY] Qdrant' -ForegroundColor Green }

Write-Host "`n[2/5] Starting local LLM/VLM service..." -ForegroundColor Green
$llm = Start-LoggedProcess -Name 'llm' -FilePath $VenvPython `
    -Arguments @('-m', 'uvicorn', 'apps.vllm_service:app', '--host', '127.0.0.1', '--port', '8002') `
    -WorkingDirectory $RepoRoot

Write-Host "`n[3/5] Starting YOLO service..." -ForegroundColor Green
$yolo = Start-LoggedProcess -Name 'yolo' -FilePath $VenvPython `
    -Arguments @('-m', 'uvicorn', 'apps.yolo_service:app', '--host', '127.0.0.1', '--port', '8001') `
    -WorkingDirectory $RepoRoot

$llmReady = Wait-ServiceHealth -Name 'LLM/VLM' -Url 'http://127.0.0.1:8002/health' -TimeoutSeconds 120
$yoloReady = Wait-ServiceHealth -Name 'YOLO' -Url 'http://127.0.0.1:8001/health' -TimeoutSeconds 60

Write-Host "`n[4/5] Starting API..." -ForegroundColor Green
$api = Start-LoggedProcess -Name 'api' -FilePath $VenvPython `
    -Arguments @('-m', 'uvicorn', 'apps.api.main:app', '--host', '127.0.0.1', '--port', '8080') `
    -WorkingDirectory $RepoRoot
$apiReady = Wait-ServiceHealth -Name 'API' -Url 'http://127.0.0.1:8080/health' -TimeoutSeconds 90

Write-Host "`n[5/5] Starting Next.js dashboard..." -ForegroundColor Green
$web = Start-LoggedProcess -Name 'web' -FilePath 'npm.cmd' `
    -Arguments @('run', 'dev', '--', '--hostname', '127.0.0.1') `
    -WorkingDirectory $WebDir
$webReady = Wait-ServiceHealth -Name 'Web UI' -Url 'http://127.0.0.1:3000' `
    -TimeoutSeconds 120 -RequestTimeoutSeconds 15

Write-Host "`n========================================================================" -ForegroundColor Cyan
if ($apiReady -and $webReady) {
    Write-Host '  Workbench started. Open a NEW CHAT before retesting the P&ID.' -ForegroundColor Green
} else {
    Write-Host '  Startup was incomplete. Check the launcher logs.' -ForegroundColor Red
}
Write-Host '  Web UI:  http://127.0.0.1:3000' -ForegroundColor Cyan
Write-Host '  API:     http://127.0.0.1:8080' -ForegroundColor Cyan
Write-Host "  Logs:    $LogDir" -ForegroundColor Cyan
Write-Host '========================================================================' -ForegroundColor Cyan

if (-not $NoBrowser -and $webReady) { Start-Process 'http://127.0.0.1:3000' }
if (-not $llmReady) {
    Write-Warning 'P&ID interpretation will report vision unavailable until LLM/VLM is healthy.'
}
if (-not $yoloReady) {
    Write-Warning 'Symbol bounding-box detection will be unavailable until YOLO is healthy.'
}
