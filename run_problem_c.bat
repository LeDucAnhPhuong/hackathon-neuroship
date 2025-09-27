@echo off
REM Run Problem C with Test Map
REM Usage: run_problem_c.bat

echo 🎯 Starting Problem C with Test Map
echo ==================================

REM Check if problem_c.py exists
if not exist "problem_c.py" (
    echo ❌ Error: problem_c.py not found!
    pause
    exit /b 1
)

echo ✅ Problem file: problem_c.py
echo.

REM Set environment variables
set PROBLEM_TYPE=C
set START_NODE=1
set END_NODE=9
echo ⚠️  Note: Problem C uses sign-based navigation (no pre-loaded map)

echo 🔧 Configuration:
echo    Problem: %PROBLEM_TYPE%
echo    Navigation: Sign-based (dynamic)
echo    Start: Conceptual Node %START_NODE%
echo    End: Detected via 'L' signs
echo.

REM Run Problem C
echo 🚀 Launching Problem C...
echo Press Ctrl+C to stop
echo.

python problem_c.py
pause