#!/bin/bash
# Run Problem A with Test Map
# Usage: ./run_problem_a.sh

echo "🎯 Starting Problem A with Test Map"
echo "=================================="

# Check if map_test.json exists
if [ ! -f "map_test.json" ]; then
    echo "❌ Error: map_test.json not found!"
    exit 1
fi

# Check if problem_a.py exists
if [ ! -f "problem_a.py" ]; then
    echo "❌ Error: problem_a.py not found!"
    exit 1
fi

echo "✅ Map file: map_test.json"
echo "✅ Problem file: problem_a.py"
echo ""

# Set environment variables for map
export MAP_FILE="map_test.json"
export PROBLEM_TYPE="A"
export START_NODE="1"
export END_NODE="9"

echo "🔧 Configuration:"
echo "   Map: $MAP_FILE"
echo "   Problem: $PROBLEM_TYPE"
echo "   Start: Node $START_NODE"
echo "   End: Node $END_NODE"
echo ""

# Run Problem A
echo "🚀 Launching Problem A..."
echo "Press Ctrl+C to stop"
echo ""

python3 problem_a.py