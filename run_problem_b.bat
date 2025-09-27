@echo off
REM Run Problem B with Test Map
REM Usage: run_problem_b.bat

echo 🎯 Starting Problem B with Test Map
echo ==================================

REM Check if map_test.json exists
if not exist "map_test.json" (
    echo ❌ Error: map_test.json not found!
    pause
    exit /b 1
)

REM Check if problem_b.py exists
if not exist "problem_b.py" (
    echo ❌ Error: problem_b.py not found!
    pause
    exit /b 1
)

echo ✅ Map file: map_test.json
echo ✅ Problem file: problem_b.py
echo.

REM Set environment variables for map
set MAP_FILE=map_test.json
set PROBLEM_TYPE=B
set START_NODE=1
set LOAD_NODES=4,5,6
set END_NODE=9

echo 🔧 Configuration:
echo    Map: %MAP_FILE%
echo    Problem: %PROBLEM_TYPE%
echo    Start: Node %START_NODE%
echo    Load Nodes: %LOAD_NODES%
echo    End: Node %END_NODE%
echo.

REM Run Problem B
echo 🚀 Launching Problem B...
echo Press Ctrl+C to stop
echo.

python problem_b.py
pause