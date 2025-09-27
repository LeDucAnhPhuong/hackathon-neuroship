@echo off
REM Run Problem A with Test Map
REM Usage: run_problem_a.bat

echo 🎯 Starting Problem A with Test Map
echo ==================================

REM Check if map_test.json exists
if not exist "map_test.json" (
    echo ❌ Error: map_test.json not found!
    pause
    exit /b 1
)

REM Check if problem_a.py exists
if not exist "problem_a.py" (
    echo ❌ Error: problem_a.py not found!
    pause
    exit /b 1
)

echo ✅ Map file: map_test.json
echo ✅ Problem file: problem_a.py
echo.

REM Set environment variables for map
set MAP_FILE=map_test.json
set PROBLEM_TYPE=A
set START_NODE=1
set END_NODE=9

echo 🔧 Configuration:
echo    Map: %MAP_FILE%
echo    Problem: %PROBLEM_TYPE%
echo    Start: Node %START_NODE%
echo    End: Node %END_NODE%
echo.

REM Run Problem A
echo 🚀 Launching Problem A...
echo Press Ctrl+C to stop
echo.

python problem_a.py
pause