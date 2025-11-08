#!/usr/bin/env python3
"""
RUN THIS ON YOUR MAC OR GIVE TO JULIUS AI
Fetches taxonomy from EOL API for 95,000 page_ids
Exports: page_id,scientific_name,genus,species,family CSV for import back to Replit

Requirements: pip install requests psycopg2-binary (or use Julius's environment)
"""

import requests
import csv
import time
from datetime import datetime
import sys

def fetch_eol_taxonomy(page_ids_file, output_csv):
    """
    Fetch taxonomy from EOL API for page_ids
    
    Args:
        page_ids_file: CSV with page_id column
        output_csv: Output CSV path
    """
    
    print("="*80)
    print("EOL TAXONOMY EXTERNAL HARVESTER")
    print("For use on Mac or by Julius AI")
    print("="*80)
    print(f"Started: {datetime.now()}")
    
    # Read page_ids from CSV
    print(f"\n📖 Reading page_ids from {page_ids_file}...")
    page_ids = []
    with open(page_ids_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('page_id'):
                page_ids.append(row['page_id'])
    
    total = len(page_ids)
    print(f"✓ Loaded {total:,} page_ids")
    
    # Output file
    outfile = open(output_csv, 'w', newline='')
    writer = csv.DictWriter(outfile, fieldnames=[
        'page_id', 'scientific_name', 'genus', 'species', 'family',
        'common_names', 'api_status', 'error'
    ])
    writer.writeheader()
    
    # Process each page_id
    fetched = 0
    failed = 0
    start_time = time.time()
    
    print(f"\n🔬 Fetching taxonomy from EOL API...")
    print(f"Rate limit: 0.5 sec/request (safe for EOL)")
    print()
    
    for idx, page_id in enumerate(page_ids, 1):
        try:
            url = f"https://eol.org/api/pages/1.0/{page_id}.json"
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                sci_name = data.get('scientificName')
                
                if sci_name:
                    # Parse genus/species from scientific name
                    parts = sci_name.split()
                    genus = parts[0] if len(parts) >= 1 else None
                    species = parts[1] if len(parts) >= 2 else None
                    
                    # Extract family from taxonomy hierarchy
                    family = None
                    if 'taxonConcepts' in data and data['taxonConcepts']:
                        tc = data['taxonConcepts'][0]
                        if 'ancestry' in tc:
                            for anc in tc['ancestry']:
                                if anc.get('taxonRank') == 'family':
                                    family = anc.get('scientificName')
                    
                    # Get common names
                    common_names = []
                    if 'vernacularNames' in data:
                        common_names = [
                            vn.get('vernacularName') 
                            for vn in data['vernacularNames'][:5]
                        ]
                    
                    writer.writerow({
                        'page_id': page_id,
                        'scientific_name': sci_name,
                        'genus': genus,
                        'species': species,
                        'family': family,
                        'common_names': ','.join(common_names) if common_names else '',
                        'api_status': 'success',
                        'error': ''
                    })
                    fetched += 1
                    
                    if idx % 100 == 0:
                        print(f"  ✓ {sci_name}")
                else:
                    # No scientific name in response
                    writer.writerow({
                        'page_id': page_id,
                        'scientific_name': '',
                        'genus': '',
                        'species': '',
                        'family': '',
                        'common_names': '',
                        'api_status': 'no_data',
                        'error': 'scientificName field empty'
                    })
                    failed += 1
            else:
                # HTTP error
                writer.writerow({
                    'page_id': page_id,
                    'scientific_name': '',
                    'genus': '',
                    'species': '',
                    'family': '',
                    'common_names': '',
                    'api_status': 'http_error',
                    'error': f'HTTP {response.status_code}'
                })
                failed += 1
        
        except Exception as e:
            writer.writerow({
                'page_id': page_id,
                'scientific_name': '',
                'genus': '',
                'species': '',
                'family': '',
                'common_names': '',
                'api_status': 'error',
                'error': str(e)
            })
            failed += 1
        
        # Rate limiting
        time.sleep(0.5)
        
        # Progress update every 100
        if idx % 100 == 0:
            elapsed = time.time() - start_time
            rate = idx / elapsed if elapsed > 0 else 0
            eta_hours = (total - idx) / rate / 3600 if rate > 0 else 0
            
            print(f"\nProgress: {idx:,}/{total:,} ({idx/total*100:.1f}%)")
            print(f"  Success: {fetched:,} | Failed: {failed:,}")
            print(f"  Rate: {rate:.2f}/sec | ETA: {eta_hours:.2f}h\n")
    
    outfile.close()
    
    # Final summary
    print(f"\n{'='*80}")
    print(f"HARVEST COMPLETE")
    print(f"{'='*80}")
    print(f"Total processed: {total:,}")
    print(f"Successfully fetched: {fetched:,}")
    print(f"Failed: {failed:,}")
    print(f"Success rate: {fetched/total*100:.1f}%")
    print(f"Output file: {output_csv}")
    print(f"Time: {(time.time() - start_time)/3600:.2f} hours")
    print(f"\n✓ Upload {output_csv} to Replit to import taxonomy data")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 EXTERNAL_FETCH_EOL_TAXONOMY.py <input_csv> [output_csv]")
        print("\nExample:")
        print("  python3 EXTERNAL_FETCH_EOL_TAXONOMY.py EOL_IMAGES_COMPLETE_95000.csv eol_taxonomy_harvested.csv")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'eol_taxonomy_harvested.csv'
    
    fetch_eol_taxonomy(input_file, output_file)
