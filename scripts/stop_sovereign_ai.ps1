# ==============================================================================
# Sovereign AI Workbench (SIH26117) — Stop All Services Script
# ==============================================================================
Write-Host 'Stopping all Sovereign AI Workbench backend and frontend services...' -ForegroundColor Yellow

$TargetPorts = @(3000, 6333, 8001, 8002, 8080)
Get-NetTCPConnection -LocalPort $TargetPorts -ErrorAction SilentlyContinue | ForEach-Object {
    Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
}

Write-Host '[✓] Stopped all background microservice processes on ports 3000, 6333, 8001, 8002, 8080.' -ForegroundColor Green
