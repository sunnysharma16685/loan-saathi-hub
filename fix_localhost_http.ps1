Write-Host "=== Loan Saathi Hub — Localhost HTTP Fixer ===" -ForegroundColor Cyan

# --- 1. Close Chrome / Edge completely
Write-Host "`n[1/5] Closing Chrome and Edge..." -ForegroundColor Yellow
Get-Process chrome, msedge -ErrorAction SilentlyContinue | Stop-Process -Force

Start-Sleep -Seconds 2

# --- 2. Clear HSTS & Network cache for Chrome / Edge
$chromePath = "$env:LOCALAPPDATA\Google\Chrome\User Data\Default"
$edgePath   = "$env:LOCALAPPDATA\Microsoft\Edge\User Data\Default"

Write-Host "[2/5] Clearing HTTPS cache (HSTS)..." -ForegroundColor Yellow
Remove-Item "$chromePath\TransportSecurity" -ErrorAction SilentlyContinue
Remove-Item "$chromePath\Network Persistent State" -ErrorAction SilentlyContinue
Remove-Item "$edgePath\TransportSecurity" -ErrorAction SilentlyContinue
Remove-Item "$edgePath\Network Persistent State" -ErrorAction SilentlyContinue

# --- 3. Ensure core system paths exist
Write-Host "[3/5] Ensuring System32 paths are accessible..." -ForegroundColor Yellow
if ($env:Path -notmatch "System32") {
    $env:Path += ";C:\Windows;C:\Windows\System32;C:\Windows\System32\WindowsPowerShell\v1.0"
}

# --- 4. Free up port 8000 if occupied
Write-Host "[4/5] Checking if port 8000 is busy..." -ForegroundColor Yellow
$portCheck = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($portCheck) {
    Stop-Process -Id $portCheck.OwningProcess -Force -ErrorAction SilentlyContinue
    Write-Host "   Port 8000 was busy — cleared." -ForegroundColor Green
}
else {
    Write-Host "   Port 8000 is free." -ForegroundColor Green
}

# --- 5. Start Django server inside your venv
Write-Host "[5/5] Starting Django development server (HTTP only)..." -ForegroundColor Cyan
$venvPython = "C:\Users\sunny\OneDrive\Documents\GitHub\loan-saathi-hub\.venv312\Scripts\python.exe"

if (Test-Path $venvPython) {
    & $venvPython manage.py runserver 127.0.0.1:8000 --insecure
}
else {
    Write-Host "❌ Python executable not found. Please activate your venv manually." -ForegroundColor Red
}
