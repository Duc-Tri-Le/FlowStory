@echo off
chcp 65001 >nul
title FlowStory Launcher

echo ========================================================
echo   🎬 FlowStory - Khởi chạy Hệ thống (Backend + Frontend)
echo ========================================================
echo.

:: 1. Kiểm tra môi trường Python
set PY_CMD=python
if exist .venv\Scripts\python.exe (
    set PY_CMD=.venv\Scripts\python.exe
    echo [*] Tìm thấy và kích hoạt môi trường ảo: .venv
) else (
    echo [*] Sử dụng Python toàn cục trên máy tính
)

:: 2. Khởi động Backend API Agent (Cổng 8100)
echo [*] Đang khởi động Backend Server tại http://127.0.0.1:8100 ...
start "FlowStory Backend (:8100)" cmd /k "%PY_CMD% -m agent.main"

:: Đợi 2 giây để backend khởi động
timeout /t 2 /nobreak >nul

:: 3. Khởi động Frontend Dashboard (Cổng 5173)
echo [*] Đang khởi động Frontend Dashboard tại http://localhost:5173 ...
start "FlowStory Dashboard (:5173)" cmd /k "cd dashboard && npm run dev"

:: Đợi 3 giây rồi mở trình duyệt
timeout /t 3 /nobreak >nul
echo.
echo ========================================================
echo   🚀 Mở trình duyệt Dashboard: http://localhost:5173
echo   🩺 Kiểm tra API Backend:     http://127.0.0.1:8100/docs
echo ========================================================
start http://localhost:5173

echo.
echo Hệ thống đã được khởi chạy trong 2 cửa sổ terminal riêng biệt.
echo Để tắt hệ thống: Đóng các cửa sổ Backend và Dashboard tương ứng.
