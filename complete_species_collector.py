"""
Complete Orchid Species Image Collection System

Goal: Obtain at least one image for every orchid species in the world (~28,000 species)

Data Sources:
- Encyclopedia of Life (EOL) - images with licenses
- GBIF - occurrence images with proper attribution
- POWO - species list from Kew Gardens

Features:
- Automatic image downloading with proper attribution
- License compliance (CC-BY, CC-BY-SA, CC0, Public Domain)
- Progress tracking toward complete coverage
- Citation generation for each image source
"""

import logging
import requests
import os
import json
from typing import Dict, List, Optional
from datetime import datetime
from urllib.parse import urlparse
from pathlib import Path

from models import OrchidRecord, OrchidTaxonomy, db
from eol_integration import EOLIntegrator
from external_databases.gbif_integration import GBIFIntegrator
from powo_integration import POWOIntegrator

logger = logging.getLogger(__name__)

class CompleteSpeciesCollector:
    """
    Systematically collect images for all orchid species from authoritative sources
    """
    
    def __init__(self):
        self.eol = EOLIntegrator()
        self.gbif = GBIFIntegrator()
        self.powo = POWOIntegrator()
        
        # Acceptable licenses for image use
        self.acceptable_licenses = [
            'CC0',
            'CC-BY',
            'CC-BY-SA',
            'CC-BY-4.0',
            'CC-BY-SA-4.0',
            'Public Domain',
            'PDM'  # Public Domain Mark
        ]
        
        # Image storage directory
        self.image_dir = Path('static/collected_images')
        self.image_dir.mkdir(parents=True, exist_ok=True)
    
    def get_species_without_images(self, limit: int = 100) -> List[str]:
        """
        Get list of orchid species that don't have images
        
        Returns:
            List of scientific names needing images
        """
        try:
            # Query database for species without images
            species_without_images = db.session.query(
                OrchidTaxonomy.scientific_name
            ).outerjoin(
                OrchidRecord,
                OrchidRecord.scientific_name == OrchidTaxonomy.scientific_name
            ).filter(
                db.or_(
                    OrchidRecord.image_url == None,
                    OrchidRecord.google_drive_id == None
                )
            ).limit(limit).all()
            
            species_list = [species[0] for species in species_without_images if species[0]]
            
            logger.info(f"📊 Found {len(species_list)} species without images")
            return species_list
            
        except Exception as e:
            logger.error(f"Error getting species without images: {e}")
            return []
    
    def collect_image_for_species(self, scientific_name: str) -> Dict:
        """
        Collect image for a single species from EOL or GBIF
        
        Returns:
            Dictionary with image info and attribution
        """
        try:
            logger.info(f"🔍 Collecting image for {scientific_name}")
            
            result = {
                'scientific_name': scientific_name,
                'image_found': False,
                'source': None,
                'image_url': None,
                'license': None,
                'attribution': None,
                'download_status': None
            }
            
            # Try EOL first (usually better quality images)
            eol_image = self._get_eol_image(scientific_name)
            if eol_image:
                result.update(eol_image)
                result['image_found'] = True
                result['source'] = 'Encyclopedia of Life'
                return result
            
            # Try GBIF if EOL doesn't have images
            gbif_image = self._get_gbif_image(scientific_name)
            if gbif_image:
                result.update(gbif_image)
                result['image_found'] = True
                result['source'] = 'GBIF'
                return result
            
            logger.warning(f"❌ No suitable images found for {scientific_name}")
            return result
            
        except Exception as e:
            logger.error(f"Error collecting image for {scientific_name}: {e}")
            return {
                'scientific_name': scientific_name,
                'error': str(e),
                'image_found': False
            }
    
    def _get_eol_image(self, scientific_name: str) -> Optional[Dict]:
        """Get image from Encyclopedia of Life"""
        try:
            # Search EOL
            search_result = self.eol.search_eol_species(scientific_name)
            if not search_result:
                return None
            
            # Get page data with images
            page_id = search_result.get('id')
            page_data = self.eol.get_eol_page_data(page_id)
            
            if not page_data:
                return None
            
            # Extract images
            images = page_data.get('images', [])
            
            # Find first image with acceptable license
            for img in images:
                license_name = img.get('license', '')
                
                if any(lic in license_name for lic in self.acceptable_licenses):
                    return {
                        'image_url': img.get('source_url'),
                        'license': license_name,
                        'attribution': f"{img.get('owner', 'Unknown')} via Encyclopedia of Life",
                        'eol_page_id': page_id,
                        'rights_holder': img.get('owner'),
                        'source_url': f"https://eol.org/pages/{page_id}"
                    }
            
            return None
            
        except Exception as e:
            logger.debug(f"EOL image search failed for {scientific_name}: {e}")
            return None
    
    def _get_gbif_image(self, scientific_name: str) -> Optional[Dict]:
        """Get image from GBIF occurrences"""
        try:
            # Get occurrences with images
            occurrences = self.gbif.get_occurrences(
                scientific_name=scientific_name,
                limit=10,
                with_images=True
            )
            
            if not occurrences or not occurrences.get('results'):
                return None
            
            # Find first occurrence with suitable image
            for occurrence in occurrences['results']:
                images = occurrence.get('images', [])
                
                for img in images:
                    license_name = img.get('license', '')
                    
                    if any(lic in license_name for lic in self.acceptable_licenses):
                        location = occurrence.get('location', {})
                        return {
                            'image_url': img.get('url'),
                            'license': license_name,
                            'attribution': f"{img.get('rights_holder', 'GBIF Contributor')} via GBIF",
                            'rights_holder': img.get('rights_holder'),
                            'source_url': f"https://www.gbif.org/occurrence/{occurrence.get('gbif_key')}",
                            'location': {
                                'country': location.get('country'),
                                'latitude': location.get('latitude'),
                                'longitude': location.get('longitude')
                            }
                        }
            
            return None
            
        except Exception as e:
            logger.debug(f"GBIF image search failed for {scientific_name}: {e}")
            return None
    
    def store_collected_image(self, image_data: Dict) -> bool:
        """
        Store collected image in database with proper attribution
        
        Args:
            image_data: Dictionary with image info from collect_image_for_species
            
        Returns:
            True if successful
        """
        try:
            if not image_data.get('image_found'):
                return False
            
            scientific_name = image_data['scientific_name']
            
            # Check if record already exists
            existing = OrchidRecord.query.filter_by(
                scientific_name=scientific_name
            ).first()
            
            if existing and existing.image_url:
                logger.info(f"✅ {scientific_name} already has an image")
                return True
            
            # Create or update record
            if existing:
                orchid = existing
            else:
                orchid = OrchidRecord()
                orchid.scientific_name = scientific_name
                
                # Parse genus/species from name
                parts = scientific_name.split()
                if len(parts) >= 1:
                    orchid.genus = parts[0]
                if len(parts) >= 2:
                    orchid.species = parts[1]
                
                orchid.display_name = scientific_name
            
            # Set image and attribution
            orchid.image_url = image_data['image_url']
            orchid.photographer = image_data.get('attribution')
            orchid.data_source = image_data.get('source')
            
            # Store metadata in eol_traits
            current_traits = {}
            if orchid.eol_traits:
                try:
                    current_traits = json.loads(orchid.eol_traits)
                except:
                    pass
            
            current_traits['collected_image'] = {
                'source': image_data.get('source'),
                'license': image_data.get('license'),
                'rights_holder': image_data.get('rights_holder'),
                'source_url': image_data.get('source_url'),
                'collected_date': datetime.now().isoformat(),
                'attribution': image_data.get('attribution')
            }
            
            if image_data.get('eol_page_id'):
                orchid.eol_page_id = image_data['eol_page_id']
            
            orchid.eol_traits = json.dumps(current_traits)
            
            if not existing:
                db.session.add(orchid)
            
            db.session.commit()
            
            logger.info(f"✅ Stored image for {scientific_name} from {image_data['source']}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing image for {image_data.get('scientific_name')}: {e}")
            db.session.rollback()
            return False
    
    def batch_collect_images(self, batch_size: int = 50) -> Dict:
        """
        Collect images for multiple species in a batch
        
        Args:
            batch_size: Number of species to process
            
        Returns:
            Summary statistics
        """
        try:
            logger.info(f"🚀 Starting batch collection of {batch_size} species images")
            
            # Get species without images
            species_list = self.get_species_without_images(limit=batch_size)
            
            stats = {
                'total_attempted': len(species_list),
                'images_found': 0,
                'images_stored': 0,
                'not_found': 0,
                'errors': 0,
                'sources': {
                    'EOL': 0,
                    'GBIF': 0
                }
            }
            
            for scientific_name in species_list:
                # Collect image
                image_data = self.collect_image_for_species(scientific_name)
                
                if image_data.get('image_found'):
                    stats['images_found'] += 1
                    stats['sources'][image_data['source']] = stats['sources'].get(image_data['source'], 0) + 1
                    
                    # Store in database
                    if self.store_collected_image(image_data):
                        stats['images_stored'] += 1
                else:
                    if image_data.get('error'):
                        stats['errors'] += 1
                    else:
                        stats['not_found'] += 1
            
            logger.info(f"✅ Batch collection complete: {stats['images_stored']}/{stats['total_attempted']} images stored")
            return stats
            
        except Exception as e:
            logger.error(f"Error in batch collection: {e}")
            return {'error': str(e)}
    
    def get_collection_progress(self) -> Dict:
        """
        Get progress toward complete orchid species coverage
        
        Returns:
            Statistics on collection progress
        """
        try:
            # Total known species in taxonomy
            total_species = db.session.query(OrchidTaxonomy).count()
            
            # Species with images
            species_with_images = db.session.query(OrchidRecord).filter(
                db.or_(
                    OrchidRecord.image_url != None,
                    OrchidRecord.google_drive_id != None
                )
            ).count()
            
            # Calculate coverage
            coverage_percent = (species_with_images / total_species * 100) if total_species > 0 else 0
            
            # Goal: 28,000 orchid species (approximate total worldwide)
            world_species_estimate = 28000
            world_coverage_percent = (species_with_images / world_species_estimate * 100)
            
            return {
                'database_species': total_species,
                'species_with_images': species_with_images,
                'species_without_images': total_species - species_with_images,
                'database_coverage_percent': round(coverage_percent, 2),
                'world_species_estimate': world_species_estimate,
                'world_coverage_percent': round(world_coverage_percent, 2),
                'goal': 'At least one image for every orchid species',
                'remaining_to_goal': max(0, world_species_estimate - species_with_images)
            }
            
        except Exception as e:
            logger.error(f"Error getting collection progress: {e}")
            return {'error': str(e)}


# Global instance
species_collector = CompleteSpeciesCollector()

logger.info("🌍 Complete Species Collector initialized - Goal: Image every orchid species worldwide")
