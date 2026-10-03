@echo off
title Claude Kill Switch - Build Standalone EXE
cd /d "%~dp0"

echo ===================================================
echo     Building Standalone ClaudeKillSwitch.exe
echo ===================================================
echo.

python -m pip install pyinstaller
echo [*] Compiling executable via PyInstaller...
python -m PyInstaller --noconsole --onefile --icon="icon.ico" --add-data "icon.ico;." --name "ClaudeKillSwitch" --collect-all customtkinter main.py

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed!
    pause
    exit /b 1
)

echo.
echo ===================================================
echo [OK] Build successful!
echo Executable is located in the 'dist' folder:
echo dist\ClaudeKillSwitch.exe
echo ===================================================
echo.
pause
