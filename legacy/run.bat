@echo off
echo ============================================
echo  Spelling Numbers Calculator - MODERN
echo ============================================
echo.

py launch.py

if errorlevel 1 (
    echo.
    echo Application exited with an error.
    pause
)
