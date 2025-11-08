#!/usr/bin/env python3
"""
URGENT EOL IMAGE SAVER
Populates user's Google Sheet and downloads 95,000 EOL images to Google Drive
BEFORE URLs ARE DESTROYED
"""

import os
import sys
import time
import requests
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from pathlib import Path
import tempfile
import json

# Database
DATABASE_URL = os.environ.get('DATABASE_URL')

# Google Sheet ID from user's link
SHEET_ID = '15vUyR7fG5u35jP28iAdLqf2MYobI3rQg'

# Google API setup
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file'
]

class UrgentEOLSaver:
    def __init__(self):
        self.db_conn = psycopg2.connect(DATABASE_URL)
        self.sheets_client = None
        self.drive_service = None
        self.worksheet = None
        self.drive_folder_id = None
        
        self.initialize_google()
    
    def initialize_google(self):
        """Initialize Google Sheets and Drive"""
        try:
            # Try service account first
            if os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON'):
                creds_dict = json.loads(os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON'))
                credentials = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
            else:
                # Fall back to API key for read/write
                print("Using Google API Key")
                credentials = None  # Will use API key instead
            
            if credentials:
                self.sheets_client = gspread.authorize(credentials)
                self.drive_service = build('drive', 'v3', credentials=credentials)
                print("✓ Connected to Google with service account")
            else:
                print("⚠ No service account - will prepare data for manual upload")
            
        except Exception as e:
            print(f"Google setup: {e}")
            print("Will prepare CSV for manual processing")
    
    def add_eol_data_to_sheet(self, batch_size=1000):
        """Add EOL image data to user's existing Google Sheet"""
        if not self.sheets_client:
            print("Creating CSV for manual upload...")
            return self.create_csv_export()
        
        try:
            # Open user's sheet
            sheet = self.sheets_client.open_by_key(SHEET_ID)
            
            # Get or create EOL worksheet
            try:
                ws = sheet.worksheet('EOL Images')
            except:
                ws = sheet.add_worksheet(title='EOL Images', rows=100000, cols=15)
                # Add headers
                ws.append_row([
                    'EOL_ID', 'Page_ID', 'Source_URL', 'EOL_URL', 
                    'License', 'Photographer', 'Date_Added',
                    'Download_Status', 'Google_Drive_ID', 'Google_Drive_URL',
                    'File_Size_KB', 'Image_Format', 'Downloaded_At',
                    'Genus', 'Species'
                ])
            
            self.worksheet = ws
            
            # Get EOL images from database
            cursor = self.db_conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT 
                    id, page_id, source_url, eol_url,
                    license, copyright, created_at
                FROM eol_images
                ORDER BY id
            """)
            
            print(f"\nAdding EOL images to sheet in batches of {batch_size}...")
            
            batch = []
            total = 0
            
            for row in cursor:
                batch.append([
                    row['id'],
                    row['page_id'],
                    row['source_url'],
                    row['eol_url'],
                    row['license'],
                    row['copyright'],
                    str(row['created_at']) if row['created_at'] else '',
                    'PENDING',
                    '',  # Drive ID
                    '',  # Drive URL
                    '',  # File size
                    '',  # Format
                    '',  # Downloaded at
                    '',  # Genus (to be matched)
                    ''   # Species (to be matched)
                ])
                
                if len(batch) >= batch_size:
                    ws.append_rows(batch)
                    total += len(batch)
                    print(f"  Added {total:,} images...")
                    batch = []
                    time.sleep(1)  # Rate limiting
            
            # Add remaining
            if batch:
                ws.append_rows(batch)
                total += len(batch)
            
            print(f"✓ Added {total:,} images to Google Sheet")
            cursor.close()
            return total
            
        except Exception as e:
            print(f"Error adding to sheet: {e}")
            return 0
    
    def create_csv_export(self):
        """Backup: Create CSV if Google Sheets fails"""
        cursor = self.db_conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM eol_images ORDER BY id")
        
        import csv
        filename = f"EOL_IMAGES_BACKUP_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        rows = cursor.fetchall()
        if rows:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
            
            print(f"✓ Created backup CSV: {filename}")
            print(f"  Total rows: {len(rows):,}")
        
        cursor.close()
        return filename
    
    def create_drive_folder(self):
        """Create EOL_Orchid_Images folder in user's Drive"""
        if not self.drive_service:
            print("⚠ Cannot create Drive folder without service account")
            return None
        
        try:
            folder_metadata = {
                'name': 'EOL_Orchid_Images_URGENT',
                'mimeType': 'application/vnd.google-apps.folder'
            }
            folder = self.drive_service.files().create(
                body=folder_metadata,
                fields='id, webViewLink'
            ).execute()
            
            self.drive_folder_id = folder.get('id')
            print(f"✓ Created Drive folder: {folder.get('webViewLink')}")
            return self.drive_folder_id
            
        except Exception as e:
            print(f"Error creating folder: {e}")
            return None
    
    def download_and_save_image(self, eol_id, page_id, source_url):
        """Download image and upload to Google Drive"""
        if not self.drive_service:
            return None
        
        try:
            # Download to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
                response = requests.get(source_url, timeout=30, stream=True)
                response.raise_for_status()
                
                for chunk in response.iter_content(chunk_size=8192):
                    tmp.write(chunk)
                
                tmp_path = tmp.name
            
            # Upload to Drive
            file_metadata = {
                'name': f'EOL_{page_id}_{eol_id}.jpg',
                'parents': [self.drive_folder_id]
            }
            media = MediaFileUpload(tmp_path, resumable=True)
            file = self.drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webViewLink, size'
            ).execute()
            
            # Clean up
            os.unlink(tmp_path)
            
            return {
                'drive_id': file.get('id'),
                'drive_url': file.get('webViewLink'),
                'size_kb': int(file.get('size', 0)) // 1024
            }
            
        except Exception as e:
            print(f"  Error with image {eol_id}: {e}")
            return None
    
    def update_database(self, eol_id, drive_id, drive_url):
        """Add Google Drive info to database"""
        cursor = self.db_conn.cursor()
        
        # Add columns if they don't exist
        cursor.execute("""
            ALTER TABLE eol_images 
            ADD COLUMN IF NOT EXISTS google_drive_id TEXT,
            ADD COLUMN IF NOT EXISTS google_drive_url TEXT,
            ADD COLUMN IF NOT EXISTS uploaded_at TIMESTAMP
        """)
        
        cursor.execute("""
            UPDATE eol_images 
            SET google_drive_id = %s,
                google_drive_url = %s,
                uploaded_at = NOW()
            WHERE id = %s
        """, (drive_id, drive_url, eol_id))
        
        self.db_conn.commit()
        cursor.close()
    
    def process_downloads(self, limit=None):
        """Download all EOL images to Google Drive"""
        if not self.drive_service or not self.drive_folder_id:
            print("\n⚠ Cannot download without Drive access")
            print("Please provide GOOGLE_SERVICE_ACCOUNT_JSON to enable downloads")
            return
        
        cursor = self.db_conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT id, page_id, source_url 
            FROM eol_images 
            WHERE source_url IS NOT NULL
            AND (google_drive_id IS NULL OR google_drive_id = '')
            ORDER BY id
        """
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query)
        images = cursor.fetchall()
        
        print(f"\n{'='*80}")
        print(f"DOWNLOADING {len(images):,} IMAGES TO GOOGLE DRIVE")
        print(f"{'='*80}\n")
        
        downloaded = 0
        failed = 0
        start_time = time.time()
        
        for idx, img in enumerate(images, 1):
            result = self.download_and_save_image(
                img['id'],
                img['page_id'],
                img['source_url']
            )
            
            if result:
                self.update_database(
                    img['id'],
                    result['drive_id'],
                    result['drive_url']
                )
                downloaded += 1
                
                if downloaded % 50 == 0:
                    elapsed = time.time() - start_time
                    rate = downloaded / elapsed
                    eta_hours = (len(images) - downloaded) / rate / 3600
                    print(f"✓ {downloaded:,}/{len(images):,} | "
                          f"{rate:.1f}/sec | ETA: {eta_hours:.1f}h")
            else:
                failed += 1
        
        print(f"\n{'='*80}")
        print(f"COMPLETE: {downloaded:,} saved | {failed:,} failed")
        print(f"{'='*80}\n")
        
        cursor.close()

def main():
    print("="*80)
    print("URGENT EOL IMAGE SAVER")
    print("SAVING 95,000 IMAGES BEFORE URLS ARE DESTROYED")
    print("="*80)
    print(f"Started: {datetime.now()}\n")
    
    saver = UrgentEOLSaver()
    
    # Step 1: Add data to Google Sheet
    print("\nSTEP 1: Adding data to your Google Sheet...")
    saver.add_eol_data_to_sheet()
    
    # Step 2: Create Drive folder
    print("\nSTEP 2: Creating Google Drive folder...")
    saver.create_drive_folder()
    
    # Step 3: Download images (start with first 100 as test)
    print("\nSTEP 3: Starting download process...")
    print("Testing with first 100 images...")
    saver.process_downloads(limit=100)
    
    print("\n" + "="*80)
    print("NEXT STEPS")
    print("="*80)
    print("1. Check your Google Sheet for the EOL data")
    print("2. Check your Google Drive for the new folder")
    print("3. If test successful, I'll download all 95,000")
    print("4. Total estimated time: ~10-15 hours for 95,000 images")

if __name__ == '__main__':
    main()
