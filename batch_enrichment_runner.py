#!/usr/bin/env python3
"""
Batch Enrichment Runner
========================
Processes orchids in batches with progress saving to handle large datasets.
Can be stopped and resumed without losing progress.
"""

import os
import sys
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional
import signal

from app import app, db
from models import OrchidRecord
from master_comprehensive_enrichment import MasterOrchidEnricher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BatchEnrichmentRunner:
    """Run enrichment in manageable batches with progress tracking"""
    
    def __init__(self, batch_size: int = 50):
        self.enricher = MasterOrchidEnricher()
        self.batch_size = batch_size
        self.progress_file = "enrichment_progress.json"
        self.stop_requested = False
        
        # Handle graceful shutdown
        signal.signal(signal.SIGINT, self.request_stop)
        signal.signal(signal.SIGTERM, self.request_stop)
    
    def request_stop(self, signum, frame):
        """Request graceful stop"""
        logger.info("\n⚠️ Stop requested - will finish current orchid and save progress...")
        self.stop_requested = True
    
    def load_progress(self) -> Dict:
        """Load progress from file"""
        if os.path.exists(self.progress_file):
            with open(self.progress_file, 'r') as f:
                return json.load(f)
        return {
            'last_id': 0,
            'total_processed': 0,
            'total_enriched': 0,
            'total_cost': 0.0,
            'batches': [],
            'started_at': datetime.now().isoformat(),
            'last_update': datetime.now().isoformat()
        }
    
    def save_progress(self, progress: Dict):
        """Save progress to file"""
        progress['last_update'] = datetime.now().isoformat()
        with open(self.progress_file, 'w') as f:
            json.dump(progress, f, indent=2)
    
    def get_next_batch(self, last_id: int) -> List[OrchidRecord]:
        """Get next batch of orchids to process"""
        with app.app_context():
            return OrchidRecord.query.filter(
                OrchidRecord.id > last_id
            ).order_by(OrchidRecord.id).limit(self.batch_size).all()
    
    def run(self, max_batches: Optional[int] = None):
        """Run batch enrichment"""
        progress = self.load_progress()
        
        logger.info("=" * 70)
        logger.info("🚀 BATCH ENRICHMENT RUNNER")
        logger.info("=" * 70)
        logger.info(f"📊 Previous progress:")
        logger.info(f"  • Processed: {progress['total_processed']} orchids")
        logger.info(f"  • Enriched: {progress['total_enriched']} orchids")
        logger.info(f"  • Cost so far: ${progress['total_cost']:.2f}")
        logger.info(f"  • Resuming from ID: {progress['last_id']}")
        logger.info("")
        
        batch_count = 0
        start_time = time.time()
        
        while True:
            if self.stop_requested:
                logger.info("✋ Stop requested - saving progress and exiting...")
                break
            
            if max_batches and batch_count >= max_batches:
                logger.info(f"✅ Reached maximum batches ({max_batches})")
                break
            
            # Process batch (fetch and enrich in same context to keep SQLAlchemy session)
            with app.app_context():
                # Get next batch within context
                batch = OrchidRecord.query.filter(
                    OrchidRecord.id > progress['last_id']
                ).order_by(OrchidRecord.id).limit(self.batch_size).all()
                
                if not batch:
                    logger.info("🎉 All orchids processed!")
                    break
                
                batch_count += 1
                batch_start = time.time()
                
                logger.info("=" * 70)
                logger.info(f"📦 BATCH {batch_count} ({len(batch)} orchids)")
                logger.info(f"   IDs: {batch[0].id} - {batch[-1].id}")
                logger.info("=" * 70)
                
                batch_results = []
                for idx, orchid in enumerate(batch, 1):
                    if self.stop_requested:
                        break
                    
                    logger.info(f"\n🌺 {idx}/{len(batch)}: {orchid.genus} {orchid.species} (ID: {orchid.id})")
                    
                    try:
                        result = self.enricher.enrich_single_orchid(orchid)
                        batch_results.append(result)
                        
                        # Update progress
                        progress['last_id'] = orchid.id
                        progress['total_processed'] += 1
                        
                        if result.get('enriched'):
                            progress['total_enriched'] += 1
                        
                        # Track cost
                        if 'ai_vision' in result and result['ai_vision']:
                            progress['total_cost'] += 0.003
                        
                        # Save progress every 10 orchids
                        if progress['total_processed'] % 10 == 0:
                            self.save_progress(progress)
                    
                    except Exception as e:
                        logger.error(f"❌ Error processing {orchid.genus} {orchid.species}: {e}")
                        progress['last_id'] = orchid.id
                        progress['total_processed'] += 1
            
            # Save batch summary
            batch_time = time.time() - batch_start
            batch_summary = {
                'batch': batch_count,
                'orchids': len(batch_results),
                'enriched': sum(1 for r in batch_results if r.get('enriched')),
                'time': batch_time,
                'timestamp': datetime.now().isoformat()
            }
            progress['batches'].append(batch_summary)
            self.save_progress(progress)
            
            logger.info(f"\n✅ Batch {batch_count} complete in {batch_time:.1f}s")
            logger.info(f"   Enriched: {batch_summary['enriched']}/{len(batch_results)}")
            logger.info(f"   Total progress: {progress['total_enriched']}/{progress['total_processed']}")
            logger.info(f"   Estimated cost so far: ${progress['total_cost']:.2f}")
        
        # Final summary
        total_time = time.time() - start_time
        logger.info("\n" + "=" * 70)
        logger.info("📊 FINAL SUMMARY")
        logger.info("=" * 70)
        logger.info(f"⏱️  Total time: {total_time/60:.1f} minutes")
        logger.info(f"🌺 Total processed: {progress['total_processed']}")
        logger.info(f"✅ Total enriched: {progress['total_enriched']}")
        logger.info(f"💰 Total cost: ${progress['total_cost']:.2f}")
        logger.info(f"📦 Batches completed: {batch_count}")
        logger.info(f"")
        logger.info(f"💾 Progress saved to: {self.progress_file}")
        logger.info("=" * 70)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Run batch orchid enrichment')
    parser.add_argument('--batch-size', type=int, default=50, help='Orchids per batch')
    parser.add_argument('--max-batches', type=int, default=None, help='Maximum batches to run')
    parser.add_argument('--reset', action='store_true', help='Reset progress and start from beginning')
    
    args = parser.parse_args()
    
    if args.reset and os.path.exists('enrichment_progress.json'):
        os.remove('enrichment_progress.json')
        logger.info("🔄 Progress reset - starting fresh")
    
    runner = BatchEnrichmentRunner(batch_size=args.batch_size)
    runner.run(max_batches=args.max_batches)
