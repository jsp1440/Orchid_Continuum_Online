"""
GBIF & EOL Image Downloader System (FIXED VERSION)
Downloads all 105,000+ orchid images from URLs to Google Drive
Organizes by genus/species and tracks progress

FIXES:
1. Uses WHERE id > last_id instead of OFFSET to avoid skipping records
2. Validates Google Drive credentials before starting
3. Routes require authentication (added in routes file)
"""

import os
import logging
import requests
import tempfile
import time
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import create_engine, text
from google_drive_service import get_drive_service, get_or_create_folder, upload_to_drive
from PIL import Image
import io

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImageDownloaderSystem:
    """Downloads and organizes orchid images to Google Drive"""
    
    def __init__(self):
        self.database_url = os.environ.get("DATABASE_URL")
        self.engine = create_engine(self.database_url)
        self.drive_service = None
        self.main_folder_id = None
        self.stats = {
            'total_processed': 0,
            'successful_downloads': 0,
            'failed_downloads': 0,
            'skipped': 0,
            'start_time': None,
            'error': None
        }
        
    def validate_credentials(self) -> bool:
        """Validate Google Drive credentials before starting"""
        try:
            self.drive_service = get_drive_service()
            if not self.drive_service:
                self.stats['error'] = "Google Drive credentials not available. Check GOOGLE_SERVICE_ACCOUNT_JSON environment variable."
                logger.error(f"❌ {self.stats['error']}")
                return False
            
            # Test Drive API access
            self.drive_service.files().list(pageSize=1).execute()
            logger.info("✅ Google Drive credentials validated successfully")
            return True
            
        except Exception as e:
            self.stats['error'] = f"Google Drive authentication failed: {str(e)}"
            logger.error(f"❌ {self.stats['error']}")
            return False
    
    def setup_folder_structure(self):
        """Create organized folder structure in Google Drive"""
        if not self.drive_service:
            raise RuntimeError("Google Drive service not initialized. Call validate_credentials() first.")
            
        logger.info("🗂️  Setting up Google Drive folder structure...")
        
        # Create main folder
        self.main_folder_id = get_or_create_folder(
            self.drive_service, 
            'Orchid_Research_Images'
        )
        
        # Create subfolders for different image sources
        self.gbif_folder_id = get_or_create_folder(
            self.drive_service,
            'GBIF_Specimens',
            self.main_folder_id
        )
        
        self.eol_folder_id = get_or_create_folder(
            self.drive_service,
            'EOL_Images',
            self.main_folder_id
        )
        
        logger.info(f"✅ Folder structure created")
        logger.info(f"   Main: {self.main_folder_id}")
        logger.info(f"   GBIF: {self.gbif_folder_id}")
        logger.info(f"   EOL: {self.eol_folder_id}")
        
        return True
    
    def download_image_from_url(self, url: str, timeout: int = 30) -> Optional[bytes]:
        """Download image from URL and return bytes"""
        try:
            headers = {
                'User-Agent': 'OrchidContinuum/1.0 (Research Project; contact@orchidcontinuum.org)'
            }
            response = requests.get(url, headers=headers, timeout=timeout, stream=True)
            response.raise_for_status()
            
            # Read image data
            image_data = response.content
            
            # Validate it's actually an image
            try:
                Image.open(io.BytesIO(image_data))
                return image_data
            except Exception as e:
                logger.error(f"Invalid image data from {url}: {e}")
                return None
                
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout downloading {url}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download {url}: {e}")
            return None
    
    def upload_image_to_drive(self, image_data: bytes, filename: str, 
                             folder_id: str, genus: str = None) -> Optional[str]:
        """Upload image to Google Drive and return file ID"""
        try:
            # Create genus subfolder if provided
            target_folder_id = folder_id
            if genus:
                genus_folder_id = get_or_create_folder(
                    self.drive_service,
                    genus,
                    folder_id
                )
                if genus_folder_id:
                    target_folder_id = genus_folder_id
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                temp_file.write(image_data)
                temp_path = temp_file.name
            
            try:
                # Upload manually with full control
                from googleapiclient.http import MediaFileUpload
                file_metadata = {
                    'name': filename,
                    'parents': [target_folder_id]
                }
                media = MediaFileUpload(temp_path, mimetype='image/jpeg')
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
                
                return file_id
                
            finally:
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
        except Exception as e:
            logger.error(f"Failed to upload image to Drive: {e}")
            return None
    
    def process_gbif_images(self, batch_size: int = 100, start_id: int = 0, 
                           limit: Optional[int] = None):
        """Download all GBIF images to Google Drive - FIXED batching logic"""
        logger.info("🔬 Starting GBIF image download...")
        
        with self.engine.connect() as conn:
            # First, add google_drive_id column if it doesn't exist
            try:
                conn.execute(text("""
                    ALTER TABLE orchid_images 
                    ADD COLUMN IF NOT EXISTS google_drive_id VARCHAR(255)
                """))
                conn.execute(text("""
                    ALTER TABLE orchid_images 
                    ADD COLUMN IF NOT EXISTS google_drive_filename VARCHAR(500)
                """))
                conn.commit()
                logger.info("✅ Added google_drive_id column to orchid_images")
            except Exception as e:
                logger.warning(f"Column may already exist: {e}")
            
            # Get total count
            result = conn.execute(text("""
                SELECT COUNT(*) 
                FROM orchid_images 
                WHERE image_url IS NOT NULL 
                AND (google_drive_id IS NULL OR google_drive_id = '')
            """))
            total_count = result.scalar()
            
            if limit:
                total_count = min(total_count, limit)
            
            logger.info(f"📊 Found {total_count} GBIF images to download")
            
            processed = 0
            last_id = 0  # FIX: Track last ID instead of using OFFSET
            
            while processed < total_count:
                # FIX: Use WHERE id > last_id instead of OFFSET
                # This prevents skipping records when rows are updated
                query = text("""
                    SELECT 
                        oi.id,
                        oi.image_url,
                        oi.gbif_occurrence_key,
                        ot.genus,
                        ot.species,
                        ot.scientific_name
                    FROM orchid_images oi
                    LEFT JOIN orchid_taxonomy ot ON oi.taxonomy_id = ot.id
                    WHERE oi.image_url IS NOT NULL
                    AND (oi.google_drive_id IS NULL OR oi.google_drive_id = '')
                    AND oi.id > :last_id
                    ORDER BY oi.id
                    LIMIT :batch_size
                """)
                
                result = conn.execute(
                    query, 
                    {'batch_size': batch_size, 'last_id': last_id}
                )
                batch = result.fetchall()
                
                if not batch:
                    break
                
                for row in batch:
                    image_id, url, gbif_key, genus, species, sci_name = row
                    
                    # Update last_id for next iteration
                    last_id = image_id
                    
                    try:
                        # Download image
                        logger.info(f"📥 [{processed + 1}/{total_count}] Downloading {sci_name or genus}...")
                        image_data = self.download_image_from_url(url)
                        
                        if not image_data:
                            self.stats['failed_downloads'] += 1
                            processed += 1
                            continue
                        
                        # Create filename
                        filename = f"GBIF_{gbif_key}_{genus}_{species or 'sp'}.jpg".replace(' ', '_')
                        
                        # Upload to Google Drive
                        file_id = self.upload_image_to_drive(
                            image_data,
                            filename,
                            self.gbif_folder_id,
                            genus=genus
                        )
                        
                        if file_id:
                            # Update database
                            update_query = text("""
                                UPDATE orchid_images
                                SET google_drive_id = :file_id,
                                    google_drive_filename = :filename,
                                    downloaded_at = NOW()
                                WHERE id = :image_id
                            """)
                            conn.execute(update_query, {
                                'file_id': file_id,
                                'filename': filename,
                                'image_id': image_id
                            })
                            conn.commit()
                            
                            self.stats['successful_downloads'] += 1
                            logger.info(f"✅ Uploaded {filename} (ID: {file_id})")
                        else:
                            self.stats['failed_downloads'] += 1
                            logger.error(f"❌ Failed to upload {filename}")
                        
                        # Rate limiting
                        time.sleep(0.5)
                        
                    except Exception as e:
                        logger.error(f"❌ Error processing image {image_id}: {e}")
                        self.stats['failed_downloads'] += 1
                    
                    processed += 1
                    self.stats['total_processed'] = processed
                
                logger.info(f"📊 Batch complete: {processed}/{total_count} processed (last_id: {last_id})")
        
        return self.stats
    
    def process_eol_images(self, batch_size: int = 100, start_id: int = 0,
                          limit: Optional[int] = None):
        """Download all EOL images to Google Drive - FIXED batching logic"""
        logger.info("🌍 Starting EOL image download...")
        
        with self.engine.connect() as conn:
            # Add google_drive_id column if it doesn't exist
            try:
                conn.execute(text("""
                    ALTER TABLE eol_images 
                    ADD COLUMN IF NOT EXISTS google_drive_id VARCHAR(255)
                """))
                conn.execute(text("""
                    ALTER TABLE eol_images 
                    ADD COLUMN IF NOT EXISTS google_drive_filename VARCHAR(500)
                """))
                conn.commit()
                logger.info("✅ Added google_drive_id column to eol_images")
            except Exception as e:
                logger.warning(f"Column may already exist: {e}")
            
            # Get total count
            result = conn.execute(text("""
                SELECT COUNT(*) 
                FROM eol_images 
                WHERE eol_url IS NOT NULL 
                AND (google_drive_id IS NULL OR google_drive_id = '')
            """))
            total_count = result.scalar()
            
            if limit:
                total_count = min(total_count, limit)
            
            logger.info(f"📊 Found {total_count} EOL images to download")
            
            processed = 0
            last_id = 0  # FIX: Track last ID instead of using OFFSET
            
            while processed < total_count:
                # FIX: Use WHERE id > last_id instead of OFFSET
                query = text("""
                    SELECT id, eol_url, page_id, content_id
                    FROM eol_images
                    WHERE eol_url IS NOT NULL
                    AND (google_drive_id IS NULL OR google_drive_id = '')
                    AND id > :last_id
                    ORDER BY id
                    LIMIT :batch_size
                """)
                
                result = conn.execute(
                    query,
                    {'batch_size': batch_size, 'last_id': last_id}
                )
                batch = result.fetchall()
                
                if not batch:
                    break
                
                for row in batch:
                    image_id, url, page_id, content_id = row
                    last_id = image_id  # Update for next iteration
                    
                    try:
                        logger.info(f"📥 [{processed + 1}/{total_count}] Downloading EOL image {content_id}...")
                        image_data = self.download_image_from_url(url)
                        
                        if not image_data:
                            self.stats['failed_downloads'] += 1
                            processed += 1
                            continue
                        
                        # Create filename
                        filename = f"EOL_{page_id}_{content_id}.jpg"
                        
                        # Upload to Google Drive
                        file_id = self.upload_image_to_drive(
                            image_data,
                            filename,
                            self.eol_folder_id
                        )
                        
                        if file_id:
                            # Update database
                            update_query = text("""
                                UPDATE eol_images
                                SET google_drive_id = :file_id,
                                    google_drive_filename = :filename
                                WHERE id = :image_id
                            """))
                            conn.execute(update_query, {
                                'file_id': file_id,
                                'filename': filename,
                                'image_id': image_id
                            })
                            conn.commit()
                            
                            self.stats['successful_downloads'] += 1
                            logger.info(f"✅ Uploaded {filename} (ID: {file_id})")
                        else:
                            self.stats['failed_downloads'] += 1
                        
                        # Rate limiting
                        time.sleep(0.5)
                        
                    except Exception as e:
                        logger.error(f"❌ Error processing EOL image {image_id}: {e}")
                        self.stats['failed_downloads'] += 1
                    
                    processed += 1
                    self.stats['total_processed'] = processed
                
                logger.info(f"📊 Batch complete: {processed}/{total_count} processed (last_id: {last_id})")
        
        return self.stats
    
    def get_download_progress(self) -> Dict[str, Any]:
        """Get current download progress statistics"""
        with self.engine.connect() as conn:
            # GBIF stats
            gbif_result = conn.execute(text("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN google_drive_id IS NOT NULL THEN 1 END) as downloaded
                FROM orchid_images
                WHERE image_url IS NOT NULL
            """))
            gbif_stats = gbif_result.fetchone()
            
            # EOL stats
            eol_result = conn.execute(text("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN google_drive_id IS NOT NULL THEN 1 END) as downloaded
                FROM eol_images
                WHERE eol_url IS NOT NULL
            """))
            eol_stats = eol_result.fetchone()
            
            return {
                'gbif': {
                    'total': gbif_stats[0],
                    'downloaded': gbif_stats[1],
                    'remaining': gbif_stats[0] - gbif_stats[1],
                    'percent': round((gbif_stats[1] / gbif_stats[0] * 100) if gbif_stats[0] > 0 else 0, 2)
                },
                'eol': {
                    'total': eol_stats[0],
                    'downloaded': eol_stats[1],
                    'remaining': eol_stats[0] - eol_stats[1],
                    'percent': round((eol_stats[1] / eol_stats[0] * 100) if eol_stats[0] > 0 else 0, 2)
                },
                'combined': {
                    'total': gbif_stats[0] + eol_stats[0],
                    'downloaded': gbif_stats[1] + eol_stats[1],
                    'remaining': (gbif_stats[0] + eol_stats[0]) - (gbif_stats[1] + eol_stats[1])
                }
            }


def start_download_process(source: str = 'both', batch_size: int = 50, limit: Optional[int] = None):
    """
    Start downloading images
    
    Args:
        source: 'gbif', 'eol', or 'both'
        batch_size: Number of images to process at once
        limit: Maximum number of images to download (None for all)
    """
    downloader = ImageDownloaderSystem()
    
    # FIX #2: Validate credentials before starting
    if not downloader.validate_credentials():
        logger.error("❌ Cannot start download - Google Drive credentials invalid")
        return downloader.stats  # Return stats with error message
    
    # Setup folder structure
    downloader.setup_folder_structure()
    downloader.stats['start_time'] = datetime.now()
    
    # Process based on source
    if source in ['gbif', 'both']:
        logger.info("\n" + "="*60)
        logger.info("STARTING GBIF IMAGE DOWNLOAD")
        logger.info("="*60 + "\n")
        downloader.process_gbif_images(batch_size=batch_size, limit=limit)
    
    if source in ['eol', 'both']:
        logger.info("\n" + "="*60)
        logger.info("STARTING EOL IMAGE DOWNLOAD")
        logger.info("="*60 + "\n")
        downloader.process_eol_images(batch_size=batch_size, limit=limit)
    
    # Final stats
    elapsed_time = datetime.now() - downloader.stats['start_time']
    logger.info("\n" + "="*60)
    logger.info("DOWNLOAD COMPLETE")
    logger.info("="*60)
    logger.info(f"✅ Total processed: {downloader.stats['total_processed']}")
    logger.info(f"✅ Successful: {downloader.stats['successful_downloads']}")
    logger.info(f"❌ Failed: {downloader.stats['failed_downloads']}")
    logger.info(f"⏱️  Time elapsed: {elapsed_time}")
    logger.info("="*60 + "\n")
    
    return downloader.stats
