#!/bin/bash
# TURBO HARVESTER LAUNCHER - Maximum Performance
# Runs 10 parallel workers with optimized batch processing

echo "========================================"
echo "🚀 TURBO HARVESTER SYSTEM"
echo "========================================"
echo "Started: $(date)"

# Use NEON_DATABASE_URL
if [ -n "$NEON_DATABASE_URL" ]; then
    export DATABASE_URL="$NEON_DATABASE_URL"
    echo "✓ Using NEON_DATABASE_URL"
fi

if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: DATABASE_URL not set"
    exit 1
fi

# Test connection
python3 -c "
import psycopg2, os
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM orchid_images')
print(f'✓ Connected - {cur.fetchone()[0]:,} images in database')
conn.close()
"

echo ""
echo "Starting 10 turbo workers..."

# Run 10 turbo workers
for i in {1..10}; do
    (
        while true; do
            python3 workers/gbif_turbo_worker.py "turbo-$i" 2>&1 | head -100
            echo "[SUPERVISOR] turbo-$i crashed, restarting in 5s..."
            sleep 5
        done
    ) &
    echo "  Started turbo-$i"
done

echo ""
echo "========================================"
echo "10 turbo workers running"
echo "========================================"

wait
