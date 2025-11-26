#!/bin/bash
# RESERVED VM HARVESTER - Standalone, no Flask, no migrations
# This script runs ONLY the harvester workers - nothing else

echo "========================================"
echo "🌺 Orchid Continuum Reserved VM Harvester"
echo "========================================"
echo "Started: $(date)"

# Verify DATABASE_URL exists
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL not set"
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
    print(f'✅ Database connected: {count:,} species, {images:,} images')
    cur.close()
    conn.close()
except Exception as e:
    print(f'❌ Database error: {e}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ Database connection failed"
    exit 1
fi

echo ""
echo "Starting 5 GBIF harvester workers..."

# Start workers in background
python3 workers/gbif_expanded_worker.py gbif-vm-1 &
PID1=$!
echo "  Worker 1 started (PID $PID1)"

python3 workers/gbif_expanded_worker.py gbif-vm-2 &
PID2=$!
echo "  Worker 2 started (PID $PID2)"

python3 workers/gbif_expanded_worker.py gbif-vm-3 &
PID3=$!
echo "  Worker 3 started (PID $PID3)"

python3 workers/gbif_expanded_worker.py gbif-vm-4 &
PID4=$!
echo "  Worker 4 started (PID $PID4)"

python3 workers/gbif_expanded_worker.py gbif-vm-5 &
PID5=$!
echo "  Worker 5 started (PID $PID5)"

echo ""
echo "Starting API Fallback Coordinator..."
python3 workers/api_fallback_coordinator.py &
PID6=$!
echo "  Coordinator started (PID $PID6)"

echo ""
echo "========================================"
echo "✅ All harvesters running 24/7"
echo "========================================"

# Keep running forever
wait
