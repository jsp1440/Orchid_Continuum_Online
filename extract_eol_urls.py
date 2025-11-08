#!/usr/bin/env python3
"""
EOL URL Extraction Script - Link to Images Without Downloading
Processes 58 manifest CSVs and extracts URLs for 13,429 orchid page IDs

OUTPUT: orchid_eol_urls.csv with taxonomy_id, image_url, license, source
"""
import csv
import os
import sys
from pathlib import Path
from collections import defaultdict

print("🌺 EOL URL EXTRACTION FOR ORCHID CONTINUUM")
print("=" * 70)

# STEP 1: Load orchid EOL page IDs
orchid_page_ids = set()
if os.path.exists('orchid_eol_page_ids.txt'):
    print("📄 Loading orchid page IDs from orchid_eol_page_ids.txt...")
    with open('orchid_eol_page_ids.txt', 'r') as f:
        for line in f:
            page_id = line.strip()
            if page_id:
                orchid_page_ids.add(page_id)
    print(f"✅ Loaded {len(orchid_page_ids):,} orchid page IDs\n")
else:
    print("❌ ERROR: orchid_eol_page_ids.txt not found!")
    sys.exit(1)

# STEP 2: Load EOL page ID to taxonomy_id mapping from database
# We'll create this file first from the database
eol_to_taxonomy = {}
if os.path.exists('eol_taxonomy_mapping.csv'):
    print("📊 Loading EOL → Taxonomy mapping...")
    with open('eol_taxonomy_mapping.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            eol_to_taxonomy[row['eol_page_id']] = row['taxonomy_id']
    print(f"✅ Loaded {len(eol_to_taxonomy):,} taxonomy mappings\n")
else:
    print("⚠️  No taxonomy mapping found - will create generic entries")
    print("   Run the mapping script first for best results\n")

# STEP 3: Find all manifest files
manifest_dir = Path('./external_databases/zenodo_data')
manifest_files = sorted(manifest_dir.glob('media_manifest_*.csv'))

if not manifest_files:
    print("❌ No manifest files found!")
    sys.exit(1)

print(f"📦 Found {len(manifest_files)} manifest files\n")

# STEP 4: Process manifests and extract URLs
output_file = 'orchid_eol_urls.csv'
total_rows_scanned = 0
orchid_urls_found = 0
urls_by_page_id = defaultdict(list)

print("🔍 Processing manifests...")
print("-" * 70)

with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
    writer = csv.DictWriter(outfile, fieldnames=[
        'eol_page_id',
        'taxonomy_id', 
        'eol_content_id',
        'image_url',
        'source_url',
        'image_license',
        'copyright_owner',
        'image_source'
    ])
    writer.writeheader()
    
    for i, manifest_file in enumerate(manifest_files, 1):
        print(f"📖 [{i:2}/{len(manifest_files)}] {manifest_file.name}...", end=' ')
        
        try:
            with open(manifest_file, 'r', encoding='utf-8', errors='ignore') as infile:
                reader = csv.DictReader(infile)
                
                file_orchids = 0
                for row in reader:
                    total_rows_scanned += 1
                    
                    # Check if this page ID is an orchid
                    page_id = row.get('EOL page ID', '').strip()
                    if page_id in orchid_page_ids:
                        # Extract URL and metadata
                        eol_url = row.get('EOL Full-Size Copy URL', '').strip()
                        source_url = row.get('Medium Source URL', '').strip()
                        
                        # Use EOL URL if available, otherwise source
                        image_url = eol_url if eol_url else source_url
                        
                        if image_url:
                            taxonomy_id = eol_to_taxonomy.get(page_id, None)
                            
                            writer.writerow({
                                'eol_page_id': page_id,
                                'taxonomy_id': taxonomy_id,
                                'eol_content_id': row.get('EOL content ID', ''),
                                'image_url': image_url,
                                'source_url': source_url,
                                'image_license': row.get('License Name', ''),
                                'copyright_owner': row.get('Copyright Owner', ''),
                                'image_source': 'EOL'
                            })
                            
                            file_orchids += 1
                            orchid_urls_found += 1
                            urls_by_page_id[page_id].append(image_url)
                
                print(f"✓ Found {file_orchids:,} orchid URLs")
                
        except Exception as e:
            print(f"⚠️  Error: {e}")
            continue

print("-" * 70)
print(f"\n✅ EXTRACTION COMPLETE!")
print(f"   📊 Total rows scanned: {total_rows_scanned:,}")
print(f"   🌺 Orchid URLs found: {orchid_urls_found:,}")
print(f"   🔢 Unique orchid species: {len(urls_by_page_id):,}")
print(f"   📁 Output file: {output_file}")

# Show top 10 species by image count
if urls_by_page_id:
    print(f"\n📈 Top 10 species by image count:")
    sorted_species = sorted(urls_by_page_id.items(), key=lambda x: len(x[1]), reverse=True)[:10]
    for page_id, urls in sorted_species:
        print(f"   EOL {page_id}: {len(urls):,} images")

print(f"\n🚀 Ready to import {orchid_urls_found:,} URLs into database!")
