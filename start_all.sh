#!/bin/bash
set -e

# Set up environment
LIBSTDCPP_DIR="$(dirname "$(find /nix/store -type f -name 'libstdc++.so.6' -print -quit)")"
export LD_LIBRARY_PATH="$LIBSTDCPP_DIR:${LD_LIBRARY_PATH:-}"
echo "✅ Using libstdc++.so.6 from: $LIBSTDCPP_DIR"

# Start GBIF enrichment in background
echo "🚀 Starting GBIF enrichment collector..."
python -u validation/enrich_gbif_stable.py > /tmp/gbif_stable.log 2>&1 &
ENRICHMENT_PID=$!
echo "✅ Enrichment started (PID: $ENRICHMENT_PID)"

# Wait a moment for enrichment to initialize
sleep 2

# Start Flask app in foreground
echo "🌸 Starting Flask application..."
exec gunicorn --workers 2 --bind 0.0.0.0:5000 --timeout 120 --access-logfile - --error-logfile - main:app
