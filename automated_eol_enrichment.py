#!/usr/bin/env python3
"""
Automated EOL Enrichment System
================================
Standalone system to enrich ALL orchids with EOL trait data
- No OpenAI dependency (no quota issues)
- Progress tracking and resume capability
- Batch processing with rate limiting
- Comprehensive error handling
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor

# Import EOL integrators
from external_databases.eol_integration import EOLIntegrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AutomatedEOLEnrichment:
    """
    Automated EOL enrichment system with progress tracking
    """
    
    def __init__(self):
        self.db_url = os.environ.get('DATABASE_URL')
        self.eol = EOLIntegrator()
        self.batch_size = 100
        self.progress_file = 'eol_enrichment_progress.json'
        
    def get_progress(self) -> Dict:
        """Load progress from file"""
        if os.path.exists(self.progress_file):
            with open(self.progress_file, 'r') as f:
                return json.load(f)
        return {
            'last_processed_id': 0,
            'total_processed': 0,
            'successfully_enriched': 0,
            'not_found': 0,
            'errors': 0,
            'started_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat()
        }
    
    def save_progress(self, progress: Dict):
        """Save progress to file"""
        progress['last_updated'] = datetime.now().isoformat()
        with open(self.progress_file, 'w') as f:
            json.dump(progress, f, indent=2)
    
    def get_orchids_to_enrich(self, last_id: int, limit: int) -> List[Dict]:
        """Get batch of orchids that need EOL enrichment"""
        conn = psycopg2.connect(self.db_url)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT id, scientific_name, genus, species
            FROM orchid_record
            WHERE id > %s
            AND scientific_name IS NOT NULL
            AND scientific_name != ''
            AND (eol_page_id IS NULL OR eol_page_id = '')
            ORDER BY id ASC
            LIMIT %s
        """, (last_id, limit))
        
        orchids = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return [dict(o) for o in orchids]
    
    def update_orchid_with_eol(self, orchid_id: int, eol_data: Dict) -> bool:
        """Update orchid with EOL enrichment data"""
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            
            # Build update query
            cursor.execute("""
                UPDATE orchid_record
                SET 
                    eol_page_id = %s,
                    eol_descriptions = %s,
                    eol_population_genetics = %s,
                    eol_morphological_variation = %s,
                    eol_environmental_adaptation = %s,
                    eol_conservation_status = %s,
                    eol_last_synced_at = %s,
                    updated_at = NOW()
                WHERE id = %s
            """, (
                eol_data.get('eol_page_id'),
                json.dumps(eol_data.get('eol_descriptions')) if eol_data.get('eol_descriptions') else None,
                json.dumps(eol_data.get('eol_population_genetics')) if eol_data.get('eol_population_genetics') else None,
                json.dumps(eol_data.get('eol_morphological_variation')) if eol_data.get('eol_morphological_variation') else None,
                json.dumps(eol_data.get('eol_environmental_adaptation')) if eol_data.get('eol_environmental_adaptation') else None,
                json.dumps(eol_data.get('eol_conservation_status')) if eol_data.get('eol_conservation_status') else None,
                eol_data.get('eol_last_synced_at'),
                orchid_id
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to update orchid {orchid_id}: {str(e)}")
            return False
    
    def enrich_batch(self, orchids: List[Dict], progress: Dict) -> Dict:
        """Enrich a batch of orchids"""
        
        for orchid in orchids:
            orchid_id = orchid['id']
            scientific_name = orchid['scientific_name']
            
            try:
                logger.info(f"🔄 Processing {scientific_name} (ID: {orchid_id})")
                
                # Get EOL enrichment data
                eol_data = self.eol.enrich_taxonomy(scientific_name)
                
                if eol_data and eol_data.get('eol_page_id'):
                    # Update orchid with EOL data
                    if self.update_orchid_with_eol(orchid_id, eol_data):
                        progress['successfully_enriched'] += 1
                        logger.info(f"✅ Enriched {scientific_name} with EOL data")
                    else:
                        progress['errors'] += 1
                else:
                    progress['not_found'] += 1
                    logger.warning(f"⚠️ No EOL data found for {scientific_name}")
                
                progress['total_processed'] += 1
                progress['last_processed_id'] = orchid_id
                
                # Save progress every 10 orchids
                if progress['total_processed'] % 10 == 0:
                    self.save_progress(progress)
                    logger.info(f"📊 Progress: {progress['total_processed']} processed, {progress['successfully_enriched']} enriched")
                
                # Rate limiting (EOL allows 30 requests/minute = 2 seconds between requests)
                time.sleep(2.5)
                
            except Exception as e:
                logger.error(f"❌ Error processing {scientific_name}: {str(e)}")
                progress['errors'] += 1
                progress['last_processed_id'] = orchid_id
                progress['total_processed'] += 1
        
        return progress
    
    def run_enrichment(self):
        """Run automated EOL enrichment for all orchids"""
        
        logger.info("=" * 80)
        logger.info("🚀 AUTOMATED EOL ENRICHMENT SYSTEM STARTING")
        logger.info("=" * 80)
        
        # Load progress
        progress = self.get_progress()
        logger.info(f"📊 Resuming from orchid ID: {progress['last_processed_id']}")
        logger.info(f"📊 Already processed: {progress['total_processed']} orchids")
        
        # Get total count
        conn = psycopg2.connect(self.db_url)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) 
            FROM orchid_record 
            WHERE scientific_name IS NOT NULL 
            AND scientific_name != ''
            AND (eol_page_id IS NULL OR eol_page_id = '')
        """)
        result = cursor.fetchone()
        total_pending = result[0] if result else 0
        cursor.close()
        conn.close()
        
        logger.info(f"📊 Total orchids pending EOL enrichment: {total_pending}")
        
        # Process in batches
        while True:
            orchids = self.get_orchids_to_enrich(progress['last_processed_id'], self.batch_size)
            
            if not orchids or len(orchids) == 0:
                logger.info("✅ No more orchids to enrich!")
                break
            
            logger.info(f"📦 Processing batch of {len(orchids)} orchids...")
            progress = self.enrich_batch(orchids, progress)
            self.save_progress(progress)
        
        # Final report
        logger.info("=" * 80)
        logger.info("🎉 EOL ENRICHMENT COMPLETED!")
        logger.info("=" * 80)
        logger.info(f"✅ Successfully enriched: {progress['successfully_enriched']}")
        logger.info(f"⚠️ Not found in EOL: {progress['not_found']}")
        logger.info(f"❌ Errors: {progress['errors']}")
        logger.info(f"📊 Total processed: {progress['total_processed']}")
        
        # Get final coverage stats
        conn = psycopg2.connect(self.db_url)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN eol_page_id IS NOT NULL AND eol_page_id != '' THEN 1 END) as with_eol
            FROM orchid_record
        """)
        result = cursor.fetchone()
        total, with_eol = result if result else (0, 0)
        coverage = (with_eol / total * 100) if total > 0 else 0
        cursor.close()
        conn.close()
        
        logger.info(f"📊 Final EOL Coverage: {with_eol}/{total} ({coverage:.1f}%)")
        logger.info("=" * 80)
        
        # Insert completion message to julius_communication
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO julius_communication (
                    message_from, message_type, subject, message, created_at
                ) VALUES (
                    'EOL Enrichment System',
                    'completion',
                    'EOL Enrichment Complete',
                    %s,
                    NOW()
                )
            """, (f"""🎉 EOL ENRICHMENT COMPLETED!

✅ Successfully enriched: {progress['successfully_enriched']} orchids
⚠️ Not found in EOL: {progress['not_found']}
❌ Errors: {progress['errors']}
📊 Total processed: {progress['total_processed']}

📊 Final Coverage: {with_eol}/{total} ({coverage:.1f}%)

All orchids now have EOL trait data where available!
""",))
            conn.commit()
            cursor.close()
            conn.close()
            logger.info("✅ Completion message saved to julius_communication table")
        except Exception as e:
            logger.warning(f"⚠️ Could not save completion message: {str(e)}")
        
        return progress


def main():
    """Main entry point"""
    enrichment = AutomatedEOLEnrichment()
    enrichment.run_enrichment()


if __name__ == "__main__":
    main()
