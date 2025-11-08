#!/usr/bin/env python3
"""
EOL TAXONOMY HARVESTER - MAC VERSION
Run this on your Mac to fetch taxonomy for 95,000 EOL orchid images

QUICK START:
1. pip3 install requests
2. python3 MAC_EOL_HARVESTER.py

The script will:
- Test with 10 records first (you'll see results in ~5 seconds)
- Ask if you want to continue with all 95,000
- Show live progress with timestamps
- Save results to eol_taxonomy_harvested.csv
"""

import requests
import csv
import time
from datetime import datetime
import sys

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header():
    print("\n" + "="*80)
    print(f"{BLUE}EOL TAXONOMY HARVESTER{RESET}")
    print("="*80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")

def test_connection():
    """Test EOL API with a known page_id"""
    print(f"{YELLOW}🔍 Testing EOL API connection...{RESET}")
    test_page = "47191960"
    
    try:
        url = f"https://eol.org/api/pages/1.0/{test_page}.json"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            sci_name = data.get('scientificName', 'Not found')
            print(f"{GREEN}✓ SUCCESS! EOL API is accessible{RESET}")
            print(f"  Test page {test_page}: {sci_name}")
            return True
        else:
            print(f"{RED}✗ ERROR: HTTP {response.status_code}{RESET}")
            return False
    except Exception as e:
        print(f"{RED}✗ ERROR: {e}{RESET}")
        return False

def fetch_taxonomy(page_id):
    """Fetch taxonomy from EOL API for a single page_id"""
    try:
        url = f"https://eol.org/api/pages/1.0/{page_id}.json"
        response = requests.get(url, timeout=30)
        
        if response.status_code != 200:
            return None, f"HTTP {response.status_code}"
        
        data = response.json()
        sci_name = data.get('scientificName')
        
        if not sci_name:
            return None, "No scientificName in response"
        
        # Parse genus/species
        parts = sci_name.split()
        genus = parts[0] if len(parts) >= 1 else None
        species = parts[1] if len(parts) >= 2 else None
        
        # Extract family
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
            common_names = [vn.get('vernacularName') for vn in data['vernacularNames'][:5]]
        
        return {
            'page_id': page_id,
            'scientific_name': sci_name,
            'genus': genus,
            'species': species,
            'family': family,
            'common_names': ','.join(common_names) if common_names else '',
            'api_status': 'success',
            'error': ''
        }, None
        
    except Exception as e:
        return None, str(e)

def run_test_mode(page_ids):
    """Test with first 10 page_ids to verify it's working"""
    print(f"\n{YELLOW}🧪 TEST MODE: Processing first 10 records...{RESET}\n")
    
    test_ids = page_ids[:10]
    success = 0
    failed = 0
    
    for idx, page_id in enumerate(test_ids, 1):
        result, error = fetch_taxonomy(page_id)
        
        if result:
            print(f"{GREEN}✓ {idx}/10{RESET} Page {page_id}: {result['scientific_name']}")
            success += 1
        else:
            print(f"{RED}✗ {idx}/10{RESET} Page {page_id}: {error}")
            failed += 1
        
        time.sleep(0.5)
    
    print(f"\n{YELLOW}TEST RESULTS:{RESET}")
    print(f"  Success: {GREEN}{success}/10{RESET}")
    print(f"  Failed:  {RED}{failed}/10{RESET}")
    
    if success >= 7:
        print(f"\n{GREEN}✓ Test passed! API is working well.{RESET}")
        return True
    else:
        print(f"\n{RED}✗ Test failed. Too many errors.{RESET}")
        return False

def run_full_harvest(page_ids, output_file):
    """Harvest taxonomy for all page_ids"""
    total = len(page_ids)
    
    print(f"\n{BLUE}📊 FULL HARVEST MODE{RESET}")
    print(f"Total records: {total:,}")
    print(f"Estimated time: {total * 0.5 / 3600:.1f} hours")
    print(f"Output file: {output_file}\n")
    
    # Create output file
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'page_id', 'scientific_name', 'genus', 'species', 'family',
            'common_names', 'api_status', 'error'
        ])
        writer.writeheader()
        
        success = 0
        failed = 0
        start_time = time.time()
        
        for idx, page_id in enumerate(page_ids, 1):
            result, error = fetch_taxonomy(page_id)
            
            if result:
                writer.writerow(result)
                success += 1
                
                # Show successful records every 50
                if idx % 50 == 0:
                    print(f"{GREEN}✓{RESET} {result['scientific_name']}")
            else:
                writer.writerow({
                    'page_id': page_id,
                    'scientific_name': '',
                    'genus': '',
                    'species': '',
                    'family': '',
                    'common_names': '',
                    'api_status': 'error',
                    'error': error
                })
                failed += 1
            
            # Flush every 100 to save progress
            if idx % 100 == 0:
                f.flush()
            
            # Progress update every 100
            if idx % 100 == 0:
                elapsed = time.time() - start_time
                rate = idx / elapsed if elapsed > 0 else 0
                eta_hours = (total - idx) / rate / 3600 if rate > 0 else 0
                success_rate = success / idx * 100
                
                print(f"\n{BLUE}[{datetime.now().strftime('%H:%M:%S')}]{RESET} Progress: {idx:,}/{total:,} ({idx/total*100:.1f}%)")
                print(f"  Success: {GREEN}{success:,}{RESET} ({success_rate:.1f}%) | Failed: {RED}{failed:,}{RESET}")
                print(f"  Rate: {rate:.2f}/sec | ETA: {eta_hours:.1f}h remaining\n")
    
    # Final summary
    print(f"\n{GREEN}{'='*80}{RESET}")
    print(f"{GREEN}HARVEST COMPLETE!{RESET}")
    print(f"{GREEN}{'='*80}{RESET}")
    print(f"Total processed: {total:,}")
    print(f"Success: {GREEN}{success:,}{RESET} ({success/total*100:.1f}%)")
    print(f"Failed: {RED}{failed:,}{RESET}")
    print(f"Time: {(time.time() - start_time)/3600:.2f} hours")
    print(f"Output: {output_file}")
    print(f"\n{GREEN}✓ Upload {output_file} to Replit!{RESET}\n")

def main():
    print_header()
    
    # Test connection
    if not test_connection():
        print(f"\n{RED}Cannot connect to EOL API. Check your internet connection.{RESET}")
        sys.exit(1)
    
    # Load page_ids from embedded data (first 100 for testing)
    # USER: Replace this with your full CSV data
    print(f"\n{YELLOW}📖 Loading page_ids...{RESET}")
    
    # For now, using sample data - USER NEEDS TO PASTE THEIR CSV DATA HERE
    print(f"{RED}ERROR: You need to paste your EOL_IMAGES_COMPLETE_95000.csv data into this script!{RESET}")
    print(f"\nInstructions:")
    print(f"1. Open EOL_IMAGES_COMPLETE_95000.csv in Replit")
    print(f"2. Copy the page_id column")
    print(f"3. Paste it into this script where it says 'PASTE HERE'")
    print(f"\nOr use the separate CSV file method (recommended)")
    
    # Check if CSV file exists
    import os
    csv_file = 'EOL_IMAGES_COMPLETE_95000.csv'
    
    if os.path.exists(csv_file):
        print(f"\n{GREEN}✓ Found {csv_file}!{RESET}")
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            page_ids = [row['page_id'] for row in reader if row.get('page_id')]
        print(f"✓ Loaded {len(page_ids):,} page_ids")
    else:
        print(f"\n{YELLOW}Download EOL_IMAGES_COMPLETE_95000.csv from Replit and place it in the same folder as this script.{RESET}")
        sys.exit(1)
    
    # Run test mode
    if run_test_mode(page_ids):
        response = input(f"\n{YELLOW}Continue with full harvest? (yes/no): {RESET}").strip().lower()
        
        if response == 'yes':
            run_full_harvest(page_ids, 'eol_taxonomy_harvested.csv')
        else:
            print(f"\n{YELLOW}Stopped. Run again when ready.{RESET}")
    else:
        print(f"\n{RED}Test failed. Not proceeding with full harvest.{RESET}")

if __name__ == '__main__':
    main()
