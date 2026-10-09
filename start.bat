@echo off
title CloudVault Launcher
echo ===================================================
echo             CLOUDVAULT SYSTEM LAUNCHER
echo ===================================================
echo.

set "APP_DIR=%~dp0"
set "VENV_PY=%APP_DIR%.venv\Scripts\python.exe"
set "SERVICE_DIR=%APP_DIR%services"

if not exist "%VENV_PY%" (
    if exist "%APP_DIR%venv\Scripts\python.exe" (
        set "VENV_PY=%APP_DIR%venv\Scripts\python.exe"
    )
)

if not exist "%VENV_PY%" (
    if exist "%APP_DIR%..\venv\Scripts\python.exe" (
        set "VENV_PY=%APP_DIR%..\venv\Scripts\python.exe"
    )
)

REM ==========================================
REM PRE-FLIGHT CHECKS
REM ==========================================

REM Kill any leftover processes from previous runs
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":9000 :9001 :3900 :3901 :8333 :8888 :8000"') do (
    taskkill /F /PID %%a >nul 2>&1
)
ping 127.0.0.1 -n 2 >nul

if not exist "%VENV_PY%" (
    echo [ERROR] Virtual environment .venv was not found.
    echo Please run install_requirements.bat first.
    pause
    exit /b 1
)

if not exist "%APP_DIR%frontend\node_modules\.bin\vite.cmd" (
    echo [ERROR] Frontend dependencies are not installed.
    echo Please run cd frontend and npm install.
    pause
    exit /b 1
)

if not exist "%SERVICE_DIR%\data-hot"     mkdir "%SERVICE_DIR%\data-hot"
if not exist "%SERVICE_DIR%\data-warm"    mkdir "%SERVICE_DIR%\data-warm"
if not exist "%SERVICE_DIR%\data-archive" mkdir "%SERVICE_DIR%\data-archive"

REM Ensure default buckets exist
if not exist "%SERVICE_DIR%\data-hot\cloudvault-hot"         mkdir "%SERVICE_DIR%\data-hot\cloudvault-hot"
if not exist "%SERVICE_DIR%\data-warm\cloudvault-warm"       mkdir "%SERVICE_DIR%\data-warm\cloudvault-warm"
if not exist "%SERVICE_DIR%\data-archive\cloudvault-archive" mkdir "%SERVICE_DIR%\data-archive\cloudvault-archive"

REM ==========================================
REM 1. START MINIO - HOT STORAGE (port 9000)
REM ==========================================
echo [INFO] Starting MinIO Hot Storage on port 9000...
start "MinIO Hot Storage [port 9000]" /D "%SERVICE_DIR%" cmd /k "..\.venv\Scripts\python.exe s3_node.py data-hot 9000 MinIO_Hot_Storage"

REM ==========================================
REM 2. START GARAGE S3 - ARCHIVE STORAGE (port 3900)
REM ==========================================
echo [INFO] Starting Garage S3 Archive Storage on port 3900...
start "Garage S3 Archive Storage [port 3900]" /D "%SERVICE_DIR%" cmd /k "..\.venv\Scripts\python.exe s3_node.py data-archive 3900 Garage_S3_Archive_Storage"

REM ==========================================
REM 3. START SEAWEEDFS - WARM STORAGE (port 8333)
REM ==========================================
if exist "%SERVICE_DIR%\weed.exe" (
    echo [INFO] Starting SeaweedFS Warm Storage on port 8333...
    start "SeaweedFS Warm Storage [port 8333]" /D "%SERVICE_DIR%" cmd /k "weed.exe server -s3 -dir=data-warm -master.dir=data-warm -s3.port=8333 -master.volumeSizeLimitMB=128 -volume.max=100"
) else (
    echo [INFO] Starting Warm Storage Node on port 8333...
    start "SeaweedFS Warm Storage [port 8333]" /D "%SERVICE_DIR%" cmd /k "..\.venv\Scripts\python.exe s3_node.py data-warm 8333 SeaweedFS_Warm_Storage"
)

REM ==========================================
REM 4. INITIALIZE STORAGE BUCKETS
REM ==========================================
echo.
echo [INFO] Initializing storage buckets...
ping 127.0.0.1 -n 3 >nul

echo [INFO] Hot bucket     cloudvault-hot     ready.
echo [INFO] Warm bucket    cloudvault-warm    ready.
echo [INFO] Archive bucket cloudvault-archive ready.

REM ==========================================
REM 5. START BACKEND (FastAPI)
REM ==========================================
echo.
echo [INFO] Starting Backend Server on port 8000...
start "CloudVault Backend [port 8000]" /D "%APP_DIR%backend" cmd /k "..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000"

REM Wait a moment for backend to start
ping 127.0.0.1 -n 3 >nul

REM ==========================================
REM 6. START FRONTEND (Vite)
REM ==========================================
echo [INFO] Starting Frontend Dev Server on port 5173...
start "CloudVault Frontend [port 5173]" /D "%APP_DIR%frontend" cmd /k "npm run dev"

REM ==========================================
REM SUMMARY
REM ==========================================
echo.
echo ===================================================
echo [SUCCESS] CloudVault launched successfully!
echo ===================================================
echo.
echo  STORAGE SERVICES:
echo  - Hot     [MinIO]     : http://localhost:9000
echo  - Warm    [SeaweedFS] : http://localhost:8333
echo  - Archive [Garage S3]  : http://localhost:3900
echo.
echo  APP SERVICES:
echo  - Frontend            : http://localhost:5173
echo  - Backend             : http://127.0.0.1:8000
echo  - API Docs            : http://127.0.0.1:8000/docs
echo.
echo  LOGIN CREDENTIALS:
echo  - Web Dashboard       : admin@example.com / Admin@123
echo  - Storage Services    : garage_admin / garage_secret_key_123
echo.
echo ---------------------------------------------------
echo  Close any cmd window to stop that service.
echo ===================================================
echo.
pause
