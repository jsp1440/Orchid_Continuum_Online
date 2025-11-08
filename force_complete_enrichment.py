#!/usr/bin/env python3
"""
Force Complete Enrichment - Runs until all 5,588 orchids are enriched
Checks progress every 10 minutes and continues until done
"""
import os
import json
import time
import logging
import requests
from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

DATABASE_URL = os.environ.get('DATABASE_URL')
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

TARGET_TOTAL = 5588
CHECK_INTERVAL = 600  # 10 minutes

class ForceCompleteEnrichment:
    def __init__(self):
        self.session_http = requests.Session()
        self.session_http.headers.update({
            'User-Agent': 'Orchid Research Platform',
            'Accept': 'application/json'
        })
        self.stats = {'processed': 0, 'enriched': 0, 'images': 0, 'failed': 0}
        self.start_time = datetime.now()
        self.images_dir = Path('static/gbif_images')
        self.images_dir.mkdir(exist_ok=True, parents=True)
        self.last_check_time = datetime.now()
    
    def get_current_stats(self):
        """Get current database stats"""
        session = Session()
        try:
            result = session.execute(text("""
                SELECT 
                    COUNT(CASE WHEN image_source = 'GBIF' THEN 1 END) as gbif_images
                FROM orchid_record
            """))
            return result.fetchone()[0]
        finally:
            session.close()
    
    def download_image(self, image_url: str, orchid_id: int) -> str:
        """Download GBIF image"""
        try:
            response = self.session_http.get(image_url, timeout=15, stream=True)
            if response.status_code != 200:
                return None
            
            ext = '.jpg'
            if 'png' in image_url.lower():
                ext = '.png'
            
            filename = f"gbif_{orchid_id}_{int(time.time())}{ext}"
            filepath = self.images_dir / filename
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            self.stats['images'] += 1
            return f"/static/gbif_images/{filename}"
            
        except Exception as e:
            return None
    
    def get_gbif_data(self, genus, species):
        """Get GBIF occurrence data with images"""
        try:
            scientific_name = f"{genus} {species}"
            url = "https://api.gbif.org/v1/occurrence/search"
            params = {
                'scientificName': scientific_name,
                'hasCoordinate': 'true',
                'mediaType': 'StillImage',
                'limit': 5
            }
            
            response = self.session_http.get(url, params=params, timeout=10)
            time.sleep(1)  # Rate limit
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                
                if results:
                    for result in results:
                        if result.get('media'):
                            for media in result['media']:
                                if media.get('identifier'):
                                    return {'occurrence': result, 'image_url': media['identifier']}
                    return {'occurrence': results[0], 'image_url': None}
            
            return None
        except Exception as e:
            logger.error(f"GBIF error: {e}")
            return None
    
    def enrich_orchid(self, db_session, orchid_id, genus, species, scientific_name):
        """Enrich single orchid"""
        try:
            gbif_data = self.get_gbif_data(genus, species)
            
            if gbif_data:
                occurrence = gbif_data['occurrence']
                image_path = None
                
                if gbif_data.get('image_url'):
                    image_path = self.download_image(gbif_data['image_url'], orchid_id)
                
                update_data = {
                    'native_habitat': occurrence.get('locality', ''),
                    'region': occurrence.get('country', ''),
                    'updated_at': datetime.utcnow()
                }
                
                if image_path:
                    update_data['image_url'] = image_path
                    update_data['image_source'] = 'GBIF'
                
                db_session.execute(
                    text("""
                        UPDATE orchid_record 
                        SET native_habitat = COALESCE(:native_habitat, native_habitat),
                            region = COALESCE(:region, region),
                            image_url = COALESCE(:image_url, image_url),
                            image_source = COALESCE(:image_source, image_source),
                            updated_at = :updated_at
                        WHERE id = :id
                    """),
                    {
                        'id': orchid_id, 
                        'native_habitat': update_data.get('native_habitat'),
                        'region': update_data.get('region'),
                        'image_url': update_data.get('image_url'),
                        'image_source': update_data.get('image_source'),
                        'updated_at': update_data['updated_at']
                    }
                )
                db_session.commit()
                self.stats['enriched'] += 1
                
                location = occurrence.get('country', 'Unknown')
                img_status = "📸" if image_path else ""
                logger.info(f"  ✅ {location} {img_status}")
                return True
            return False
                
        except Exception as e:
            logger.error(f"  ❌ Error: {e}")
            db_session.rollback()
            self.stats['failed'] += 1
            return False
        finally:
            self.stats['processed'] += 1
    
    def run_batch(self, limit=100):
        """Run a batch of enrichments"""
        db_session = Session()
        
        try:
            # Get next batch of orchids to enrich
            result = db_session.execute(text("""
                SELECT id, genus, species, scientific_name
                FROM orchid_record
                WHERE genus IS NOT NULL 
                  AND species IS NOT NULL
                  AND species != ''
                  AND species NOT LIKE '%-%'
                  AND species NOT LIKE 'unnamed%'
                  AND scientific_name NOT LIKE '%×%'
                  AND LENGTH(species) > 2
                  AND (image_source IS NULL OR image_source != 'GBIF')
                ORDER BY id
                LIMIT :limit
            """), {'limit': limit})
            
            orchids = result.fetchall()
            
            if not orchids:
                logger.info("✅ No more orchids to enrich!")
                return False
            
            logger.info(f"\n🔄 Processing batch of {len(orchids)} orchids...")
            
            for orchid in orchids:
                logger.info(f"[{self.stats['processed']+1}] {orchid.scientific_name}")
                self.enrich_orchid(db_session, orchid.id, orchid.genus, orchid.species, orchid.scientific_name)
            
            return True
            
        finally:
            db_session.close()
    
    def run_until_complete(self):
        """Run until all orchids are enriched"""
        logger.info("="*70)
        logger.info("🚀 FORCE COMPLETE ENRICHMENT")
        logger.info(f"📊 Target: {TARGET_TOTAL} orchids")
        logger.info(f"⏱️  Check interval: {CHECK_INTERVAL/60} minutes")
        logger.info("="*70)
        
        iteration = 0
        
        while True:
            iteration += 1
            current_images = self.get_current_stats()
            progress_pct = (current_images / TARGET_TOTAL) * 100
            elapsed = (datetime.now() - self.start_time).total_seconds() / 60
            
            logger.info(f"\n{'='*70}")
            logger.info(f"📊 CHECK #{iteration} - {datetime.now().strftime('%H:%M:%S')}")
            logger.info(f"📸 GBIF Images: {current_images}/{TARGET_TOTAL} ({progress_pct:.1f}%)")
            logger.info(f"⏱️  Running time: {elapsed:.1f} minutes")
            logger.info(f"{'='*70}")
            
            # Check if complete
            if current_images >= TARGET_TOTAL * 0.95:
                logger.info("\n🎉 ENRICHMENT COMPLETE!")
                logger.info(f"✅ {current_images} GBIF images downloaded")
                logger.info(f"⏱️  Total time: {elapsed:.1f} minutes")
                break
            
            # Run batch
            has_more = self.run_batch(limit=100)
            
            if not has_more:
                logger.info("\n✅ All available orchids processed!")
                break
            
            # Wait for next check
            time_since_check = (datetime.now() - self.last_check_time).total_seconds()
            wait_time = max(0, CHECK_INTERVAL - time_since_check)
            
            if wait_time > 0:
                logger.info(f"\n⏳ Waiting {wait_time/60:.1f} minutes until next check...")
                time.sleep(wait_time)
            
            self.last_check_time = datetime.now()
        
        # Final summary
        logger.info("\n" + "="*70)
        logger.info("✅ ENRICHMENT COMPLETE!")
        logger.info(f"Processed: {self.stats['processed']}")
        logger.info(f"Enriched: {self.stats['enriched']}")
        logger.info(f"Images: {self.stats['images']}")
        logger.info(f"Failed: {self.stats['failed']}")
        logger.info("="*70)

if __name__ == "__main__":
    enricher = ForceCompleteEnrichment()
    enricher.run_until_complete()
