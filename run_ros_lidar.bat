@echo off
REM Run Original ROS LIDAR Follower with Test Map
REM Usage: run_ros_lidar.bat [A|B|C]

set PROBLEM=%1
if "%PROBLEM%"=="" set PROBLEM=A

echo 🎯 Starting ROS LIDAR Follower with Test Map
echo ============================================

REM Check if map_test.json exists
if not exist "map_test.json" (
    echo ❌ Error: map_test.json not found!
    pause
    exit /b 1
)

REM Check if ros_lidar_follower.py exists
if not exist "ros_lidar_follower.py" (
    echo ❌ Error: ros_lidar_follower.py not found!
    pause
    exit /b 1
)

echo ✅ Map file: map_test.json
echo ✅ Problem file: ros_lidar_follower.py
echo.

REM Set environment variables
set MAP_FILE=map_test.json
set PROBLEM_TYPE=%PROBLEM%
set START_NODE=1
set END_NODE=9

if "%PROBLEM%"=="A" (
    set LOAD_NODES=
    echo 🔧 Problem A Configuration:
    echo    Navigation: START → END
) else if "%PROBLEM%"=="B" (
    set LOAD_NODES=4,5,6
    echo 🔧 Problem B Configuration:
    echo    Navigation: START → Load Nodes → END
    echo    Load Nodes: %LOAD_NODES%
) else if "%PROBLEM%"=="C" (
    set LOAD_NODES=
    echo 🔧 Problem C Configuration:
    echo    Navigation: Sign-based (dynamic)
) else (
    echo ❌ Unknown problem type: %PROBLEM%
    echo Usage: run_ros_lidar.bat [A^|B^|C]
    pause
    exit /b 1
)

echo    Map: %MAP_FILE%
echo    Problem: %PROBLEM_TYPE%
echo    Start: Node %START_NODE%
echo    End: Node %END_NODE%
echo.

REM Run ROS LIDAR Follower
echo 🚀 Launching ROS LIDAR Follower...
echo Press Ctrl+C to stop
echo.

python ros_lidar_follower.py
pause