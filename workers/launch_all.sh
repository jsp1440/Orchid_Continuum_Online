#!/bin/bash
# Master Launcher for Source-Specific Workers
# ============================================
# Starts all 17 workers distributed across 7 API sources
# Usage: ./workers/launch_all.sh

echo "🌺 Launching Orchid Continuum Multi-Source Harvesters"
echo "======================================================"
echo ""

# Create logs directory if it doesn't exist
mkdir -p logs

# Make scripts executable
chmod +x workers/*.py

# Check required environment variables
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL not set"
    exit 1
fi

if [ -z "$TROPICOS_API_KEY" ]; then
    echo "⚠️  WARNING: TROPICOS_API_KEY not set (Tropicos workers will skip)"
fi

if [ -z "$BHL_API_KEY" ]; then
    echo "⚠️  WARNING: BHL_API_KEY not set (BHL workers will skip)"
fi

echo ""
echo "Starting workers in background..."
echo ""

# GBIF Workers (8 workers - main source)
echo "🌍 Starting 8 GBIF workers..."
for i in {1..8}; do
    python3 workers/gbif_worker.py "gbif-$i" > logs/gbif-$i.log 2>&1 &
    echo "  ✓ gbif-$i (PID: $!)"
done

# iNaturalist Workers (3 workers)
echo "🦋 Starting 3 iNaturalist workers..."
for i in {1..3}; do
    python3 workers/inaturalist_worker.py "inat-$i" > logs/inat-$i.log 2>&1 &
    echo "  ✓ inat-$i (PID: $!)"
done

# iDigBio Workers (2 workers)
echo "🏛️  Starting 2 iDigBio workers..."
for i in {1..2}; do
    python3 workers/idigbio_worker.py "idigbio-$i" > logs/idigbio-$i.log 2>&1 &
    echo "  ✓ idigbio-$i (PID: $!)"
done

# Tropicos Workers (2 workers - requires API key)
if [ ! -z "$TROPICOS_API_KEY" ]; then
    echo "🌿 Starting 2 Tropicos workers..."
    for i in {1..2}; do
        python3 workers/tropicos_worker.py "tropicos-$i" > logs/tropicos-$i.log 2>&1 &
        echo "  ✓ tropicos-$i (PID: $!)"
    done
else
    echo "⏭️  Skipping Tropicos workers (no API key)"
fi

# BHL Worker (1 worker - requires API key)
if [ ! -z "$BHL_API_KEY" ]; then
    echo "📚 Starting 1 BHL worker..."
    python3 workers/bhl_worker.py "bhl-1" > logs/bhl-1.log 2>&1 &
    echo "  ✓ bhl-1 (PID: $!)"
else
    echo "⏭️  Skipping BHL worker (no API key)"
fi

# EOL+ALA Worker (1 worker)
echo "🌎 Starting 1 EOL+ALA worker..."
python3 workers/eol_ala_worker.py "eol-ala-1" > logs/eol-ala-1.log 2>&1 &
echo "  ✓ eol-ala-1 (PID: $!)"

echo ""
echo "======================================================"
echo "✅ All workers launched!"
echo ""
echo "Monitor logs:"
echo "  tail -f logs/gbif-1.log"
echo "  tail -f logs/inat-1.log"
echo "  tail -f logs/idigbio-1.log"
echo ""
echo "Stop all workers:"
echo "  pkill -f 'workers/.*_worker.py'"
echo ""
echo "Check running workers:"
echo "  ps aux | grep '_worker.py' | grep -v grep"
echo "======================================================"
