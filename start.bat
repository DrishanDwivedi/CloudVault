@echo off
title CloudVault Launcher
echo ===================================================
echo             CLOUDVAULT SYSTEM LAUNCHER
echo ===================================================
echo.

REM ==========================================
REM PRE-FLIGHT CHECKS
REM ==========================================

REM Kill any leftover processes from previous runs
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":9000 :9001 :9010 :9011 :18000 :8333 :8888 :9333 :8000"') do (
    taskkill /F /PID %%a >nul 2>&1
)
timeout /t 2 /nobreak >nul
if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment 'venv' not found.
    echo Please run the initial setup commands first.
    pause
    exit /b 1
)

if not exist "services\minio.exe" (
    echo [ERROR] services\minio.exe not found!
    echo Please run setup_services.bat first to download storage binaries.
    pause
    exit /b 1
)

if not exist "services\data-hot"     mkdir services\data-hot
if not exist "services\data-warm"    mkdir services\data-warm

REM ==========================================
REM 1. START MINIO - HOT STORAGE (port 9000)
REM ==========================================
echo [INFO] Starting MinIO - Hot Storage (port 9000, UI: 9001)...
start "MinIO Hot Storage [port 9000]" cmd /k "set MINIO_ROOT_USER=cloudvault_admin&& set MINIO_ROOT_PASSWORD=minio_secure_password_123&& services\minio.exe server services\data-hot --address :9000 --console-address :9001"

REM ==========================================
REM 2. START SCALITY S3 SERVER - ARCHIVE STORAGE (port 18000)
REM ==========================================
if not exist "services\data-archive" mkdir services\data-archive
echo [INFO] Starting Scality S3 Server Emulator (MinIO on port 18000)...
start "Scality S3 Server Emulator [port 18000]" cmd /k "set MINIO_ROOT_USER=scality_admin&& set MINIO_ROOT_PASSWORD=scality_secret_key_123&& services\minio.exe server services\data-archive --address :18000 --console-address :18001"

REM ==========================================
REM 3. START SEAWEEDFS - WARM STORAGE (port 8333)
REM ==========================================
if exist "services\weed.exe" (
    echo [INFO] Starting SeaweedFS - Warm Storage on S3 port 8333...
    start "SeaweedFS Warm Storage [port 8333]" cmd /k "services\weed.exe server -s3 -dir=services\data-warm -master.dir=services\data-warm -s3.port=8333 -master.volumeSizeLimitMB=128"
) else (
    echo [WARN] services\weed.exe not found - Warm storage will use fallback mock.
    echo        Run setup_services.bat to download SeaweedFS.
)

REM ==========================================
REM 4. WAIT FOR SERVICES TO BOOT
REM ==========================================
echo.
echo [INFO] Waiting 8 seconds for storage services to initialize...
timeout /t 8 /nobreak >nul

REM ==========================================
REM 5. CREATE BUCKETS via mc.exe (if available)
REM ==========================================
if exist "services\mc.exe" (
    echo [INFO] Configuring storage buckets...
    
    REM Register MinIO Hot with mc
    services\mc.exe alias set cv-hot http://localhost:9000 cloudvault_admin minio_secure_password_123 >nul 2>&1
    REM Create the hot bucket
    services\mc.exe mb cv-hot/cloudvault-hot >nul 2>&1
    echo [INFO]   Hot bucket     'cloudvault-hot'      ready.
    
    REM Register Scality with mc
    services\mc.exe alias set cv-archive http://localhost:18000 scality_admin scality_secret_key_123 >nul 2>&1
    REM Create the archive bucket
    services\mc.exe mb cv-archive/cloudvault-archive >nul 2>&1
    echo [INFO]   Archive bucket  'cloudvault-archive'   ready.

    REM Create SeaweedFS warm bucket via filer HTTP API
    curl -s -X POST http://localhost:8888/buckets/cloudvault-warm/ >nul 2>&1
    if %errorlevel% equ 0 (
        echo [INFO]   Warm bucket    'cloudvault-warm'      created.
    ) else (
        echo [INFO]   Warm bucket    'cloudvault-warm'      already exists.
    )
) else (
    echo [INFO] mc.exe not found, buckets will be auto-created on first upload.
)

REM ==========================================
REM 6. START BACKEND (FastAPI)
REM ==========================================
echo.
echo [INFO] Starting Backend Server (FastAPI on port 8000)...
start "CloudVault Backend [port 8000]" cmd /k "cd backend && ..\venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000"

REM Wait a moment for backend to start
timeout /t 3 /nobreak >nul

REM ==========================================
REM 7. START FRONTEND (Vite)
REM ==========================================
echo [INFO] Starting Frontend Dev Server (Vite on port 5173)...
start "CloudVault Frontend [port 5173]" cmd /k "cd frontend && npm run dev"

REM ==========================================
REM SUMMARY
REM ==========================================
echo.
echo ===================================================
echo [SUCCESS] CloudVault launched successfully!
echo ===================================================
echo.
echo  STORAGE SERVICES:
echo  - Hot     (MinIO): http://localhost:9000  (S3 API)
echo  - Hot UI         : http://localhost:9001  (Web Console)
echo  - Warm (SeaweedFS): http://localhost:8333  (S3 API)
echo  - Warm UI        : http://localhost:8888  (Filer Web UI)
echo  - Archive (Scality S3): http://localhost:18000  (S3 API)
echo.
echo  APP SERVICES:
echo  - Backend       : http://127.0.0.1:8000
echo  - Frontend      : http://localhost:5173
echo  - API Docs      : http://127.0.0.1:8000/docs
echo.
echo  CREDENTIALS:
echo  - Hot (MinIO)  : cloudvault_admin / minio_secure_password_123
echo  - Archive      : scality_admin / scality_secret_key_123
echo.
echo ---------------------------------------------------
echo  Close any cmd window to stop that service.
echo ===================================================
echo.
pause
