#!/usr/bin/env python3
"""
Batch Enrichment System for 5,915 Orchids with AI Vision Analysis
Enriches ALL orchid records with:
- GBIF and EOL metadata + downloads public images
- AI-powered visual metadata extraction using OpenAI GPT-4o Vision
"""

import os
import sys
import json
import time
import logging
import requests
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import Flask app context
sys.path.insert(0, '.')
from app import app, db
from models import OrchidRecord

# Import new GBIF and EOL integration modules
try:
    from external_databases.gbif_integration import GBIFIntegrator
    GBIF_AVAILABLE = True
    logger.info("✅ GBIF Integration module loaded")
except Exception as e:
    GBIF_AVAILABLE = False
    logger.warning(f"⚠️ GBIF unavailable: {e}")

try:
    from external_databases.eol_integration import EOLIntegrator
    EOL_AVAILABLE = True
    logger.info("✅ EOL Integration module loaded")
except Exception as e:
    EOL_AVAILABLE = False
    logger.warning(f"⚠️ EOL unavailable: {e}")

# Import AI Vision Enrichment
try:
    from ai_vision_enrichment import AIVisionEnrichment
    AI_VISION_AVAILABLE = True
    logger.info("✅ AI Vision Enrichment module loaded")
except Exception as e:
    AI_VISION_AVAILABLE = False
    logger.warning(f"⚠️ AI Vision unavailable: {e}")

class BatchOrchidEnrichment:
    """Batch enrichment system for all orchids using GBIF and EOL"""
    
    def __init__(self, enable_ai_vision=True):
        # Initialize GBIF and EOL integrators
        self.gbif = GBIFIntegrator() if GBIF_AVAILABLE else None
        self.eol = EOLIntegrator() if EOL_AVAILABLE else None
        
        if self.gbif:
            logger.info("🌍 GBIF Integration: ENABLED")
        else:
            logger.warning("🌍 GBIF Integration: DISABLED")
            
        if self.eol:
            logger.info("🌿 EOL Integration: ENABLED")
        else:
            logger.warning("🌿 EOL Integration: DISABLED")
        
        # Session for image downloads
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Orchid Continuum Research Platform',
            'Accept': 'application/json'
        })
        
        # AI Vision enrichment
        self.ai_vision = None
        if enable_ai_vision and AI_VISION_AVAILABLE:
            try:
                self.ai_vision = AIVisionEnrichment()
                logger.info("🎨 AI Vision Analysis: ENABLED")
            except Exception as e:
                logger.warning(f"AI Vision disabled: {e}")
        else:
            logger.info("🎨 AI Vision Analysis: DISABLED")
        
        # Progress tracking
        self.stats = {
            'total': 0,
            'processed': 0,
            'enriched': 0,
            'images_downloaded': 0,
            'ai_vision_analyzed': 0,
            'failed': 0,
            'start_time': None,
            'errors': []
        }
        
        # Create images directory
        self.images_dir = Path('static/enrichment_images')
        self.images_dir.mkdir(exist_ok=True, parents=True)
    
    def download_image(self, image_url: str, orchid_id: int, source: str) -> Optional[str]:
        """Download a public image from GBIF or EOL"""
        try:
            response = self.session.get(image_url, timeout=15, stream=True)
            if response.status_code != 200:
                return None
            
            # Determine file extension
            content_type = response.headers.get('content-type', '')
            ext = '.jpg'
            if 'png' in content_type:
                ext = '.png'
            elif 'jpeg' in content_type or 'jpg' in content_type:
                ext = '.jpg'
            
            # Save image
            filename = f"{source}_{orchid_id}_{int(time.time())}{ext}"
            filepath = self.images_dir / filename
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"📸 Downloaded image: {filename}")
            return f"/static/enrichment_images/{filename}"
            
        except Exception as e:
            logger.error(f"Image download error: {e}")
            return None
    
    def save_progress(self):
        """Save current progress to JSON file"""
        import json
        progress_data = {
            **self.stats,
            'start_time': self.stats['start_time'].isoformat() if self.stats['start_time'] else None
        }
        with open('enrichment_progress.json', 'w') as f:
            json.dump(progress_data, f, indent=2)
    
    def enrich_orchid(self, orchid: OrchidRecord) -> bool:
        """Enrich a single orchid with GBIF and EOL data using new production integrations"""
        try:
            genus = orchid.genus
            species = orchid.species
            
            if not genus or not species:
                logger.warning(f"Skipping orchid {orchid.id}: missing genus/species")
                return False
            
            scientific_name = f"{genus} {species}"
            logger.info(f"\n🌺 Enriching: {scientific_name} (ID: {orchid.id})")
            
            enriched = False
            
            # Get GBIF occurrence data using new integration
            if self.gbif:
                gbif_data = self.gbif.enrich_occurrence(scientific_name)
                if gbif_data:
                    logger.info(f"  ✅ GBIF occurrence data found")
                    # Apply GBIF occurrence fields to orchid (OrchidRecord fields)
                    for field, value in gbif_data.items():
                        if value is not None and hasattr(orchid, field):
                            setattr(orchid, field, value)
                    enriched = True
                
                # Get GBIF images if orchid has no image
                if not orchid.image_url:
                    images = self.gbif.get_species_images(scientific_name, limit=1)
                    if images:
                        img = images[0]
                        image_path = self.download_image(img['url'], orchid.id, 'gbif')
                        if image_path:
                            orchid.image_url = image_path
                            self.stats['images_downloaded'] += 1
                            logger.info(f"  📸 Downloaded GBIF image")
            
            # Get EOL enrichment data using new integration
            if self.eol:
                eol_data = self.eol.enrich_taxonomy(scientific_name)
                if eol_data:
                    logger.info(f"  ✅ EOL enrichment found")
                    # Apply EOL enrichment fields to orchid
                    for field, value in eol_data.items():
                        if value is not None and hasattr(orchid, field):
                            setattr(orchid, field, value)
                    enriched = True
            
            # AI Vision Analysis - analyze downloaded images
            if enriched and orchid.image_url and self.ai_vision:
                try:
                    logger.info(f"  🎨 Running AI vision analysis...")
                    if self.ai_vision.enrich_orchid_with_vision(orchid):
                        self.stats['ai_vision_analyzed'] += 1
                        logger.info(f"  ✅ AI vision metadata extracted")
                    else:
                        logger.warning(f"  ⚠️ AI vision analysis failed")
                except Exception as e:
                    logger.error(f"  ❌ AI vision error: {e}")
            
            if enriched:
                orchid.updated_at = datetime.utcnow()
                db.session.commit()
                self.stats['enriched'] += 1
                logger.info(f"  💾 Saved enrichment data")
            else:
                logger.warning(f"  ⚠️ No data found")
            
            return enriched
            
        except Exception as e:
            logger.error(f"Enrichment error for orchid {orchid.id}: {e}")
            db.session.rollback()
            self.stats['errors'].append(f"Orchid {orchid.id}: {str(e)}")
            return False
    
    def run_batch_enrichment(self, limit: Optional[int] = None):
        """Run batch enrichment on all orchids"""
        logger.info("=" * 80)
        logger.info("🚀 STARTING BATCH ORCHID ENRICHMENT")
        logger.info("=" * 80)
        
        self.stats['start_time'] = datetime.now()
        
        with app.app_context():
            # Get all orchids (or limit for testing) - skip unknown/invalid orchids
            query = db.session.query(OrchidRecord).filter(
                OrchidRecord.genus.isnot(None),
                OrchidRecord.species.isnot(None),
                OrchidRecord.scientific_name.isnot(None),
                OrchidRecord.scientific_name != '',
                OrchidRecord.scientific_name != 'Unknown Orchid',
                OrchidRecord.genus != 'Unknown'
            ).order_by(OrchidRecord.id)
            
            if limit:
                orchids = query.limit(limit).all()
            else:
                orchids = query.all()
            
            self.stats['total'] = len(orchids)
            logger.info(f"📊 Found {self.stats['total']} orchids to enrich\n")
            
            # Process each orchid
            for i, orchid in enumerate(orchids, 1):
                try:
                    logger.info(f"\n[{i}/{self.stats['total']}] Processing orchid...")
                    
                    self.enrich_orchid(orchid)
                    self.stats['processed'] += 1
                    
                    # Save progress every 5 orchids
                    if i % 5 == 0:
                        self.save_progress()
                    
                    # Progress update every 10 orchids
                    if i % 10 == 0:
                        elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
                        rate = self.stats['processed'] / elapsed if elapsed > 0 else 0
                        remaining = (self.stats['total'] - i) / rate if rate > 0 else 0
                        
                        logger.info(f"\n{'='*60}")
                        logger.info(f"📊 PROGRESS: {i}/{self.stats['total']} ({i/self.stats['total']*100:.1f}%)")
                        logger.info(f"✅ Enriched: {self.stats['enriched']}")
                        logger.info(f"📸 Images downloaded: {self.stats['images_downloaded']}")
                        logger.info(f"🎨 AI vision analyzed: {self.stats['ai_vision_analyzed']}")
                        logger.info(f"⏱️  Est. time remaining: {remaining/60:.1f} minutes")
                        logger.info(f"{'='*60}\n")
                    
                except Exception as e:
                    logger.error(f"Failed to process orchid {orchid.id}: {e}")
                    self.stats['failed'] += 1
                    continue
        
        # Final summary
        elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ BATCH ENRICHMENT COMPLETE!")
        logger.info("=" * 80)
        logger.info(f"Total orchids: {self.stats['total']}")
        logger.info(f"Successfully processed: {self.stats['processed']}")
        logger.info(f"Enriched with data: {self.stats['enriched']}")
        logger.info(f"Images downloaded: {self.stats['images_downloaded']}")
        logger.info(f"🎨 AI vision analyzed: {self.stats['ai_vision_analyzed']}")
        logger.info(f"Failed: {self.stats['failed']}")
        logger.info(f"Total time: {elapsed/60:.1f} minutes")
        logger.info(f"Rate: {self.stats['processed']/elapsed*60:.1f} orchids/minute")
        logger.info("=" * 80)
        
        # Save summary
        summary = {
            **self.stats,
            'start_time': self.stats['start_time'].isoformat(),
            'end_time': datetime.now().isoformat(),
            'duration_minutes': elapsed / 60
        }
        
        with open('enrichment_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"\n📄 Summary saved to: enrichment_summary.json\n")

if __name__ == "__main__":
    # Test mode: process first 50 orchids
    # Full mode: process all orchids
    
    import argparse
    parser = argparse.ArgumentParser(description='Batch enrich orchids with GBIF/EOL data')
    parser.add_argument('--limit', type=int, help='Limit number of orchids (for testing)')
    parser.add_argument('--full', action='store_true', help='Process all orchids')
    parser.add_argument('--no-ai-vision', action='store_true', help='Disable AI Vision (faster, GBIF/EOL only)')
    parser.add_argument('--gbif-only', action='store_true', help='Use GBIF only (fastest, skip EOL)')
    args = parser.parse_args()
    
    # Create enricher with or without AI Vision
    enable_ai = not args.no_ai_vision
    enricher = BatchOrchidEnrichment(enable_ai_vision=enable_ai)
    
    # Disable EOL if --gbif-only flag is set (for speed)
    if args.gbif_only:
        enricher.eol = None
        logger.info("⚡ GBIF-ONLY MODE - EOL disabled for maximum speed")
    
    if args.no_ai_vision:
        logger.info("⚡ AI Vision DISABLED - Fast GBIF/EOL enrichment only")
    
    if args.full:
        logger.info("🚀 FULL MODE: Processing all 5,915 orchids")
        enricher.run_batch_enrichment()
    else:
        limit = args.limit or 50
        logger.info(f"🧪 TEST MODE: Processing first {limit} orchids")
        enricher.run_batch_enrichment(limit=limit)
