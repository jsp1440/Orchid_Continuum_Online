#!/usr/bin/env python3
"""
Production-Ready Ethnobotany Enrichment Agent
Uses SQLAlchemy ORM with retry logic and proper error handling
"""

import sys
import json
import logging
from datetime import datetime
from typing import Dict, Optional, List
import time

from app import app, db
from models import OrchidRecord
from ethnobotany_knowledge_base import get_ethnobotany_for_genus, ETHNOBOTANY_DATABASE

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EthnobotanyEnrichmentAgent:
    """Production-ready ethnobotany enrichment agent using SQLAlchemy ORM"""
    
    def __init__(self, batch_size: int = 100):
        self.batch_size = batch_size
        self.stats = {
            'total_processed': 0,
            'total_enriched': 0,
            'total_skipped': 0,
            'total_errors': 0,
            'genera_coverage': {}
        }
    
    def retry_on_db_error(self, func, max_retries=3, delay=1):
        """Retry database operations on failure"""
        for attempt in range(max_retries):
            try:
                return func()
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Database error (attempt {attempt + 1}/{max_retries}): {e}")
                    time.sleep(delay * (attempt + 1))  # Exponential backoff
                    db.session.rollback()
                else:
                    raise
    
    def get_orchids_needing_enrichment(self, limit: int = None) -> List[OrchidRecord]:
        """Get orchids that need ethnobotany enrichment using SQLAlchemy"""
        def query_func():
            query = db.session.query(OrchidRecord).filter(
                OrchidRecord.ethnobotany_data.is_(None),
                OrchidRecord.genus.isnot(None)
            )
            
            if limit:
                query = query.limit(limit)
            
            return query.all()
        
        return self.retry_on_db_error(query_func)
    
    def enrich_orchid(self, orchid: OrchidRecord) -> bool:
        """Enrich single orchid with ethnobotany data"""
        try:
            if not orchid.genus:
                logger.debug(f"Orchid {orchid.id} has no genus - skipping")
                return False
            
            # Get ethnobotany data from knowledge base
            ethno_data = get_ethnobotany_for_genus(orchid.genus)
            
            if not ethno_data:
                logger.debug(f"No ethnobotany data for genus: {orchid.genus}")
                return False
            
            # Prepare enrichment data
            enrichment = {
                'genus': orchid.genus,
                'traditional_uses': ethno_data.get('traditional_uses', []),
                'indigenous_names': ethno_data.get('indigenous_names', {}),
                'cultural_significance': ethno_data.get('cultural_significance', ''),
                'medicinal_uses': ethno_data.get('medicinal_uses', []),
                'regions': ethno_data.get('regions', []),
                'conservation_notes': ethno_data.get('conservation_notes', ''),
                'modern_research': ethno_data.get('modern_research', ''),
                'enrichment_source': 'ethnobotany_knowledge_base',
                'enrichment_version': '2.0',
                'last_updated': datetime.utcnow().isoformat()
            }
            
            # Add optional detailed fields if available
            for optional_field in ['salep_preparation', 'cultural_context', 'nutritional_content', 
                                  'species_used', 'conservation_crisis', 'conservation_efforts',
                                  'authentic_sources', 'active_compounds', 'research_applications',
                                  'cultivation_notes', 'species_varieties', 'traditional_preparation']:
                if optional_field in ethno_data:
                    enrichment[optional_field] = ethno_data[optional_field]
            
            # Update orchid using ORM
            def update_func():
                orchid.ethnobotany_data = enrichment
                orchid.ethnobotany_last_updated = datetime.utcnow()
                db.session.commit()
            
            self.retry_on_db_error(update_func)
            
            logger.info(f"✓ Enriched orchid {orchid.id} ({orchid.genus} {orchid.species or ''}) with ethnobotany data")
            
            # Update stats
            if orchid.genus not in self.stats['genera_coverage']:
                self.stats['genera_coverage'][orchid.genus] = 0
            self.stats['genera_coverage'][orchid.genus] += 1
            
            return True
            
        except Exception as e:
            logger.error(f"Error enriching orchid {orchid.id}: {e}")
            db.session.rollback()
            raise
    
    def run_enrichment(self, limit: Optional[int] = None) -> Dict:
        """Run ethnobotany enrichment on orchids"""
        logger.info("=" * 80)
        logger.info("PRODUCTION ETHNOBOTANY ENRICHMENT AGENT")
        logger.info(f"Knowledge Base Coverage: {len(ETHNOBOTANY_DATABASE)} genera")
        logger.info("=" * 80)
        
        with app.app_context():
            try:
                # Get orchids needing enrichment
                orchids = self.get_orchids_needing_enrichment(limit=limit)
                total_orchids = len(orchids)
                
                logger.info(f"Found {total_orchids} orchids needing ethnobotany enrichment")
                
                if total_orchids == 0:
                    logger.info("No orchids need enrichment. Exiting.")
                    return self.stats
                
                # Process in batches
                for i in range(0, total_orchids, self.batch_size):
                    batch = orchids[i:i + self.batch_size]
                    batch_num = (i // self.batch_size) + 1
                    total_batches = (total_orchids + self.batch_size - 1) // self.batch_size
                    
                    logger.info(f"\nProcessing batch {batch_num}/{total_batches} ({len(batch)} orchids)")
                    
                    for orchid in batch:
                        try:
                            self.stats['total_processed'] += 1
                            
                            if self.enrich_orchid(orchid):
                                self.stats['total_enriched'] += 1
                            else:
                                self.stats['total_skipped'] += 1
                            
                            # Progress indicator
                            if self.stats['total_processed'] % 50 == 0:
                                logger.info(f"Progress: {self.stats['total_processed']}/{total_orchids} "
                                          f"({self.stats['total_enriched']} enriched, "
                                          f"{self.stats['total_skipped']} skipped)")
                        
                        except Exception as e:
                            self.stats['total_errors'] += 1
                            logger.error(f"Failed to process orchid {orchid.id}: {e}")
                            continue
                
                # Final report
                logger.info("\n" + "=" * 80)
                logger.info("ENRICHMENT COMPLETE")
                logger.info("=" * 80)
                logger.info(f"Total Processed: {self.stats['total_processed']}")
                logger.info(f"Successfully Enriched: {self.stats['total_enriched']}")
                logger.info(f"Skipped (no data): {self.stats['total_skipped']}")
                logger.info(f"Errors: {self.stats['total_errors']}")
                logger.info("\nGenera Coverage:")
                for genus, count in sorted(self.stats['genera_coverage'].items(), key=lambda x: x[1], reverse=True):
                    logger.info(f"  {genus}: {count} orchids")
                logger.info("=" * 80)
                
                return self.stats
                
            except Exception as e:
                logger.error(f"Fatal error in enrichment process: {e}")
                db.session.rollback()
                raise


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Enrich orchids with ethnobotany data')
    parser.add_argument('--limit', type=int, help='Limit number of orchids to process')
    parser.add_argument('--batch-size', type=int, default=100, help='Batch size for processing')
    
    args = parser.parse_args()
    
    agent = EthnobotanyEnrichmentAgent(batch_size=args.batch_size)
    stats = agent.run_enrichment(limit=args.limit)
    
    # Print final JSON stats
    print("\n" + json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
