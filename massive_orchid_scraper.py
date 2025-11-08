"""
MASSIVE ORCHID IMAGE SCRAPER
Continuously downloads ALL orchid images from GBIF, iNaturalist, EOL until complete
Target: 100,000+ real orchid images
"""

import requests
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from app import db
from models import OrchidRecord
from datetime import datetime
import time
from typing import List, Dict
import os

logger = logging.getLogger(__name__)

class MassiveOrchidScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'OrchidContinuum/1.0 (Botanical Research)'
        })
        
        # Import Google Drive manager
        try:
            from gdrive_manager import GDriveManager
            self.gdrive = GDriveManager()
            logger.info("✅ Google Drive ready for mass upload")
        except Exception as e:
            logger.error(f"CRITICAL: Google Drive not available: {e}")
            self.gdrive = None
    
    def get_all_gbif_orchid_images(self):
        """
        Query GBIF for ALL orchid occurrences with images
        No limits - get everything
        """
        logger.info("🌍 Querying GBIF for ALL orchid images...")
        
        all_images = []
        offset = 0
        limit = 300  # GBIF max per request
        
        while True:
            try:
                response = self.session.get(
                    'https://api.gbif.org/v1/occurrence/search',
                    params={
                        'familyKey': 157167872,  # Orchidaceae family
                        'mediaType': 'StillImage',
                        'hasCoordinate': 'true',
                        'limit': limit,
                        'offset': offset
                    },
                    timeout=30
                )
                
                if response.status_code != 200:
                    logger.error(f"GBIF request failed: {response.status_code}")
                    break
                
                data = response.json()
                results = data.get('results', [])
                
                if not results:
                    logger.info(f"✅ GBIF complete: {len(all_images)} total images found")
                    break
                
                # Extract images from results
                for occurrence in results:
                    if 'media' in occurrence:
                        for media in occurrence['media']:
                            if media.get('type') == 'StillImage':
                                all_images.append({
                                    'url': media.get('identifier'),
                                    'source': 'GBIF',
                                    'scientific_name': occurrence.get('scientificName', 'Unknown'),
                                    'country': occurrence.get('country'),
                                    'lat': occurrence.get('decimalLatitude'),
                                    'lon': occurrence.get('decimalLongitude'),
                                    'license': media.get('license', 'Unknown'),
                                    'occurrence_id': occurrence.get('key')
                                })
                
                logger.info(f"📸 GBIF progress: {len(all_images)} images collected (offset: {offset})")
                offset += limit
                
                # Small delay to be respectful
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error fetching GBIF batch at offset {offset}: {e}")
                break
        
        return all_images
    
    def get_all_inaturalist_orchids(self):
        """
        Query iNaturalist for ALL orchid observations with photos
        """
        logger.info("🦋 Querying iNaturalist for ALL orchid images...")
        
        all_images = []
        page = 1
        per_page = 200
        
        while True:
            try:
                response = self.session.get(
                    'https://api.inaturalist.org/v1/observations',
                    params={
                        'taxon_name': 'Orchidaceae',
                        'photos': 'true',
                        'quality_grade': 'research',
                        'per_page': per_page,
                        'page': page
                    },
                    timeout=30
                )
                
                if response.status_code != 200:
                    logger.error(f"iNaturalist request failed: {response.status_code}")
                    break
                
                data = response.json()
                results = data.get('results', [])
                
                if not results:
                    logger.info(f"✅ iNaturalist complete: {len(all_images)} total images found")
                    break
                
                # Extract images
                for obs in results:
                    if 'photos' in obs and obs['photos']:
                        for photo in obs['photos']:
                            all_images.append({
                                'url': photo.get('url', '').replace('square', 'original'),
                                'source': 'iNaturalist',
                                'scientific_name': obs.get('taxon', {}).get('name', 'Unknown'),
                                'country': obs.get('place_guess', ''),
                                'lat': obs.get('geojson', {}).get('coordinates', [None, None])[1],
                                'lon': obs.get('geojson', {}).get('coordinates', [None, None])[0],
                                'license': photo.get('license_code', 'Unknown'),
                                'observer': obs.get('user', {}).get('login', 'Unknown')
                            })
                
                logger.info(f"📸 iNaturalist progress: {len(all_images)} images collected (page: {page})")
                page += 1
                
                # Respectful delay
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error fetching iNaturalist page {page}: {e}")
                break
        
        return all_images
    
    def download_image(self, image_data: Dict) -> bool:
        """
        Download a single image and store in Google Drive
        Returns True if successful
        """
        if not self.gdrive or not image_data.get('url'):
            return False
        
        try:
            # Download image
            response = self.session.get(image_data['url'], timeout=20, stream=True)
            if response.status_code != 200:
                return False
            
            # Create or update orchid record
            scientific_name = image_data.get('scientific_name', 'Unknown')
            
            # Find or create orchid
            orchid = OrchidRecord.query.filter_by(scientific_name=scientific_name).first()
            if not orchid:
                orchid = OrchidRecord()
                orchid.scientific_name = scientific_name
                orchid.display_name = scientific_name
                orchid.ingestion_source = image_data.get('source', 'Mass Scraper')
                
                if image_data.get('lat') and image_data.get('lon'):
                    orchid.decimal_latitude = image_data['lat']
                    orchid.decimal_longitude = image_data['lon']
                if image_data.get('country'):
                    orchid.country = image_data['country']
                
                db.session.add(orchid)
                db.session.commit()
            
            # Upload to Google Drive if doesn't have image already
            if not orchid.google_drive_id:
                filename = f"{scientific_name.replace(' ', '_')}_{image_data.get('source')}_{orchid.id}.jpg"
                
                gdrive_id = self.gdrive.upload_image(
                    image_data=response.content,
                    filename=filename,
                    folder='Orchid_Quick_Images',
                    metadata={
                        'source': image_data.get('source'),
                        'license': image_data.get('license'),
                        'scientific_name': scientific_name
                    }
                )
                
                if gdrive_id:
                    orchid.google_drive_id = gdrive_id
                    orchid.image_source = image_data.get('source')
                    db.session.commit()
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to download {image_data.get('url')}: {e}")
            return False
    
    def massive_parallel_download(self, image_list: List[Dict], max_workers: int = 50):
        """
        Download images in parallel using thread pool
        max_workers=50 means 50 simultaneous downloads
        """
        total = len(image_list)
        logger.info(f"🚀 Starting MASSIVE parallel download: {total} images with {max_workers} workers")
        
        downloaded = 0
        failed = 0
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all download tasks
            future_to_image = {
                executor.submit(self.download_image, img): img 
                for img in image_list
            }
            
            # Process results as they complete
            for future in as_completed(future_to_image):
                if future.result():
                    downloaded += 1
                else:
                    failed += 1
                
                # Log progress every 100 images
                if (downloaded + failed) % 100 == 0:
                    logger.info(f"📊 Progress: {downloaded} downloaded, {failed} failed, {total - downloaded - failed} remaining")
        
        logger.info(f"✅ DOWNLOAD COMPLETE: {downloaded} successful, {failed} failed out of {total} total")
        return downloaded, failed


def run_massive_scrape():
    """
    Main function to run the massive scrape
    Called from admin interface
    """
    from app import app
    
    with app.app_context():
        scraper = MassiveOrchidScraper()
        
        start_time = datetime.now()
        logger.info("=" * 80)
        logger.info("🚀 MASSIVE ORCHID SCRAPE INITIATED")
        logger.info(f"Start Time: {start_time}")
        logger.info("=" * 80)
        
        # Step 1: Collect ALL image URLs from ALL sources
        logger.info("\n📡 PHASE 1: COLLECTING IMAGE URLs FROM ALL SOURCES\n")
        
        all_images = []
        
        # GBIF
        gbif_images = scraper.get_all_gbif_orchid_images()
        all_images.extend(gbif_images)
        logger.info(f"✅ GBIF: {len(gbif_images)} images")
        
        # iNaturalist
        inat_images = scraper.get_all_inaturalist_orchids()
        all_images.extend(inat_images)
        logger.info(f"✅ iNaturalist: {len(inat_images)} images")
        
        logger.info(f"\n📊 TOTAL IMAGES TO DOWNLOAD: {len(all_images)}\n")
        
        # Step 2: Download everything in parallel
        logger.info("\n💾 PHASE 2: MASSIVE PARALLEL DOWNLOAD\n")
        
        downloaded, failed = scraper.massive_parallel_download(all_images, max_workers=50)
        
        # Final stats
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ MASSIVE SCRAPE COMPLETE")
        logger.info(f"Duration: {duration/60:.1f} minutes")
        logger.info(f"Downloaded: {downloaded} images")
        logger.info(f"Failed: {failed} images")
        logger.info(f"Success Rate: {(downloaded/(downloaded+failed)*100):.1f}%")
        logger.info("=" * 80)
        
        return {
            'total_found': len(all_images),
            'downloaded': downloaded,
            'failed': failed,
            'duration_minutes': duration/60,
            'images_per_minute': downloaded / (duration/60) if duration > 0 else 0
        }
