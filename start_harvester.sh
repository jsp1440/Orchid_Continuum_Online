#!/bin/bash
# ORCHID HARVESTER - STABLE RUNNER
# Keeps harvester running continuously with auto-restart

echo "🌺 Starting Orchid Harvester..."
echo "Process will run continuously in background"
echo ""

while true; do
    echo "[$(date '+%I:%M:%S %p')] Starting harvester cycle..."
    python3 -u replit_harvester_working.py 2>&1 | tee -a harvester_log.txt
    
    # If it exits, wait 5 seconds and restart
    echo "[$(date '+%I:%M:%S %p')] Harvester stopped. Restarting in 5 seconds..."
    sleep 5
done
