@echo off
title Claude Kill Switch - Installer
cd /d "%~dp0"

echo ===================================================
echo     Claude Kill Switch - Setup & Installation
echo ===================================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python not found on your system!
    echo Please install Python 3.10+ from https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo [*] Installing required Python dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo [OK] Setup completed successfully!
echo You can now launch the app using run.bat or run_silent.vbs.
echo.
pause
