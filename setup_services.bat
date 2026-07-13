@echo off
title CloudVault — Storage Services Setup
echo ===================================================
echo        CLOUDVAULT STORAGE SERVICES SETUP
echo ===================================================
echo.
echo This script downloads MinIO and SeaweedFS binaries
echo into the services\ folder. Run this ONCE before
echo starting the app for the first time.
echo.

:: Create services directory
if not exist "services" mkdir services
if not exist "services\data-hot" mkdir services\data-hot
if not exist "services\data-warm" mkdir services\data-warm
if not exist "services\data-archive" mkdir services\data-archive

:: ==========================================
:: 1. Download MinIO
:: ==========================================
if exist "services\minio.exe" (
    echo [SKIP] minio.exe already exists, skipping download.
) else (
    echo [INFO] Downloading MinIO ^(Hot Storage^)...
    curl -L -o services\minio.exe https://dl.min.io/server/minio/release/windows-amd64/minio.exe
    if errorlevel 1 (
        echo [ERROR] Failed to download minio.exe. Check your internet connection.
        pause
        exit /b 1
    )
    echo [PASS] minio.exe downloaded successfully.
)

:: ==========================================
:: 2. Download MinIO Client (mc) for bucket creation
:: ==========================================
if exist "services\mc.exe" (
    echo [SKIP] mc.exe already exists, skipping download.
) else (
    echo [INFO] Downloading MinIO Client ^(mc.exe^)...
    curl -L -o services\mc.exe https://dl.min.io/client/mc/release/windows-amd64/mc.exe
    if errorlevel 1 (
        echo [ERROR] Failed to download mc.exe. Check your internet connection.
        pause
        exit /b 1
    )
    echo [PASS] mc.exe downloaded successfully.
)

:: ==========================================
:: 3. Download SeaweedFS
:: ==========================================
if exist "services\weed.exe" (
    echo [SKIP] weed.exe already exists, skipping download.
) else (
    echo [INFO] Downloading SeaweedFS ^(Warm Storage^)...
    echo       ^(Fetching latest release URL from GitHub...^)
    
    :: Download the latest windows_amd64 release archive
    :: We use the stable version URL directly
    curl -L -o services\weed_windows.tar.gz https://github.com/seaweedfs/seaweedfs/releases/download/3.68/windows_amd64.tar.gz
    if errorlevel 1 (
        echo [WARN] Failed to download SeaweedFS from primary URL.
        echo       Trying alternative version 3.65...
        curl -L -o services\weed_windows.tar.gz https://github.com/seaweedfs/seaweedfs/releases/download/3.65/windows_amd64.tar.gz
        if errorlevel 1 (
            echo [ERROR] Failed to download SeaweedFS. Please download manually from:
            echo         https://github.com/seaweedfs/seaweedfs/releases
            echo         Extract weed.exe and place it in the services\ folder.
            pause
            exit /b 1
        )
    )
    
    :: Extract weed.exe from the tar.gz using PowerShell
    echo [INFO] Extracting weed.exe...
    powershell -Command "& { Add-Type -AssemblyName System.IO.Compression.FileSystem; try { $tar = [System.IO.Compression.TarFile]::ExtractToDirectory('services\weed_windows.tar.gz', 'services\weed_temp') } catch { tar -xzf 'services\weed_windows.tar.gz' -C 'services\weed_temp' 2>$null } }"
    
    :: Try PowerShell tar command (available on Windows 10+)
    tar -xzf services\weed_windows.tar.gz -C services\ weed.exe 2>nul
    if not exist "services\weed.exe" (
        :: Try extracting from a temp folder
        if not exist "services\weed_temp" mkdir services\weed_temp
        tar -xzf services\weed_windows.tar.gz -C services\weed_temp\ 2>nul
        if exist "services\weed_temp\weed.exe" (
            copy services\weed_temp\weed.exe services\weed.exe >nul
            rmdir /s /q services\weed_temp 2>nul
        )
    )
    
    :: Cleanup archive
    del services\weed_windows.tar.gz 2>nul
    if exist "services\weed_temp" rmdir /s /q services\weed_temp 2>nul
    
    if exist "services\weed.exe" (
        echo [PASS] weed.exe extracted successfully.
    ) else (
        echo [WARN] Could not auto-extract weed.exe.
        echo        Please download manually from:
        echo        https://github.com/seaweedfs/seaweedfs/releases
        echo        Extract weed.exe into the services\ folder and re-run this script.
    )
)

echo.
echo ===================================================
echo            SETUP COMPLETE — SUMMARY
echo ===================================================
echo.
echo Files in services\ folder:
dir /b services\*.exe 2>nul
echo.
echo Data directories:
echo   Hot  (MinIO)     : services\data-hot\
echo   Warm (SeaweedFS) : services\data-warm\
echo   Archive (MinIO2) : services\data-archive\
echo.
echo Now run start.bat to launch all services.
echo ===================================================
pause
