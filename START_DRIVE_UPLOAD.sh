#!/bin/bash
# Start the Google Drive uploader

echo "🌺 Orchid Continuum - Google Drive Uploader"
echo "==========================================="
echo ""
echo "This will:"
echo "  1. Download all 107,000+ images from URLs"
echo "  2. Upload to your Google Drive folder"
echo "  3. Populate your Google Sheet"
echo "  4. Update database with Drive URLs"
echo ""
echo "Estimated time: 12-24 hours"
echo ""
read -p "Start now? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo "🚀 Starting uploader..."
    nohup python3 automated_drive_uploader.py > drive_upload_output.log 2>&1 &
    PID=$!
    echo $PID > drive_upload.pid
    echo "✅ Uploader started (PID: $PID)"
    echo "📊 Monitor progress: tail -f drive_upload.log"
    echo "🛑 Stop anytime: kill $(cat drive_upload.pid)"
fi
