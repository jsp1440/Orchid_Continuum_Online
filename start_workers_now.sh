#!/bin/bash

echo "=========================================="
echo "STARTING ORCHID HARVESTER WORKERS"
echo "=========================================="

# Start job seeder
python3 -u continuous_job_seeder.py > /tmp/seeder.log 2>&1 &
SEEDER_PID=$!
echo "Job seeder started (PID: $SEEDER_PID)"

# Start 8 workers (conservative number to avoid crashes)
for i in {1..8}; do
    python3 -u julius_multi_source_worker.py "worker-$i" > /tmp/worker_$i.log 2>&1 &
    WORKER_PID=$!
    echo "Worker $i started (PID: $WORKER_PID)"
    sleep 1
done

echo ""
echo "=========================================="
echo "All workers started!"
echo "=========================================="
echo ""
echo "Monitor logs:"
echo "  tail -f /tmp/worker_1.log"
echo "  tail -f /tmp/seeder.log"
echo ""
echo "To stop all workers:"
echo "  pkill -9 -f julius_multi_source_worker"
