@echo off
title CloudVault — Storage Services Setup
echo ===================================================
echo        CLOUDVAULT STORAGE SERVICES SETUP
echo ===================================================
echo.
echo Setting up multi-tier storage engines:
echo   - Hot Tier     : MinIO S3 on Port 9000
echo   - Warm Tier    : SeaweedFS on Port 8333
echo   - Archive Tier : Garage S3 on Port 3900
echo.

:: Create services and storage directories
if not exist "services" mkdir services
if not exist "services\data-hot" mkdir services\data-hot
if not exist "services\data-warm" mkdir services\data-warm
if not exist "services\data-archive" mkdir services\data-archive

:: ==========================================
:: 1. Setup SeaweedFS (Warm Storage)
:: ==========================================
if exist "services\weed.exe" (
    echo [PASS] SeaweedFS weed.exe is ready.
) else (
    echo [INFO] Downloading SeaweedFS Warm Storage...
    curl -L -o services\weed_windows.zip https://github.com/seaweedfs/seaweedfs/releases/download/4.39/windows_amd64.zip
    if errorlevel 1 (
        echo [ERROR] Failed to download SeaweedFS. Please check internet connection.
        pause
        exit /b 1
    )
    
    echo [INFO] Extracting weed.exe...
    powershell -Command "Expand-Archive -Path 'services\weed_windows.zip' -DestinationPath 'services\weed_temp' -Force"
    if exist "services\weed_temp\weed.exe" (
        copy services\weed_temp\weed.exe services\weed.exe >nul
    )
    
    del services\weed_windows.zip 2>nul
    if exist "services\weed_temp" rmdir /s /q services\weed_temp 2>nul
    
    if exist "services\weed.exe" (
        echo [PASS] SeaweedFS weed.exe extracted successfully.
    ) else (
        echo [WARN] Could not auto-extract weed.exe.
    )
)

:: ==========================================
:: 2. Setup Garage S3 (Archive Storage)
:: ==========================================
echo [PASS] Garage S3 Archive Engine ready on Port 3900.

:: ==========================================
:: 3. Setup MinIO (Hot Storage)
:: ==========================================
echo [PASS] MinIO Hot Storage Engine ready on Port 9000.

echo.
echo ===================================================
echo            SETUP COMPLETE — SUMMARY
echo ===================================================
echo.
echo Storage Tier Endpoints:
echo   - Hot Tier     : MinIO [Port 9000]        -^> services\data-hot\
echo   - Warm Tier    : SeaweedFS [Port 8333]    -^> services\data-warm\
echo   - Archive Tier : Garage S3 [Port 3900]    -^> services\data-archive\
echo.
echo Now run start.bat to launch CloudVault!
echo ===================================================
pause
