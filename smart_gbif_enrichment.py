#!/usr/bin/env python3
"""
Smart GBIF Enrichment - Only process orchids with complete species names
Downloads images and metadata from GBIF
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

class SmartGBIFEnrichment:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Orchid Research Platform',
            'Accept': 'application/json'
        })
        self.stats = {
            'processed': 0, 
            'enriched': 0, 
            'images_downloaded': 0,
            'failed': 0
        }
        self.start_time = datetime.now()
        
        # Create images directory
        self.images_dir = Path('static/gbif_images')
        self.images_dir.mkdir(exist_ok=True, parents=True)
    
    def download_image(self, image_url: str, orchid_id: int) -> str:
        """Download GBIF image"""
        try:
            response = self.session.get(image_url, timeout=15, stream=True)
            if response.status_code != 200:
                return None
            
            # Save image
            ext = '.jpg'
            if 'png' in image_url.lower():
                ext = '.png'
            
            filename = f"gbif_{orchid_id}_{int(time.time())}{ext}"
            filepath = self.images_dir / filename
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            self.stats['images_downloaded'] += 1
            return f"/static/gbif_images/{filename}"
            
        except Exception as e:
            logger.error(f"Image download error: {e}")
            return None
    
    def get_gbif_data(self, genus, species):
        """Get GBIF occurrence data with images"""
        try:
            scientific_name = f"{genus} {species}"
            
            # First try: get occurrences WITH media (images)
            url = "https://api.gbif.org/v1/occurrence/search"
            params = {
                'scientificName': scientific_name,
                'hasCoordinate': 'true',
                'mediaType': 'StillImage',
                'limit': 5
            }
            
            response = self.session.get(url, params=params, timeout=10)
            time.sleep(1)  # GBIF rate limit
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                
                if results:
                    # Find occurrence with best image
                    for result in results:
                        if result.get('media'):
                            for media in result['media']:
                                if media.get('identifier'):
                                    return {
                                        'occurrence': result,
                                        'image_url': media['identifier']
                                    }
                    
                    # If no images in results, just return first occurrence
                    return {
                        'occurrence': results[0],
                        'image_url': None
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"GBIF error for {genus} {species}: {e}")
            return None
    
    def enrich_orchid(self, db_session, orchid_id, genus, species, scientific_name):
        """Enrich orchid with GBIF data and images"""
        try:
            logger.info(f"[{self.stats['processed']+1}] {scientific_name}")
            
            # Get GBIF data
            gbif_data = self.get_gbif_data(genus, species)
            
            if gbif_data:
                occurrence = gbif_data['occurrence']
                
                # Download image if available
                image_path = None
                if gbif_data.get('image_url'):
                    image_path = self.download_image(gbif_data['image_url'], orchid_id)
                    if image_path:
                        logger.info(f"  📸 Downloaded image from GBIF")
                
                # Extract metadata
                update_data = {
                    'native_habitat': occurrence.get('locality', ''),
                    'region': occurrence.get('country', ''),
                    'updated_at': datetime.utcnow()
                }
                
                # Add image if downloaded
                if image_path:
                    update_data['image_url'] = image_path
                    update_data['image_source'] = 'GBIF'
                
                # Update database
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
                img_status = "📸 with image" if image_path else ""
                logger.info(f"  ✅ {location} {img_status}")
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
        """Run smart enrichment on complete species only"""
        logger.info("="*70)
        logger.info("🚀 SMART GBIF ENRICHMENT - Complete Species Names Only")
        logger.info("="*70)
        
        db_session = Session()
        
        try:
            # Get ONLY orchids with complete genus + species names
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
                ORDER BY id
            """))
            
            orchids = result.fetchall()
            total = len(orchids)
            logger.info(f"📊 Found {total} orchids with complete species names")
            logger.info(f"🔍 Will download images from GBIF when available\n")
            
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
                    
                    logger.info(f"\n{'='*70}")
                    logger.info(f"📊 Progress: {self.stats['processed']}/{total} ({self.stats['processed']/total*100:.1f}%)")
                    logger.info(f"✅ Enriched: {self.stats['enriched']}")
                    logger.info(f"📸 Images: {self.stats['images_downloaded']}")
                    logger.info(f"❌ Failed: {self.stats['failed']}")
                    logger.info(f"⏱️  Rate: {rate*60:.1f} orchids/min")
                    logger.info(f"⏱️  ETA: {remaining/60:.1f} minutes")
                    logger.info(f"{'='*70}\n")
            
        finally:
            db_session.close()
        
        # Final summary
        elapsed = (datetime.now() - self.start_time).total_seconds()
        
        logger.info("\n" + "="*70)
        logger.info("✅ SMART ENRICHMENT COMPLETE!")
        logger.info("="*70)
        logger.info(f"Total processed: {self.stats['processed']}")
        logger.info(f"Successfully enriched: {self.stats['enriched']}")
        logger.info(f"Images downloaded: {self.stats['images_downloaded']}")
        logger.info(f"Failed: {self.stats['failed']}")
        logger.info(f"Time: {elapsed/60:.1f} minutes")
        logger.info(f"Rate: {self.stats['processed']/elapsed*60:.1f} orchids/min")
        logger.info("="*70)
        
        # Save summary
        with open('smart_enrichment_summary.json', 'w') as f:
            json.dump({
                'processed': self.stats['processed'],
                'enriched': self.stats['enriched'],
                'images_downloaded': self.stats['images_downloaded'],
                'failed': self.stats['failed'],
                'duration_minutes': elapsed / 60,
                'rate_per_minute': self.stats['processed'] / elapsed * 60,
                'completed_at': datetime.now().isoformat()
            }, f, indent=2)
        
        logger.info(f"\n📄 Summary saved to: smart_enrichment_summary.json")

if __name__ == "__main__":
    enricher = SmartGBIFEnrichment()
    enricher.run()
