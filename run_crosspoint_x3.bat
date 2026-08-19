@echo off
chcp 65001 >nul
title Khởi chạy Máy ảo Xteink X3 (CrossPoint Virtual Machine)

echo ======================================================================
echo          KÍCH HOẠT MÁY ẢO XTEINK X3 (CROSSPOINT VIRTUAL MACHINE)
echo ======================================================================
echo.

:: 1. Tìm đường dẫn Python trên máy Windows
set "PY_EXE="
if exist "C:\miniconda3\python.exe" set "PY_EXE=C:\miniconda3\python.exe"
if not defined PY_EXE if exist "%~dp0.venv\Scripts\python.exe" set "PY_EXE=%~dp0.venv\Scripts\python.exe"
if not defined PY_EXE if exist "%~dp0backend\.venv\Scripts\python.exe" set "PY_EXE=%~dp0backend\.venv\Scripts\python.exe"
if not defined PY_EXE (
    where python >nul 2>nul
    if not errorlevel 1 set "PY_EXE=python"
)

:: 2. Kiểm tra Backend Z-Truyen có đang chạy không
echo [1/3] Kiểm tra Z-Truyen Backend Server (port 8080)...
netstat -ano | findstr ":8080 " | findstr "LISTENING" >nul
if %errorlevel% neq 0 (
    echo [*] Backend chưa chạy. Đang tự động khởi chạy Backend Z-Truyen...
    if defined PY_EXE (
        start "Z-Truyen Backend Server (Port 8080)" /min cmd /c "cd /d "%~dp0backend" && "%PY_EXE%" -m uvicorn app.main:app --host 0.0.0.0 --port 8080"
    ) else (
        start "Z-Truyen Backend Server (Port 8080)" /min cmd /c "cd /d "%~dp0backend" && python -m uvicorn app.main:app --host 0.0.0.0 --port 8080"
    )
    timeout /t 2 /nobreak >nul
    echo [OK] Backend Z-Truyen đã sẵn sàng tại http://localhost:8080/opds
) else (
    echo [OK] Backend Z-Truyen đang hoạt động tại http://localhost:8080/opds
)

echo.
echo [2/3] Kiểm tra Môi trường WSL Ubuntu & CrossPoint Firmware...
wsl.exe -d Ubuntu -e bash -c "test -f /root/crosspoint-reader/.pio/build/simulator_x3/program"
if %errorlevel% neq 0 (
    echo [!] File binary giả lập chưa sẵn sàng, đang tiến hành biên dịch...
    wsl.exe -d Ubuntu -e bash -c "cd /root/crosspoint-reader && pio run -e simulator_x3"
)

echo [OK] Firmware X3 Simulator đã sẵn sàng!
echo.
echo [3/3] Đang khởi chạy Cửa sổ Máy ảo Xteink X3...
echo ----------------------------------------------------------------------
echo  HƯỚNG DẪN ĐIỀU KHIỂN MÁY ẢO X3 (CROSSPOINT VIRTUAL MACHINE):
echo    - Các phím mũi tên: Di chuyển danh mục / Lật trang sách
echo    - Phím Enter / Space: Chọn / Mở mục (Select/OK)
echo    - Phím ESC / Backspace: Quay lại trang trước (Back)
echo    - Chuột trái: Chạm cảm ứng màn hình (Touch Screen)
echo    - Phím P: Tắt/mở nguồn ảo (Power / Sleep)
echo ----------------------------------------------------------------------
echo.

wsl.exe -d Ubuntu -e /root/crosspoint-reader/run_simulator.sh

pause
