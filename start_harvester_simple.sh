#!/bin/bash
# FINAL HARVESTER STARTUP - Production Ready

echo "🌺 Starting Orchid Continuum Harvesters..."

# Wait for database to be ready (30 seconds max)
echo "Waiting for database..."
for i in {1..30}; do
  python3 -c "
import psycopg2, os
try:
  conn = psycopg2.connect(os.environ['DATABASE_URL'])
  conn.close()
  print('✅ Database ready')
  exit(0)
except:
  exit(1)
" && break || sleep 1
done

# Verify database schema exists
python3 << 'EOF'
import psycopg2, os
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM harvest_jobs")
print(f"✅ harvest_jobs table accessible: {cur.fetchone()[0]} rows")
cur.close()
conn.close()
EOF

# Start workers
echo "Starting 5 GBIF workers..."
python3 workers/gbif_expanded_worker.py gbif-1 &
python3 workers/gbif_expanded_worker.py gbif-2 &
python3 workers/gbif_expanded_worker.py gbif-3 &
python3 workers/gbif_expanded_worker.py gbif-4 &
python3 workers/gbif_expanded_worker.py gbif-5 &

echo "Starting API Fallback Coordinator..."
python3 workers/api_fallback_coordinator.py &

echo "🌺 All harvesters started. Monitoring..."
wait
