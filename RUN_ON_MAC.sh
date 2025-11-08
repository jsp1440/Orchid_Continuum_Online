#!/bin/bash
# Orchid Harvester - Mac Setup Script
# Run this on your Mac terminal

echo "🌺 Setting up Orchid Harvester on Mac..."

# Step 1: Set database connection (REPLACE WITH ACTUAL DATABASE_URL)
export DATABASE_URL="GET_THIS_FROM_REPLIT_SECRETS"

# Step 2: Download worker script (if not already downloaded)
# You'll need to copy queue_worker.py from Replit to your Mac first

# Step 3: Run workers (you can run up to 4 simultaneously)
echo "Starting 4 workers..."

python3 queue_worker.py mac-worker-1 > mac_worker_1.log 2>&1 &
echo "Started mac-worker-1 (PID: $!)"

python3 queue_worker.py mac-worker-2 > mac_worker_2.log 2>&1 &
echo "Started mac-worker-2 (PID: $!)"

python3 queue_worker.py mac-worker-3 > mac_worker_3.log 2>&1 &
echo "Started mac-worker-3 (PID: $!)"

python3 queue_worker.py mac-worker-4 > mac_worker_4.log 2>&1 &
echo "Started mac-worker-4 (PID: $!)"

echo ""
echo "✅ All 4 Mac workers running!"
echo ""
echo "To monitor:"
echo "  tail -f mac_worker_1.log"
echo ""
echo "To stop all workers:"
echo "  pkill -f queue_worker.py"
