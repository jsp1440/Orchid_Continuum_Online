#!/bin/bash
# Launch Multiple Autonomous Orchid Workers
# Usage: ./launch_multiple_workers.sh [number_of_workers]

NUM_WORKERS=${1:-5}  # Default to 5 workers if not specified

echo "🚀 Launching $NUM_WORKERS autonomous orchid workers..."
echo ""

# Create logs directory
mkdir -p logs

# Start Julius AI Scraper (only need 1)
echo "1️⃣ Starting Julius AI Scraper (discovers orchids)..."
nohup python julius_ai_scraper_worker.py > logs/julius_scraper.log 2>&1 &
echo "   Started PID $!"

sleep 2

# Start multiple download workers
echo ""
echo "2️⃣ Starting $NUM_WORKERS download workers..."
for i in $(seq 1 $NUM_WORKERS); do
    nohup python standalone_image_worker.py > logs/worker_$i.log 2>&1 &
    worker_pid=$!
    echo "   Worker $i started (PID $worker_pid)"
    sleep 0.5
done

echo ""
echo "✅ SYSTEM LAUNCHED!"
echo ""
echo "📊 Expected Performance:"
images_per_hour=$((1380 * NUM_WORKERS))
echo "   ~$images_per_hour images/hour"
echo ""
echo "📝 Monitor logs:"
echo "   tail -f logs/worker_1.log"
echo ""
echo "🛑 Stop all workers:"
echo "   pkill -f julius_ai_scraper_worker"
echo "   pkill -f standalone_image_worker"
echo ""
echo "🌸 Happy collecting!"
