@echo off
setlocal
chcp 65001 >nul
title MAY AO XTEINK X3 — E-INK OPDS READER SIMULATOR

set "PY_EXE="
if exist "C:\miniconda3\python.exe" set "PY_EXE=C:\miniconda3\python.exe"
if not defined PY_EXE if exist "%~dp0.venv\Scripts\python.exe" set "PY_EXE=%~dp0.venv\Scripts\python.exe"
if not defined PY_EXE if exist "%~dp0backend\.venv\Scripts\python.exe" set "PY_EXE=%~dp0backend\.venv\Scripts\python.exe"
if not defined PY_EXE (
    where python >nul 2>nul
    if not errorlevel 1 set "PY_EXE=python"
)
if not defined PY_EXE (
    where py >nul 2>nul
    if not errorlevel 1 set "PY_EXE=py"
)

if not defined PY_EXE (
    echo [ERROR] Khong tim thay Python tren may tinh!
    pause
    exit /b 1
)

"%PY_EXE%" "%~dp0scripts\opds_simulator.py"

if %errorlevel% neq 0 (
    echo.
    pause
)
