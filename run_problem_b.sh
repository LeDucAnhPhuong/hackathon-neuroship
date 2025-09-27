#!/bin/bash
# Run Problem B with Test Map
# Usage: ./run_problem_b.sh

echo "🎯 Starting Problem B with Test Map"
echo "=================================="

# Check if map_test.json exists
if [ ! -f "map_test.json" ]; then
    echo "❌ Error: map_test.json not found!"
    exit 1
fi

# Check if problem_b.py exists
if [ ! -f "problem_b.py" ]; then
    echo "❌ Error: problem_b.py not found!"
    exit 1
fi

echo "✅ Map file: map_test.json"
echo "✅ Problem file: problem_b.py"
echo ""

# Set environment variables for map
export MAP_FILE="map_test.json"
export PROBLEM_TYPE="B"
export START_NODE="1"
export LOAD_NODES="4,5,6"  # Example load nodes
export END_NODE="9"

echo "🔧 Configuration:"
echo "   Map: $MAP_FILE"
echo "   Problem: $PROBLEM_TYPE"
echo "   Start: Node $START_NODE"
echo "   Load Nodes: $LOAD_NODES"
echo "   End: Node $END_NODE"
echo ""

# Run Problem B
echo "🚀 Launching Problem B..."
echo "Press Ctrl+C to stop"
echo ""

python3 problem_b.py