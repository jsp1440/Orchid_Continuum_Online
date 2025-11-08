#!/bin/bash
set -e
LIBSTDCPP_DIR="$(dirname "$(find /nix/store -type f -name 'libstdc++.so.6' -print -quit)")"
export LD_LIBRARY_PATH="$LIBSTDCPP_DIR:${LD_LIBRARY_PATH:-}"
echo "✅ Using libstdc++.so.6 from: $LIBSTDCPP_DIR"

# Optional: show numpy/pandas versions
python - <<'PY'
import sys, importlib
for m in ("numpy","pandas"):
    try:
        mod = importlib.import_module(m)
        print(f"✅ {m} {mod.__version__} @ {mod.__file__}")
    except Exception as e:
        print(f"⚠️  {m} import issue:", e)
print("🐍 Python:", sys.version)
PY

# Start GBIF enrichment in background
echo ""
echo "🚀 Starting GBIF Image Enrichment (background)..."
python -u validation/enrich_gbif_stable.py > /tmp/gbif_stable.log 2>&1 &
ENRICHMENT_PID=$!
echo "✅ Enrichment running (PID: $ENRICHMENT_PID)"
echo "   Monitor with: tail -f /tmp/gbif_stable.log"
echo ""

# Start Flask application in foreground
echo "🌸 Starting Flask application..."
exec gunicorn --workers 2 --bind 0.0.0.0:5000 --timeout 120 --access-logfile - --error-logfile - main:app
