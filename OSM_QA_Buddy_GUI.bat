@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
title OSM QA Buddy - JOSM GUI Bridge

:menu
cls
echo ================================================
echo          OSM QA Buddy - JOSM GUI Bridge
echo ================================================
echo.
echo   1. Start a NEW QA run
echo   2. FINALIZE the latest QA run
echo   3. Update QA Buddy from GitHub
echo   4. Exit
echo.
choice /c 1234 /n /m "Choose [1-4]: "
if errorlevel 4 exit /b 0
if errorlevel 3 goto update
if errorlevel 2 goto finalize
if errorlevel 1 goto prepare

:check_python
set "PYTHON="
py -3.12 -c "import sys; raise SystemExit(0 if sys.version_info >= (3,12) else 1)" >nul 2>&1
if not errorlevel 1 set "PYTHON=py -3.12"
if not defined PYTHON (
    python -c "import sys; raise SystemExit(0 if sys.version_info >= (3,12) else 1)" >nul 2>&1
    if not errorlevel 1 set "PYTHON=python"
)
if not defined PYTHON (
    echo.
    echo ERROR: Python 3.12+ was not found.
    echo Install Python 3.12+ and try again.
    pause
    goto menu
)
exit /b 0

:prepare
call :check_python
if errorlevel 1 goto menu

echo.
echo Checking dependencies...
%PYTHON% -c "import shapely" >nul 2>&1
if errorlevel 1 (
    echo Shapely is missing. Installing project requirements...
    %PYTHON% -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo ERROR: Could not install requirements.
        pause
        goto menu
    )
)

where osmium >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Osmium was not found on PATH.
    echo Make sure "osmium --version" works in Command Prompt.
    pause
    goto menu
)

echo.
echo Select the OSM PBF file...
for /f "delims=" %%F in ('powershell -NoProfile -STA -Command "Add-Type -AssemblyName System.Windows.Forms; $d=New-Object System.Windows.Forms.OpenFileDialog; $d.Title='Select OSM PBF'; $d.Filter='OSM PBF (*.osm.pbf)|*.osm.pbf|All files (*.*)|*.*'; $d.Multiselect=$false; if($d.ShowDialog() -eq 'OK'){[Console]::WriteLine($d.FileName)}"') do set "PBF=%%F"
if not defined PBF (
    echo No PBF selected.
    pause
    goto menu
)

echo.
echo Select the Task Grid GeoJSON file...
for /f "delims=" %%F in ('powershell -NoProfile -STA -Command "Add-Type -AssemblyName System.Windows.Forms; $d=New-Object System.Windows.Forms.OpenFileDialog; $d.Title='Select Task Grid GeoJSON'; $d.Filter='GeoJSON (*.geojson;*.json)|*.geojson;*.json|All files (*.*)|*.*'; $d.Multiselect=$false; if($d.ShowDialog() -eq 'OK'){[Console]::WriteLine($d.FileName)}"') do set "TASKS=%%F"
if not defined TASKS (
    echo No Task Grid selected.
    pause
    goto menu
)

for /f "delims=" %%T in ('powershell -NoProfile -Command "(Get-Date).ToString('yyyyMMdd_HHmmss')"') do set "STAMP=%%T"
set "OUTPUT=%CD%\gui_runs\%STAMP%"
if not exist "%CD%\gui_runs" mkdir "%CD%\gui_runs"

echo.
echo ================================================
echo Preparing QA run...
echo ================================================
echo PBF:   %PBF%
echo Tasks: %TASKS%
echo Output: %OUTPUT%
echo.

%PYTHON% -u gui_pipeline.py prepare "%PBF%" "%TASKS%" "%OUTPUT%"
if errorlevel 1 (
    echo.
    echo ERROR: QA preparation failed.
    pause
    goto menu
)

> "%CD%\.gui_session.txt" (
    echo TASKS=%TASKS%
    echo OUTPUT=%OUTPUT%
)

echo.
echo Opening sample.osm in the default OSM/JOSM application...
start "" "%OUTPUT%\sample.osm"

echo.
echo ================================================
echo JOSM HANDOFF READY
echo ================================================
echo.
echo In JOSM:
echo   1. Run Validator: Shift+V
echo   2. Select the Validation errors layer
echo   3. File -^> Save As
echo   4. Save the validation results as XML
echo.
echo Then come back here and choose:
echo   2. FINALIZE the latest QA run
echo.
echo Your run folder is:
echo %OUTPUT%
echo.
pause
goto menu

:finalize
call :check_python
if errorlevel 1 goto menu

if not exist "%CD%\.gui_session.txt" (
    echo.
    echo No previous QA run was found.
    echo Start a NEW QA run first.
    pause
    goto menu
)

set "TASKS="
set "OUTPUT="
for /f "usebackq tokens=1,* delims==" %%A in ("%CD%\.gui_session.txt") do (
    if /i "%%A"=="TASKS" set "TASKS=%%B"
    if /i "%%A"=="OUTPUT" set "OUTPUT=%%B"
)

if not defined TASKS (
    echo Session file is incomplete.
    pause
    goto menu
)
if not defined OUTPUT (
    echo Session file is incomplete.
    pause
    goto menu
)

if not exist "%TASKS%" (
    echo.
    echo ERROR: The original Task Grid file no longer exists:
    echo %TASKS%
    pause
    goto menu
)

echo.
echo Latest run:
echo %OUTPUT%
echo.
echo Select the XML file exported by JOSM...
for /f "delims=" %%F in ('powershell -NoProfile -STA -Command "Add-Type -AssemblyName System.Windows.Forms; $d=New-Object System.Windows.Forms.OpenFileDialog; $d.Title='Select JOSM Validation XML'; $d.Filter='JOSM Validation XML (*.xml)|*.xml|All files (*.*)|*.*'; $d.Multiselect=$false; if($d.ShowDialog() -eq 'OK'){[Console]::WriteLine($d.FileName)}"') do set "XML=%%F"
if not defined XML (
    echo No XML selected.
    pause
    goto menu
)

echo.
echo ================================================
echo Finalizing QA run...
echo ================================================
echo Tasks: %TASKS%
echo XML:   %XML%
echo Output: %OUTPUT%
echo.

set "QABOT_WORK_DIR=%CD%\work"
%PYTHON% -u gui_pipeline.py finalize "%TASKS%" "%XML%" "%OUTPUT%"
if errorlevel 1 (
    echo.
    echo ERROR: QA finalization failed.
    pause
    goto menu
)

echo.
echo ================================================
echo QA RUN COMPLETE
echo ================================================
echo.
echo Results:
echo   %OUTPUT%\task_grid_qa_summary.geojson
echo   %OUTPUT%\qa_errors.geojson
echo   %OUTPUT%\report.html
echo   %OUTPUT%\map.html
echo.
echo Opening the report...
start "" "%OUTPUT%\report.html"
echo Opening the map...
start "" "%OUTPUT%\map.html"
echo.
pause
goto menu

:update
echo.
echo ================================================
echo Updating QA Buddy from GitHub
echo ================================================
echo.
git fetch origin
if errorlevel 1 (
    echo.
    echo WARNING: GitHub update failed. Your local copy was not changed.
    pause
    goto menu
)

git checkout main
if errorlevel 1 (
    echo.
    echo ERROR: Could not switch to main.
    pause
    goto menu
)

git pull --ff-only
if errorlevel 1 (
    echo.
    echo WARNING: Fast-forward update failed.
    echo No reset or forced update was performed.
    pause
    goto menu
)

echo.
echo QA Buddy is now on the latest main branch.
git log -1 --oneline
echo.
pause
goto menu
