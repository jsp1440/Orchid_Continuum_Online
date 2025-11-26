#!/bin/bash
# Production harvester runner - no migrations, just pure workers

echo "🌺 Orchid Continuum - Production Harvester"
echo "=========================================="

# Test database connection
python3 << 'TESTEOF'
import psycopg2, os, sys
try:
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM orchid_taxonomy")
    count = cur.fetchone()[0]
    print(f"✅ Database: {count:,} species in taxonomy")
    cur.close()
    conn.close()
except Exception as e:
    print(f"❌ Database error: {e}")
    sys.exit(1)
TESTEOF

# Start workers
echo ""
echo "Starting harvesters..."
python3 workers/gbif_expanded_worker.py gbif-1 &
python3 workers/gbif_expanded_worker.py gbif-2 &
python3 workers/gbif_expanded_worker.py gbif-3 &
python3 workers/gbif_expanded_worker.py gbif-4 &
python3 workers/gbif_expanded_worker.py gbif-5 &
python3 workers/api_fallback_coordinator.py &

echo "✅ All workers started"
wait
