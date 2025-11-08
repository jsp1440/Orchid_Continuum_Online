#!/usr/bin/env python3
"""
Automated Orchid Enrichment - Runs continuously until ALL orchids enriched
Handles errors, retries, reconnects - NEVER gives up
"""
import os
import time
import logging
import requests
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

DATABASE_URL = os.environ.get('DATABASE_URL')

class AutomatedEnrichment:
    def __init__(self):
        self.stats = {'total': 0, 'enriched': 0, 'failed': 0, 'errors': 0}
        self.start_time = datetime.now()
    
    def get_fresh_db(self):
        """Get fresh database connection"""
        engine = create_engine(DATABASE_URL, poolclass=NullPool)
        return sessionmaker(bind=engine)()
    
    def validate_gbif(self, scientific_name):
        """Quick GBIF validation"""
        try:
            response = requests.get(
                "https://api.gbif.org/v1/species/match",
                params={'name': scientific_name},
                timeout=5
            )
            time.sleep(0.3)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('matchType') == 'EXACT' and data.get('status') == 'ACCEPTED':
                    return data.get('usageKey')
        except:
            pass
        return None
    
    def get_gbif_image(self, genus, species):
        """Get GBIF occurrence image"""
        try:
            response = requests.get(
                "https://api.gbif.org/v1/occurrence/search",
                params={
                    'scientificName': f"{genus} {species}",
                    'mediaType': 'StillImage',
                    'limit': 1
                },
                timeout=5
            )
            time.sleep(0.3)
            
            if response.status_code == 200:
                results = response.json().get('results', [])
                if results and results[0].get('media'):
                    media = results[0]['media'][0]
                    return {
                        'url': media.get('identifier'),
                        'country': results[0].get('country', '')
                    }
        except:
            pass
        return None
    
    def process_single_orchid(self, orchid_id, genus, species, scientific_name):
        """Process one orchid with fresh connection each time"""
        db = None
        try:
            db = self.get_fresh_db()
            
            self.stats['total'] += 1
            logger.info(f"[{self.stats['total']}] {scientific_name or f'{genus} {species}'}")
            
            # Skip if already has GBIF data
            check = db.execute(
                text("SELECT gbif_species_key, image_source FROM orchid_record WHERE id = :id"),
                {'id': orchid_id}
            ).fetchone()
            
            if check and check[0]:
                logger.info("  ⏭️  Already has GBIF key")
                db.close()
                return
            
            # Validate GBIF
            if scientific_name:
                gbif_key = self.validate_gbif(scientific_name)
                if gbif_key:
                    db.execute(
                        text("UPDATE orchid_record SET gbif_species_key = :key WHERE id = :id"),
                        {'id': orchid_id, 'key': gbif_key}
                    )
                    db.commit()
                    self.stats['enriched'] += 1
                    logger.info(f"  ✅ GBIF validated (key: {gbif_key})")
                    
                    # Try to get image if doesn't have one
                    if not check[1]:  # No image source
                        image_data = self.get_gbif_image(genus, species)
                        if image_data and image_data['url']:
                            db.execute(
                                text("""UPDATE orchid_record 
                                       SET image_url = :url, 
                                           image_source = 'GBIF',
                                           region = COALESCE(:region, region)
                                       WHERE id = :id"""),
                                {'id': orchid_id, 'url': image_data['url'], 
                                 'region': image_data['country']}
                            )
                            db.commit()
                            logger.info(f"  📸 Image from {image_data['country']}")
                else:
                    logger.info("  ⚠️  Not in GBIF")
                    self.stats['failed'] += 1
            
            db.close()
            
        except Exception as e:
            logger.error(f"  ❌ Error: {e}")
            self.stats['errors'] += 1
            if db:
                try:
                    db.close()
                except:
                    pass
    
    def get_next_batch(self, limit=50):
        """Get next batch to process"""
        db = None
        try:
            db = self.get_fresh_db()
            result = db.execute(text("""
                SELECT id, genus, species, scientific_name
                FROM orchid_record
                WHERE scientific_name IS NOT NULL
                  AND LENGTH(scientific_name) > 5
                  AND gbif_species_key IS NULL
                ORDER BY id
                LIMIT :limit
            """), {'limit': limit})
            
            orchids = result.fetchall()
            db.close()
            return orchids
        except Exception as e:
            logger.error(f"Batch fetch error: {e}")
            if db:
                try:
                    db.close()
                except:
                    pass
            return []
    
    def run(self):
        """Run continuous enrichment"""
        logger.info("="*70)
        logger.info("🤖 AUTOMATED CONTINUOUS ENRICHMENT")
        logger.info("="*70)
        
        batch_num = 0
        
        while True:
            # Get next batch
            orchids = self.get_next_batch(50)
            
            if not orchids:
                logger.info("\n✅ ALL ORCHIDS PROCESSED!")
                break
            
            batch_num += 1
            logger.info(f"\n{'='*70}")
            logger.info(f"📦 BATCH {batch_num} - {len(orchids)} orchids")
            logger.info(f"{'='*70}")
            
            # Process each orchid individually with fresh connections
            for orchid in orchids:
                self.process_single_orchid(
                    orchid.id, 
                    orchid.genus, 
                    orchid.species, 
                    orchid.scientific_name
                )
            
            # Progress report
            elapsed = (datetime.now() - self.start_time).total_seconds() / 60
            rate = self.stats['total'] / elapsed if elapsed > 0 else 0
            
            logger.info(f"\n{'='*70}")
            logger.info(f"📊 PROGRESS REPORT")
            logger.info(f"Processed: {self.stats['total']}")
            logger.info(f"Enriched: {self.stats['enriched']}")
            logger.info(f"Failed: {self.stats['failed']}")
            logger.info(f"Errors: {self.stats['errors']}")
            logger.info(f"Rate: {rate:.1f}/min | Time: {elapsed:.1f} min")
            logger.info(f"{'='*70}")
            
            # Small pause between batches
            time.sleep(2)
        
        # Final report
        elapsed = (datetime.now() - self.start_time).total_seconds() / 60
        logger.info("\n" + "="*70)
        logger.info("🎉 ENRICHMENT COMPLETE!")
        logger.info(f"Total processed: {self.stats['total']}")
        logger.info(f"Successfully enriched: {self.stats['enriched']}")
        logger.info(f"Not in GBIF: {self.stats['failed']}")
        logger.info(f"Errors: {self.stats['errors']}")
        logger.info(f"Total time: {elapsed:.1f} minutes")
        logger.info("="*70)

if __name__ == "__main__":
    enricher = AutomatedEnrichment()
    enricher.run()
