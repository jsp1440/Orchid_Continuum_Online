#!/usr/bin/env python3
"""
Orchid Image Downloader with Google Shared Drive Upload
Downloads images from GBIF/EOL and uploads directly to Google Shared Drive
"""

import os
import sys
import csv
import logging
import requests
import hashlib
from pathlib import Path
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from PIL import Image
import imagehash
import time
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import tempfile

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('gdrive_upload.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
SHARED_DRIVE_ID = '0ACirEfOT4qC_Uk9PVA'  # Orchid_Image_Archives
EOL_CSV = 'EOL_IMAGES_COMPLETE_95000.csv'
BATCH_SIZE = 50
DOWNLOAD_TIMEOUT = 30
MAX_RETRIES = 3

class GoogleDriveImageUploader:
    """Download images and upload directly to Google Shared Drive"""
    
    def __init__(self, source='gbif'):
        self.source = source  # 'gbif' or 'eol'
        self.db_conn = None
        self.drive_service = None
        self.temp_dir = Path(tempfile.mkdtemp())
        self.stats = {
            'total': 0,
            'downloaded': 0,
            'uploaded': 0,
            'failed': 0,
            'skipped': 0
        }
        
        # Create subfolder names
        self.gdrive_folder_name = 'orchid_gbif' if source == 'gbif' else 'orchid_eol'
        self.gdrive_folder_id = None
    
    def initialize_google_drive(self):
        """Initialize Google Drive API with service account"""
        try:
            # Load credentials from environment or file
            creds_json = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON')
            
            if creds_json:
                creds_dict = json.loads(creds_json)
                credentials = service_account.Credentials.from_service_account_info(
                    creds_dict,
                    scopes=['https://www.googleapis.com/auth/drive']
                )
            else:
                # Try loading from file
                credentials = service_account.Credentials.from_service_account_file(
                    'service-account-key.json',
                    scopes=['https://www.googleapis.com/auth/drive']
                )
            
            self.drive_service = build('drive', 'v3', credentials=credentials)
            logger.info("✅ Google Drive API initialized")
            
            # Create or find subfolder in Shared Drive root
            # For shared drives, we need to get the root folder first
            self.gdrive_folder_id = self.get_or_create_folder_in_shared_drive(
                self.gdrive_folder_name,
                SHARED_DRIVE_ID
            )
            logger.info(f"✅ Using folder: {self.gdrive_folder_name} (ID: {self.gdrive_folder_id})")
            
        except Exception as e:
            logger.error(f"❌ Google Drive initialization failed: {e}")
            raise
    
    def get_or_create_folder_in_shared_drive(self, folder_name: str, shared_drive_id: str) -> str:
        """Get or create folder in Shared Drive"""
        try:
            # Search for existing folder in shared drive
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            
            results = self.drive_service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)',
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
                corpora='drive',
                driveId=shared_drive_id
            ).execute()
            
            files = results.get('files', [])
            
            if files:
                logger.info(f"📁 Found existing folder: {folder_name}")
                return files[0]['id']
            
            # Create new folder in shared drive root
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [shared_drive_id]
            }
            
            folder = self.drive_service.files().create(
                body=file_metadata,
                fields='id',
                supportsAllDrives=True
            ).execute()
            
            logger.info(f"📁 Created new folder: {folder_name}")
            return folder['id']
            
        except Exception as e:
            logger.error(f"❌ Folder creation failed: {e}")
            raise
    
    def upload_to_drive(self, file_path: Path, filename: str, description: str = '') -> str:
        """Upload file to Google Shared Drive and make it visible"""
        try:
            file_metadata = {
                'name': filename,
                'parents': [self.gdrive_folder_id],
                'description': description  # Add metadata description
            }
            
            media = MediaFileUpload(
                str(file_path),
                mimetype='image/jpeg',
                resumable=True
            )
            
            file = self.drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webViewLink',
                supportsAllDrives=True
            ).execute()
            
            file_id = file.get('id')
            
            # CRITICAL: Make file visible by granting domain-wide read access
            # This fixes the "invisible files" issue
            try:
                # Grant read access to fcosorchids.org domain
                domain_permission = {
                    'type': 'domain',
                    'role': 'reader',
                    'domain': 'fcosorchids.org'
                }
                
                self.drive_service.permissions().create(
                    fileId=file_id,
                    body=domain_permission,
                    supportsAllDrives=True,
                    fields='id'
                ).execute()
                
                logger.debug(f"  🔓 File shared with fcosorchids.org domain")
                
            except Exception as perm_error:
                # If domain sharing fails, try direct user sharing
                logger.warning(f"  ⚠️  Domain sharing failed, trying direct user share: {perm_error}")
                
                # Grant write access to specific user
                user_permission = {
                    'type': 'user',
                    'role': 'writer',
                    'emailAddress': os.environ.get('ADMIN_EMAIL', 'President@fcosorchids.org')
                }
                
                self.drive_service.permissions().create(
                    fileId=file_id,
                    body=user_permission,
                    supportsAllDrives=True,
                    sendNotificationEmail=False
                ).execute()
                
                logger.debug(f"  🔓 File shared with user directly")
            
            return file.get('webViewLink', '')
            
        except Exception as e:
            logger.error(f"❌ Upload failed: {e}")
            return None
    
    def initialize_database(self):
        """Initialize database connection"""
        try:
            database_url = os.environ.get('DATABASE_URL')
            if not database_url:
                raise ValueError("DATABASE_URL not found")
            
            self.db_conn = psycopg2.connect(database_url)
            logger.info("✅ Database connected")
            
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise
    
    def download_image(self, url: str, image_id: str) -> tuple:
        """Download image to temp folder"""
        for attempt in range(MAX_RETRIES):
            try:
                headers = {
                    'User-Agent': 'OrchidContinuum/1.0 (Scientific Data Preservation)'
                }
                
                response = requests.get(url, headers=headers, timeout=DOWNLOAD_TIMEOUT, stream=True)
                response.raise_for_status()
                
                content_type = response.headers.get('Content-Type', '')
                if not content_type.startswith('image/'):
                    return None, {}
                
                # Save to temp file
                filename = f"{self.source}_{image_id}.jpg"
                file_path = self.temp_dir / filename
                
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                # Verify and hash
                try:
                    img = Image.open(file_path)
                    img.verify()
                    
                    sha256 = hashlib.sha256()
                    with open(file_path, 'rb') as f:
                        for chunk in iter(lambda: f.read(8192), b''):
                            sha256.update(chunk)
                    
                    img = Image.open(file_path)
                    phash = str(imagehash.average_hash(img))
                    
                    return file_path, {
                        'sha256': sha256.hexdigest(),
                        'phash': phash,
                        'filename': filename
                    }
                    
                except Exception as e:
                    if file_path.exists():
                        file_path.unlink()
                    return None, {}
                
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)
                else:
                    return None, {}
        
        return None, {}
    
    def process_gbif_batch(self, start_idx: int, batch_size: int):
        """Process GBIF images batch"""
        with self.db_conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get unprocessed GBIF images with taxonomy data
            cur.execute("""
                SELECT 
                    oi.id, 
                    oi.gbif_occurrence_key, 
                    oi.image_url,
                    oi.country,
                    oi.state_province,
                    oi.locality,
                    oi.observation_date,
                    oi.observer_name,
                    oi.latitude,
                    oi.longitude,
                    ot.genus,
                    ot.species,
                    ot.subspecies,
                    ot.scientific_name
                FROM orchid_images oi
                LEFT JOIN orchid_taxonomy ot ON oi.taxonomy_id = ot.id
                WHERE oi.image_source = 'GBIF'
                AND (oi.google_drive_url IS NULL OR oi.google_drive_url = '')
                ORDER BY oi.id
                LIMIT %s OFFSET %s
            """, (batch_size, start_idx))
            
            images = cur.fetchall()
            
            if not images:
                logger.info("✅ All GBIF images uploaded!")
                return False
            
            logger.info(f"\n📦 BATCH (images {start_idx+1}-{start_idx+len(images)})")
            
            for img in images:
                image_id = img['id']
                url = img['image_url']
                
                logger.info(f"[{image_id}] Downloading...")
                
                # Download
                file_path, hashes = self.download_image(url, image_id)
                if not file_path:
                    self.stats['failed'] += 1
                    logger.warning(f"  ❌ Download failed")
                    continue
                
                self.stats['downloaded'] += 1
                file_size_mb = file_path.stat().st_size / 1024 / 1024
                logger.info(f"  ✅ Downloaded {file_size_mb:.2f} MB")
                
                # Build scientific name from database or use prebuilt
                scientific_name = img.get('scientific_name', '')
                if not scientific_name:
                    genus = img.get('genus', 'Unknown')
                    species = img.get('species', '')
                    subspecies = img.get('subspecies', '')
                
                    if species:
                        scientific_name = f"{genus} {species}"
                        if subspecies:
                            scientific_name += f" {subspecies}"
                    else:
                        scientific_name = genus if genus != 'Unknown' else 'Unknown Orchid'
                
                # Create meaningful filename
                safe_name = scientific_name.replace(' ', '_').replace('/', '-')[:40]
                country = img.get('country', 'Unknown')[:20]
                gbif_key = img.get('gbif_occurrence_key', image_id)
                meaningful_filename = f"{safe_name}_{country}_GBIF{gbif_key}.jpg"
                
                # Create metadata description
                location = f"{img.get('country', 'N/A')}"
                if img.get('state_province'):
                    location += f", {img['state_province']}"
                if img.get('locality'):
                    location += f", {img['locality']}"
                
                coords = ""
                if img.get('latitude') and img.get('longitude'):
                    coords = f"{img['latitude']}, {img['longitude']}"
                
                description = f"""🌺 {scientific_name}

📍 Location: {location}
🗺️  Coordinates: {coords or 'N/A'}
📅 Date: {img.get('observation_date', 'Unknown')}
👤 Observer: {img.get('observer_name', 'Unknown')}
🔗 GBIF ID: {gbif_key}

Source: Global Biodiversity Information Facility (GBIF)
License: {img.get('image_license', 'Unknown')}"""
                
                logger.info(f"  🏷️  {scientific_name}")
                
                # Upload to Google Drive with meaningful name and metadata
                gdrive_url = self.upload_to_drive(file_path, meaningful_filename, description)
                if not gdrive_url:
                    self.stats['failed'] += 1
                    logger.warning(f"  ❌ Upload failed")
                    file_path.unlink()
                    continue
                
                self.stats['uploaded'] += 1
                logger.info(f"  ☁️  Uploaded to Google Drive")
                
                # Update database
                cur.execute("""
                    UPDATE orchid_images
                    SET google_drive_url = %s,
                        file_sha256 = %s,
                        perceptual_hash = %s,
                        download_status = 'google_drive_preserved',
                        downloaded_at = NOW()
                    WHERE id = %s
                """, (gdrive_url, hashes['sha256'], hashes['phash'], image_id))
                
                self.db_conn.commit()
                logger.info(f"  💾 Database updated\n")
                
                # Cleanup temp file
                file_path.unlink()
            
            logger.info(f"📊 Batch complete: {len(images)} processed")
            return True
    
    def run_gbif(self):
        """Run GBIF download and upload"""
        logger.info("\n" + "="*60)
        logger.info("🌺 GBIF → GOOGLE DRIVE UPLOAD")
        logger.info("="*60 + "\n")
        
        start_idx = 0
        while True:
            try:
                has_more = self.process_gbif_batch(start_idx, BATCH_SIZE)
                if not has_more:
                    break
                start_idx += BATCH_SIZE
                time.sleep(2)
                
            except KeyboardInterrupt:
                logger.info("\n⚠️  Interrupted by user")
                break
            except Exception as e:
                logger.error(f"❌ Batch failed: {e}")
                time.sleep(30)
        
        logger.info("\n" + "="*60)
        logger.info("🎉 GBIF UPLOAD COMPLETE!")
        logger.info(f"Downloaded: {self.stats['downloaded']}")
        logger.info(f"Uploaded: {self.stats['uploaded']}")
        logger.info(f"Failed: {self.stats['failed']}")
        logger.info("="*60 + "\n")
    
    def cleanup(self):
        """Clean up resources"""
        if self.db_conn:
            self.db_conn.close()
        
        # Cleanup temp directory
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

def main():
    """Main entry point"""
    source = sys.argv[1] if len(sys.argv) > 1 else 'gbif'
    
    logger.info("\n" + "="*60)
    logger.info(f"🌺 ORCHID IMAGE PRESERVATION → GOOGLE SHARED DRIVE")
    logger.info(f"   Source: {source.upper()}")
    logger.info("="*60 + "\n")
    
    uploader = GoogleDriveImageUploader(source=source)
    
    try:
        uploader.initialize_database()
        uploader.initialize_google_drive()
        
        if source == 'gbif':
            uploader.run_gbif()
        else:
            logger.error("EOL support coming soon!")
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)
    finally:
        uploader.cleanup()

if __name__ == "__main__":
    main()
