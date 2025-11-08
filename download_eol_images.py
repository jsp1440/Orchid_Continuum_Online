#!/usr/bin/env python3
"""
EOL Image Preservation System
Downloads 95,000 EOL orchid images with full taxonomy and trait data
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('eol_download.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
EOL_CSV = 'EOL_IMAGES_COMPLETE_95000.csv'
STATIC_DIR = Path('static/images/eol')
BATCH_SIZE = 100
DOWNLOAD_TIMEOUT = 30
MAX_RETRIES = 3
EOL_API_BASE = 'https://eol.org/api'

class EOLImagePreserver:
    """Download and organize EOL orchid images with complete metadata"""
    
    def __init__(self):
        self.static_dir = STATIC_DIR
        self.db_conn = None
        self.stats = {
            'total': 0,
            'downloaded': 0,
            'failed': 0,
            'api_enriched': 0
        }
        self.eol_images = []
    
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
    
    def load_eol_csv(self):
        """Load EOL images from CSV"""
        try:
            with open(EOL_CSV, 'r') as f:
                reader = csv.DictReader(f)
                self.eol_images = list(reader)
            
            self.stats['total'] = len(self.eol_images)
            logger.info(f"📋 Loaded {self.stats['total']} EOL images from CSV")
            
        except Exception as e:
            logger.error(f"❌ Failed to load CSV: {e}")
            raise
    
    def get_eol_page_data(self, page_id: str) -> dict:
        """Fetch taxonomy and traits from EOL API"""
        try:
            url = f"{EOL_API_BASE}/pages/1.0/{page_id}.json"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract taxonomy
                taxonomy = {}
                if 'taxonConcept' in data:
                    tc = data['taxonConcept']
                    taxonomy = {
                        'scientific_name': tc.get('scientificName', ''),
                        'common_names': tc.get('vernacularNames', []),
                        'classification': {}
                    }
                    
                    # Get classification hierarchy
                    if 'taxonConcepts' in tc:
                        for concept in tc.get('taxonConcepts', []):
                            taxonomy['classification'] = concept.get('nameAccordingTo', {})
                
                # Extract traits
                traits = []
                if 'dataObjects' in data:
                    for obj in data['dataObjects']:
                        if obj.get('dataType') == 'http://purl.org/dc/dcmitype/Text':
                            traits.append({
                                'label': obj.get('subject', ''),
                                'value': obj.get('description', '')
                            })
                
                return {
                    'taxonomy': taxonomy,
                    'traits': traits
                }
            
            return {}
            
        except Exception as e:
            logger.warning(f"⚠️  EOL API error for page {page_id}: {e}")
            return {}
    
    def download_image(self, url: str, eol_id: str) -> tuple:
        """Download EOL image and save to static folder"""
        for attempt in range(MAX_RETRIES):
            try:
                headers = {
                    'User-Agent': 'OrchidContinuum/1.0 (Scientific Data Preservation)'
                }
                
                response = requests.get(url, headers=headers, timeout=DOWNLOAD_TIMEOUT, stream=True)
                response.raise_for_status()
                
                # Check content type
                content_type = response.headers.get('Content-Type', '')
                if not content_type.startswith('image/'):
                    return None, {}
                
                # Save image
                filename = f"eol_{eol_id}.jpg"
                file_path = self.static_dir / filename
                
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
                    
                    return filename, {
                        'sha256': sha256.hexdigest(),
                        'phash': phash
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
    
    def insert_to_database(self, image_data: dict, filename: str, hashes: dict, eol_metadata: dict):
        """Insert EOL image with full metadata to database"""
        try:
            static_url = f"/static/images/eol/{filename}"
            
            taxonomy = eol_metadata.get('taxonomy', {})
            traits = eol_metadata.get('traits', [])
            
            with self.db_conn.cursor() as cur:
                # Insert into orchid_images (or create new eol_images table)
                cur.execute("""
                    INSERT INTO orchid_images (
                        image_url, eol_data_object_id, image_source,
                        image_license, image_rights_holder, image_description,
                        eol_metadata, local_path, file_sha256, perceptual_hash,
                        download_status, downloaded_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (image_url) DO UPDATE SET
                        local_path = EXCLUDED.local_path,
                        file_sha256 = EXCLUDED.file_sha256,
                        perceptual_hash = EXCLUDED.perceptual_hash,
                        download_status = EXCLUDED.download_status,
                        eol_metadata = EXCLUDED.eol_metadata
                """, (
                    image_data.get('eol_url'),
                    image_data.get('content_id'),
                    'EOL - Encyclopedia of Life',
                    image_data.get('license'),
                    image_data.get('photographer'),
                    taxonomy.get('scientific_name', ''),
                    json.dumps({'taxonomy': taxonomy, 'traits': traits}),
                    static_url,
                    hashes.get('sha256'),
                    hashes.get('phash'),
                    'eol_preserved'
                ))
                
                self.db_conn.commit()
                
        except Exception as e:
            logger.error(f"❌ Database insert failed: {e}")
            self.db_conn.rollback()
    
    def process_batch(self, start_idx: int, batch_size: int):
        """Process one batch of EOL images"""
        batch_num = (start_idx // batch_size) + 1
        end_idx = min(start_idx + batch_size, len(self.eol_images))
        
        logger.info(f"\n{'='*60}")
        logger.info(f"📦 BATCH #{batch_num} (images {start_idx+1}-{end_idx})")
        logger.info(f"{'='*60}\n")
        
        batch_downloaded = 0
        batch_failed = 0
        batch_enriched = 0
        
        for i in range(start_idx, end_idx):
            image_data = self.eol_images[i]
            eol_id = image_data.get('eol_id')
            page_id = image_data.get('page_id')
            eol_url = image_data.get('eol_url')
            
            logger.info(f"[{i+1}/{self.stats['total']}] EOL ID {eol_id}")
            
            # Download image
            filename, hashes = self.download_image(eol_url, eol_id)
            if not filename:
                batch_failed += 1
                self.stats['failed'] += 1
                logger.warning(f"  ❌ Download failed\n")
                continue
            
            batch_downloaded += 1
            self.stats['downloaded'] += 1
            
            file_path = self.static_dir / filename
            file_size_mb = file_path.stat().st_size / 1024 / 1024
            logger.info(f"  ✅ Downloaded {file_size_mb:.2f} MB")
            
            # Enrich with EOL API data
            eol_metadata = {}
            if page_id:
                eol_metadata = self.get_eol_page_data(page_id)
                if eol_metadata.get('taxonomy'):
                    batch_enriched += 1
                    self.stats['api_enriched'] += 1
                    sci_name = eol_metadata['taxonomy'].get('scientific_name', 'N/A')
                    logger.info(f"  🔬 Taxonomy: {sci_name}")
                time.sleep(0.5)  # Rate limiting
            
            # Save to database
            self.insert_to_database(image_data, filename, hashes, eol_metadata)
            logger.info(f"  💾 Database updated\n")
        
        logger.info(f"\n📊 Batch #{batch_num} Complete:")
        logger.info(f"  Downloaded: {batch_downloaded}")
        logger.info(f"  Enriched: {batch_enriched}")
        logger.info(f"  Failed: {batch_failed}")
        logger.info(f"  Total so far: {self.stats['downloaded']}/{self.stats['total']}\n")
    
    def run(self):
        """Run continuous batch processing"""
        start_idx = 0
        
        while start_idx < len(self.eol_images):
            try:
                self.process_batch(start_idx, BATCH_SIZE)
                start_idx += BATCH_SIZE
                time.sleep(1)
                
            except KeyboardInterrupt:
                logger.info("\n⚠️  Interrupted by user")
                break
            except Exception as e:
                logger.error(f"❌ Batch failed: {e}")
                logger.info("Waiting 30 seconds...")
                time.sleep(30)
        
        logger.info("\n" + "="*60)
        logger.info("🎉 EOL DOWNLOAD COMPLETE!")
        logger.info("="*60)
        logger.info(f"Images downloaded: {self.stats['downloaded']}")
        logger.info(f"API enriched: {self.stats['api_enriched']}")
        logger.info(f"Images failed: {self.stats['failed']}")
        logger.info("="*60 + "\n")
    
    def cleanup(self):
        """Clean up resources"""
        if self.db_conn:
            self.db_conn.close()

def main():
    """Main entry point"""
    logger.info("\n" + "="*60)
    logger.info("🌺 EOL ORCHID IMAGE PRESERVATION SYSTEM")
    logger.info("   Saving 95,000 Images with Full Metadata")
    logger.info("="*60 + "\n")
    
    preserver = EOLImagePreserver()
    
    try:
        preserver.setup_directories()
        preserver.initialize_database()
        preserver.load_eol_csv()
        preserver.run()
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)
    finally:
        preserver.cleanup()

if __name__ == "__main__":
    main()
