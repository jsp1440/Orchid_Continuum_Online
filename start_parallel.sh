#!/bin/bash
# Start 8 parallel harvesters

echo "🌺 Starting 8 Parallel Orchid Harvesters..."
echo "Each instance will work on different species batches"
echo ""

# Kill any existing harvesters
pkill -9 -f parallel_harvester.py 2>/dev/null
sleep 1

# Start 8 instances
for i in {0..7}; do
    python3 -u parallel_harvester.py $i 8 >> harvester_${i}.log 2>&1 &
    PID=$!
    echo "Started Harvester #$i (PID: $PID)"
    sleep 0.5
done

echo ""
echo "✅ All 8 harvesters running!"
echo "Monitor with: tail -f harvester_*.log"
echo "Check status: python3 check_harvester_status.py"
