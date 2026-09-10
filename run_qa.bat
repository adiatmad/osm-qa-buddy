@echo off
setlocal

cd /d "%~dp0"
echo ========================================
echo OSM QA Buddy - Native Windows
 echo ========================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo Python was not found.
    echo Install Python 3.12+ with Tkinter and try again.
    pause
    exit /b 1
)

python setup_native.py
if errorlevel 1 (
    echo.
    echo Native prerequisite setup failed.
    pause
    exit /b 1
)

echo.
echo Starting OSM QA Buddy GUI...
python app.py
if errorlevel 1 (
    echo.
    echo The application failed to start.
    pause
    exit /b 1
)
endlocal
