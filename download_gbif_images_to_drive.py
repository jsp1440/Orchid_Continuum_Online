#!/usr/bin/env python3
"""
GBIF Image Downloader → Google Drive Uploader
Downloads orchid images from GBIF URLs and uploads them to Google Drive
"""

import os
import sys
import json
import logging
import requests
import tempfile
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict
import psycopg2
from psycopg2.extras import RealDictCursor
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.service_account import Credentials
from PIL import Image
import imagehash

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Google Drive configuration
SCOPES = ['https://www.googleapis.com/auth/drive.file']
DRIVE_FOLDER_NAME = 'Orchid_GBIF_Images'

# Download configuration
MAX_DOWNLOADS = 1000  # Limit for first batch
BATCH_SIZE = 50       # Commit every 50 images
TIMEOUT = 30          # Request timeout in seconds

class GBIFImageDownloader:
    """Download GBIF images and upload to Google Drive"""
    
    def __init__(self):
        self.drive_service = None
        self.folder_id = None
        self.db_conn = None
        self.stats = {
            'total': 0,
            'downloaded': 0,
            'uploaded': 0,
            'failed': 0,
            'skipped': 0
        }
    
    def initialize_drive(self):
        """Initialize Google Drive service"""
        try:
            service_account_json = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON')
            if not service_account_json:
                raise ValueError("GOOGLE_SERVICE_ACCOUNT_JSON not found in environment")
            
            credentials_info = json.loads(service_account_json)
            credentials = Credentials.from_service_account_info(
                credentials_info,
                scopes=SCOPES
            )
            
            self.drive_service = build('drive', 'v3', credentials=credentials)
            logger.info("✅ Google Drive service initialized")
            
            # Get or create folder
            self.folder_id = self._get_or_create_folder(DRIVE_FOLDER_NAME)
            logger.info(f"✅ Using Google Drive folder: {DRIVE_FOLDER_NAME} (ID: {self.folder_id})")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Google Drive: {e}")
            raise
    
    def _get_or_create_folder(self, folder_name: str) -> str:
        """Get existing folder or create new one"""
        try:
            # Search for existing folder
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.drive_service.files().list(q=query, fields='files(id, name)').execute()
            folders = results.get('files', [])
            
            if folders:
                return folders[0]['id']
            
            # Create new folder
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            folder = self.drive_service.files().create(body=folder_metadata, fields='id').execute()
            logger.info(f"📁 Created new folder: {folder_name}")
            return folder.get('id')
            
        except Exception as e:
            logger.error(f"❌ Failed to get/create folder: {e}")
            raise
    
    def initialize_database(self):
        """Initialize database connection"""
        try:
            database_url = os.environ.get('DATABASE_URL')
            if not database_url:
                raise ValueError("DATABASE_URL not found in environment")
            
            self.db_conn = psycopg2.connect(database_url)
            logger.info("✅ Database connected")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to database: {e}")
            raise
    
    def get_images_to_download(self, limit: int = MAX_DOWNLOADS) -> list:
        """Get GBIF images that need to be downloaded"""
        try:
            with self.db_conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Find images without local_path or asset_id
                cur.execute("""
                    SELECT id, image_url, taxonomy_id, gbif_occurrence_key,
                           image_license, latitude, longitude, country
                    FROM orchid_images
                    WHERE (image_source LIKE '%%GBIF%%' OR gbif_occurrence_key IS NOT NULL)
                      AND is_duplicate IS NOT TRUE
                      AND image_url IS NOT NULL
                      AND image_url != ''
                      AND image_url NOT LIKE '%%imageprotected%%'
                      AND (local_path IS NULL OR local_path = '')
                      AND (download_status IS NULL OR download_status != 'completed')
                    ORDER BY id
                    LIMIT %s
                """, (limit,))
                
                images = cur.fetchall()
                logger.info(f"📋 Found {len(images)} GBIF images to download")
                return images
                
        except Exception as e:
            logger.error(f"❌ Failed to query images: {e}")
            raise
    
    def download_image(self, url: str) -> Optional[bytes]:
        """Download image from URL"""
        try:
            headers = {
                'User-Agent': 'OrchidContinuum/1.0 (Educational Research; contact@orchidcontinuum.org)'
            }
            
            response = requests.get(url, headers=headers, timeout=TIMEOUT, stream=True)
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get('Content-Type', '')
            if not content_type.startswith('image/'):
                logger.warning(f"⚠️  Not an image: {content_type}")
                return None
            
            # Read image data
            image_data = response.content
            
            # Verify it's a valid image
            try:
                with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                    tmp.write(image_data)
                    tmp_path = tmp.name
                
                img = Image.open(tmp_path)
                img.verify()  # Verify it's valid
                os.unlink(tmp_path)
                
                return image_data
                
            except Exception as e:
                logger.warning(f"⚠️  Invalid image data: {e}")
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                return None
            
        except requests.exceptions.Timeout:
            logger.warning(f"⏱️  Timeout downloading image")
            return None
        except requests.exceptions.RequestException as e:
            logger.warning(f"⚠️  Download failed: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error downloading: {e}")
            return None
    
    def calculate_hashes(self, image_data: bytes) -> Dict[str, str]:
        """Calculate SHA256 and perceptual hash"""
        try:
            # SHA256
            sha256 = hashlib.sha256(image_data).hexdigest()
            
            # Perceptual hash
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                tmp.write(image_data)
                tmp_path = tmp.name
            
            img = Image.open(tmp_path)
            phash = str(imagehash.average_hash(img))
            os.unlink(tmp_path)
            
            return {
                'sha256': sha256,
                'phash': phash
            }
            
        except Exception as e:
            logger.warning(f"⚠️  Failed to calculate hashes: {e}")
            return {
                'sha256': hashlib.sha256(image_data).hexdigest(),
                'phash': None
            }
    
    def upload_to_drive(self, image_data: bytes, filename: str) -> Optional[str]:
        """Upload image to Google Drive"""
        try:
            # Save to temp file
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                tmp.write(image_data)
                tmp_path = tmp.name
            
            # Upload to Drive
            file_metadata = {
                'name': filename,
                'parents': [self.folder_id]
            }
            
            media = MediaFileUpload(tmp_path, mimetype='image/jpeg')
            file = self.drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            file_id = file.get('id')
            
            # Make publicly viewable
            self.drive_service.permissions().create(
                fileId=file_id,
                body={'role': 'reader', 'type': 'anyone'}
            ).execute()
            
            # Clean up temp file
            os.unlink(tmp_path)
            
            return file_id
            
        except Exception as e:
            logger.error(f"❌ Failed to upload to Drive: {e}")
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            return None
    
    def update_database(self, image_id: int, drive_file_id: str, hashes: Dict[str, str], status: str):
        """Update database with Drive file info"""
        try:
            drive_url = f"https://drive.google.com/uc?id={drive_file_id}"
            
            with self.db_conn.cursor() as cur:
                cur.execute("""
                    UPDATE orchid_images
                    SET local_path = %s,
                        file_sha256 = %s,
                        perceptual_hash = %s,
                        download_status = %s,
                        downloaded_at = NOW()
                    WHERE id = %s
                """, (drive_url, hashes['sha256'], hashes['phash'], status, image_id))
                
                self.db_conn.commit()
                
        except Exception as e:
            logger.error(f"❌ Failed to update database: {e}")
            self.db_conn.rollback()
    
    def process_images(self):
        """Main processing loop"""
        try:
            images = self.get_images_to_download()
            self.stats['total'] = len(images)
            
            if not images:
                logger.info("✅ No images to download!")
                return
            
            logger.info(f"\n🚀 Starting download of {len(images)} images...")
            logger.info(f"📦 Batch size: {BATCH_SIZE}, Max downloads: {MAX_DOWNLOADS}\n")
            
            for i, image in enumerate(images, 1):
                image_id = image['id']
                url = image['image_url']
                
                # Generate filename
                occurrence_key = image.get('gbif_occurrence_key', 'unknown')
                filename = f"gbif_{occurrence_key}_{image_id}.jpg"
                
                logger.info(f"[{i}/{len(images)}] Processing ID {image_id}...")
                
                # Download image
                image_data = self.download_image(url)
                if not image_data:
                    self.stats['failed'] += 1
                    self.update_database(image_id, '', {}, 'failed')
                    logger.warning(f"  ❌ Download failed: {url}")
                    continue
                
                self.stats['downloaded'] += 1
                logger.info(f"  ✅ Downloaded {len(image_data)} bytes")
                
                # Calculate hashes
                hashes = self.calculate_hashes(image_data)
                logger.info(f"  🔒 SHA256: {hashes['sha256'][:16]}...")
                
                # Upload to Drive
                drive_file_id = self.upload_to_drive(image_data, filename)
                if not drive_file_id:
                    self.stats['failed'] += 1
                    self.update_database(image_id, '', hashes, 'upload_failed')
                    logger.warning(f"  ❌ Upload to Drive failed")
                    continue
                
                self.stats['uploaded'] += 1
                logger.info(f"  ☁️  Uploaded to Drive: {drive_file_id}")
                
                # Update database
                self.update_database(image_id, drive_file_id, hashes, 'completed')
                logger.info(f"  💾 Database updated\n")
                
                # Commit batch
                if i % BATCH_SIZE == 0:
                    logger.info(f"✅ Batch {i//BATCH_SIZE} completed ({i}/{len(images)})\n")
            
            # Final stats
            self.print_stats()
            
        except KeyboardInterrupt:
            logger.info("\n⚠️  Interrupted by user")
            self.print_stats()
        except Exception as e:
            logger.error(f"❌ Processing failed: {e}")
            raise
    
    def print_stats(self):
        """Print final statistics"""
        logger.info("\n" + "="*60)
        logger.info("📊 DOWNLOAD STATISTICS")
        logger.info("="*60)
        logger.info(f"Total images:      {self.stats['total']}")
        logger.info(f"Downloaded:        {self.stats['downloaded']}")
        logger.info(f"Uploaded to Drive: {self.stats['uploaded']}")
        logger.info(f"Failed:            {self.stats['failed']}")
        logger.info(f"Skipped:           {self.stats['skipped']}")
        logger.info("="*60 + "\n")
    
    def cleanup(self):
        """Clean up resources"""
        if self.db_conn:
            self.db_conn.close()
            logger.info("✅ Database connection closed")

def main():
    """Main entry point"""
    logger.info("\n" + "="*60)
    logger.info("🌺 ORCHID CONTINUUM - GBIF IMAGE DOWNLOADER")
    logger.info("="*60 + "\n")
    
    downloader = GBIFImageDownloader()
    
    try:
        # Initialize services
        downloader.initialize_drive()
        downloader.initialize_database()
        
        # Process images
        downloader.process_images()
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)
    finally:
        downloader.cleanup()
    
    logger.info("✅ All done!\n")

if __name__ == "__main__":
    main()
