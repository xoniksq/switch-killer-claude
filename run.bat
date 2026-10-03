@echo off
title Claude Kill Switch
cd /d "%~dp0"
python main.py
if errorlevel 1 (
    echo.
    echo [ERROR] An error occurred while launching Claude Kill Switch.
    pause
)
