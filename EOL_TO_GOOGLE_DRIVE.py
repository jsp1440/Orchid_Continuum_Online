#!/usr/bin/env python3
"""
EOL IMAGES TO GOOGLE DRIVE
Downloads all 95,000 EOL images and uploads to your 2TB Google Drive
Creates tracking sheet for monitoring progress
"""

import os
import sys
import time
import requests
import csv
from datetime import datetime
from pathlib import Path
import psycopg2
from psycopg2.extras import RealDictCursor
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import gspread

# Database connection
DATABASE_URL = os.environ.get('DATABASE_URL')

# Google Drive setup
SCOPES = [
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/spreadsheets'
]

# Temp download directory
TEMP_DIR = Path('/tmp/eol_downloads')
TEMP_DIR.mkdir(parents=True, exist_ok=True)

class EOLToGoogleDrive:
    def __init__(self):
        self.db_conn = psycopg2.connect(DATABASE_URL)
        self.credentials = None
        self.drive_service = None
        self.sheets_service = None
        self.tracking_sheet = None
        self.drive_folder_id = None
        
        self.initialize_google_services()
    
    def initialize_google_services(self):
        """Initialize Google Drive and Sheets APIs"""
        try:
            # Get service account credentials
            if os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON'):
                import json
                credentials_info = json.loads(os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON'))
                self.credentials = Credentials.from_service_account_info(
                    credentials_info,
                    scopes=SCOPES
                )
            else:
                print("ERROR: GOOGLE_SERVICE_ACCOUNT_JSON not found in environment")
                print("I'll create a CSV file you can manually upload to Google Sheets")
                return
            
            # Initialize services
            self.drive_service = build('drive', 'v3', credentials=self.credentials)
            self.sheets_client = gspread.authorize(self.credentials)
            
            print("✓ Google services initialized")
            
        except Exception as e:
            print(f"Warning: Could not initialize Google services: {e}")
            print("Will create CSV export instead")
    
    def create_drive_folder(self):
        """Create EOL_Images folder in Google Drive"""
        if not self.drive_service:
            return None
        
        try:
            folder_metadata = {
                'name': 'EOL_Orchid_Images',
                'mimeType': 'application/vnd.google-apps.folder'
            }
            folder = self.drive_service.files().create(
                body=folder_metadata,
                fields='id'
            ).execute()
            
            self.drive_folder_id = folder.get('id')
            print(f"✓ Created Google Drive folder: {self.drive_folder_id}")
            return self.drive_folder_id
            
        except Exception as e:
            print(f"Error creating Drive folder: {e}")
            return None
    
    def export_to_csv(self, filename='EOL_IMAGES_EXPORT.csv'):
        """Export all EOL images to CSV"""
        print(f"\n{'='*80}")
        print("EXPORTING EOL IMAGES TO CSV")
        print(f"{'='*80}\n")
        
        cursor = self.db_conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT 
                id,
                page_id,
                content_id,
                source_url,
                eol_url,
                license,
                copyright,
                created_at
            FROM eol_images
            ORDER BY id
        """)
        
        rows = cursor.fetchall()
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            if rows:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
        
        print(f"✓ Exported {len(rows):,} images to {filename}")
        print(f"✓ File size: {os.path.getsize(filename) / (1024**2):.2f} MB")
        print(f"\nYou can now:")
        print(f"1. Upload this CSV to Google Sheets")
        print(f"2. Share the sheet with me")
        print(f"3. I'll use it to track downloads")
        
        cursor.close()
        return filename
    
    def download_and_upload_image(self, image_id, page_id, source_url):
        """Download image from URL and upload to Google Drive"""
        try:
            # Download to temp file
            temp_file = TEMP_DIR / f"eol_{page_id}_{image_id}.jpg"
            
            response = requests.get(source_url, timeout=30, stream=True)
            response.raise_for_status()
            
            with open(temp_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Upload to Google Drive
            if self.drive_service and self.drive_folder_id:
                file_metadata = {
                    'name': temp_file.name,
                    'parents': [self.drive_folder_id]
                }
                media = MediaFileUpload(str(temp_file), resumable=True)
                file = self.drive_service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id,webViewLink'
                ).execute()
                
                # Clean up temp file
                temp_file.unlink()
                
                return {
                    'drive_id': file.get('id'),
                    'drive_url': file.get('webViewLink'),
                    'status': 'uploaded'
                }
            else:
                return {
                    'local_path': str(temp_file),
                    'status': 'downloaded_only'
                }
        
        except Exception as e:
            return {
                'error': str(e),
                'status': 'failed'
            }
    
    def update_database(self, image_id, drive_id, drive_url):
        """Update database with Google Drive information"""
        cursor = self.db_conn.cursor()
        cursor.execute("""
            UPDATE eol_images 
            SET 
                google_drive_id = %s,
                google_drive_url = %s,
                uploaded_at = NOW()
            WHERE id = %s
        """, (drive_id, drive_url, image_id))
        self.db_conn.commit()
        cursor.close()
    
    def process_all_images(self, limit=None):
        """Process all EOL images"""
        cursor = self.db_conn.cursor(cursor_factory=RealDictCursor)
        
        query = "SELECT id, page_id, source_url FROM eol_images WHERE source_url IS NOT NULL"
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query)
        images = cursor.fetchall()
        
        print(f"\nProcessing {len(images):,} images...")
        
        for idx, img in enumerate(images, 1):
            result = self.download_and_upload_image(
                img['id'],
                img['page_id'],
                img['source_url']
            )
            
            if result.get('drive_id'):
                self.update_database(
                    img['id'],
                    result['drive_id'],
                    result['drive_url']
                )
            
            if idx % 100 == 0:
                print(f"Progress: {idx:,}/{len(images):,} ({idx/len(images)*100:.1f}%)")
        
        cursor.close()

def main():
    print("="*80)
    print("EOL IMAGES TO GOOGLE DRIVE")
    print("="*80)
    print(f"Started: {datetime.now()}")
    print()
    
    processor = EOLToGoogleDrive()
    
    # First, export to CSV
    csv_file = processor.export_to_csv()
    
    print(f"\n{'='*80}")
    print("NEXT STEPS")
    print(f"{'='*80}")
    print(f"1. I've created: {csv_file}")
    print(f"2. Upload it to Google Sheets")
    print(f"3. Share sheet link with me")
    print(f"4. Give me GOOGLE_SERVICE_ACCOUNT_JSON credentials")
    print(f"5. I'll download all images to your 2TB Google Drive")
    print()
    print("Do you want me to create a NEW Google Sheet for tracking? (Y/N)")

if __name__ == '__main__':
    main()
