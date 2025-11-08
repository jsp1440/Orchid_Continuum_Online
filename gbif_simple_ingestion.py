#!/usr/bin/env python3
"""
Simplified GBIF Orchid Ingestion - No Drive Upload
Stores original GBIF URLs directly in database and Google Sheet
"""
import os
import json
import time
import requests
import psycopg2
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Configuration
SPREADSHEET_ID = "1UQZj4ZaA7cWnU0SozR4_qReWNOm0V9xz"
BATCH_SIZE = 20

# Search by actual orchid genus names with verification
ORCHID_SEARCHES = [
    {'scientificName': 'Phalaenopsis amabilis'},
    {'scientificName': 'Cattleya labiata'},
    {'scientificName': 'Dendrobium nobile'},
    {'scientificName': 'Oncidium flexuosum'},
    {'scientificName': 'Cymbidium ensifolium'},
]

def get_sheets_service():
    """Initialize Google Sheets API"""
    creds_json = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON')
    creds_dict = json.loads(creds_json)
    creds = service_account.Credentials.from_service_account_info(
        creds_dict,
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    return build('sheets', 'v4', credentials=creds)

def fetch_gbif_by_species(species_name, limit=20):
    """Fetch GBIF occurrences for a specific species"""
    print(f"\n📡 Searching GBIF for: {species_name}")
    
    try:
        response = requests.get(
            'https://api.gbif.org/v1/occurrence/search',
            params={
                'scientificName': species_name,
                'mediaType': 'StillImage',
                'hasCoordinate': 'true',
                'limit': limit
            },
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        results = data.get('results', [])
        print(f"✅ Found {len(results)} occurrences")
        return results
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def extract_image_data(occurrence):
    """Extract image URLs and metadata from occurrence"""
    images = []
    media = occurrence.get('media', [])
    
    for item in media:
        if item.get('type') == 'StillImage':
            images.append({
                'occurrence_key': occurrence.get('key'),
                'image_url': item.get('identifier'),
                'scientific_name': occurrence.get('scientificName', ''),
                'genus': occurrence.get('genus', ''),
                'species': occurrence.get('species', ''),
                'country': occurrence.get('country', ''),
                'latitude': occurrence.get('decimalLatitude'),
                'longitude': occurrence.get('decimalLongitude'),
                'photographer': occurrence.get('recordedBy', ''),
                'license': item.get('license', ''),
                'date': occurrence.get('eventDate', '')
            })
    
    return images

def add_to_database(conn, records):
    """Insert records to staging table"""
    if not records:
        return 0
    
    cur = conn.cursor()
    inserted = 0
    
    for record in records:
        try:
            # Build metadata JSON
            metadata = {
                'scientific_name': record.get('scientific_name'),
                'genus': record.get('genus'),
                'species': record.get('species'),
                'country': record.get('country'),
                'latitude': record.get('latitude'),
                'longitude': record.get('longitude'),
                'photographer': record.get('photographer'),
                'date': record.get('date')
            }
            
            cur.execute("""
                INSERT INTO staging_gbif_images 
                (occurrence_key, image_url, media_json, license, created_at)
                SELECT %s, %s, %s, %s, %s
                WHERE NOT EXISTS (
                    SELECT 1 FROM staging_gbif_images WHERE image_url = %s
                )
            """, (
                str(record.get('occurrence_key')),
                record.get('image_url'),
                json.dumps(metadata),
                record.get('license'),
                datetime.now(),
                record.get('image_url')
            ))
            if cur.rowcount > 0:
                inserted += 1
        except Exception as e:
            print(f"   ⚠️  DB error: {e}")
            conn.rollback()
            continue
    
    conn.commit()
    return inserted

def add_to_sheet(sheets_service, records):
    """Add records to Google Sheet"""
    if not records:
        return 0
    
    try:
        # Get next ID
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range='Sheet1!A:A'
        ).execute()
        
        values = result.get('values', [])
        next_id = len(values) if values else 1
        
        # Build rows
        rows = []
        for i, record in enumerate(records):
            row = [
                next_id + i,
                record.get('scientific_name', ''),
                record.get('scientific_name', ''),
                record.get('genus', ''),
                record.get('species', ''),
                '',  # region
                record.get('country', ''),
                str(record.get('latitude', '')),
                str(record.get('longitude', '')),
                '',  # growth_habit
                '',  # bloom_time
                '',  # flower_color
                '',  # is_flowering
                record.get('image_url', ''),
                record.get('photographer', ''),
                'GBIF',
                datetime.now().isoformat()
            ]
            rows.append(row)
        
        # Append
        body = {'values': rows}
        sheets_service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range='Sheet1!A:Q',
            valueInputOption='RAW',
            insertDataOption='INSERT_ROWS',
            body=body
        ).execute()
        
        return len(rows)
    except Exception as e:
        print(f"   ⚠️  Sheet error: {e}")
        return 0

def main():
    print("\n🌺 Simplified GBIF Orchid Ingestion")
    print("=" * 70)
    print("Strategy: Direct GBIF URLs → Database (Google Sheets API disabled)")
    print("=" * 70 + "\n")
    
    # Initialize
    try:
        sheets_service = get_sheets_service()
        sheets_enabled = True
    except:
        sheets_service = None
        sheets_enabled = False
        print("⚠️  Google Sheets API disabled - skipping sheet updates\n")
    
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    print("✅ Connected to Database\n")
    
    total_images = 0
    total_db = 0
    total_sheet = 0
    
    # Process each species
    for search in ORCHID_SEARCHES:
        species = search['scientificName']
        occurrences = fetch_gbif_by_species(species, limit=BATCH_SIZE)
        
        all_images = []
        for occ in occurrences:
            images = extract_image_data(occ)
            all_images.extend(images)
        
        if all_images:
            print(f"📸 Found {len(all_images)} images for {species}")
            db_count = add_to_database(conn, all_images)
            
            if sheets_enabled and sheets_service:
                sheet_count = add_to_sheet(sheets_service, all_images)
            else:
                sheet_count = 0
            
            total_images += len(all_images)
            total_db += db_count
            total_sheet += sheet_count
            
            print(f"   ✅ {db_count} added to database")
        
        time.sleep(2)  # Rate limiting
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 Final Results")
    print("=" * 70)
    print(f"   Total images found: {total_images}")
    print(f"   Added to database: {total_db}")
    if sheets_enabled:
        print(f"   Added to sheet: {total_sheet}")
    print("=" * 70 + "\n")
    
    conn.close()

if __name__ == '__main__':
    main()
