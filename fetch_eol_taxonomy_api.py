#!/usr/bin/env python3
"""
Fetch missing orchid taxonomy from EOL API (JSON endpoints - no key needed!)
EOL provides public JSON endpoints for each page
"""
import os
import time
import requests
import psycopg2
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

print("🌺 FETCHING MISSING EOL TAXONOMY VIA API")
print("=" * 70)

# Connect to database
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

# Get existing EOL page IDs
cur.execute("SELECT eol_page_id FROM orchid_taxonomy WHERE eol_page_id IS NOT NULL")
existing_eol_ids = set(str(row[0]) for row in cur.fetchall())
print(f"✅ Existing species: {len(existing_eol_ids):,}\n")

# Load all orchid EOL page IDs
all_orchid_ids = set()
with open('orchid_eol_page_ids.txt', 'r') as f:
    for line in f:
        page_id = line.strip()
        if page_id:
            all_orchid_ids.add(page_id)

missing_ids = all_orchid_ids - existing_eol_ids
print(f"📊 Total orchid IDs: {len(all_orchid_ids):,}")
print(f"🔍 Missing: {len(missing_ids):,}\n")

# Fetch first 500 as test batch
missing_list = sorted(list(missing_ids))[:500]
print(f"🌐 Fetching {len(missing_list)} species from EOL API...")
print("-" * 70)

session = requests.Session()
session.headers.update({'User-Agent': 'OrchidContinuum/1.0'})

inserted = 0
failed = 0

for i, page_id in enumerate(missing_list, 1):
    try:
        # EOL provides JSON at: https://eol.org/api/pages/1.0/{page_id}.json
        url = f"https://eol.org/api/pages/1.0/{page_id}.json"
        response = session.get(url, timeout=15, verify=False)
        
        if response.status_code != 200:
            failed += 1
            if i % 50 == 0:
                print(f"[{i}/{len(missing_list)}] Progress: ✅ {inserted} | ❌ {failed}")
            time.sleep(0.5)
            continue
        
        data = response.json()
        
        # Extract taxonomy
        scientific_name = data.get('scientificName', '')
        
        # Parse genus/species from scientific name
        genus = None
        species_part = None
        
        if scientific_name and ' ' in scientific_name:
            parts = scientific_name.split()
            genus = parts[0]
            if len(parts) > 1:
                species_part = ' '.join(parts[1:])
        
        # Get family from taxon ancestors
        family = None
        ancestors = data.get('taxonConcepts', [{}])[0].get('ancestors', []) if data.get('taxonConcepts') else []
        for ancestor in ancestors:
            if ancestor.get('taxonRank', '').lower() == 'family':
                family = ancestor.get('scientificName', '')
                break
        
        if not family:
            family = 'Orchidaceae'  # Default
        
        # Insert if we have genus
        if genus:
            try:
                cur.execute("""
                    INSERT INTO orchid_taxonomy (
                        eol_page_id, genus, species, family, scientific_name, created_at
                    ) VALUES (%s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (eol_page_id) DO UPDATE 
                    SET genus = EXCLUDED.genus,
                        species = EXCLUDED.species,
                        family = EXCLUDED.family,
                        scientific_name = EXCLUDED.scientific_name
                """, (page_id, genus, species_part or '', family, scientific_name))
                conn.commit()
                inserted += 1
            except Exception as db_err:
                conn.rollback()
                failed += 1
        else:
            failed += 1
        
        # Progress every 50
        if i % 50 == 0:
            print(f"[{i}/{len(missing_list)}] Progress: ✅ {inserted} | ❌ {failed}")
        
        # Rate limit
        time.sleep(0.3)  # ~3 req/sec
        
    except Exception as e:
        failed += 1
        time.sleep(1)

print("-" * 70)
print(f"\n✅ BATCH COMPLETE!")
print(f"   Inserted: {inserted}")
print(f"   Failed: {failed}")
print(f"\n💡 This fetched {len(missing_list)} species.")
print(f"   {len(missing_ids) - len(missing_list):,} species remaining")

cur.close()
conn.close()
