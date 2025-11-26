#!/bin/sh
# RESERVED VM HARVESTER - BULLETPROOF SUPERVISOR VERSION
# Uses /bin/sh for production compatibility
# Auto-restarts workers if they die

echo "========================================"
echo "Orchid Continuum Reserved VM Harvester"
echo "========================================"
echo "Started: $(date)"

# Verify DATABASE_URL exists
if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: DATABASE_URL not set"
    exit 1
fi

# Test database connectivity
echo "Testing database connection..."
python3 -c "
import psycopg2, os, sys
try:
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM orchid_taxonomy')
    count = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM orchid_images')
    images = cur.fetchone()[0]
    print('Database connected: {} species, {} images'.format(count, images))
    cur.close()
    conn.close()
except Exception as e:
    print('Database error: {}'.format(e))
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo "Database connection failed"
    exit 1
fi

echo ""
echo "Starting supervised workers..."

# Function to run a worker with auto-restart
run_worker() {
    WORKER_NAME=$1
    while true; do
        echo "[SUPERVISOR] Starting $WORKER_NAME..."
        python3 workers/gbif_expanded_worker.py "$WORKER_NAME"
        EXIT_CODE=$?
        echo "[SUPERVISOR] $WORKER_NAME exited with code $EXIT_CODE, restarting in 10s..."
        sleep 10
    done
}

# Start 5 supervised workers in background
run_worker gbif-vm-1 &
run_worker gbif-vm-2 &
run_worker gbif-vm-3 &
run_worker gbif-vm-4 &
run_worker gbif-vm-5 &

# Start API Fallback Coordinator with auto-restart
while true; do
    echo "[SUPERVISOR] Starting API Fallback Coordinator..."
    python3 workers/api_fallback_coordinator.py
    echo "[SUPERVISOR] Coordinator exited, restarting in 10s..."
    sleep 10
done &

echo ""
echo "========================================"
echo "All harvesters running with supervision"
echo "========================================"

# Keep the main process alive
wait
