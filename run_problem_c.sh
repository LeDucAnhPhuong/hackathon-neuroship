#!/bin/bash
# Run Problem C with Test Map
# Usage: ./run_problem_c.sh

echo "🎯 Starting Problem C with Test Map"
echo "=================================="

# Check if problem_c.py exists
if [ ! -f "problem_c.py" ]; then
    echo "❌ Error: problem_c.py not found!"
    exit 1
fi

echo "✅ Problem file: problem_c.py"
echo ""

# Set environment variables
export PROBLEM_TYPE="C"
export START_NODE="1"
export END_NODE="9"
echo "⚠️  Note: Problem C uses sign-based navigation (no pre-loaded map)"

echo "🔧 Configuration:"
echo "   Problem: $PROBLEM_TYPE"
echo "   Navigation: Sign-based (dynamic)"
echo "   Start: Conceptual Node $START_NODE"
echo "   End: Detected via 'L' signs"
echo ""

# Run Problem C
echo "🚀 Launching Problem C..."
echo "Press Ctrl+C to stop"
echo ""

python3 problem_c.py