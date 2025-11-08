#!/usr/bin/env python3
"""
MAC TERMINAL SCRIPT: Filter EOL Manifest for Orchids Only
Run this on your Mac to pre-filter the 5.7M EOL images for orchids

USAGE:
1. Download media_manifest files from Zenodo to a folder
2. Place this script in that folder
3. Run: python3 mac_filter_eol_orchids.py

OUTPUT: orchid_images_filtered.csv with ONLY orchid images
"""
import csv
import os
import sys
from pathlib import Path

print("🌺 EOL ORCHID FILTER FOR MAC")
print("=" * 70)

# STEP 1: Get list of orchid EOL page IDs
# You'll need to provide these - either from your database or from EOL's taxonomy API
# For now, we'll create a placeholder that you can fill in

ORCHID_PAGE_IDS = set([
    # ADD YOUR ORCHID EOL PAGE IDs HERE
    # Example: '1234567', '2345678', '3456789'
    # You can export these from your database with:
    # SELECT DISTINCT eol_page_id FROM orchid_images WHERE eol_page_id IS NOT NULL;
])

# ALTERNATIVE: Load from a text file (one page ID per line)
if os.path.exists('orchid_eol_page_ids.txt'):
    print("📄 Loading orchid page IDs from orchid_eol_page_ids.txt...")
    with open('orchid_eol_page_ids.txt', 'r') as f:
        for line in f:
            page_id = line.strip()
            if page_id:
                ORCHID_PAGE_IDS.add(page_id)
    print(f"✅ Loaded {len(ORCHID_PAGE_IDS):,} orchid page IDs")

if not ORCHID_PAGE_IDS:
    print("❌ ERROR: No orchid page IDs loaded!")
    print()
    print("SOLUTION:")
    print("1. Create 'orchid_eol_page_ids.txt' with one page ID per line")
    print("2. Or edit this script and add page IDs to ORCHID_PAGE_IDS set")
    sys.exit(1)

# Find all manifest files
manifest_files = sorted(Path('.').glob('media_manifest_*.csv'))

if not manifest_files:
    print("❌ No media_manifest_*.csv files found in current directory!")
    sys.exit(1)

print(f"📦 Found {len(manifest_files)} manifest files")
print()

# Open output file
output_file = 'orchid_images_filtered.csv'
total_rows_scanned = 0
orchid_rows_found = 0

with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
    writer = None
    
    for manifest_file in manifest_files:
        print(f"📖 Processing {manifest_file}...")
        
        try:
            with open(manifest_file, 'r', encoding='utf-8') as infile:
                reader = csv.DictReader(infile)
                
                # Initialize writer with same headers
                if writer is None:
                    writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames)
                    writer.writeheader()
                
                for row in reader:
                    total_rows_scanned += 1
                    
                    page_id = row.get('EOL page ID', '').strip()
                    
                    # Check if this is an orchid page
                    if page_id in ORCHID_PAGE_IDS:
                        writer.writerow(row)
                        orchid_rows_found += 1
                        
                        if orchid_rows_found % 100 == 0:
                            print(f"  ✅ Found {orchid_rows_found:,} orchid images...")
                    
                    # Progress update
                    if total_rows_scanned % 100000 == 0:
                        print(f"  ⏳ Scanned {total_rows_scanned:,} rows...")
        
        except Exception as e:
            print(f"  ⚠️  Error: {e}")
            continue

print()
print("=" * 70)
print(f"✅ FILTERING COMPLETE!")
print(f"📊 Total rows scanned: {total_rows_scanned:,}")
print(f"🌺 Orchid images found: {orchid_rows_found:,}")
print(f"📄 Output file: {output_file}")
print("=" * 70)
print()
print("NEXT STEPS:")
print("1. Upload orchid_images_filtered.csv to Replit")
print("2. Run the download script with the filtered CSV")
