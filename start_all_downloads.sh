#!/bin/bash
# Simple reliable download starter
# Kills existing, starts fresh

echo "🌺 ORCHID CONTINUUM - DOWNLOAD STARTER"
echo "======================================"

# Kill any existing downloads
pkill -f "import_gbif_52_columns" 2>/dev/null
pkill -f "download_idigbio" 2>/dev/null  
pkill -f "download_tropicos" 2>/dev/null
pkill -f "download_eol_batch2" 2>/dev/null
sleep 2

# Create log directory
mkdir -p logs

# Start each download
echo ""
echo "Starting downloads..."
echo ""

echo "1️⃣  GBIF (9,774 living photos)"
nohup python -u import_gbif_52_columns.py > logs/gbif.log 2>&1 &
GBIF_PID=$!
echo "   Started - PID: $GBIF_PID"
sleep 2

echo ""
echo "2️⃣  iDigBio (10,000 herbarium sheets)"
nohup python -u download_idigbio_herbarium.py > logs/idigbio.log 2>&1 &
IDIGBIO_PID=$!
echo "   Started - PID: $IDIGBIO_PID"
sleep 2

echo ""
echo "3️⃣  Tropicos (5,000 herbarium sheets)"
nohup python -u download_tropicos_herbarium.py > logs/tropicos.log 2>&1 &
TROPICOS_PID=$!
echo "   Started - PID: $TROPICOS_PID"
sleep 2

echo ""
echo "4️⃣  EOL Batch 2 (95,000 living photos)"
nohup python -u download_eol_batch2.py > logs/eol_batch2.log 2>&1 &
EOL_PID=$!
echo "   Started - PID: $EOL_PID"

echo ""
echo "======================================"
echo "✅ ALL 4 DOWNLOADS STARTED"
echo "======================================"
echo ""
echo "📁 Log files:"
echo "   - logs/gbif.log"
echo "   - logs/idigbio.log"
echo "   - logs/tropicos.log"
echo "   - logs/eol_batch2.log"
echo ""
echo "📊 Check progress:"
echo "   tail -f logs/gbif.log"
echo ""
echo "⏸️  Stop all downloads:"
echo "   ./stop_all_downloads.sh"
echo ""
echo "======================================"

# Wait a bit and check if they're still running
sleep 5
RUNNING=$(ps aux | grep -E "(import_gbif|download_idigbio|download_tropicos|download_eol)" | grep -v grep | wc -l)
echo "✅ Currently running: $RUNNING processes"
