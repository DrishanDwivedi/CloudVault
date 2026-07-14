@echo off
title CloudVault Dependency Installer
echo ===================================================
echo             CLOUDVAULT DEPENDENCY SETUP
echo ===================================================
echo.

set "APP_DIR=%~dp0"
cd /d "%APP_DIR%"

:: 1. Create Python Virtual Environment if missing
if not exist "%APP_DIR%.venv" (
    echo [INFO] Python virtual environment (.venv) not found.
    echo [INFO] Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment. Please make sure Python is installed and in your PATH.
        pause
        exit /b 1
    )
)

:: 2. Upgrade pip and install backend requirements
echo [INFO] Installing Python backend requirements...
"%APP_DIR%.venv\Scripts\python.exe" -m pip install --upgrade pip
"%APP_DIR%.venv\Scripts\pip.exe" install -r "%APP_DIR%backend\requirements.txt"
if errorlevel 1 (
    echo [ERROR] Failed to install backend requirements.
    pause
    exit /b 1
)
echo [PASS] Backend requirements installed successfully.
echo.

:: 3. Install frontend requirements
if exist "%APP_DIR%frontend" (
    echo [INFO] Installing frontend node packages...
    cd /d "%APP_DIR%frontend"
    call npm install
    if errorlevel 1 (
        echo [ERROR] Failed to install frontend dependencies.
        cd /d "%APP_DIR%"
        pause
        exit /b 1
    )
    echo [PASS] Frontend dependencies installed successfully.
    cd /d "%APP_DIR%"
) else (
    echo [WARNING] frontend/ folder not found. Skipping frontend dependencies setup.
)

echo.
echo ===================================================
echo         DEPENDENCIES INSTALLED SUCCESSFULLY
echo ===================================================
echo Next steps:
echo   1. Run setup_services.bat (to download storage binaries)
echo   2. Run start.bat (to launch the system)
echo ===================================================
pause
