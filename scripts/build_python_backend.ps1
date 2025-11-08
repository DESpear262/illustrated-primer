# Build Python backend executable using PyInstaller
# Run this from project root

Write-Host "Building Python backend executable..." -ForegroundColor Green

# Check if venv is activated
if (-not $env:VIRTUAL_ENV) {
    Write-Host "Warning: Virtual environment not detected. Activating venv..." -ForegroundColor Yellow
    if (Test-Path "venv\Scripts\Activate.ps1") {
        & "venv\Scripts\Activate.ps1"
    } else {
        Write-Host "Error: venv not found. Please create and activate a virtual environment first." -ForegroundColor Red
        exit 1
    }
}

# Install PyInstaller if not already installed
Write-Host "Checking PyInstaller installation..." -ForegroundColor Cyan
pip install pyinstaller | Out-Null

# Build executable - ensure we're in project root
$projectRoot = Split-Path $PSScriptRoot -Parent
Push-Location $projectRoot

Write-Host "Running PyInstaller from: $projectRoot" -ForegroundColor Cyan
$specPath = Join-Path $PSScriptRoot "build_backend.spec"

# Check source file timestamps
$sourceFile = Join-Path $projectRoot "start_backend.py"
if (Test-Path $sourceFile) {
    $sourceInfo = Get-Item $sourceFile
    Write-Host "Source file: $sourceFile" -ForegroundColor Cyan
    Write-Host "  Modified: $($sourceInfo.LastWriteTime)" -ForegroundColor Cyan
}

# Clean previous build artifacts
Write-Host "Cleaning previous build artifacts..." -ForegroundColor Cyan
$buildDir = Join-Path $projectRoot "build\build_backend"
$distDir = Join-Path $projectRoot "dist\backend"
if (Test-Path $buildDir) {
    Remove-Item $buildDir -Recurse -Force -ErrorAction SilentlyContinue
}
if (Test-Path $distDir) {
    Remove-Item $distDir -Recurse -Force -ErrorAction SilentlyContinue
}

# Run PyInstaller with clean flag
Write-Host "Running PyInstaller..." -ForegroundColor Cyan
pyinstaller --clean --noconfirm $specPath

Pop-Location

# Check if build succeeded
$exePath = Join-Path $projectRoot "dist\backend\backend.exe"
if (Test-Path $exePath) {
    $exeInfo = Get-Item $exePath
    Write-Host "Backend executable built successfully: $exePath" -ForegroundColor Green
    Write-Host "  Size: $($exeInfo.Length) bytes" -ForegroundColor Cyan
    Write-Host "  Modified: $($exeInfo.LastWriteTime)" -ForegroundColor Cyan
    
    # Copy to Tauri resources directory (for bundled resources)
    $tauriResources = Join-Path $projectRoot "frontend\src-tauri\resources"
    New-Item -ItemType Directory -Force -Path $tauriResources | Out-Null
    $resourcesDest = Join-Path $tauriResources "backend.exe"
    Copy-Item $exePath $resourcesDest -Force
    Write-Host "Copied to Tauri resources: $resourcesDest" -ForegroundColor Green
    
    # Also copy to src-tauri root (Tauri looks for resources relative to src-tauri)
    $tauriRoot = Join-Path $projectRoot "frontend\src-tauri"
    $rootDest = Join-Path $tauriRoot "backend.exe"
    Copy-Item $exePath $rootDest -Force
    Write-Host "Copied to Tauri root: $rootDest" -ForegroundColor Green
    
    # Verify both copies
    if (Test-Path $resourcesDest) {
        $resourcesInfo = Get-Item $resourcesDest
        Write-Host "  Resources copy verified: $($resourcesInfo.Length) bytes, $($resourcesInfo.LastWriteTime)" -ForegroundColor Cyan
    } else {
        Write-Host "  WARNING: Resources copy not found!" -ForegroundColor Yellow
    }
    
    if (Test-Path $rootDest) {
        $rootInfo = Get-Item $rootDest
        Write-Host "  Root copy verified: $($rootInfo.Length) bytes, $($rootInfo.LastWriteTime)" -ForegroundColor Cyan
    } else {
        Write-Host "  WARNING: Root copy not found!" -ForegroundColor Yellow
    }
} else {
    Write-Host "Error: Build failed. Executable not found at: $exePath" -ForegroundColor Red
    Write-Host "Expected location: $exePath" -ForegroundColor Yellow
    exit 1
}

