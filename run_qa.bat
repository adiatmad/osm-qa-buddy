@echo off
setlocal

cd /d "%~dp0"
echo ========================================
echo OSM QA Buddy - Native Windows
echo ========================================
echo.

set "PYTHON="

py -3.12 -c "import sys; raise SystemExit(0 if sys.version_info >= (3,12) else 1)" >nul 2>&1
if not errorlevel 1 set "PYTHON=py -3.12"

if not defined PYTHON (
    python -c "import sys; raise SystemExit(0 if sys.version_info >= (3,12) else 1)" >nul 2>&1
    if not errorlevel 1 set "PYTHON=python"
)

if not defined PYTHON (
    echo Python 3.12+ was not found.
    echo Install Python 3.12+ with Tkinter and try again.
    pause
    exit /b 1
)

echo Using Python: %PYTHON%
%PYTHON% setup_native.py
if errorlevel 1 (
    echo.
    echo Native prerequisite setup failed.
    pause
    exit /b 1
)

echo.
echo Starting OSM QA Buddy GUI...
%PYTHON% app.py
if errorlevel 1 (
    echo.
    echo The application failed to start.
    pause
    exit /b 1
)
endlocal
