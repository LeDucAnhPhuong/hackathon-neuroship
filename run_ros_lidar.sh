#!/bin/bash
# Run Original ROS LIDAR Follower with Test Map
# Usage: ./run_ros_lidar.sh [problem_type]

PROBLEM=${1:-"A"}  # Default to Problem A

echo "🎯 Starting ROS LIDAR Follower with Test Map"
echo "============================================"

# Check if map_test.json exists
if [ ! -f "map_test.json" ]; then
    echo "❌ Error: map_test.json not found!"
    exit 1
fi

# Check if ros_lidar_follower.py exists
if [ ! -f "ros_lidar_follower.py" ]; then
    echo "❌ Error: ros_lidar_follower.py not found!"
    exit 1
fi

echo "✅ Map file: map_test.json"
echo "✅ Problem file: ros_lidar_follower.py"
echo ""

# Set environment variables
export MAP_FILE="map_test.json"
export PROBLEM_TYPE="$PROBLEM"
export START_NODE="1"
export END_NODE="9"

case $PROBLEM in
    "A")
        export LOAD_NODES=""
        echo "🔧 Problem A Configuration:"
        echo "   Navigation: START → END"
        ;;
    "B")
        export LOAD_NODES="4,5,6"
        echo "🔧 Problem B Configuration:"
        echo "   Navigation: START → Load Nodes → END"
        echo "   Load Nodes: $LOAD_NODES"
        ;;
    "C")
        export LOAD_NODES=""
        echo "🔧 Problem C Configuration:"
        echo "   Navigation: Sign-based (dynamic)"
        ;;
    *)
        echo "❌ Unknown problem type: $PROBLEM"
        echo "Usage: ./run_ros_lidar.sh [A|B|C]"
        exit 1
        ;;
esac

echo "   Map: $MAP_FILE"
echo "   Problem: $PROBLEM_TYPE"
echo "   Start: Node $START_NODE"
echo "   End: Node $END_NODE"
echo ""

# Run ROS LIDAR Follower
echo "🚀 Launching ROS LIDAR Follower..."
echo "Press Ctrl+C to stop"
echo ""

python3 ros_lidar_follower.py