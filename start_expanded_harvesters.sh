#!/bin/bash
echo "🌺 Starting Expanded Orchid Harvester Fleet"
echo "==========================================="
echo ""

# Start API Fallback Coordinator (background monitoring)
echo "🔄 Starting API Fallback Coordinator..."
python3 workers/api_fallback_coordinator.py > logs/api_coordinator.log 2>&1 &
COORDINATOR_PID=$!
echo "✓ API Coordinator started (PID $COORDINATOR_PID)"
echo ""

# Start 12 GBIF Expanded Workers (ALL 247 countries)
echo "🌍 Starting 12 GBIF Expanded Workers (ALL countries)..."
for i in {1..12}; do
    python3 workers/gbif_expanded_worker.py gbif-exp-$i > logs/gbif-exp-$i.log 2>&1 &
    PID=$!
    echo "✓ Started gbif-exp-$i (PID $PID)"
done
echo ""

# Start 2 iNaturalist Workers (fallback + expansion)
echo "🦋 Starting 2 iNaturalist Workers..."
for i in {1..2}; do
    python3 workers/inaturalist_worker.py inat-$i > logs/inat-$i.log 2>&1 &
    PID=$!
    echo "✓ Started inat-$i (PID $PID)"
done
echo ""

# Start 2 Tropicos Workers (fallback)
echo "🌿 Starting 2 Tropicos Workers..."
for i in {1..2}; do
    python3 workers/tropicos_worker.py tropicos-$i > logs/tropicos-$i.log 2>&1 &
    PID=$!
    echo "✓ Started tropicos-$i (PID $PID)"
done
echo ""

# Start 1 iDigBio Worker
echo "🏛️ Starting iDigBio Worker..."
python3 workers/idigbio_worker.py idigbio-1 > logs/idigbio-1.log 2>&1 &
PID=$!
echo "✓ Started idigbio-1 (PID $PID)"
echo ""

echo "==========================================="
echo "✅ All workers + coordinator launched!"
echo "==========================================="
echo ""
echo "Monitor progress:"
echo "  python3 check_harvester_status.py"
echo ""
echo "View coordinator:"
echo "  tail -f logs/api_coordinator.log"
