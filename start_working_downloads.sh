#!/bin/bash
# Start only the working downloads: GBIF and iDigBio

echo "🌺 ORCHID CONTINUUM - WORKING DOWNLOADS"
echo "======================================"
echo "Starting 2 verified working sources:"
echo "  ✅ GBIF (9,774 images)"
echo "  ✅ iDigBio (10,000 herbarium sheets)"
echo ""

# Kill any existing
pkill -f "import_gbif_52_columns" 2>/dev/null
pkill -f "download_idigbio" 2>/dev/null
sleep 2

mkdir -p logs

echo "1️⃣  Starting GBIF Import..."
nohup python -u import_gbif_52_columns.py > logs/gbif.log 2>&1 &
GBIF_PID=$!
echo "   PID: $GBIF_PID"
sleep 2

echo ""
echo "2️⃣  Starting iDigBio Download..."
nohup python -u download_idigbio_herbarium.py > logs/idigbio.log 2>&1 &
IDIGBIO_PID=$!
echo "   PID: $IDIGBIO_PID"

echo ""
echo "======================================"
echo "✅ 2 DOWNLOADS STARTED"
echo "======================================"
echo ""
echo "📁 Log files:"
echo "   - logs/gbif.log"
echo "   - logs/idigbio.log"
echo ""
echo "📊 Monitor: ./check_download_progress.sh"
echo "⏸️  Stop: pkill -f 'download_'"
echo ""

sleep 5
RUNNING=$(ps aux | grep -E "(import_gbif|download_idigbio)" | grep -v grep | wc -l)
echo "✅ Currently running: $RUNNING processes"
