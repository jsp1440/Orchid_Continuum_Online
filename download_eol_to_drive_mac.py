#!/usr/bin/env python3
"""
EOL Images to Google Drive - Mac Version
Run this on your iMac to download 95,000 EOL images and save to your 2TB Google Drive

SETUP (First time only):
1. Install dependencies: pip3 install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client requests
2. Download your OAuth credentials from Google Cloud Console
3. Place credentials.json in same folder as this script
4. Run: python3 download_eol_to_drive_mac.py

This will open a browser to authenticate with YOUR Google account.
Once authenticated, it will download all 95,000 images to your Drive.
"""

import os
import csv
import pickle
import requests
import time
from pathlib import Path
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import tempfile

# Google Drive API scope
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# CSV file from Replit
CSV_FILE = 'EOL_IMAGES_COMPLETE_95000.csv'

class EOLDownloader:
    def __init__(self):
        self.creds = None
        self.service = None
        self.folder_id = None
        
        self.downloaded = 0
        self.uploaded = 0
        self.failed = 0
        self.skipped = 0
        
        self.authenticate()
        self.create_folder()
    
    def authenticate(self):
        """Authenticate with Google Drive using YOUR Google account"""
        # Token file stores the user's access and refresh tokens
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                self.creds = pickle.load(token)
        
        # If there are no (valid) credentials available, let the user log in
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                if not os.path.exists('credentials.json'):
                    print("\n❌ ERROR: credentials.json not found!")
                    print("\nTO GET CREDENTIALS:")
                    print("1. Go to: https://console.cloud.google.com/")
                    print("2. Create a project (or use existing)")
                    print("3. Enable Google Drive API")
                    print("4. Create OAuth 2.0 credentials (Desktop app)")
                    print("5. Download credentials.json to this folder")
                    print("6. Run this script again\n")
                    exit(1)
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                self.creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(self.creds, token)
        
        self.service = build('drive', 'v3', credentials=self.creds)
        print("✓ Authenticated with YOUR Google Drive\n")
    
    def create_folder(self):
        """Create folder in YOUR Google Drive"""
        folder_metadata = {
            'name': 'EOL_Orchid_Images_95000',
            'mimeType': 'application/vnd.google-apps.folder'
        }
        
        folder = self.service.files().create(
            body=folder_metadata,
            fields='id, webViewLink'
        ).execute()
        
        self.folder_id = folder.get('id')
        print(f"✓ Created folder in your Drive: {folder.get('webViewLink')}\n")
    
    def download_and_upload(self, row_num, eol_id, page_id, source_url):
        """Download image from URL and upload to your Drive"""
        try:
            # Check if already uploaded (in case of restart)
            filename = f'eol_{page_id}_{eol_id}.jpg'
            
            # Search if file already exists
            query = f"name='{filename}' and '{self.folder_id}' in parents and trashed=false"
            results = self.service.files().list(q=query, fields='files(id)').execute()
            if results.get('files'):
                self.skipped += 1
                return {'status': 'skipped', 'reason': 'already exists'}
            
            # Download to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
                response = requests.get(source_url, timeout=30, stream=True)
                response.raise_for_status()
                
                for chunk in response.iter_content(chunk_size=8192):
                    tmp.write(chunk)
                
                tmp_path = tmp.name
            
            self.downloaded += 1
            
            # Upload to YOUR Drive
            file_metadata = {
                'name': filename,
                'parents': [self.folder_id]
            }
            
            media = MediaFileUpload(tmp_path, resumable=True)
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webViewLink'
            ).execute()
            
            # Clean up
            os.unlink(tmp_path)
            
            self.uploaded += 1
            return {
                'status': 'success',
                'drive_id': file.get('id'),
                'drive_url': file.get('webViewLink')
            }
            
        except Exception as e:
            self.failed += 1
            return {'status': 'failed', 'error': str(e)}
    
    def process_csv(self):
        """Process all images from CSV"""
        if not os.path.exists(CSV_FILE):
            print(f"❌ ERROR: {CSV_FILE} not found!")
            print(f"\nDownload it from Replit and place it in this folder.")
            return
        
        print(f"{'='*80}")
        print(f"DOWNLOADING 95,000 IMAGES TO YOUR GOOGLE DRIVE")
        print(f"{'='*80}\n")
        
        start_time = time.time()
        
        with open(CSV_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            total = 95000  # We know there are 95,000
            
            for row_num, row in enumerate(reader, 1):
                if row_num == 1:
                    print(f"Starting download of {total:,} images...")
                    print(f"This will take approximately 10-15 hours\n")
                
                result = self.download_and_upload(
                    row_num,
                    row['eol_id'],
                    row['page_id'],
                    row['source_url']
                )
                
                # Progress every 50 images
                if row_num % 50 == 0:
                    elapsed = time.time() - start_time
                    rate = row_num / elapsed
                    eta_hours = (total - row_num) / rate / 3600 if rate > 0 else 0
                    
                    print(f"Progress: {row_num:,}/{total:,} ({row_num/total*100:.1f}%) | "
                          f"Rate: {rate:.1f}/sec | ETA: {eta_hours:.1f}h | "
                          f"✓{self.uploaded:,} ↓{self.downloaded:,} ✗{self.failed:,} ⊘{self.skipped:,}")
                
                # Save progress every 1000 images
                if row_num % 1000 == 0:
                    self.save_progress(row_num)
        
        elapsed = time.time() - start_time
        print(f"\n{'='*80}")
        print(f"COMPLETE!")
        print(f"{'='*80}")
        print(f"Uploaded: {self.uploaded:,}")
        print(f"Downloaded: {self.downloaded:,}")
        print(f"Failed: {self.failed:,}")
        print(f"Skipped: {self.skipped:,}")
        print(f"Time: {elapsed/3600:.2f} hours")
        print(f"\nAll images saved to your Google Drive!")
    
    def save_progress(self, row_num):
        """Save progress to file (in case of interruption)"""
        with open('progress.txt', 'w') as f:
            f.write(f"Last processed: {row_num}\n")
            f.write(f"Uploaded: {self.uploaded}\n")
            f.write(f"Failed: {self.failed}\n")
            f.write(f"Timestamp: {datetime.now()}\n")

def main():
    print("="*80)
    print("EOL IMAGES TO YOUR GOOGLE DRIVE")
    print("="*80)
    print(f"Started: {datetime.now()}")
    print()
    
    # Check if CSV exists
    if not os.path.exists(CSV_FILE):
        print(f"❌ {CSV_FILE} not found in current directory")
        print(f"\n1. Download {CSV_FILE} from Replit")
        print(f"2. Place it in the same folder as this script")
        print(f"3. Run this script again\n")
        return
    
    # Run downloader
    downloader = EOLDownloader()
    downloader.process_csv()

if __name__ == '__main__':
    main()
