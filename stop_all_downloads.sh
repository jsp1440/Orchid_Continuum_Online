#!/bin/bash
# Stop all downloads

echo "⏸️  Stopping all downloads..."

pkill -f "import_gbif_52_columns"
pkill -f "download_idigbio"
pkill -f "download_tropicos"
pkill -f "download_eol_batch2"

sleep 2

RUNNING=$(ps aux | grep -E "(import_gbif|download_idigbio|download_tropicos|download_eol)" | grep -v grep | wc -l)

if [ $RUNNING -eq 0 ]; then
    echo "✅ All downloads stopped"
else
    echo "⚠️  $RUNNING processes still running"
fi
