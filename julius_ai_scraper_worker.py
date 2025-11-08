"""
Julius AI Autonomous Scraping Worker
Continuously discovers orchid images and metadata, writes to julius_ingest_events
Database triggers automatically launch processing pipelines
"""

import logging
import time
import requests
import json
from datetime import datetime
from typing import List, Dict, Optional
import psycopg2
from psycopg2.extras import Json
import os

logger = logging.getLogger(__name__)

class JuliusAIScraperWorker:
    """
    Autonomous worker that discovers orchid data and triggers pipeline processing
    """
    
    def __init__(self):
        self.db_url = os.environ.get('DATABASE_URL')
        self.conn = None
        self.cursor = None
        self.worker_id = f"julius_scraper_{int(time.time())}"
        
        # Major orchid data sources to scrape
        self.data_sources = [
            {
                'name': 'iNaturalist',
                'api_url': 'https://api.inaturalist.org/v1/observations',
                'family_id': 47217,  # Orchidaceae (CORRECTED)
                'pipeline': 'institutional'
            },
            {
                'name': 'GBIF',
                'api_url': 'https://api.gbif.org/v1/occurrence/search',
                'family_key': 7707728,  # Orchidaceae
                'pipeline': 'eol_gbif'
            },
            {
                'name': 'Flickr_Orchids',
                'api_url': 'https://www.flickr.com/services/rest/',
                'tags': 'orchid,orchidaceae',
                'pipeline': 'ai_discovery'
            }
        ]
        
        self.running = True
        self.heartbeat_interval = 30  # seconds
        self.last_heartbeat = time.time()
    
    def connect_db(self):
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(self.db_url)
            self.cursor = self.conn.cursor()
            logger.info(f"✅ Julius AI Worker {self.worker_id} connected to database")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    def update_heartbeat(self, task_info: Optional[Dict] = None):
        """Update worker heartbeat to show it's alive"""
        try:
            self.cursor.execute("""
                INSERT INTO worker_heartbeats (worker_id, worker_type, status, last_heartbeat, current_task)
                VALUES (%s, %s, %s, NOW(), %s)
                ON CONFLICT (worker_id) 
                DO UPDATE SET 
                    status = EXCLUDED.status,
                    last_heartbeat = NOW(),
                    current_task = EXCLUDED.current_task,
                    tasks_processed = worker_heartbeats.tasks_processed + 1
            """, (self.worker_id, 'julius_scraper', 'running', Json(task_info or {})))
            self.conn.commit()
            self.last_heartbeat = time.time()
        except Exception as e:
            logger.error(f"Heartbeat update failed: {e}")
            self.conn.rollback()
    
    def scrape_inaturalist(self, limit: int = 100) -> List[Dict]:
        """Scrape iNaturalist for orchid observations with photos"""
        discoveries = []
        try:
            params = {
                'taxon_id': 47217,  # Orchidaceae family (CORRECTED)
                'has[]': 'photos',
                'quality_grade': 'research',
                'per_page': limit,
                'order_by': 'created_at',
                'order': 'desc'
            }
            
            response = requests.get(
                'https://api.inaturalist.org/v1/observations',
                params=params,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                for obs in data.get('results', []):
                    if obs.get('taxon') and obs.get('photos'):
                        scientific_name = obs['taxon'].get('name', '')
                        photos = [photo.get('url', '').replace('square', 'large') 
                                 for photo in obs['photos']]
                        
                        discoveries.append({
                            'scientific_name': scientific_name,
                            'source_url': f"https://www.inaturalist.org/observations/{obs.get('id')}",
                            'image_urls': photos,
                            'metadata': {
                                'location': obs.get('place_guess'),
                                'observed_on': obs.get('observed_on'),
                                'quality_grade': obs.get('quality_grade'),
                                'source': 'iNaturalist'
                            },
                            'pipeline': 'institutional',
                            'priority': 7
                        })
            
            logger.info(f"🔍 iNaturalist: Found {len(discoveries)} observations")
        except Exception as e:
            logger.error(f"iNaturalist scraping error: {e}")
        
        return discoveries
    
    def scrape_gbif_occurrences(self, limit: int = 100) -> List[Dict]:
        """Scrape GBIF for orchid occurrences with media"""
        discoveries = []
        try:
            params = {
                'familyKey': 7707728,  # Orchidaceae
                'mediaType': 'StillImage',
                'limit': limit
            }
            
            response = requests.get(
                'https://api.gbif.org/v1/occurrence/search',
                params=params,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                for occ in data.get('results', []):
                    if occ.get('scientificName') and occ.get('media'):
                        image_urls = [media.get('identifier') 
                                     for media in occ['media'] 
                                     if media.get('type') == 'StillImage']
                        
                        if image_urls:
                            discoveries.append({
                                'scientific_name': occ.get('scientificName'),
                                'source_url': f"https://www.gbif.org/occurrence/{occ.get('key')}",
                                'image_urls': image_urls,
                                'metadata': {
                                    'country': occ.get('country'),
                                    'year': occ.get('year'),
                                    'basis_of_record': occ.get('basisOfRecord'),
                                    'source': 'GBIF'
                                },
                                'pipeline': 'eol_gbif',
                                'priority': 6
                            })
            
            logger.info(f"🔍 GBIF: Found {len(discoveries)} occurrences")
        except Exception as e:
            logger.error(f"GBIF scraping error: {e}")
        
        return discoveries
    
    def record_discoveries(self, discoveries: List[Dict]):
        """Write discoveries to julius_ingest_events (triggers pipelines automatically)"""
        recorded = 0
        for disc in discoveries:
            try:
                self.cursor.execute("""
                    INSERT INTO julius_ingest_events (
                        event_type, scientific_name, source_url, image_urls, 
                        metadata, priority, pipeline_assigned
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    'image_discovered',
                    disc['scientific_name'],
                    disc['source_url'],
                    Json(disc['image_urls']),
                    Json(disc['metadata']),
                    disc['priority'],
                    disc['pipeline']
                ))
                
                event_id = self.cursor.fetchone()[0]
                self.conn.commit()
                recorded += 1
                
                logger.info(f"✅ Recorded discovery: {disc['scientific_name']} (Event ID: {event_id})")
            
            except Exception as e:
                logger.error(f"Failed to record discovery: {e}")
                self.conn.rollback()
        
        logger.info(f"📝 Recorded {recorded}/{len(discoveries)} discoveries to database")
        logger.info(f"🚀 Database triggers will automatically launch {recorded} pipeline tasks")
        return recorded
    
    def run_discovery_cycle(self):
        """Run one complete discovery cycle across all sources"""
        logger.info("🔍 Starting Julius AI discovery cycle...")
        
        all_discoveries = []
        
        # Scrape iNaturalist
        self.update_heartbeat({'task': 'scraping_inaturalist'})
        inaturalist_discoveries = self.scrape_inaturalist(limit=50)
        all_discoveries.extend(inaturalist_discoveries)
        time.sleep(2)  # Rate limiting
        
        # Scrape GBIF
        self.update_heartbeat({'task': 'scraping_gbif'})
        gbif_discoveries = self.scrape_gbif_occurrences(limit=50)
        all_discoveries.extend(gbif_discoveries)
        time.sleep(2)
        
        # Record all discoveries (this triggers pipelines automatically via database triggers)
        if all_discoveries:
            self.update_heartbeat({'task': 'recording_discoveries', 'count': len(all_discoveries)})
            recorded = self.record_discoveries(all_discoveries)
            logger.info(f"✅ Discovery cycle complete: {recorded} triggers sent to pipelines")
        else:
            logger.info("ℹ️ No new discoveries this cycle")
        
        self.update_heartbeat({'task': 'idle', 'last_cycle_discoveries': len(all_discoveries)})
    
    def run_continuous(self, cycle_interval: int = 300):
        """
        Run continuously, discovering and recording data
        cycle_interval: seconds between discovery cycles (default 5 minutes)
        """
        logger.info(f"🚀 Julius AI Scraper Worker {self.worker_id} starting continuous operation")
        logger.info(f"📅 Running discovery cycles every {cycle_interval} seconds")
        
        self.connect_db()
        
        try:
            while self.running:
                try:
                    self.run_discovery_cycle()
                    
                    # Sleep but check heartbeat during sleep
                    sleep_chunks = cycle_interval // self.heartbeat_interval
                    for _ in range(sleep_chunks):
                        time.sleep(self.heartbeat_interval)
                        if time.time() - self.last_heartbeat > self.heartbeat_interval:
                            self.update_heartbeat({'task': 'sleeping'})
                
                except Exception as e:
                    logger.error(f"Error in discovery cycle: {e}")
                    time.sleep(30)  # Brief pause before retry
        
        finally:
            logger.info(f"🛑 Julius AI Scraper Worker {self.worker_id} shutting down")
            if self.cursor:
                self.cursor.close()
            if self.conn:
                self.conn.close()
    
    def stop(self):
        """Stop the worker"""
        self.running = False


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    worker = JuliusAIScraperWorker()
    try:
        worker.run_continuous(cycle_interval=300)  # Run every 5 minutes
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
        worker.stop()
