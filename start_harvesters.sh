#!/bin/bash
# Persistent Harvester Launcher
# Runs all 17 source-specific workers in background and keeps them alive

echo "🌺 Starting Orchid Harvester Fleet"
echo "=================================="

# Create logs directory
mkdir -p logs

# Function to start a worker
start_worker() {
    local script=$1
    local worker_id=$2
    local log_file="logs/${worker_id}.log"
    
    # Start worker in background with auto-restart on crash
    while true; do
        python3 -u "$script" "$worker_id" >> "$log_file" 2>&1
        echo "[$(date '+%H:%M:%S')] $worker_id crashed, restarting in 5s..." >> "$log_file"
        sleep 5
    done &
    
    echo "✓ Started $worker_id (restart loop: PID $!)"
}

# Start all 17 workers
echo ""
echo "🌍 Starting 8 GBIF workers..."
for i in {1..8}; do
    start_worker "workers/gbif_worker.py" "gbif-$i"
done

echo "🦋 Starting 3 iNaturalist workers..."
for i in {1..3}; do
    start_worker "workers/inaturalist_worker.py" "inat-$i"
done

echo "🏛️ Starting 2 iDigBio workers..."
for i in {1..2}; do
    start_worker "workers/idigbio_worker.py" "idigbio-$i"
done

echo "🌿 Starting 2 Tropicos workers..."
for i in {1..2}; do
    start_worker "workers/tropicos_worker.py" "tropicos-$i"
done

echo "📚 Starting 1 BHL worker..."
start_worker "workers/bhl_worker.py" "bhl-1"

echo "🌎 Starting 1 EOL+ALA worker..."
start_worker "workers/eol_ala_worker.py" "eol-ala-1"

echo ""
echo "=================================="
echo "✅ All 17 workers launched with auto-restart!"
echo "=================================="
echo ""
echo "Monitor progress:"
echo "  python3 check_harvester_status.py"
echo ""
echo "View logs:"
echo "  tail -f logs/gbif-1.log"
echo ""

# Keep script running
wait
