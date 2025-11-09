#!/bin/bash
echo "🌺 Starting Orchid Harvester Fleet for Production"
echo "=================================================="
echo ""

# Start all 17 harvesters with auto-restart
./start_harvesters.sh

# Keep the deployment alive and monitor
while true; do
    sleep 300  # Check every 5 minutes
    
    # Count active workers
    WORKER_COUNT=$(ps aux | grep -E '(gbif|inat|idigbio|tropicos|eol_ala)_worker.py' | grep -v grep | wc -l)
    
    if [ "$WORKER_COUNT" -eq "0" ]; then
        echo "⚠️  $(date): Workers stopped - restarting..."
        ./start_harvesters.sh
    else
        echo "✅ $(date): $WORKER_COUNT workers running"
        python3 check_harvester_status.py | grep "Images:"
    fi
done
