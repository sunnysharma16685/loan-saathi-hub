Write-Host "=== Loan Saathi Hub: Pre-Deploy Checklist ===" -ForegroundColor Cyan

# Step 1: Syntax check
Write-Host "`n[1/4] Checking Python syntax..."
python -m py_compile manage.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Syntax error detected. Fix before deploying." -ForegroundColor Red
    exit 1
}

# Step 2: Migrations dry-run check
Write-Host "`n[2/4] Checking for pending migrations..."
python manage.py makemigrations --check --dry-run
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Unapplied model changes detected. Run makemigrations first." -ForegroundColor Red
    exit 1
}

# Step 3: Apply migrations
Write-Host "`n[3/4] Applying migrations..."
python manage.py migrate
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Migration failed. Check models and DB connection." -ForegroundColor Red
    exit 1
}

# Step 4: Runserver sanity test (short run)
Write-Host "`n[4/4] Starting Django dev server (5s test)..."
$process = Start-Process -FilePath "python" -ArgumentList "manage.py runserver" -PassThru
Start-Sleep -Seconds 5
Stop-Process -Id $process.Id -Force
Write-Host "✅ Dev server started successfully." -ForegroundColor Green

Write-Host "`n=== Pre-deploy checks passed! You can deploy safely. ===" -ForegroundColor Cyan
