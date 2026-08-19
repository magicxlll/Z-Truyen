@echo off
chcp 65001 >nul
title Đóng gói Z-Truyen cho Android

echo ======================================================================
echo    ĐÓNG GÓI Z-TRUYEN ĐỂ CHUYỂN SANG ĐIỆN THOẠI ANDROID
echo ======================================================================
echo.

set OUTPUT_ZIP=%~dp0..\ztruyen-android.zip

echo [*] Đang nén mã nguồn Z-Truyen vào file: ztruyen-android.zip...
powershell -Command "Compress-Archive -Path '%~dp0..\backend', '%~dp0..\android' -DestinationPath '%OUTPUT_ZIP%' -Force"

echo.
echo [OK] ĐÃ TẠO THÀNH CÔNG: ztruyen-android.zip (ở thư mục gốc dự án)
echo.
echo 📱 BẠN CÓ THỂ CHUYỂN FILE NÀY SANG ĐIỆN THOẠI BẰNG:
echo    1. Cáp USB cắm vào điện thoại
echo    2. Gửi qua Quick Share / Zalo / Telegram / Google Drive
echo.
echo 📖 Xem hướng dẫn cài đặt tại docs\ANDROID_SMARTPHONE_HOST_GUIDE.md
echo ======================================================================
pause
