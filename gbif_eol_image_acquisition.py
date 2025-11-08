"""
GBIF and EOL Automated Image Acquisition System
Downloads orchid images from GBIF occurrences and EOL pages
Stores images in Google Drive and links them to orchid records
"""

import os
import logging
import requests
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from io import BytesIO
from app import db
from models import OrchidRecord
import time

logger = logging.getLogger(__name__)

class GBIFEOLImageAcquisition:
    """
    Automated image downloading from GBIF and EOL databases
    Priority: GBIF occurrences > EOL pages > iNaturalist
    """
    
    def __init__(self):
        self.gbif_base = "https://api.gbif.org/v1"
        self.eol_base = "https://eol.org/api"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'OrchidContinuum/1.0 (Botanical Research; fcospresident@gmail.com)'
        })
        
        # Try to import Google Drive manager
        self.gdrive = None
        try:
            from gdrive_manager import GDriveManager
            self.gdrive = GDriveManager()
            logger.info("✅ Google Drive manager loaded for image storage")
        except Exception as e:
            logger.warning(f"Google Drive not available: {e}")
    
    def acquire_gbif_images(self, orchid_record: OrchidRecord, limit: int = 3) -> List[str]:
        """
        Download images from GBIF occurrences
        Returns list of Google Drive image URLs
        """
        if not orchid_record.scientific_name:
            return []
        
        scientific_name = orchid_record.scientific_name
        logger.info(f"🔍 Searching GBIF for images: {scientific_name}")
        
        try:
            # Search for occurrences with images
            response = self.session.get(
                f"{self.gbif_base}/occurrence/search",
                params={
                    'scientificName': scientific_name,
                    'mediaType': 'StillImage',
                    'limit': 20,  # Get more to filter for quality
                    'hasCoordinate': 'true'  # Prefer geotagged images
                },
                timeout=15
            )
            
            if response.status_code != 200:
                logger.warning(f"GBIF search failed for {scientific_name}: {response.status_code}")
                return []
            
            data = response.json()
            results = data.get('results', [])
            
            if not results:
                logger.info(f"No GBIF images found for {scientific_name}")
                return []
            
            downloaded_urls = []
            
            for occurrence in results[:limit]:  # Limit downloads
                if 'media' not in occurrence:
                    continue
                
                for media_item in occurrence['media']:
                    if media_item.get('type') != 'StillImage':
                        continue
                    
                    image_url = media_item.get('identifier')
                    license = media_item.get('license', 'Unknown')
                    
                    if not image_url:
                        continue
                    
                    # Download and store image
                    gdrive_url = self._download_and_store_image(
                        image_url=image_url,
                        orchid_id=orchid_record.id,
                        source='GBIF',
                        scientific_name=scientific_name,
                        license=license,
                        occurrence_id=occurrence.get('key')
                    )
                    
                    if gdrive_url:
                        downloaded_urls.append(gdrive_url)
                        logger.info(f"✅ Downloaded GBIF image: {scientific_name}")
                    
                    if len(downloaded_urls) >= limit:
                        break
                
                if len(downloaded_urls) >= limit:
                    break
            
            return downloaded_urls
        
        except Exception as e:
            logger.error(f"Error acquiring GBIF images for {scientific_name}: {e}")
            return []
    
    def acquire_eol_images(self, orchid_record: OrchidRecord, limit: int = 3) -> List[str]:
        """
        Download images from Encyclopedia of Life
        Returns list of Google Drive image URLs
        """
        if not orchid_record.scientific_name:
            return []
        
        scientific_name = orchid_record.scientific_name
        logger.info(f"🔍 Searching EOL for images: {scientific_name}")
        
        try:
            # Step 1: Search for EOL page ID
            search_response = self.session.get(
                f"{self.eol_base}/search/1.0.json",
                params={'q': scientific_name},
                timeout=15
            )
            
            if search_response.status_code != 200:
                logger.warning(f"EOL search failed for {scientific_name}: {search_response.status_code}")
                return []
            
            search_data = search_response.json()
            results = search_data.get('results', [])
            
            if not results:
                logger.info(f"No EOL page found for {scientific_name}")
                return []
            
            page_id = results[0].get('id')
            
            # Step 2: Get images from EOL page
            page_response = self.session.get(
                f"{self.eol_base}/pages/1.0/{page_id}.json",
                params={
                    'images_per_page': limit * 2,  # Get extras for filtering
                    'details': 'true'
                },
                timeout=15
            )
            
            if page_response.status_code != 200:
                logger.warning(f"EOL page fetch failed for {scientific_name}: {page_response.status_code}")
                return []
            
            page_data = page_response.json()
            data_objects = page_data.get('dataObjects', [])
            
            downloaded_urls = []
            
            for obj in data_objects:
                if obj.get('dataType') != 'http://purl.org/dc/dcmitype/StillImage':
                    continue
                
                image_url = obj.get('eolMediaURL')
                license = obj.get('license', 'Unknown')
                rights_holder = obj.get('rightsHolder', 'Unknown')
                
                if not image_url:
                    continue
                
                # Download and store image
                gdrive_url = self._download_and_store_image(
                    image_url=image_url,
                    orchid_id=orchid_record.id,
                    source='EOL',
                    scientific_name=scientific_name,
                    license=license,
                    attribution=rights_holder
                )
                
                if gdrive_url:
                    downloaded_urls.append(gdrive_url)
                    logger.info(f"✅ Downloaded EOL image: {scientific_name}")
                
                if len(downloaded_urls) >= limit:
                    break
            
            return downloaded_urls
        
        except Exception as e:
            logger.error(f"Error acquiring EOL images for {scientific_name}: {e}")
            return []
    
    def _download_and_store_image(
        self,
        image_url: str,
        orchid_id: int,
        source: str,
        scientific_name: str,
        license: str = 'Unknown',
        occurrence_id: str = None,
        attribution: str = None
    ) -> Optional[str]:
        """
        Download image from URL and store in Google Drive
        Returns Google Drive URL or None if failed
        """
        if not self.gdrive:
            logger.warning("Google Drive not available - cannot store image")
            return None
        
        try:
            # Download image
            response = self.session.get(image_url, timeout=20, stream=True)
            
            if response.status_code != 200:
                logger.warning(f"Failed to download image from {image_url}: {response.status_code}")
                return None
            
            # Determine file extension
            content_type = response.headers.get('content-type', '')
            ext = 'jpg'
            if 'png' in content_type:
                ext = 'png'
            elif 'jpeg' in content_type or 'jpg' in content_type:
                ext = 'jpg'
            
            # Create filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_name = scientific_name.replace(' ', '_').replace('.', '')[:50]
            filename = f"{safe_name}_{source}_{timestamp}.{ext}"
            
            # Read image content
            image_content = BytesIO(response.content)
            
            # Store in Google Drive
            gdrive_url = self.gdrive.upload_image(
                image_content,
                filename,
                folder_name='Imported_Orchids'  # Use existing folder
            )
            
            if gdrive_url:
                logger.info(f"✅ Stored {source} image in Google Drive: {filename}")
                return gdrive_url
            else:
                logger.warning(f"Failed to store image in Google Drive: {filename}")
                return None
        
        except Exception as e:
            logger.error(f"Error downloading/storing image from {image_url}: {e}")
            return None
    
    def acquire_images_for_orchid(self, orchid_record: OrchidRecord) -> Dict[str, any]:
        """
        Acquire images from all sources for a single orchid
        Returns dict with results
        """
        results = {
            'orchid_id': orchid_record.id,
            'scientific_name': orchid_record.scientific_name,
            'gbif_images': [],
            'eol_images': [],
            'total_acquired': 0
        }
        
        # Skip if already has images
        if orchid_record.image_url and len(orchid_record.image_url) > 50:
            logger.info(f"Skipping {orchid_record.scientific_name} - already has image")
            return results
        
        # Try GBIF first (higher quality, occurrence-based)
        gbif_urls = self.acquire_gbif_images(orchid_record, limit=2)
        results['gbif_images'] = gbif_urls
        
        # Try EOL if GBIF didn't provide enough
        if len(gbif_urls) < 2:
            eol_urls = self.acquire_eol_images(orchid_record, limit=2)
            results['eol_images'] = eol_urls
        
        # Update orchid record with first image
        all_urls = gbif_urls + results['eol_images']
        if all_urls and not orchid_record.image_url:
            orchid_record.image_url = all_urls[0]
            orchid_record.image_source = 'GBIF' if gbif_urls else 'EOL'
            db.session.commit()
            logger.info(f"✅ Updated {orchid_record.scientific_name} with new image")
        
        results['total_acquired'] = len(all_urls)
        return results
    
    def batch_acquire_images(self, limit: int = 50) -> Dict[str, any]:
        """
        Batch process orchids without images
        Returns summary statistics
        """
        logger.info(f"🚀 Starting batch image acquisition (limit: {limit})")
        
        # Get orchids without images
        orchids_without_images = OrchidRecord.query.filter(
            (OrchidRecord.image_url == None) | (OrchidRecord.image_url == '')
        ).order_by(OrchidRecord.id.desc()).limit(limit).all()
        
        logger.info(f"Found {len(orchids_without_images)} orchids without images")
        
        summary = {
            'total_processed': 0,
            'total_images_acquired': 0,
            'gbif_images': 0,
            'eol_images': 0,
            'failed': 0
        }
        
        for orchid in orchids_without_images:
            try:
                results = self.acquire_images_for_orchid(orchid)
                summary['total_processed'] += 1
                summary['gbif_images'] += len(results['gbif_images'])
                summary['eol_images'] += len(results['eol_images'])
                summary['total_images_acquired'] += results['total_acquired']
                
                # Rate limiting - be respectful to APIs
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Failed to acquire images for {orchid.scientific_name}: {e}")
                summary['failed'] += 1
        
        logger.info(f"✅ Batch acquisition complete: {summary}")
        return summary


# Singleton instance
image_acquisition = GBIFEOLImageAcquisition()


def run_image_acquisition(limit: int = 50):
    """
    Run image acquisition job
    Can be called from scheduler
    """
    return image_acquisition.batch_acquire_images(limit=limit)
