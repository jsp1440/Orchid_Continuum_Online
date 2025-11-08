#!/usr/bin/env python3
"""
Batch POWO (Kew Gardens) Enrichment
Runs in parallel with GBIF for faster completion
"""
import sys
sys.path.insert(0, '.')

from app import app, db
from models import OrchidRecord
from powo_integration import POWOIntegrator
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BatchPOWOEnrichment:
    def __init__(self):
        self.powo = POWOIntegrator()
        self.stats = {
            'total': 0,
            'processed': 0,
            'enriched': 0,
            'failed': 0,
            'start_time': datetime.utcnow()
        }
    
    def enrich_orchid(self, orchid):
        """Enrich single orchid with POWO data"""
        scientific_name = f"{orchid.genus} {orchid.species}".strip()
        
        if not scientific_name or scientific_name == "":
            return False
        
        try:
            # Get accepted name from POWO
            powo_data = self.powo.get_accepted_name(scientific_name)
            
            if powo_data:
                # Update orchid with POWO data
                if powo_data.get('accepted_name'):
                    orchid.powo_accepted_name = powo_data['accepted_name']
                if powo_data.get('powo_id'):
                    orchid.powo_taxon_id = str(powo_data['powo_id'])
                
                # Get distribution if available
                if powo_data.get('powo_id'):
                    dist = self.powo.get_distribution(powo_data['powo_id'])
                    if dist:
                        orchid.powo_native_range = dist
                
                orchid.powo_last_synced_at = datetime.utcnow()
                db.session.commit()
                
                logger.info(f"  ✅ POWO: {powo_data.get('accepted_name')}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"  ❌ POWO enrichment failed: {str(e)}")
            return False
    
    def run_batch(self, limit=None):
        """Run batch enrichment"""
        logger.info("="*80)
        logger.info("🌿 STARTING POWO (KEW GARDENS) ENRICHMENT")
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
                
                self.stats['processed'] += 1
                
                if i % 50 == 0:
                    logger.info(f"Progress: {i}/{self.stats['total']} ({i/self.stats['total']*100:.1f}%)")
        
        # Final summary
        elapsed = (datetime.utcnow() - self.stats['start_time']).total_seconds()
        logger.info("\n" + "="*80)
        logger.info("✅ POWO ENRICHMENT COMPLETE!")
        logger.info("="*80)
        logger.info(f"Total: {self.stats['total']}")
        logger.info(f"Enriched: {self.stats['enriched']}")
        logger.info(f"Time: {elapsed/60:.1f} minutes")
        logger.info("="*80)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--full', action='store_true')
    parser.add_argument('--limit', type=int, default=50)
    args = parser.parse_args()
    
    enricher = BatchPOWOEnrichment()
    
    if args.full:
        logger.info("🚀 FULL MODE: All orchids")
        enricher.run_batch()
    else:
        logger.info(f"🧪 TEST MODE: First {args.limit}")
        enricher.run_batch(limit=args.limit)
