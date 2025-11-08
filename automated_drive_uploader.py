#!/usr/bin/env python3
"""
Automated Google Drive Uploader for Orchid Continuum
Downloads images from URLs and uploads to Google Drive + Google Sheets
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
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.service_account import Credentials
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('drive_upload.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Your specific Google Drive configuration
DRIVE_FOLDER_ID = '1jQoQ9x-2f1ENZq7iVCgneAmoQIvc6xIS'
SHEET_ID = '1UQZj4ZaA7cWnU0SozR4_qReWNOm0V9xz'
SHEET_NAME = 'Sheet1'

SCOPES = [
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/spreadsheets'
]

BATCH_SIZE = 100  # Process 100 images at a time
TIMEOUT = 30
MAX_RETRIES = 3

class OrchidDriveUploader:
    """Upload orchid images to Google Drive and populate Google Sheets"""
    
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
            'skipped': 0,
            'start_time': datetime.now()
        }
    
    def initialize_services(self):
        """Initialize Google Drive and Sheets services"""
        try:
            service_account_json = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON')
            if not service_account_json:
                raise ValueError("GOOGLE_SERVICE_ACCOUNT_JSON not found")
            
            credentials_info = json.loads(service_account_json)
            credentials = Credentials.from_service_account_info(
                credentials_info,
                scopes=SCOPES
            )
            
            self.drive_service = build('drive', 'v3', credentials=credentials)
            self.sheets_service = build('sheets', 'v4', credentials=credentials)
            
            logger.info("✅ Google services initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Google services: {e}")
            raise
    
    def initialize_database(self):
        """Initialize database connection"""
        try:
            database_url = os.environ.get('DATABASE_URL')
            if not database_url:
                raise ValueError("DATABASE_URL not found")
            
            self.db_conn = psycopg2.connect(database_url)
            logger.info("✅ Database connected")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to database: {e}")
            raise
    
    def get_images_to_upload(self, limit: int = BATCH_SIZE, offset: int = 0) -> List[Dict]:
        """Get images that need uploading"""
        try:
            with self.db_conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        oi.id,
                        oi.image_url,
                        oi.taxonomy_id,
                        ot.scientific_name,
                        ot.genus,
                        ot.species,
                        oi.country,
                        oi.latitude,
                        oi.longitude,
                        oi.image_source,
                        oi.observer_name,
                        oi.observation_date,
                        oi.wild_specimen,
                        oi.image_license
                    FROM orchid_images oi
                    JOIN orchid_taxonomy ot ON oi.taxonomy_id = ot.id
                    WHERE oi.image_url IS NOT NULL
                    AND oi.image_url != ''
                    AND (oi.google_drive_url IS NULL OR oi.google_drive_url = '')
                    ORDER BY oi.id
                    LIMIT %s OFFSET %s
                """, (limit, offset))
                
                return cur.fetchall()
                
        except Exception as e:
            logger.error(f"❌ Failed to fetch images: {e}")
            return []
    
    def download_image(self, url: str, image_id: int) -> Optional[str]:
        """Download image from URL to temporary file"""
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.get(url, timeout=TIMEOUT, stream=True)
                response.raise_for_status()
                
                # Determine file extension
                content_type = response.headers.get('content-type', '')
                ext = '.jpg'
                if 'png' in content_type:
                    ext = '.png'
                elif 'gif' in content_type:
                    ext = '.gif'
                
                # Save to temp file
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
                for chunk in response.iter_content(chunk_size=8192):
                    temp_file.write(chunk)
                temp_file.close()
                
                return temp_file.name
                
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)
                else:
                    logger.error(f"Failed to download {url}: {e}")
                    return None
    
    def upload_to_drive(self, file_path: str, filename: str) -> Optional[str]:
        """Upload file to Google Drive and return file ID"""
        try:
            file_metadata = {
                'name': filename,
                'parents': [DRIVE_FOLDER_ID]
            }
            
            media = MediaFileUpload(
                file_path,
                mimetype='image/jpeg',
                resumable=True
            )
            
            file = self.drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webViewLink'
            ).execute()
            
            # Make file publicly readable
            self.drive_service.permissions().create(
                fileId=file['id'],
                body={'type': 'anyone', 'role': 'reader'}
            ).execute()
            
            return file.get('id')
            
        except Exception as e:
            logger.error(f"Failed to upload to Drive: {e}")
            return None
    
    def add_to_sheet(self, rows: List[List]):
        """Add rows to Google Sheet"""
        try:
            body = {
                'values': rows
            }
            
            self.sheets_service.spreadsheets().values().append(
                spreadsheetId=SHEET_ID,
                range=f'{SHEET_NAME}!A:Q',
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            logger.info(f"✅ Added {len(rows)} rows to Google Sheet")
            self.stats['sheet_rows'] += len(rows)
            
        except Exception as e:
            logger.error(f"Failed to add to sheet: {e}")
    
    def update_database(self, image_id: int, drive_url: str):
        """Update database with Drive URL"""
        try:
            with self.db_conn.cursor() as cur:
                cur.execute("""
                    UPDATE orchid_images
                    SET google_drive_url = %s,
                        updated_at = NOW()
                    WHERE id = %s
                """, (drive_url, image_id))
                self.db_conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to update database: {e}")
            self.db_conn.rollback()
    
    def process_batch(self, batch: List[Dict]):
        """Process a batch of images"""
        sheet_rows = []
        
        for img in batch:
            self.stats['total'] += 1
            
            try:
                # Download image
                logger.info(f"[{self.stats['total']}] Downloading: {img['scientific_name']}")
                temp_file = self.download_image(img['image_url'], img['id'])
                
                if not temp_file:
                    self.stats['failed'] += 1
                    continue
                
                self.stats['downloaded'] += 1
                
                # Upload to Drive
                filename = f"{img['genus']}_{img['species']}_{img['id']}.jpg"
                drive_id = self.upload_to_drive(temp_file, filename)
                
                # Clean up temp file
                try:
                    os.unlink(temp_file)
                except:
                    pass
                
                if not drive_id:
                    self.stats['failed'] += 1
                    continue
                
                self.stats['uploaded'] += 1
                
                # Generate Drive URL
                drive_url = f"https://drive.google.com/file/d/{drive_id}/view?usp=drivesdk"
                
                # Update database
                self.update_database(img['id'], drive_url)
                
                # Prepare sheet row
                sheet_row = [
                    img['id'],
                    img['scientific_name'],
                    img['scientific_name'],
                    img['genus'] or '',
                    img['species'] or '',
                    '',  # region
                    img['country'] or '',
                    img['latitude'] or '',
                    img['longitude'] or '',
                    '',  # growth_habit
                    '',  # bloom_time
                    '',  # flower_color
                    'TRUE' if img.get('wild_specimen') else 'FALSE',
                    drive_url,
                    img['observer_name'] or '',
                    img['image_source'] or '',
                    img['observation_date'] or datetime.now().isoformat()
                ]
                sheet_rows.append(sheet_row)
                
                # Add to sheet every 50 rows
                if len(sheet_rows) >= 50:
                    self.add_to_sheet(sheet_rows)
                    sheet_rows = []
                
                # Log progress
                if self.stats['total'] % 10 == 0:
                    elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
                    rate = self.stats['uploaded'] / (elapsed / 60) if elapsed > 0 else 0
                    logger.info(f"Progress: {self.stats['uploaded']:,} uploaded, {self.stats['failed']} failed, {rate:.1f} images/min")
                
            except Exception as e:
                logger.error(f"Error processing image {img['id']}: {e}")
                self.stats['failed'] += 1
        
        # Add remaining rows to sheet
        if sheet_rows:
            self.add_to_sheet(sheet_rows)
    
    def run(self, max_images: Optional[int] = None):
        """Run the uploader"""
        logger.info("🚀 Starting Orchid Drive Uploader")
        logger.info(f"   Drive Folder: {DRIVE_FOLDER_ID}")
        logger.info(f"   Google Sheet: {SHEET_ID}")
        
        self.initialize_services()
        self.initialize_database()
        
        # Get total count
        with self.db_conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) FROM orchid_images
                WHERE image_url IS NOT NULL
                AND image_url != ''
                AND (google_drive_url IS NULL OR google_drive_url = '')
            """)
            total_to_upload = cur.fetchone()[0]
        
        logger.info(f"📊 Found {total_to_upload:,} images to upload")
        
        if max_images:
            total_to_upload = min(total_to_upload, max_images)
            logger.info(f"   Limited to {max_images:,} images")
        
        # Process in batches
        offset = 0
        while offset < total_to_upload:
            batch = self.get_images_to_upload(BATCH_SIZE, offset)
            
            if not batch:
                break
            
            logger.info(f"\n📦 Processing batch {offset//BATCH_SIZE + 1} ({offset+1}-{offset+len(batch)} of {total_to_upload:,})")
            self.process_batch(batch)
            
            offset += BATCH_SIZE
        
        # Final stats
        elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
        logger.info("\n" + "="*80)
        logger.info("🎉 UPLOAD COMPLETE!")
        logger.info("="*80)
        logger.info(f"⏱️  Total time: {elapsed/3600:.1f} hours")
        logger.info(f"📊 Total processed: {self.stats['total']:,}")
        logger.info(f"✅ Downloaded: {self.stats['downloaded']:,}")
        logger.info(f"☁️  Uploaded to Drive: {self.stats['uploaded']:,}")
        logger.info(f"📋 Added to Sheet: {self.stats['sheet_rows']:,} rows")
        logger.info(f"❌ Failed: {self.stats['failed']}")
        logger.info(f"🚀 Average rate: {self.stats['uploaded']/(elapsed/60):.1f} images/min")
        logger.info("="*80)

if __name__ == '__main__':
    import sys
    
    # Check if limit specified
    max_images = None
    if len(sys.argv) > 1:
        max_images = int(sys.argv[1])
        print(f"🎯 Limited run: {max_images:,} images")
    
    uploader = OrchidDriveUploader()
    uploader.run(max_images)
