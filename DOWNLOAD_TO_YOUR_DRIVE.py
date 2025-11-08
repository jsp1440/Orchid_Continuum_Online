#!/usr/bin/env python3
"""
Download all 95,000 EOL images and upload to user's Google Drive
Uses Shared Drive to access user's 2TB storage
"""

import os
import json
import requests
import tempfile
import time
from pathlib import Path
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import concurrent.futures

DATABASE_URL = os.environ.get('DATABASE_URL')

SCOPES = ['https://www.googleapis.com/auth/drive']

class EOLImageDownloader:
    def __init__(self, shared_drive_id=None):
        self.db_conn = psycopg2.connect(DATABASE_URL)
        self.drive_service = None
        self.shared_drive_id = shared_drive_id
        self.folder_id = None
        
        self.downloaded = 0
        self.uploaded = 0
        self.failed = 0
        self.start_time = time.time()
        
        self.initialize_drive()
    
    def initialize_drive(self):
        """Initialize Google Drive connection"""
        try:
            creds_dict = json.loads(os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON'))
            credentials = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
            self.drive_service = build('drive', 'v3', credentials=credentials)
            print("✓ Connected to Google Drive")
        except Exception as e:
            print(f"Error connecting to Drive: {e}")
    
    def create_shared_drive_folder(self):
        """Create folder in Shared Drive for EOL images"""
        if not self.drive_service:
            return None
        
        try:
            folder_metadata = {
                'name': 'EOL_Orchid_Images_95000',
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            # If using Shared Drive
            if self.shared_drive_id:
                folder_metadata['parents'] = [self.shared_drive_id]
                folder = self.drive_service.files().create(
                    body=folder_metadata,
                    fields='id, webViewLink',
                    supportsAllDrives=True
                ).execute()
            else:
                # Regular Drive folder
                folder = self.drive_service.files().create(
                    body=folder_metadata,
                    fields='id, webViewLink'
                ).execute()
            
            self.folder_id = folder.get('id')
            print(f"✓ Created folder: {folder.get('webViewLink')}")
            return self.folder_id
            
        except Exception as e:
            print(f"Error creating folder: {e}")
            return None
    
    def list_shared_drives(self):
        """List available Shared Drives"""
        try:
            results = self.drive_service.drives().list(pageSize=10).execute()
            drives = results.get('drives', [])
            
            if drives:
                print("\nAvailable Shared Drives:")
                for drive in drives:
                    print(f"  - {drive['name']} (ID: {drive['id']})")
            else:
                print("\nNo Shared Drives found.")
                print("Please create a Shared Drive in your Google Drive and share it with the service account.")
            
            return drives
        except Exception as e:
            print(f"Error listing drives: {e}")
            return []
    
    def download_and_upload_image(self, eol_id, page_id, source_url):
        """Download image from URL and upload to Drive"""
        try:
            # Download to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
                response = requests.get(source_url, timeout=30, stream=True)
                response.raise_for_status()
                
                for chunk in response.iter_content(chunk_size=8192):
                    tmp.write(chunk)
                
                tmp_path = tmp.name
                file_size = Path(tmp_path).stat().st_size
            
            # Upload to Drive
            file_metadata = {
                'name': f'eol_{page_id}_{eol_id}.jpg'
            }
            
            if self.folder_id:
                file_metadata['parents'] = [self.folder_id]
            
            media = MediaFileUpload(tmp_path, resumable=True)
            
            # Upload with Shared Drive support
            file = self.drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webViewLink, size',
                supportsAllDrives=True
            ).execute()
            
            # Clean up temp file
            os.unlink(tmp_path)
            
            # Update database
            cursor = self.db_conn.cursor()
            cursor.execute("""
                UPDATE eol_images 
                SET google_drive_id = %s,
                    google_drive_url = %s,
                    file_size_kb = %s,
                    download_status = 'uploaded',
                    uploaded_at = NOW()
                WHERE id = %s
            """, (file.get('id'), file.get('webViewLink'), file_size // 1024, eol_id))
            self.db_conn.commit()
            cursor.close()
            
            self.uploaded += 1
            return {'status': 'success', 'drive_id': file.get('id')}
            
        except Exception as e:
            self.failed += 1
            return {'status': 'failed', 'error': str(e)}
    
    def process_all_images(self, limit=None, max_workers=10):
        """Download all images in parallel"""
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
        total = len(images)
        
        print(f"\n{'='*80}")
        print(f"DOWNLOADING {total:,} IMAGES TO YOUR GOOGLE DRIVE")
        print(f"{'='*80}\n")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            for img in images:
                future = executor.submit(
                    self.download_and_upload_image,
                    img['id'],
                    img['page_id'],
                    img['source_url']
                )
                futures[future] = img
            
            completed = 0
            for future in concurrent.futures.as_completed(futures):
                completed += 1
                
                if completed % 50 == 0:
                    elapsed = time.time() - self.start_time
                    rate = completed / elapsed
                    eta_hours = (total - completed) / rate / 3600 if rate > 0 else 0
                    
                    print(f"Progress: {completed:,}/{total:,} ({completed/total*100:.1f}%) | "
                          f"Rate: {rate:.1f}/sec | ETA: {eta_hours:.1f}h | "
                          f"✓{self.uploaded:,} ✗{self.failed:,}")
        
        cursor.close()

def main():
    print("="*80)
    print("EOL IMAGES → YOUR GOOGLE DRIVE")
    print("="*80)
    print(f"Started: {datetime.now()}\n")
    
    downloader = EOLImageDownloader()
    
    # Check for Shared Drives
    print("\nChecking for Shared Drives...")
    drives = downloader.list_shared_drives()
    
    if drives:
        print("\nIMPORTANT: Using Shared Drive for your 2TB storage")
        print(f"Using: {drives[0]['name']}")
        downloader.shared_drive_id = drives[0]['id']
    else:
        print("\n⚠️  NO SHARED DRIVE FOUND")
        print("\nTO USE YOUR 2TB STORAGE:")
        print("1. Go to Google Drive")
        print("2. Create a new 'Shared drive'")
        print("3. Share it with the service account email")
        print("4. Run this script again")
        return
    
    # Create folder
    print("\nCreating folder...")
    downloader.create_shared_drive_folder()
    
    # Test with first 10 images
    print("\nTesting with first 10 images...")
    downloader.process_all_images(limit=10, max_workers=5)
    
    elapsed = time.time() - downloader.start_time
    print(f"\n{'='*80}")
    print(f"TEST COMPLETE")
    print(f"{'='*80}")
    print(f"Uploaded: {downloader.uploaded}")
    print(f"Failed: {downloader.failed}")
    print(f"Time: {elapsed:.1f} seconds")
    
    if downloader.uploaded > 0:
        print("\n✓ SUCCESS! Ready to download all 95,000 images")
        print("\nTo download ALL images, run:")
        print("  downloader.process_all_images(max_workers=20)")
    else:
        print("\n✗ Test failed. Check Shared Drive permissions.")

if __name__ == '__main__':
    main()
