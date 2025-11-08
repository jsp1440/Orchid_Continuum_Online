#!/usr/bin/env python3
"""
Fetch missing orchid taxonomy from EOL pages via web scraping
No API key needed - just scrapes the public EOL pages
"""
import os
import csv
import time
import requests
import psycopg2
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import urllib3

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

print("🌺 FETCHING MISSING EOL TAXONOMY DATA")
print("=" * 70)

# Connect to database
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

# Get existing EOL page IDs from taxonomy
cur.execute("SELECT eol_page_id FROM orchid_taxonomy WHERE eol_page_id IS NOT NULL")
existing_eol_ids = set(str(row[0]) for row in cur.fetchall())
print(f"✅ Found {len(existing_eol_ids):,} existing EOL species in database\n")

# Load all orchid EOL page IDs
all_orchid_ids = set()
with open('orchid_eol_page_ids.txt', 'r') as f:
    for line in f:
        page_id = line.strip()
        if page_id:
            all_orchid_ids.add(page_id)

print(f"📊 Total orchid EOL page IDs: {len(all_orchid_ids):,}")

# Find missing ones
missing_ids = all_orchid_ids - existing_eol_ids
print(f"🔍 Missing from database: {len(missing_ids):,}")
print()

if not missing_ids:
    print("✅ No missing species - all EOL IDs already in database!")
    cur.close()
    conn.close()
    exit(0)

# Fetch taxonomy for missing species
print("🌐 Fetching taxonomy from EOL pages...")
print(f"   (Batch size: 100, Rate limit: 1 req/sec)")
print("-" * 70)

missing_list = sorted(list(missing_ids))[:100]  # Start with first 100 as test
fetched = 0
failed = 0
inserted = 0

session = requests.Session()
session.headers.update({
    'User-Agent': 'OrchidContinuum/1.0 (Educational Research Platform)'
})

for i, page_id in enumerate(missing_list, 1):
    try:
        # Fetch EOL page
        url = f"https://eol.org/pages/{page_id}"
        response = session.get(url, timeout=10, verify=False)
        
        if response.status_code != 200:
            print(f"[{i:3}/{len(missing_list)}] EOL {page_id}: ⚠️  HTTP {response.status_code}")
            failed += 1
            time.sleep(1)
            continue
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract scientific name from page title or h1
        scientific_name = None
        h1 = soup.find('h1')
        if h1:
            scientific_name = h1.get_text(strip=True)
        
        # Try to extract taxonomy from breadcrumb or classification
        genus = None
        species = None
        family = None
        
        # Parse scientific name (usually "Genus species")
        if scientific_name and ' ' in scientific_name:
            parts = scientific_name.split()
            if len(parts) >= 2:
                genus = parts[0]
                species = ' '.join(parts[1:])  # Handle subspecies/varieties
        
        # Look for family in classification section
        classification = soup.find('div', {'class': 'classification'}) or soup.find('section', {'id': 'classification'})
        if classification:
            family_link = classification.find('a', string=lambda t: t and 'aceae' in t)
            if family_link:
                family = family_link.get_text(strip=True)
        
        # If we got at least genus, insert it
        if genus:
            try:
                cur.execute("""
                    INSERT INTO orchid_taxonomy (
                        eol_page_id,
                        genus,
                        species,
                        family,
                        scientific_name,
                        created_at
                    ) VALUES (%s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (eol_page_id) DO NOTHING
                """, (
                    page_id,
                    genus,
                    species or '',
                    family or 'Orchidaceae',  # Default to Orchidaceae if not found
                    scientific_name or f"{genus} {species or 'sp.'}"
                ))
                conn.commit()
                inserted += 1
                print(f"[{i:3}/{len(missing_list)}] EOL {page_id}: ✅ {scientific_name or genus}")
            except Exception as db_err:
                print(f"[{i:3}/{len(missing_list)}] EOL {page_id}: ⚠️  DB error: {db_err}")
                conn.rollback()
                failed += 1
        else:
            print(f"[{i:3}/{len(missing_list)}] EOL {page_id}: ⚠️  No genus found")
            failed += 1
        
        fetched += 1
        
        # Progress update every 20 records
        if i % 20 == 0:
            print(f"   Progress: {i}/{len(missing_list)} | Inserted: {inserted} | Failed: {failed}")
        
        # Rate limit: 1 request per second
        time.sleep(1)
        
    except requests.exceptions.Timeout:
        print(f"[{i:3}/{len(missing_list)}] EOL {page_id}: ⚠️  Timeout")
        failed += 1
        time.sleep(2)
    except Exception as e:
        print(f"[{i:3}/{len(missing_list)}] EOL {page_id}: ⚠️  Error: {e}")
        failed += 1
        time.sleep(1)

print("-" * 70)
print(f"\n✅ BATCH COMPLETE!")
print(f"   Pages fetched: {fetched}")
print(f"   Species inserted: {inserted}")
print(f"   Failed: {failed}")

cur.close()
conn.close()

print(f"\n💡 This was a test batch of 100 species.")
print(f"   To fetch all {len(missing_ids):,} missing species:")
print(f"   1. Edit script to remove [:100] limit")
print(f"   2. Run: python3 fetch_missing_eol_taxonomy.py")
print(f"   3. Estimated time: ~{len(missing_ids) / 3600:.1f} hours at 1 req/sec")
