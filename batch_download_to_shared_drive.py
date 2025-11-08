#!/usr/bin/env python3
"""
BATCH GBIF Image Preservation System
Downloads GBIF orchid images in batches and uploads to Google Shared Drive
Designed for long-running background operation with automatic resume capability
"""

import os
import sys
import json
import logging
import requests
import tempfile
import hashlib
import shutil
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
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('image_preservation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Google Drive configuration
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# IMPORTANT: Set this to your Shared Drive ID after creating it
# Get from: https://drive.google.com/drive/folders/XXXXXXXXXXXXXXXXXXXXX
SHARED_DRIVE_ID = os.environ.get('SHARED_DRIVE_ID', '')  # You'll add this to Replit Secrets
DRIVE_FOLDER_NAME = 'Orchid_Species_Archive'

# Batch configuration for efficient processing
BATCH_SIZE = 100           # Process 100 images per batch
TEMP_DIR = '/tmp/orchid_batch'  # Temporary storage (cleared after each batch)
DOWNLOAD_TIMEOUT = 30      # Request timeout in seconds
MAX_RETRIES = 3            # Retry failed downloads
DELAY_BETWEEN_UPLOADS = 0.5  # Prevent API rate limiting

class OrchidImagePreserver:
    """Batch download and preserve orchid images to Shared Drive"""
    
    def __init__(self, shared_drive_id: str):
        self.shared_drive_id = shared_drive_id
        self.drive_service = None
        self.folder_id = None
        self.db_conn = None
        self.temp_dir = Path(TEMP_DIR)
        self.stats = {
            'total_found': 0,
            'batch_downloaded': 0,
            'batch_uploaded': 0,
            'batch_failed': 0,
            'cumulative_uploaded': 0,
            'cumulative_failed': 0
        }
    
    def setup_temp_directory(self):
        """Create/clear temporary directory"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 Temp directory ready: {self.temp_dir}")
    
    def cleanup_temp_directory(self):
        """Clean up temporary files after batch"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        logger.info("🧹 Temp directory cleared")
    
    def initialize_drive(self):
        """Initialize Google Drive service with Shared Drive support"""
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
            
            # Get or create folder in Shared Drive
            self.folder_id = self._get_or_create_folder(DRIVE_FOLDER_NAME)
            logger.info(f"✅ Using Shared Drive folder: {DRIVE_FOLDER_NAME}")
            logger.info(f"   Shared Drive ID: {self.shared_drive_id}")
            logger.info(f"   Folder ID: {self.folder_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Google Drive: {e}")
            raise
    
    def _get_or_create_folder(self, folder_name: str) -> str:
        """Get existing folder or create new one (works with regular folders or Shared Drives)"""
        try:
            # Just use the parent folder ID directly
            # The user already created the folder and shared it with us
            logger.info(f"📁 Using folder: {folder_name}")
            return self.shared_drive_id
            
        except Exception as e:
            logger.error(f"❌ Failed to access folder: {e}")
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
    
    def get_next_batch(self, batch_size: int = BATCH_SIZE) -> list:
        """Get next batch of images that need preservation"""
        try:
            with self.db_conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, image_url, taxonomy_id, gbif_occurrence_key,
                           image_license, latitude, longitude, country
                    FROM orchid_images
                    WHERE (image_source LIKE '%%GBIF%%' OR gbif_occurrence_key IS NOT NULL)
                      AND is_duplicate IS NOT TRUE
                      AND image_url IS NOT NULL
                      AND image_url != ''
                      AND image_url NOT LIKE '%%imageprotected%%'
                      AND (download_status IS NULL OR download_status NOT IN ('completed', 'preserved'))
                    ORDER BY id
                    LIMIT %s
                """, (batch_size,))
                
                images = cur.fetchall()
                return images
                
        except Exception as e:
            logger.error(f"❌ Failed to query images: {e}")
            raise
    
    def download_image(self, url: str, image_id: int) -> Optional[Path]:
        """Download image to temporary directory"""
        for attempt in range(MAX_RETRIES):
            try:
                headers = {
                    'User-Agent': 'OrchidContinuum/1.0 (Scientific Data Preservation; Educational Research)'
                }
                
                response = requests.get(url, headers=headers, timeout=DOWNLOAD_TIMEOUT, stream=True)
                response.raise_for_status()
                
                # Check content type
                content_type = response.headers.get('Content-Type', '')
                if not content_type.startswith('image/'):
                    logger.warning(f"⚠️  Not an image: {content_type}")
                    return None
                
                # Save to temp file
                file_path = self.temp_dir / f"image_{image_id}.jpg"
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                # Verify it's a valid image
                try:
                    img = Image.open(file_path)
                    img.verify()
                    return file_path
                except Exception as e:
                    logger.warning(f"⚠️  Invalid image: {e}")
                    if file_path.exists():
                        file_path.unlink()
                    return None
                
            except requests.exceptions.Timeout:
                if attempt < MAX_RETRIES - 1:
                    logger.warning(f"⏱️  Timeout, retry {attempt + 1}/{MAX_RETRIES}")
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.warning(f"⏱️  Timeout after {MAX_RETRIES} attempts")
                    return None
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    logger.warning(f"⚠️  Download error, retry {attempt + 1}/{MAX_RETRIES}: {e}")
                    time.sleep(2 ** attempt)
                else:
                    logger.error(f"❌ Download failed after {MAX_RETRIES} attempts: {e}")
                    return None
        
        return None
    
    def calculate_hashes(self, file_path: Path) -> Dict[str, str]:
        """Calculate SHA256 and perceptual hash"""
        try:
            # SHA256
            sha256 = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    sha256.update(chunk)
            
            # Perceptual hash
            img = Image.open(file_path)
            phash = str(imagehash.average_hash(img))
            
            return {
                'sha256': sha256.hexdigest(),
                'phash': phash
            }
            
        except Exception as e:
            logger.warning(f"⚠️  Failed to calculate hashes: {e}")
            sha256 = hashlib.sha256()
            with open(file_path, 'rb') as f:
                sha256.update(f.read())
            return {
                'sha256': sha256.hexdigest(),
                'phash': None
            }
    
    def upload_to_shared_drive(self, file_path: Path, filename: str) -> Optional[str]:
        """Upload image to Google Drive folder"""
        try:
            file_metadata = {
                'name': filename,
                'parents': [self.folder_id]
            }
            
            media = MediaFileUpload(str(file_path), mimetype='image/jpeg')
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
            
            time.sleep(DELAY_BETWEEN_UPLOADS)  # Rate limiting
            
            return file_id
            
        except Exception as e:
            logger.error(f"❌ Failed to upload to Drive: {e}")
            return None
    
    def update_database(self, image_id: int, drive_file_id: Optional[str], 
                       hashes: Dict[str, str], status: str):
        """Update database with preservation status"""
        try:
            drive_url = f"https://drive.google.com/uc?id={drive_file_id}" if drive_file_id else None
            
            with self.db_conn.cursor() as cur:
                cur.execute("""
                    UPDATE orchid_images
                    SET local_path = %s,
                        file_sha256 = %s,
                        perceptual_hash = %s,
                        download_status = %s,
                        downloaded_at = NOW()
                    WHERE id = %s
                """, (drive_url, hashes.get('sha256'), hashes.get('phash'), status, image_id))
                
                self.db_conn.commit()
                
        except Exception as e:
            logger.error(f"❌ Failed to update database: {e}")
            self.db_conn.rollback()
    
    def process_batch(self, batch_number: int):
        """Process one batch of images"""
        logger.info(f"\n{'='*60}")
        logger.info(f"📦 BATCH #{batch_number}")
        logger.info(f"{'='*60}\n")
        
        # Reset batch stats
        self.stats['batch_downloaded'] = 0
        self.stats['batch_uploaded'] = 0
        self.stats['batch_failed'] = 0
        
        # Get next batch
        images = self.get_next_batch()
        if not images:
            logger.info("✅ No more images to process!")
            return False  # No more work
        
        logger.info(f"📋 Processing {len(images)} images in this batch\n")
        
        # Setup temp directory
        self.setup_temp_directory()
        
        # Process each image
        for i, image in enumerate(images, 1):
            image_id = image['id']
            url = image['image_url']
            occurrence_key = image.get('gbif_occurrence_key', 'unknown')
            filename = f"orchid_{occurrence_key}_{image_id}.jpg"
            
            logger.info(f"[{i}/{len(images)}] ID {image_id}")
            
            # Download
            file_path = self.download_image(url, image_id)
            if not file_path:
                self.stats['batch_failed'] += 1
                self.stats['cumulative_failed'] += 1
                self.update_database(image_id, None, {}, 'download_failed')
                logger.warning(f"  ❌ Download failed\n")
                continue
            
            self.stats['batch_downloaded'] += 1
            file_size_mb = file_path.stat().st_size / 1024 / 1024
            logger.info(f"  ✅ Downloaded {file_size_mb:.2f} MB")
            
            # Calculate hashes
            hashes = self.calculate_hashes(file_path)
            logger.info(f"  🔒 SHA256: {hashes['sha256'][:16]}...")
            
            # Upload to Shared Drive
            drive_file_id = self.upload_to_shared_drive(file_path, filename)
            if not drive_file_id:
                self.stats['batch_failed'] += 1
                self.stats['cumulative_failed'] += 1
                self.update_database(image_id, None, hashes, 'upload_failed')
                logger.warning(f"  ❌ Upload failed\n")
                continue
            
            self.stats['batch_uploaded'] += 1
            self.stats['cumulative_uploaded'] += 1
            self.update_database(image_id, drive_file_id, hashes, 'preserved')
            logger.info(f"  ☁️  Preserved: {drive_file_id}")
            logger.info(f"  💾 Database updated\n")
        
        # Clean up temp directory
        self.cleanup_temp_directory()
        
        # Print batch summary
        self.print_batch_summary(batch_number)
        
        return True  # More work to do
    
    def print_batch_summary(self, batch_number: int):
        """Print batch statistics"""
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 BATCH #{batch_number} SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"Downloaded:  {self.stats['batch_downloaded']}")
        logger.info(f"Uploaded:    {self.stats['batch_uploaded']}")
        logger.info(f"Failed:      {self.stats['batch_failed']}")
        logger.info(f"\n📈 CUMULATIVE TOTALS:")
        logger.info(f"Preserved:   {self.stats['cumulative_uploaded']}")
        logger.info(f"Failed:      {self.stats['cumulative_failed']}")
        logger.info(f"{'='*60}\n")
    
    def run_continuous(self):
        """Run continuous batch processing"""
        batch_number = 1
        
        while True:
            try:
                has_more = self.process_batch(batch_number)
                if not has_more:
                    break
                batch_number += 1
                time.sleep(2)  # Brief pause between batches
                
            except KeyboardInterrupt:
                logger.info("\n⚠️  Interrupted by user")
                break
            except Exception as e:
                logger.error(f"❌ Batch failed: {e}")
                logger.info("Waiting 30 seconds before retry...")
                time.sleep(30)
        
        logger.info("\n" + "="*60)
        logger.info("🎉 PRESERVATION COMPLETE!")
        logger.info("="*60)
        logger.info(f"Total batches processed: {batch_number}")
        logger.info(f"Images preserved: {self.stats['cumulative_uploaded']}")
        logger.info(f"Images failed: {self.stats['cumulative_failed']}")
        logger.info("="*60 + "\n")
    
    def cleanup(self):
        """Clean up resources"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
        if self.db_conn:
            self.db_conn.close()
            logger.info("✅ Cleanup complete")

def main():
    """Main entry point"""
    logger.info("\n" + "="*60)
    logger.info("🌺 ORCHID SPECIES PRESERVATION SYSTEM")
    logger.info("   Protecting Botanical Biodiversity Data")
    logger.info("="*60 + "\n")
    
    # Check for Shared Drive ID
    shared_drive_id = os.environ.get('SHARED_DRIVE_ID', '')
    if not shared_drive_id:
        logger.error("❌ SHARED_DRIVE_ID not set!")
        logger.info("\nPlease set SHARED_DRIVE_ID in Replit Secrets:")
        logger.info("1. Create a Google Shared Drive")
        logger.info("2. Add service account: google-service-account@orchid-photo-studio.iam.gserviceaccount.com")
        logger.info("3. Copy the Shared Drive ID from the URL")
        logger.info("4. Add to Replit Secrets as SHARED_DRIVE_ID\n")
        sys.exit(1)
    
    preserver = OrchidImagePreserver(shared_drive_id)
    
    try:
        # Initialize services
        preserver.initialize_drive()
        preserver.initialize_database()
        
        # Run continuous batch processing
        preserver.run_continuous()
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)
    finally:
        preserver.cleanup()
    
    logger.info("✅ All done!\n")

if __name__ == "__main__":
    main()
