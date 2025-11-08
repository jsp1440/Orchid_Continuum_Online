#!/usr/bin/env python3
"""
GBIF Species Validator - Pre-checks which orchids have valid GBIF taxonomy
Marks orchids as GBIF-matchable before attempting enrichment
"""
import os
import time
import logging
import requests
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

DATABASE_URL = os.environ.get('DATABASE_URL')
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

class GBIFSpeciesValidator:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Orchid Research Platform',
            'Accept': 'application/json'
        })
        self.stats = {'total': 0, 'valid': 0, 'invalid': 0}
    
    def validate_species(self, scientific_name):
        """Check if species exists in GBIF"""
        try:
            url = "https://api.gbif.org/v1/species/match"
            params = {'name': scientific_name}
            
            response = self.session.get(url, params=params, timeout=10)
            time.sleep(0.5)  # Rate limit
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if it's an accepted species (not hybrid/cultivar)
                if data.get('matchType') == 'EXACT' and data.get('status') == 'ACCEPTED':
                    return {
                        'valid': True,
                        'gbif_key': data.get('usageKey'),
                        'canonical_name': data.get('canonicalName'),
                        'rank': data.get('rank')
                    }
            
            return {'valid': False}
            
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return {'valid': False}
    
    def run(self):
        """Validate all orchids"""
        logger.info("="*70)
        logger.info("🔍 GBIF SPECIES VALIDATOR")
        logger.info("="*70)
        
        db_session = Session()
        
        try:
            # Get all orchids with scientific names
            result = db_session.execute(text("""
                SELECT id, scientific_name
                FROM orchid_record
                WHERE scientific_name IS NOT NULL
                  AND scientific_name != ''
                  AND LENGTH(scientific_name) > 5
                  AND gbif_species_key IS NULL
                ORDER BY id
            """))
            
            orchids = result.fetchall()
            total = len(orchids)
            
            logger.info(f"📊 Found {total} orchids to validate\n")
            
            for orchid in orchids:
                self.stats['total'] += 1
                name = orchid.scientific_name
                
                logger.info(f"[{self.stats['total']}/{total}] {name}")
                
                validation = self.validate_species(name)
                
                if validation['valid']:
                    # Mark as GBIF-valid
                    db_session.execute(
                        text("""
                            UPDATE orchid_record
                            SET gbif_species_key = :key
                            WHERE id = :id
                        """),
                        {
                            'id': orchid.id,
                            'key': validation['gbif_key']
                        }
                    )
                    db_session.commit()
                    self.stats['valid'] += 1
                    logger.info(f"  ✅ Valid GBIF species (key: {validation['gbif_key']})")
                else:
                    self.stats['invalid'] += 1
                    logger.info(f"  ❌ Not in GBIF (hybrid/cultivar/invalid)")
                
                # Progress update every 100
                if self.stats['total'] % 100 == 0:
                    logger.info(f"\n{'='*70}")
                    logger.info(f"Progress: {self.stats['total']}/{total}")
                    logger.info(f"Valid: {self.stats['valid']} | Invalid: {self.stats['invalid']}")
                    logger.info(f"{'='*70}\n")
        
        finally:
            db_session.close()
        
        # Summary
        logger.info("\n" + "="*70)
        logger.info("✅ VALIDATION COMPLETE")
        logger.info(f"Total: {self.stats['total']}")
        logger.info(f"Valid GBIF species: {self.stats['valid']}")
        logger.info(f"Invalid/hybrids/cultivars: {self.stats['invalid']}")
        logger.info("="*70)

if __name__ == "__main__":
    validator = GBIFSpeciesValidator()
    validator.run()
