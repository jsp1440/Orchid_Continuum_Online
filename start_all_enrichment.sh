#!/bin/bash

echo "🚀 Starting All Enrichment Sources in Parallel"
echo "="*80

# Create logs directory
mkdir -p logs

# Kill any existing
pkill -f "batch_gbif" 2>/dev/null
pkill -f "batch_powo" 2>/dev/null  
sleep 2

# Start GBIF
echo "Starting GBIF..."
nohup python -u batch_gbif_eol_enrichment.py --full --no-ai-vision --gbif-only > logs/gbif.log 2>&1 < /dev/null &
GBIF_PID=$!
echo "  ✅ GBIF PID: $GBIF_PID"

sleep 5

# Start POWO
echo "Starting POWO..."
nohup python -u batch_powo_enrichment.py --full > logs/powo.log 2>&1 < /dev/null &
POWO_PID=$!
echo "  ✅ POWO PID: $POWO_PID"

echo ""
echo "✅ ENRICHMENT STARTED!"
echo "="*80
echo "Monitor with:"
echo "  tail -f logs/gbif.log"
echo "  tail -f logs/powo.log"
echo ""
echo "Check status:"
echo "  ps aux | grep batch"
