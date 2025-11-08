#!/usr/bin/env python3
"""
Batch Tropicos (Missouri Botanical Garden) Enrichment
Enriches orchids with nomenclature and taxonomic authority data
"""
import sys
sys.path.insert(0, '.')

from app import app, db
from models import OrchidRecord
from external_databases.tropicos_integration import TropicosIntegrator
import logging
from datetime import datetime
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BatchTropicosEnrichment:
    def __init__(self):
        self.tropicos = TropicosIntegrator()
        self.stats = {
            'total': 0,
            'processed': 0,
            'enriched': 0,
            'failed': 0,
            'start_time': datetime.utcnow()
        }
    
    def enrich_orchid(self, orchid):
        """Enrich single orchid with Tropicos data"""
        scientific_name = f"{orchid.genus} {orchid.species}".strip()
        
        if not scientific_name or scientific_name == "":
            return False
        
        try:
            # Search Tropicos
            tropicos_data = self.tropicos.search_name(scientific_name)
            
            if tropicos_data:
                # Update orchid with Tropicos data
                if tropicos_data.get('tropicos_id'):
                    orchid.tropicos_id = str(tropicos_data['tropicos_id'])
                
                if tropicos_data.get('accepted_name'):
                    orchid.tropicos_accepted_name = tropicos_data['accepted_name']
                
                if tropicos_data.get('author'):
                    orchid.tropicos_author = tropicos_data['author']
                
                if tropicos_data.get('nomenclature_status'):
                    orchid.tropicos_nomenclature_status = tropicos_data['nomenclature_status']
                
                orchid.tropicos_last_synced_at = datetime.utcnow()
                db.session.commit()
                
                logger.info(f"  ✅ Tropicos: {tropicos_data.get('accepted_name', 'Data saved')}")
                time.sleep(1)  # Rate limiting
                return True
            
            time.sleep(1)  # Rate limiting even on failure
            return False
            
        except Exception as e:
            logger.error(f"  ❌ Tropicos enrichment failed: {str(e)}")
            time.sleep(1)  # Rate limiting
            return False
    
    def run_batch(self, limit=None):
        """Run batch enrichment"""
        logger.info("="*80)
        logger.info("🌿 STARTING TROPICOS (MISSOURI BOTANICAL) ENRICHMENT")
        logger.info("="*80)
        
        with app.app_context():
            query = db.session.query(OrchidRecord).filter(
                OrchidRecord.genus.isnot(None),
                OrchidRecord.species.isnot(None)
            )
            
            if limit:
                orchids = query.limit(limit).all()
            else:
                orchids = query.all()
            
            self.stats['total'] = len(orchids)
            logger.info(f"📊 Found {self.stats['total']} orchids to enrich")
            
            for i, orchid in enumerate(orchids, 1):
                logger.info(f"\n[{i}/{self.stats['total']}] {orchid.genus} {orchid.species}")
                
                if self.enrich_orchid(orchid):
                    self.stats['enriched'] += 1
                else:
                    self.stats['failed'] += 1
                
                self.stats['processed'] += 1
                
                if i % 50 == 0:
                    logger.info(f"Progress: {i}/{self.stats['total']} ({i/self.stats['total']*100:.1f}%)")
        
        # Final summary
        elapsed = (datetime.utcnow() - self.stats['start_time']).total_seconds()
        logger.info("\n" + "="*80)
        logger.info("✅ TROPICOS ENRICHMENT COMPLETE!")
        logger.info("="*80)
        logger.info(f"Total: {self.stats['total']}")
        logger.info(f"Enriched: {self.stats['enriched']}")
        logger.info(f"Failed: {self.stats['failed']}")
        logger.info(f"Time: {elapsed/60:.1f} minutes")
        logger.info("="*80)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--full', action='store_true')
    parser.add_argument('--limit', type=int, default=10)
    args = parser.parse_args()
    
    enricher = BatchTropicosEnrichment()
    
    if args.full:
        logger.info("🚀 FULL MODE: All orchids")
        enricher.run_batch()
    else:
        logger.info(f"🧪 TEST MODE: First {args.limit}")
        enricher.run_batch(limit=args.limit)
