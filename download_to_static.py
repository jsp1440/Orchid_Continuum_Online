#!/usr/bin/env python3
"""
Download GBIF Images to Static Folder
Hosts images directly with your Flask app on Render
"""

import os
import sys
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('static_image_download.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
STATIC_DIR = Path('static/images/orchid')
BATCH_SIZE = 100
DOWNLOAD_TIMEOUT = 30
MAX_RETRIES = 3

class StaticImageDownloader:
    """Download GBIF images to static folder for Flask hosting"""
    
    def __init__(self):
        self.static_dir = STATIC_DIR
        self.db_conn = None
        self.stats = {
            'total': 0,
            'downloaded': 0,
            'failed': 0,
            'skipped': 0
        }
    
    def setup_directories(self):
        """Create static directory structure"""
        self.static_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 Static directory ready: {self.static_dir}")
    
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
    
    def get_next_batch(self, batch_size: int = BATCH_SIZE) -> list:
        """Get next batch of images to download"""
        try:
            with self.db_conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, image_url, taxonomy_id, gbif_occurrence_key
                    FROM orchid_images
                    WHERE (image_source LIKE '%%GBIF%%' OR gbif_occurrence_key IS NOT NULL)
                      AND is_duplicate IS NOT TRUE
                      AND image_url IS NOT NULL
                      AND image_url != ''
                      AND image_url NOT LIKE '%%imageprotected%%'
                      AND (download_status IS NULL OR download_status NOT IN ('completed', 'static_hosted'))
                    ORDER BY id
                    LIMIT %s
                """, (batch_size,))
                
                return cur.fetchall()
                
        except Exception as e:
            logger.error(f"❌ Query failed: {e}")
            raise
    
    def download_image(self, url: str, image_id: int) -> tuple:
        """Download image and save to static folder"""
        for attempt in range(MAX_RETRIES):
            try:
                headers = {
                    'User-Agent': 'OrchidContinuum/1.0 (Scientific Research)'
                }
                
                response = requests.get(url, headers=headers, timeout=DOWNLOAD_TIMEOUT, stream=True)
                response.raise_for_status()
                
                # Check content type
                content_type = response.headers.get('Content-Type', '')
                if not content_type.startswith('image/'):
                    return None, {}
                
                # Save image
                filename = f"orchid_{image_id}.jpg"
                file_path = self.static_dir / filename
                
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                # Verify it's valid
                try:
                    img = Image.open(file_path)
                    img.verify()
                    
                    # Calculate hashes
                    sha256 = hashlib.sha256()
                    with open(file_path, 'rb') as f:
                        for chunk in iter(lambda: f.read(8192), b''):
                            sha256.update(chunk)
                    
                    img = Image.open(file_path)
                    phash = str(imagehash.average_hash(img))
                    
                    hashes = {
                        'sha256': sha256.hexdigest(),
                        'phash': phash
                    }
                    
                    return filename, hashes
                    
                except Exception as e:
                    logger.warning(f"⚠️  Invalid image: {e}")
                    if file_path.exists():
                        file_path.unlink()
                    return None, {}
                
            except requests.exceptions.Timeout:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)
                else:
                    return None, {}
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)
                else:
                    logger.error(f"❌ Download failed: {e}")
                    return None, {}
        
        return None, {}
    
    def update_database(self, image_id: int, filename: str, hashes: dict, status: str):
        """Update database with static file path"""
        try:
            # Static URL path that Flask will serve
            static_url = f"/static/images/orchid/{filename}" if filename else None
            
            with self.db_conn.cursor() as cur:
                cur.execute("""
                    UPDATE orchid_images
                    SET local_path = %s,
                        file_sha256 = %s,
                        perceptual_hash = %s,
                        download_status = %s,
                        downloaded_at = NOW()
                    WHERE id = %s
                """, (static_url, hashes.get('sha256'), hashes.get('phash'), status, image_id))
                
                self.db_conn.commit()
                
        except Exception as e:
            logger.error(f"❌ Database update failed: {e}")
            self.db_conn.rollback()
    
    def process_batch(self, batch_number: int):
        """Process one batch of images"""
        logger.info(f"\n{'='*60}")
        logger.info(f"📦 BATCH #{batch_number}")
        logger.info(f"{'='*60}\n")
        
        images = self.get_next_batch()
        if not images:
            logger.info("✅ No more images to download!")
            return False
        
        logger.info(f"📋 Processing {len(images)} images\n")
        
        batch_downloaded = 0
        batch_failed = 0
        
        for i, image in enumerate(images, 1):
            image_id = image['id']
            url = image['image_url']
            
            logger.info(f"[{i}/{len(images)}] ID {image_id}")
            
            # Download
            filename, hashes = self.download_image(url, image_id)
            if not filename:
                batch_failed += 1
                self.stats['failed'] += 1
                self.update_database(image_id, None, {}, 'download_failed')
                logger.warning(f"  ❌ Download failed\n")
                continue
            
            batch_downloaded += 1
            self.stats['downloaded'] += 1
            
            file_path = self.static_dir / filename
            file_size_mb = file_path.stat().st_size / 1024 / 1024
            
            logger.info(f"  ✅ Downloaded {file_size_mb:.2f} MB")
            logger.info(f"  🔒 SHA256: {hashes['sha256'][:16]}...")
            logger.info(f"  📂 Saved: /static/images/orchid/{filename}")
            
            self.update_database(image_id, filename, hashes, 'static_hosted')
            logger.info(f"  💾 Database updated\n")
        
        logger.info(f"\n📊 Batch #{batch_number} Complete:")
        logger.info(f"  Downloaded: {batch_downloaded}")
        logger.info(f"  Failed: {batch_failed}")
        logger.info(f"  Total so far: {self.stats['downloaded']}\n")
        
        return True
    
    def run(self):
        """Run continuous batch processing"""
        batch_number = 1
        
        while True:
            try:
                has_more = self.process_batch(batch_number)
                if not has_more:
                    break
                batch_number += 1
                time.sleep(1)
                
            except KeyboardInterrupt:
                logger.info("\n⚠️  Interrupted by user")
                break
            except Exception as e:
                logger.error(f"❌ Batch failed: {e}")
                logger.info("Waiting 30 seconds...")
                time.sleep(30)
        
        logger.info("\n" + "="*60)
        logger.info("🎉 DOWNLOAD COMPLETE!")
        logger.info("="*60)
        logger.info(f"Total batches: {batch_number}")
        logger.info(f"Images downloaded: {self.stats['downloaded']}")
        logger.info(f"Images failed: {self.stats['failed']}")
        logger.info("="*60 + "\n")
        logger.info("✅ Images are now hosted at: /static/images/orchid/")
        logger.info("✅ Deploy to Render and they'll be available!")
    
    def cleanup(self):
        """Clean up resources"""
        if self.db_conn:
            self.db_conn.close()

def main():
    """Main entry point"""
    logger.info("\n" + "="*60)
    logger.info("🌺 ORCHID CONTINUUM - STATIC IMAGE DOWNLOADER")
    logger.info("   Download images for Flask static hosting")
    logger.info("="*60 + "\n")
    
    downloader = StaticImageDownloader()
    
    try:
        downloader.setup_directories()
        downloader.initialize_database()
        downloader.run()
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)
    finally:
        downloader.cleanup()

if __name__ == "__main__":
    main()
