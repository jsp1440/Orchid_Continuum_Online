"""
PIPELINE 1: Automated EOL/GBIF Image Harvester
Goal: Systematically acquire images for all 35,320 taxonomy entries
Approach: Queue-based worker system with license filtering and duplicate detection
"""

import logging
import requests
import os
import hashlib
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
from sqlalchemy import func
from collections import defaultdict

from app import db
from models import OrchidRecord, OrchidTaxonomy
from eol_integration import EOLIntegrator
from external_databases.gbif_integration import GBIFIntegrator

logger = logging.getLogger(__name__)

class ImageAcquisitionPipeline1:
    """
    Automated EOL/GBIF image harvester with queue-based processing
    """
    
    def __init__(self):
        self.eol = EOLIntegrator()
        self.gbif = GBIFIntegrator()
        
        # Acceptable licenses
        self.acceptable_licenses = [
            'CC0', 'CC-BY', 'CC-BY-SA', 'CC-BY-4.0', 'CC-BY-SA-4.0',
            'Public Domain', 'PDM'
        ]
        
        # Storage setup
        self.image_dir = Path('static/pipeline1_images')
        self.image_dir.mkdir(parents=True, exist_ok=True)
        
        # Tracking
        self.stats = {
            'processed': 0,
            'images_found': 0,
            'images_downloaded': 0,
            'duplicates_skipped': 0,
            'errors': 0,
            'no_images_available': 0
        }
        
        # Image hash cache for duplicate detection
        self.image_hashes = set()
        self._load_existing_hashes()
    
    def _load_existing_hashes(self):
        """Load hashes of existing images to prevent duplicates"""
        try:
            for img_file in self.image_dir.glob('*.jpg'):
                with open(img_file, 'rb') as f:
                    img_hash = hashlib.md5(f.read()).hexdigest()
                    self.image_hashes.add(img_hash)
            logger.info(f"📊 Loaded {len(self.image_hashes)} existing image hashes")
        except Exception as e:
            logger.error(f"Error loading image hashes: {e}")
    
    def get_priority_queue(self, batch_size: int = 100) -> List[Dict]:
        """
        Get prioritized list of species needing images
        Priority: 1) Records without images, 2) Taxonomy without records
        """
        queue = []
        
        # Priority 1: Existing records without images
        records_without_images = db.session.query(
            OrchidRecord.scientific_name,
            OrchidRecord.id
        ).filter(
            db.and_(
                OrchidRecord.image_url == None,
                OrchidRecord.google_drive_id == None
            )
        ).limit(batch_size // 2).all()
        
        for name, record_id in records_without_images:
            queue.append({
                'scientific_name': name,
                'record_id': record_id,
                'priority': 1,
                'type': 'existing_record'
            })
        
        # Priority 2: Taxonomy entries without any records (need to create records)
        taxonomy_without_records = db.session.query(
            OrchidTaxonomy.scientific_name,
            OrchidTaxonomy.genus,
            OrchidTaxonomy.species
        ).outerjoin(
            OrchidRecord,
            OrchidRecord.scientific_name == OrchidTaxonomy.scientific_name
        ).filter(
            OrchidRecord.id == None
        ).limit(batch_size // 2).all()
        
        for name, genus, species in taxonomy_without_records:
            queue.append({
                'scientific_name': name,
                'genus': genus,
                'species': species,
                'priority': 2,
                'type': 'taxonomy_only'
            })
        
        logger.info(f"📋 Built priority queue with {len(queue)} items")
        return queue
    
    def fetch_images_from_eol(self, scientific_name: str) -> List[Dict]:
        """Fetch all available images from EOL for a species"""
        try:
            images = []
            eol_data = self.eol.get_species_info(scientific_name)
            
            if eol_data and 'images' in eol_data:
                for img in eol_data['images'][:5]:  # Max 5 images per species from EOL
                    if img.get('license') in self.acceptable_licenses:
                        images.append({
                            'url': img.get('mediaURL'),
                            'license': img.get('license'),
                            'attribution': img.get('owner', 'Unknown'),
                            'source': 'EOL',
                            'source_url': img.get('eolMediaURL', '')
                        })
            
            return images
        except Exception as e:
            logger.error(f"EOL fetch error for {scientific_name}: {e}")
            return []
    
    def fetch_images_from_gbif(self, scientific_name: str) -> List[Dict]:
        """Fetch all available images from GBIF for a species"""
        try:
            images = []
            occurrences = self.gbif.get_occurrences_with_images(scientific_name, limit=10)
            
            for occ in occurrences:
                if 'media' in occ:
                    for media in occ['media'][:3]:  # Max 3 per occurrence
                        if media.get('format', '').startswith('image'):
                            images.append({
                                'url': media.get('identifier'),
                                'license': media.get('license', 'Unknown'),
                                'attribution': media.get('creator', 'GBIF'),
                                'source': 'GBIF',
                                'source_url': f"https://www.gbif.org/occurrence/{occ.get('key', '')}"
                            })
            
            return images
        except Exception as e:
            logger.error(f"GBIF fetch error for {scientific_name}: {e}")
            return []
    
    def download_image(self, image_info: Dict, scientific_name: str) -> Optional[str]:
        """Download image and return local path if successful"""
        try:
            response = requests.get(image_info['url'], timeout=15)
            if response.status_code != 200:
                return None
            
            # Check for duplicates using hash
            img_hash = hashlib.md5(response.content).hexdigest()
            if img_hash in self.image_hashes:
                self.stats['duplicates_skipped'] += 1
                logger.debug(f"⏭️ Skipping duplicate image for {scientific_name}")
                return None
            
            # Save image
            safe_name = scientific_name.replace(' ', '_').replace('/', '_')
            timestamp = int(time.time())
            filename = f"{safe_name}_{timestamp}_{img_hash[:8]}.jpg"
            filepath = self.image_dir / filename
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            # Add to hash cache
            self.image_hashes.add(img_hash)
            self.stats['images_downloaded'] += 1
            
            return f"/static/pipeline1_images/{filename}"
        
        except Exception as e:
            logger.error(f"Download error for {scientific_name}: {e}")
            return None
    
    def process_queue_item(self, item: Dict) -> Dict:
        """Process a single queue item and collect images"""
        scientific_name = item['scientific_name']
        results = {
            'scientific_name': scientific_name,
            'images_collected': [],
            'status': 'no_images'
        }
        
        # Fetch images from both sources
        eol_images = self.fetch_images_from_eol(scientific_name)
        gbif_images = self.fetch_images_from_gbif(scientific_name)
        
        all_images = eol_images + gbif_images
        
        if not all_images:
            self.stats['no_images_available'] += 1
            return results
        
        # Download images
        for img_info in all_images[:10]:  # Max 10 images per species per run
            local_path = self.download_image(img_info, scientific_name)
            if local_path:
                results['images_collected'].append({
                    'local_path': local_path,
                    'url': img_info['url'],
                    'license': img_info['license'],
                    'attribution': img_info['attribution'],
                    'source': img_info['source'],
                    'source_url': img_info['source_url']
                })
        
        if results['images_collected']:
            self.stats['images_found'] += len(results['images_collected'])
            results['status'] = 'success'
            
            # Update or create database record
            if item['type'] == 'existing_record':
                self._update_existing_record(item['record_id'], results['images_collected'][0])
            else:
                self._create_new_record(item, results['images_collected'][0])
        
        self.stats['processed'] += 1
        return results
    
    def _update_existing_record(self, record_id: int, image_data: Dict):
        """Update existing OrchidRecord with image"""
        try:
            record = OrchidRecord.query.get(record_id)
            if record:
                record.image_url = image_data['local_path']
                record.image_source = image_data['source']
                record.image_attribution = image_data['attribution']
                record.image_license = image_data['license']
                db.session.commit()
                logger.info(f"✅ Updated record {record_id} with image")
        except Exception as e:
            logger.error(f"Error updating record {record_id}: {e}")
            db.session.rollback()
    
    def _create_new_record(self, item: Dict, image_data: Dict):
        """Create new OrchidRecord from taxonomy data"""
        try:
            new_record = OrchidRecord(
                scientific_name=item['scientific_name'],
                display_name=item['scientific_name'],
                genus=item.get('genus', ''),
                species=item.get('species', ''),
                image_url=image_data['local_path'],
                image_source=image_data['source'],
                image_attribution=image_data['attribution'],
                image_license=image_data['license'],
                data_source='Pipeline 1: Automated EOL/GBIF Harvester',
                upload_date=datetime.utcnow()
            )
            db.session.add(new_record)
            db.session.commit()
            logger.info(f"✅ Created new record for {item['scientific_name']}")
        except Exception as e:
            logger.error(f"Error creating record for {item['scientific_name']}: {e}")
            db.session.rollback()
    
    def run_batch(self, batch_size: int = 100) -> Dict:
        """Run a batch acquisition cycle"""
        start_time = time.time()
        logger.info(f"🚀 Starting Pipeline 1 batch (size: {batch_size})")
        
        queue = self.get_priority_queue(batch_size)
        
        if not queue:
            logger.info("✅ Pipeline 1: No items in queue")
            return self.stats
        
        for item in queue:
            try:
                self.process_queue_item(item)
                time.sleep(0.5)  # Rate limiting
            except Exception as e:
                self.stats['errors'] += 1
                logger.error(f"Error processing {item['scientific_name']}: {e}")
        
        elapsed = time.time() - start_time
        logger.info(f"✅ Pipeline 1 batch complete in {elapsed:.1f}s")
        logger.info(f"📊 Stats: {self.stats}")
        
        return self.stats
    
    def get_progress_report(self) -> Dict:
        """Get comprehensive progress report"""
        total_taxonomy = db.session.query(func.count(OrchidTaxonomy.id)).scalar()
        total_records = db.session.query(func.count(OrchidRecord.id)).scalar()
        records_with_images = db.session.query(func.count(OrchidRecord.id)).filter(
            db.or_(
                OrchidRecord.image_url != None,
                OrchidRecord.google_drive_id != None
            )
        ).scalar()
        
        return {
            'pipeline': 'Pipeline 1: EOL/GBIF Automated Harvester',
            'total_taxonomy_entries': total_taxonomy,
            'total_records': total_records,
            'records_with_images': records_with_images,
            'records_without_images': total_records - records_with_images,
            'coverage_percent': round((records_with_images / total_records * 100), 2) if total_records > 0 else 0,
            'session_stats': self.stats,
            'images_cached': len(self.image_hashes)
        }
