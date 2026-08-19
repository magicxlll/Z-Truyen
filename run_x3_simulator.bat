@echo off
chcp 65001 >nul
title MÁY ẢO XTEINK X3 — E-INK OPDS READER SIMULATOR

echo ======================================================================
echo       📱 MÁY ẢO XTEINK X3 — TRÌNH MÔ PHỎNG E-READER CROSSVI / OPDS
echo ======================================================================
echo.
echo  Mô phỏng 100%% cơ chế duyệt thư viện OPDS, tìm kiếm, đọc từng chương
echo  và tải EPUB chuẩn hóa trên máy đọc sách E-ink Xteink X3.
echo.
echo ----------------------------------------------------------------------

:: 1. Tìm Python trên máy Windows
set "PY_EXE="
if exist "C:\miniconda3\python.exe" set "PY_EXE=C:\miniconda3\python.exe"
if "%PY_EXE%"=="" if exist "%~dp0.venv\Scripts\python.exe" set "PY_EXE=%~dp0.venv\Scripts\python.exe"
if "%PY_EXE%"=="" (
    where python >nul 2>nul
    if %errorlevel% equ 0 set "PY_EXE=python"
)
if "%PY_EXE%"=="" (
    where py >nul 2>nul
    if %errorlevel% equ 0 set "PY_EXE=py"
)

if "%PY_EXE%"=="" (
    echo ❌ Không tìm thấy Python trên máy tính!
    echo Vui lòng cài đặt Python hoặc kích hoạt môi trường ảo.
    pause
    exit /b 1
)

:: 2. Nhập URL của Pocket Host Server
echo.
echo  🌐 CẤU HÌNH KẾT NỐI MÁY CHỦ:
echo     - Nếu Server đang chạy trên Điện thoại phát Hotspot: Nhập http://192.168.43.1:8080
echo     - Nếu Server đang chạy cùng mạng Wi-Fi với máy tính: Nhập IP điện thoại (VD: http://192.168.1.5:8080)
echo     - Nếu chạy Backend ngay trên máy tính: Bấm ENTER để dùng mặc định [http://localhost:8080]
echo.
set "HOST_URL=http://localhost:8080"
set /p "USER_INPUT=👉 Nhập URL Server (bấm Enter để dùng mặc định %HOST_URL%): "
if not "%USER_INPUT%"=="" set "HOST_URL=%USER_INPUT%"

echo.
echo [*] Đang kết nối tới máy chủ: %HOST_URL% ...
echo ----------------------------------------------------------------------
echo.

"%PY_EXE%" "%~dp0scripts\opds_simulator.py" --url "%HOST_URL%"

echo.
pause
