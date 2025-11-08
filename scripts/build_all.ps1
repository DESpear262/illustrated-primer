# Complete build script for Tauri app
# Run from project root

Write-Host "=== Building AI Tutor Desktop App ===" -ForegroundColor Cyan

# Step 1: Build Python backend
Write-Host "`n[1/4] Building Python backend..." -ForegroundColor Yellow
Write-Host "Current directory: $(Get-Location)" -ForegroundColor Gray
Write-Host "Script directory: $PSScriptRoot" -ForegroundColor Gray
& "$PSScriptRoot\build_python_backend.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Backend build failed!" -ForegroundColor Red
    exit 1
}

# Verify backend.exe was copied correctly
$backendExe = Join-Path (Get-Location) "frontend\src-tauri\backend.exe"
if (Test-Path $backendExe) {
    $info = Get-Item $backendExe
    Write-Host "Verified backend.exe at: $backendExe" -ForegroundColor Green
    Write-Host "  Size: $($info.Length) bytes, Modified: $($info.LastWriteTime)" -ForegroundColor Cyan
} else {
    Write-Host "WARNING: backend.exe not found at expected location: $backendExe" -ForegroundColor Yellow
}

# Step 2: Build frontend
Write-Host "`n[2/4] Building frontend..." -ForegroundColor Yellow
Set-Location frontend
npm run build
if ($LASTEXITCODE -ne 0) {
    Write-Host "Frontend build failed!" -ForegroundColor Red
    Set-Location ..
    exit 1
}
Set-Location ..

# Step 3: Update tauri.conf.json to include backend.exe resource
Write-Host "`n[3/4] Updating Tauri config..." -ForegroundColor Yellow
$tauriConfigPath = Join-Path (Get-Location) "frontend\src-tauri\tauri.conf.json"
$tauriConfig = Get-Content $tauriConfigPath | ConvertFrom-Json
$tauriConfig.bundle.resources = @("backend.exe")
$tauriConfig | ConvertTo-Json -Depth 10 | Set-Content $tauriConfigPath
Write-Host "Updated tauri.conf.json to include backend.exe" -ForegroundColor Green

# Step 4: Build Tauri app
Write-Host "`n[4/4] Building Tauri app..." -ForegroundColor Yellow
Write-Host "Verifying backend.exe exists before Tauri build..." -ForegroundColor Cyan
$backendExe = Join-Path (Get-Location) "frontend\src-tauri\backend.exe"
if (Test-Path $backendExe) {
    $info = Get-Item $backendExe
    Write-Host "  Found: $backendExe ($($info.Length) bytes, $($info.LastWriteTime))" -ForegroundColor Green
} else {
    Write-Host "  ERROR: backend.exe not found! Tauri build will fail." -ForegroundColor Red
    exit 1
}
Set-Location frontend
npm run tauri:build
if ($LASTEXITCODE -ne 0) {
    Write-Host "Tauri build failed!" -ForegroundColor Red
    Set-Location ..
    exit 1
}
Set-Location ..

Write-Host "`n=== Build Complete ===" -ForegroundColor Green
Write-Host "Executable location: frontend\src-tauri\target\release\ai-tutor.exe" -ForegroundColor Cyan

