#!/usr/bin/env python3
"""Continue downloading to reach comprehensive orchid coverage"""
import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Start the downloader in background
print("🚀 Starting comprehensive orchid downloader...")
print("📊 Current database: 11,717 images")
print("🎯 Target: Add 10,000+ more from GBIF, ALA, botanical illustrations")
print("\nThis will run for several hours. Check download_progress.log for status.")

os.system("nohup python3 replit_comprehensive_orchid_downloader.py > download_progress.log 2>&1 &")
print("\n✅ Downloader started in background!")
print("📝 Monitor progress: tail -f download_progress.log")
