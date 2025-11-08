#!/usr/bin/env python3
"""
GBIF Orchid Image Ingestion System
Fetches orchid images from GBIF, uploads to Google Drive, updates Google Sheets
"""
import os
import json
import time
import requests
import psycopg2
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

# Configuration
SPREADSHEET_ID = "1UQZj4ZaA7cWnU0SozR4_qReWNOm0V9xz"
DRIVE_FOLDER_ID = "1jQoQ9x-2f1ENZq7iVCgneAmoQIvc6xIS"
TEMP_DIR = Path("/tmp/orchid_images")
BATCH_SIZE = 50  # Images per batch
MAX_IMAGES = 100  # Limit for this run (increase later)

# GBIF API configuration
GBIF_API_BASE = "https://api.gbif.org/v1"
GBIF_FAMILY = "Orchidaceae"

# Popular orchid genera to search (rotate through these)
ORCHID_GENERA = [
    'Phalaenopsis', 'Cattleya', 'Dendrobium', 'Oncidium', 'Paphiopedilum',
    'Cymbidium', 'Vanda', 'Masdevallia', 'Epidendrum', 'Bulbophyllum',
    'Pleurothallis', 'Maxillaria', 'Habenaria', 'Vanilla', 'Orchis'
]

# Ensure temp directory exists
TEMP_DIR.mkdir(exist_ok=True)

class GBIFIngestionSystem:
    """Complete GBIF orchid image ingestion system"""
    
    def __init__(self):
        self.sheets_service = None
        self.drive_service = None
        self.db_conn = None
        self.current_genus_index = 0
        self.stats = {
            'fetched': 0,
            'downloaded': 0,
            'uploaded': 0,
            'inserted_db': 0,
            'inserted_sheet': 0,
            'errors': 0
        }
    
    def initialize(self):
        """Initialize Google services and database connection"""
        print("\n🌺 GBIF Orchid Ingestion System")
        print("=" * 70)
        
        # Initialize Google services
        try:
            creds_json = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON')
            if not creds_json:
                raise ValueError("GOOGLE_SERVICE_ACCOUNT_JSON not found")
            
            creds_dict = json.loads(creds_json)
            creds = service_account.Credentials.from_service_account_info(
                creds_dict,
                scopes=[
                    'https://www.googleapis.com/auth/spreadsheets',
                    'https://www.googleapis.com/auth/drive'
                ]
            )
            
            self.sheets_service = build('sheets', 'v4', credentials=creds)
            self.drive_service = build('drive', 'v3', credentials=creds)
            print("✅ Connected to Google Sheets & Drive")
        except Exception as e:
            print(f"❌ Failed to connect to Google services: {e}")
            return False
        
        # Initialize database
        try:
            self.db_conn = psycopg2.connect(os.environ['DATABASE_URL'])
            print("✅ Connected to PostgreSQL database")
        except Exception as e:
            print(f"❌ Failed to connect to database: {e}")
            return False
        
        print("=" * 70 + "\n")
        return True
    
    def fetch_gbif_occurrences(self, limit=100, offset=0):
        """
        Fetch orchid occurrences with images from GBIF
        Returns list of occurrence records
        """
        # Rotate through orchid genera for diversity
        genus = ORCHID_GENERA[self.current_genus_index % len(ORCHID_GENERA)]
        print(f"📡 Fetching {limit} {genus} occurrences (offset: {offset})...")
        
        params = {
            'genus': genus,
            'mediaType': 'StillImage',
            'hasCoordinate': 'true',
            'limit': limit,
            'offset': offset
        }
        
        try:
            response = requests.get(
                f"{GBIF_API_BASE}/occurrence/search",
                params=params,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            results = data.get('results', [])
            self.stats['fetched'] += len(results)
            print(f"✅ Fetched {len(results)} {genus} occurrences")
            
            # Move to next genus for next batch
            self.current_genus_index += 1
            
            return results
        except Exception as e:
            print(f"❌ Error fetching GBIF data: {e}")
            self.stats['errors'] += 1
            self.current_genus_index += 1  # Try next genus on error
            return []
    
    def extract_images_from_occurrence(self, occurrence):
        """Extract all image URLs from a GBIF occurrence record"""
        images = []
        media = occurrence.get('media', [])
        
        for item in media:
            if item.get('type') == 'StillImage':
                image_url = item.get('identifier')
                if image_url:
                    images.append({
                        'occurrence_key': occurrence.get('key'),
                        'image_url': image_url,
                        'scientific_name': occurrence.get('scientificName', ''),
                        'genus': occurrence.get('genus', ''),
                        'species': occurrence.get('species', ''),
                        'country': occurrence.get('country', ''),
                        'latitude': occurrence.get('decimalLatitude'),
                        'longitude': occurrence.get('decimalLongitude'),
                        'recorded_by': occurrence.get('recordedBy', ''),
                        'license': item.get('license', ''),
                        'publisher': item.get('publisher', ''),
                        'date': occurrence.get('eventDate', '')
                    })
        
        return images
    
    def download_image(self, image_url, filename):
        """Download image from URL to temp directory"""
        try:
            response = requests.get(image_url, timeout=30, stream=True)
            response.raise_for_status()
            
            filepath = TEMP_DIR / filename
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            self.stats['downloaded'] += 1
            return filepath
        except Exception as e:
            print(f"   ⚠️  Download failed: {e}")
            self.stats['errors'] += 1
            return None
    
    def upload_to_drive(self, filepath, filename):
        """Upload image to Google Drive and return shareable link"""
        try:
            file_metadata = {
                'name': filename,
                'parents': [DRIVE_FOLDER_ID]
            }
            
            media = MediaFileUpload(str(filepath), resumable=True)
            file = self.drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webViewLink'
            ).execute()
            
            # Make file publicly readable
            permission = {
                'type': 'anyone',
                'role': 'reader'
            }
            self.drive_service.permissions().create(
                fileId=file['id'],
                body=permission
            ).execute()
            
            self.stats['uploaded'] += 1
            return file.get('webViewLink')
        except Exception as e:
            print(f"   ⚠️  Drive upload failed: {e}")
            self.stats['errors'] += 1
            return None
    
    def add_to_google_sheet(self, records):
        """Add batch of records to Google Sheet"""
        if not records:
            return
        
        try:
            # Get next ID
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=SPREADSHEET_ID,
                range='Sheet1!A:A'
            ).execute()
            
            values = result.get('values', [])
            next_id = len(values)  # Header is row 1, so this gives us the next ID
            
            # Convert records to rows
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
                    record.get('drive_url', ''),
                    record.get('recorded_by', ''),
                    'GBIF',
                    datetime.now().isoformat()
                ]
                rows.append(row)
            
            # Append to sheet
            body = {'values': rows}
            self.sheets_service.spreadsheets().values().append(
                spreadsheetId=SPREADSHEET_ID,
                range='Sheet1!A:Q',
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            self.stats['inserted_sheet'] += len(rows)
            print(f"   ✅ Added {len(rows)} rows to Google Sheet")
        except Exception as e:
            print(f"   ⚠️  Google Sheet update failed: {e}")
            self.stats['errors'] += 1
    
    def insert_to_database(self, records):
        """Insert records into staging_gbif_images table"""
        if not records:
            return
        
        try:
            cur = self.db_conn.cursor()
            
            for record in records:
                # Use WHERE NOT EXISTS to avoid conflicts
                cur.execute("""
                    INSERT INTO staging_gbif_images 
                    (occurrence_key, image_url, scientific_name, genus, species,
                     country, decimal_latitude, decimal_longitude, photographer, 
                     license, created_at)
                    SELECT %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    WHERE NOT EXISTS (
                        SELECT 1 FROM staging_gbif_images WHERE image_url = %s
                    )
                """, (
                    record.get('occurrence_key'),
                    record.get('image_url'),
                    record.get('scientific_name'),
                    record.get('genus'),
                    record.get('species'),
                    record.get('country'),
                    record.get('latitude'),
                    record.get('longitude'),
                    record.get('recorded_by'),
                    record.get('license'),
                    datetime.now(),
                    record.get('image_url')  # For WHERE NOT EXISTS check
                ))
            
            self.db_conn.commit()
            self.stats['inserted_db'] += len(records)
            print(f"   ✅ Inserted {len(records)} records to database")
        except Exception as e:
            self.db_conn.rollback()
            print(f"   ⚠️  Database insert failed: {e}")
            self.stats['errors'] += 1
    
    def process_batch(self, occurrences):
        """Process a batch of occurrences: download, upload, insert"""
        all_records = []
        
        for occ in occurrences:
            images = self.extract_images_from_occurrence(occ)
            
            for img in images:
                print(f"\n📸 Processing: {img['scientific_name']}")
                print(f"   URL: {img['image_url'][:60]}...")
                
                # Generate filename
                occurrence_key = img['occurrence_key']
                ext = Path(urlparse(img['image_url']).path).suffix or '.jpg'
                filename = f"gbif_{occurrence_key}_{len(all_records)}{ext}"
                
                # Download image
                filepath = self.download_image(img['image_url'], filename)
                if not filepath:
                    continue
                
                # Upload to Drive
                drive_url = self.upload_to_drive(filepath, filename)
                if not drive_url:
                    continue
                
                # Add Drive URL to record
                img['drive_url'] = drive_url
                all_records.append(img)
                
                # Clean up temp file
                try:
                    filepath.unlink()
                except:
                    pass
                
                # Respect rate limits
                time.sleep(0.5)
        
        # Batch insert to database and Google Sheet
        if all_records:
            self.insert_to_database(all_records)
            self.add_to_google_sheet(all_records)
        
        return all_records
    
    def run(self, max_images=100):
        """Run the ingestion system"""
        if not self.initialize():
            return
        
        print(f"🎯 Target: {max_images} images\n")
        
        processed = 0
        offset = 0
        
        while processed < max_images:
            # Fetch batch from GBIF
            occurrences = self.fetch_gbif_occurrences(
                limit=min(BATCH_SIZE, max_images - processed),
                offset=offset
            )
            
            if not occurrences:
                print("⚠️  No more occurrences found")
                break
            
            # Process batch
            records = self.process_batch(occurrences)
            processed += len(records)
            offset += BATCH_SIZE
            
            print(f"\n📊 Progress: {processed} / {max_images} images processed")
            
            # Rate limiting
            time.sleep(2)
        
        # Print final stats
        self.print_stats()
        
        # Cleanup
        if self.db_conn:
            self.db_conn.close()
    
    def print_stats(self):
        """Print ingestion statistics"""
        print("\n" + "=" * 70)
        print("📊 Ingestion Statistics")
        print("=" * 70)
        print(f"   Occurrences fetched: {self.stats['fetched']}")
        print(f"   Images downloaded: {self.stats['downloaded']}")
        print(f"   Images uploaded to Drive: {self.stats['uploaded']}")
        print(f"   Records in database: {self.stats['inserted_db']}")
        print(f"   Rows in Google Sheet: {self.stats['inserted_sheet']}")
        print(f"   Errors: {self.stats['errors']}")
        print("=" * 70)
        print(f"\n🔗 View Google Sheet:")
        print(f"   https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
        print(f"\n🔗 View Google Drive:")
        print(f"   https://drive.google.com/drive/folders/{DRIVE_FOLDER_ID}")
        print("=" * 70 + "\n")

if __name__ == '__main__':
    system = GBIFIngestionSystem()
    system.run(max_images=MAX_IMAGES)
