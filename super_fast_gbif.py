#!/usr/bin/env python3
"""
SUPER FAST GBIF-ONLY ENRICHMENT - NO FLASK APP LOADING
Direct database connection, minimal imports, maximum speed
"""
import os
import json
import time
import logging
import requests
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Database connection
DATABASE_URL = os.environ.get('DATABASE_URL')
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

class FastGBIF:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Orchid Research Platform',
            'Accept': 'application/json'
        })
        self.stats = {'processed': 0, 'enriched': 0, 'failed': 0}
        self.start_time = datetime.now()
    
    def get_gbif_occurrence(self, genus, species):
        """Get GBIF occurrence data"""
        try:
            scientific_name = f"{genus} {species}"
            url = "https://api.gbif.org/v1/occurrence/search"
            params = {
                'scientificName': scientific_name,
                'hasCoordinate': 'true',
                'limit': 1
            }
            
            response = self.session.get(url, params=params, timeout=10)
            time.sleep(1)  # GBIF rate limit
            
            if response.status_code == 200:
                data = response.json()
                if data.get('results'):
                    return data['results'][0]
            return None
        except Exception as e:
            logger.error(f"GBIF error for {genus} {species}: {e}")
            return None
    
    def enrich_orchid(self, db_session, orchid_id, genus, species, scientific_name):
        """Enrich single orchid with GBIF data"""
        try:
            logger.info(f"[{self.stats['processed']+1}] {scientific_name}")
            
            # Get GBIF data
            occurrence = self.get_gbif_occurrence(genus, species)
            
            if occurrence:
                # Extract key data
                update_data = {
                    'native_habitat': occurrence.get('locality', ''),
                    'region': occurrence.get('country', ''),
                    'updated_at': datetime.utcnow()
                }
                
                # Update database
                db_session.execute(
                    text("""
                        UPDATE orchid_record 
                        SET native_habitat = :native_habitat,
                            region = :region,
                            updated_at = :updated_at
                        WHERE id = :id
                    """),
                    {'id': orchid_id, **update_data}
                )
                db_session.commit()
                
                self.stats['enriched'] += 1
                logger.info(f"  ✅ Enriched: {occurrence.get('country', 'Unknown')}")
                return True
            else:
                logger.info(f"  ⚠️ No GBIF data")
                return False
                
        except Exception as e:
            logger.error(f"  ❌ Error: {e}")
            db_session.rollback()
            self.stats['failed'] += 1
            return False
        finally:
            self.stats['processed'] += 1
    
    def run(self):
        """Run fast enrichment"""
        logger.info("="*60)
        logger.info("🚀 SUPER FAST GBIF ENRICHMENT STARTING")
        logger.info("="*60)
        
        db_session = Session()
        
        try:
            # Get valid orchids
            result = db_session.execute(text("""
                SELECT id, genus, species, scientific_name
                FROM orchid_record
                WHERE genus IS NOT NULL 
                  AND species IS NOT NULL
                  AND scientific_name IS NOT NULL
                  AND scientific_name != ''
                  AND scientific_name != 'Unknown Orchid'
                  AND genus != 'Unknown'
                ORDER BY id
            """))
            
            orchids = result.fetchall()
            total = len(orchids)
            logger.info(f"📊 Found {total} orchids to enrich\n")
            
            # Process each orchid
            for orchid in orchids:
                self.enrich_orchid(
                    db_session,
                    orchid.id,
                    orchid.genus,
                    orchid.species,
                    orchid.scientific_name
                )
                
                # Progress update every 50
                if self.stats['processed'] % 50 == 0:
                    elapsed = (datetime.now() - self.start_time).total_seconds()
                    rate = self.stats['processed'] / elapsed if elapsed > 0 else 0
                    remaining = (total - self.stats['processed']) / rate if rate > 0 else 0
                    
                    logger.info(f"\n{'='*60}")
                    logger.info(f"📊 Progress: {self.stats['processed']}/{total} ({self.stats['processed']/total*100:.1f}%)")
                    logger.info(f"✅ Enriched: {self.stats['enriched']}")
                    logger.info(f"❌ Failed: {self.stats['failed']}")
                    logger.info(f"⏱️  Rate: {rate*60:.1f} orchids/min")
                    logger.info(f"⏱️  ETA: {remaining/60:.1f} minutes")
                    logger.info(f"{'='*60}\n")
            
        finally:
            db_session.close()
        
        # Final summary
        elapsed = (datetime.now() - self.start_time).total_seconds()
        
        logger.info("\n" + "="*60)
        logger.info("✅ ENRICHMENT COMPLETE!")
        logger.info("="*60)
        logger.info(f"Total: {self.stats['processed']}")
        logger.info(f"Enriched: {self.stats['enriched']}")
        logger.info(f"Failed: {self.stats['failed']}")
        logger.info(f"Time: {elapsed/60:.1f} minutes")
        logger.info(f"Rate: {self.stats['processed']/elapsed*60:.1f} orchids/min")
        logger.info("="*60)
        
        # Save summary
        with open('fast_enrichment_summary.json', 'w') as f:
            json.dump({
                'processed': self.stats['processed'],
                'enriched': self.stats['enriched'],
                'failed': self.stats['failed'],
                'duration_minutes': elapsed / 60,
                'rate_per_minute': self.stats['processed'] / elapsed * 60,
                'completed_at': datetime.now().isoformat()
            }, f, indent=2)

if __name__ == "__main__":
    enricher = FastGBIF()
    enricher.run()
