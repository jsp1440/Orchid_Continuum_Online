#!/bin/bash

echo "🚀 Starting Parallel Enrichment..."
echo "="*60

# Start GBIF
echo "Starting GBIF enrichment..."
nohup python -u batch_gbif_eol_enrichment.py --full --no-ai-vision --gbif-only > gbif_live.log 2>&1 </dev/null &
GBIF_PID=$!
echo "  ✅ GBIF PID: $GBIF_PID"

# Wait for initialization
sleep 5

# Start POWO  
echo "Starting POWO enrichment..."
nohup python -u batch_powo_enrichment.py --full > powo_live.log 2>&1 </dev/null &
POWO_PID=$!
echo "  ✅ POWO PID: $POWO_PID"

echo ""
echo "✅ BOTH PROCESSES LAUNCHED!"
echo "Monitor with:"
echo "  tail -f gbif_live.log"
echo "  tail -f powo_live.log"
