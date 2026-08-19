# Development startup script for Z-Truyen Backend on Windows PowerShell
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location "$ScriptDir\..\backend"

Write-Host "=== Starting Z-Truyen Backend (Windows Development Mode) ===" -ForegroundColor Green

if (-not (Test-Path ".venv")) {
    Write-Host "Creating Python virtual environment..."
    python -m venv .venv
}

& .venv\Scripts\Activate.ps1
pip install -e ".[dev]"

Write-Host "Starting Uvicorn Server on http://localhost:8080..." -ForegroundColor Cyan
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
