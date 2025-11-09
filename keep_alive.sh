#!/bin/bash
# Keep harvesters running and ping periodically to prevent sleep
echo "🌺 Starting Keep-Alive Harvester Service"
echo "========================================"

# Start harvesters
./start_harvesters.sh

# Keep process alive and show status every 5 minutes
while true; do
    sleep 300  # 5 minutes
    echo ""
    echo "⏰ Status Check - $(date)"
    python3 check_harvester_status.py | tail -5
    
    # Check if workers are still running
    WORKER_COUNT=$(ps aux | grep -E '(gbif|inat|idigbio|tropicos|eol_ala)_worker.py' | grep -v grep | wc -l)
    if [ "$WORKER_COUNT" -eq "0" ]; then
        echo "⚠️  Workers stopped - restarting..."
        ./start_harvesters.sh
    else
        echo "✅ $WORKER_COUNT workers still running"
    fi
done
