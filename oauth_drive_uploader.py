#!/usr/bin/env python3
"""
OAuth-Based Google Drive Uploader for Orchid Continuum
Uses YOUR personal Google account (fcospresident@gmail.com) and 2TB storage
"""

import os
import json
import logging
import requests
import tempfile
import time
from datetime import datetime
from typing import Optional, Dict, List
import psycopg2
from psycopg2.extras import RealDictCursor
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('oauth_upload.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Your specific configuration
DRIVE_FOLDER_ID = '1jQoQ9x-2f1ENZq7iVCgneAmoQIvc6xIS'
SHEET_ID = '1UQZj4ZaA7cWnU0SozR4_qReWNOm0V9xz'
SHEET_NAME = 'Sheet1'

# OAuth scopes - full Drive and Sheets access
SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets'
]

BATCH_SIZE = 100
TIMEOUT = 30
MAX_RETRIES = 3

class OAuthDriveUploader:
    """Upload to YOUR personal Google Drive using OAuth"""
    
    def __init__(self):
        self.drive_service = None
        self.sheets_service = None
        self.db_conn = None
        self.stats = {
            'total': 0,
            'downloaded': 0,
            'uploaded': 0,
            'sheet_rows': 0,
            'failed': 0,
            'start_time': datetime.now()
        }
    
    def authenticate(self):
        """Authenticate with Google using OAuth (uses YOUR account)"""
        creds = None
        
        # Check for existing token
        if os.path.exists('token.json'):
            logger.info("📝 Found existing token...")
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
        # If no valid credentials, authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info("🔄 Refreshing expired token...")
                creds.refresh(Request())
            else:
                # Get OAuth credentials from Replit Secrets
                logger.info("🔐 Starting OAuth authentication...")
                oauth_json = os.environ.get('GOOGLE_OAUTH_CREDENTIALS')
                
                if not oauth_json:
                    logger.error("❌ GOOGLE_OAUTH_CREDENTIALS not found in Secrets")
                    logger.error("")
                    logger.error("TO FIX:")
                    logger.error("1. Go to: https://console.cloud.google.com/apis/credentials")
                    logger.error("2. Create OAuth Client ID → Desktop app")
                    logger.error("3. Download JSON")
                    logger.error("4. Add to Replit Secrets as GOOGLE_OAUTH_CREDENTIALS")
                    logger.error("")
                    raise ValueError("GOOGLE_OAUTH_CREDENTIALS required")
                
                # Parse and save temporarily
                credentials_data = json.loads(oauth_json)
                with open('temp_oauth.json', 'w') as f:
                    json.dump(credentials_data, f)
                
                # Run console flow (for Replit)
                flow = InstalledAppFlow.from_client_secrets_file(
                    'temp_oauth.json', 
                    SCOPES,
                    redirect_uri='urn:ietf:wg:oauth:2.0:oob'
                )
                
                logger.info("")
                logger.info("="*80)
                logger.info("🌐 AUTHORIZATION REQUIRED")
                logger.info("="*80)
                
                # Get authorization URL
                auth_url, _ = flow.authorization_url(
                    prompt='consent',
                    access_type='offline'
                )
                
                logger.info("1. Open this URL in your browser:")
                logger.info("")
                logger.info(auth_url)
                logger.info("")
                logger.info("2. Sign in with fcospresident@gmail.com")
                logger.info("3. Click 'Allow'")
                logger.info("4. Copy the authorization code")
                logger.info("")
                
                # Get code from user
                code = input("Paste authorization code here: ").strip()
                
                # Exchange code for credentials
                flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
                flow.fetch_token(code=code)
                creds = flow.credentials
                
                # Clean up
                os.remove('temp_oauth.json')
                
                logger.info("")
                logger.info("✅ Authorization successful!")
            
            # Save token for next time
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
            logger.info("💾 Token saved to token.json")
        
        return creds
    
    def initialize_services(self):
        """Initialize Google services with OAuth"""
        try:
            creds = self.authenticate()
            
            self.drive_service = build('drive', 'v3', credentials=creds)
            self.sheets_service = build('sheets', 'v4', credentials=creds)
            
            # Verify it's YOUR account
            about = self.drive_service.about().get(fields='user').execute()
            email = about.get('user', {}).get('emailAddress')
            
            logger.info("="*80)
            logger.info(f"✅ Authenticated as: {email}")
            logger.info(f"📁 Target folder: {DRIVE_FOLDER_ID}")
            logger.info(f"📊 Target sheet: {SHEET_ID}")
            logger.info("="*80)
            
            if email != 'fcospresident@gmail.com':
                logger.warning(f"⚠️  Warning: Expected fcospresident@gmail.com, got {email}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize: {e}")
            raise
    
    def initialize_database(self):
        """Initialize database"""
        try:
            database_url = os.environ.get('DATABASE_URL')
            if not database_url:
                raise ValueError("DATABASE_URL not found")
            
            self.db_conn = psycopg2.connect(database_url)
            logger.info("✅ Database connected")
            
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise
    
    def get_images_to_upload(self, limit: int = BATCH_SIZE) -> List[Dict]:
        """Get images needing upload (always fetches next batch with OFFSET 0)"""
        try:
            with self.db_conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        oi.id, oi.image_url, oi.taxonomy_id,
                        ot.scientific_name, ot.genus, ot.species,
                        oi.country, oi.latitude, oi.longitude,
                        oi.image_source, oi.observer_name,
                        oi.observation_date, oi.wild_specimen,
                        oi.image_license
                    FROM orchid_images oi
                    JOIN orchid_taxonomy ot ON oi.taxonomy_id = ot.id
                    WHERE oi.image_url IS NOT NULL
                    AND oi.image_url != ''
                    AND (oi.google_drive_url IS NULL OR oi.google_drive_url = '')
                    ORDER BY oi.id
                    LIMIT %s
                """, (limit,))
                
                return cur.fetchall()
                
        except Exception as e:
            logger.error(f"❌ Failed to fetch images: {e}")
            return []
    
    def download_image(self, url: str) -> Optional[str]:
        """Download image to temp file"""
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.get(url, timeout=TIMEOUT, stream=True)
                response.raise_for_status()
                
                # Determine extension
                content_type = response.headers.get('content-type', '')
                ext = '.jpg'
                if 'png' in content_type:
                    ext = '.png'
                elif 'gif' in content_type:
                    ext = '.gif'
                
                # Save to temp
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
                for chunk in response.iter_content(chunk_size=8192):
                    temp_file.write(chunk)
                temp_file.close()
                
                return temp_file.name
                
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)
                else:
                    logger.error(f"Download failed: {e}")
                    return None
    
    def upload_to_drive(self, file_path: str, filename: str) -> Optional[str]:
        """Upload to YOUR Google Drive"""
        try:
            file_metadata = {
                'name': filename,
                'parents': [DRIVE_FOLDER_ID]
            }
            
            media = MediaFileUpload(file_path, mimetype='image/jpeg', resumable=True)
            
            file = self.drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webViewLink'
            ).execute()
            
            # Make publicly readable
            self.drive_service.permissions().create(
                fileId=file['id'],
                body={'type': 'anyone', 'role': 'reader'}
            ).execute()
            
            return file.get('id')
            
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            return None
    
    def add_to_sheet(self, rows: List[List]):
        """Add rows to Google Sheet"""
        try:
            body = {'values': rows}
            
            self.sheets_service.spreadsheets().values().append(
                spreadsheetId=SHEET_ID,
                range=f'{SHEET_NAME}!A:Q',
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            logger.info(f"✅ Added {len(rows)} rows to Sheet")
            self.stats['sheet_rows'] += len(rows)
            
        except Exception as e:
            logger.error(f"Sheet update failed: {e}")
    
    def update_database(self, image_id: int, drive_url: str):
        """Update database with Drive URL"""
        try:
            with self.db_conn.cursor() as cur:
                cur.execute("""
                    UPDATE orchid_images
                    SET google_drive_url = %s, updated_at = NOW()
                    WHERE id = %s
                """, (drive_url, image_id))
                self.db_conn.commit()
                
        except Exception as e:
            logger.error(f"Database update failed: {e}")
            self.db_conn.rollback()
    
    def process_batch(self, batch: List[Dict]):
        """Process a batch"""
        sheet_rows = []
        
        for img in batch:
            self.stats['total'] += 1
            
            try:
                logger.info(f"[{self.stats['total']}] Processing: {img['scientific_name']}")
                
                # Download
                temp_file = self.download_image(img['image_url'])
                if not temp_file:
                    self.stats['failed'] += 1
                    continue
                
                self.stats['downloaded'] += 1
                
                # Upload
                filename = f"{img['genus']}_{img['species']}_{img['id']}.jpg"
                drive_id = self.upload_to_drive(temp_file, filename)
                
                # Cleanup
                try:
                    os.unlink(temp_file)
                except:
                    pass
                
                if not drive_id:
                    self.stats['failed'] += 1
                    continue
                
                self.stats['uploaded'] += 1
                
                # Generate URL
                drive_url = f"https://drive.google.com/file/d/{drive_id}/view?usp=drivesdk"
                
                # Update database
                self.update_database(img['id'], drive_url)
                
                # Prepare sheet row (convert Decimals to strings for JSON serialization)
                sheet_row = [
                    img['id'], img['scientific_name'], img['scientific_name'],
                    img['genus'] or '', img['species'] or '', '',
                    img['country'] or '', 
                    str(img['latitude']) if img['latitude'] is not None else '', 
                    str(img['longitude']) if img['longitude'] is not None else '',
                    '', '', '', 'TRUE' if img.get('wild_specimen') else 'FALSE',
                    drive_url, img['observer_name'] or '', img['image_source'] or '',
                    str(img['observation_date']) if img['observation_date'] else datetime.now().isoformat()
                ]
                sheet_rows.append(sheet_row)
                
                # Add to sheet in batches
                if len(sheet_rows) >= 50:
                    self.add_to_sheet(sheet_rows)
                    sheet_rows = []
                
                # Progress log
                if self.stats['total'] % 10 == 0:
                    elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
                    rate = self.stats['uploaded'] / (elapsed / 60) if elapsed > 0 else 0
                    logger.info(f"📊 Progress: {self.stats['uploaded']:,} uploaded, {rate:.1f}/min")
                
            except Exception as e:
                logger.error(f"Error processing {img['id']}: {e}")
                self.stats['failed'] += 1
        
        # Add remaining rows
        if sheet_rows:
            self.add_to_sheet(sheet_rows)
    
    def run(self, max_images: Optional[int] = None):
        """Run uploader"""
        logger.info("🌺 Orchid Continuum - OAuth Drive Uploader")
        logger.info("="*80)
        
        self.initialize_services()
        self.initialize_database()
        
        # Get total count
        with self.db_conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) FROM orchid_images
                WHERE image_url IS NOT NULL AND image_url != ''
                AND (google_drive_url IS NULL OR google_drive_url = '')
            """)
            total_to_upload = cur.fetchone()[0]
        
        logger.info(f"📊 Found {total_to_upload:,} images to upload")
        
        if max_images:
            total_to_upload = min(total_to_upload, max_images)
            logger.info(f"   Limited to {max_images:,} images")
        
        # Process in batches (always fetch from OFFSET 0 since processed rows are removed from results)
        batch_num = 0
        total_processed = 0
        
        while total_processed < total_to_upload:
            batch = self.get_images_to_upload(BATCH_SIZE)
            
            if not batch:
                logger.info("✅ No more images to process")
                break
            
            batch_num += 1
            logger.info(f"\n📦 Batch {batch_num} ({total_processed+1}-{total_processed+len(batch)} of {total_to_upload:,})")
            self.process_batch(batch)
            
            total_processed += len(batch)
            
            # Recalculate remaining (live count)
            with self.db_conn.cursor() as cur:
                cur.execute("""
                    SELECT COUNT(*) FROM orchid_images
                    WHERE image_url IS NOT NULL AND image_url != ''
                    AND (google_drive_url IS NULL OR google_drive_url = '')
                """)
                remaining = cur.fetchone()[0]
                logger.info(f"📊 Remaining: {remaining:,} images")
        
        # Final stats
        elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
        logger.info("\n" + "="*80)
        logger.info("🎉 UPLOAD COMPLETE!")
        logger.info(f"⏱️  Time: {elapsed/3600:.1f} hours")
        logger.info(f"✅ Uploaded: {self.stats['uploaded']:,}")
        logger.info(f"📋 Sheet rows: {self.stats['sheet_rows']:,}")
        logger.info(f"❌ Failed: {self.stats['failed']}")
        logger.info(f"🚀 Rate: {self.stats['uploaded']/(elapsed/60):.1f} images/min")
        logger.info("="*80)

if __name__ == '__main__':
    import sys
    
    max_images = None
    if len(sys.argv) > 1:
        max_images = int(sys.argv[1])
    
    uploader = OAuthDriveUploader()
    uploader.run(max_images)
