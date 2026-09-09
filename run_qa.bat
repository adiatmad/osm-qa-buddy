@echo off
setlocal

cd /d "%~dp0"
echo ========================================
echo OSM QA Buddy - 3rd Pass Validation
echo ========================================
echo.

where docker >nul 2>&1
if errorlevel 1 (
    echo Docker Desktop / Docker CLI was not found.
    echo Please install Docker Desktop and try again.
    pause
    exit /b 1
)

where python >nul 2>&1
if errorlevel 1 (
    echo Python was not found.
    echo Please install Python 3 with Tkinter and try again.
    pause
    exit /b 1
)

echo Building Docker QA image...
docker build -t qabot
if errorlevel 1 (
    echo.
    echo Docker image build failed.
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
