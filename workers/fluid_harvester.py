#!/usr/bin/env python3
"""
Fluid Multi-Source Harvester v1.0
================================
Dynamically switches between data sources based on real-time performance.
Uses in-memory taxonomy cache and async batch processing for maximum throughput.

Features:
- Multi-source: GBIF, iNaturalist, iDigBio, ALA, EOL
- Dynamic source switching based on yield rate
- In-memory taxonomy cache (no per-record DB calls)
- Batch processing with connection pooling
- Automatic failover when sources slow down

Target: 3,000+ images/hour per worker
"""

import os
import sys
import time
import json
import random
import logging
import hashlib
import requests
from datetime import datetime, timedelta
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from psycopg2.extras import execute_values, RealDictCursor
from psycopg2.pool import ThreadedConnectionPool

# Configuration
WORKER_ID = os.environ.get('WORKER_ID', 'fluid-1')
DATABASE_URL = os.environ.get('NEON_DATABASE_URL') or os.environ.get('DATABASE_URL')
BATCH_SIZE = 100
MIN_SOURCE_SWITCH_INTERVAL = 30  # seconds before considering source switch
PERFORMANCE_WINDOW = 60  # seconds to track source performance
REQUEST_TIMEOUT = 15

# Logging
logging.basicConfig(
    level=logging.INFO,
    format=f'[{WORKER_ID}] %(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Fix DATABASE_URL if needed
if DATABASE_URL:
    DATABASE_URL = DATABASE_URL.strip().replace('\n', '').replace('\r', '')

# Connection pool
db_pool = None

def get_db_pool():
    """Get or create database connection pool."""
    global db_pool
    if db_pool is None:
        db_pool = ThreadedConnectionPool(2, 20, DATABASE_URL)
    return db_pool

def get_connection():
    """Get a connection from the pool."""
    return get_db_pool().getconn()

def release_connection(conn):
    """Return a connection to the pool."""
    get_db_pool().putconn(conn)


class TaxonomyCache:
    """In-memory taxonomy cache to eliminate per-record DB lookups."""
    
    def __init__(self):
        self.genus_to_id = {}
        self.species_to_id = {}
        self.valid_genera = set()
        self.last_refresh = None
        self.refresh_interval = 300  # 5 minutes
        
    def needs_refresh(self):
        if self.last_refresh is None:
            return True
        return (datetime.now() - self.last_refresh).seconds > self.refresh_interval
    
    def refresh(self):
        """Load all taxonomy into memory."""
        logger.info("Refreshing taxonomy cache...")
        conn = get_connection()
        try:
            cur = conn.cursor()
            
            # Load all genera
            cur.execute("SELECT DISTINCT genus FROM orchid_taxonomy WHERE genus IS NOT NULL")
            self.valid_genera = {row[0].lower() for row in cur.fetchall()}
            
            # Load genus -> id mapping
            cur.execute("SELECT id, genus FROM orchid_taxonomy WHERE genus IS NOT NULL")
            for row in cur.fetchall():
                genus = row[1].lower()
                if genus not in self.genus_to_id:
                    self.genus_to_id[genus] = row[0]
            
            # Load species -> id mapping
            cur.execute("SELECT id, genus, species FROM orchid_taxonomy WHERE species IS NOT NULL")
            for row in cur.fetchall():
                key = f"{row[1].lower()}_{row[2].lower()}"
                self.species_to_id[key] = row[0]
            
            self.last_refresh = datetime.now()
            logger.info(f"Taxonomy cache loaded: {len(self.valid_genera)} genera, {len(self.species_to_id)} species")
            
        finally:
            release_connection(conn)
    
    def validate_and_get_id(self, genus, species=None):
        """Validate taxonomy and return ID if valid. No DB calls."""
        if self.needs_refresh():
            self.refresh()
            
        if not genus:
            return None
            
        genus_lower = genus.lower().strip()
        
        # Check if genus is valid orchid
        if genus_lower not in self.valid_genera:
            return None
        
        # Try species match first
        if species:
            species_lower = species.lower().strip()
            key = f"{genus_lower}_{species_lower}"
            if key in self.species_to_id:
                return self.species_to_id[key]
        
        # Fall back to genus match
        return self.genus_to_id.get(genus_lower)


class SourceAdapter:
    """Base class for data source adapters."""
    
    name = "base"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'OrchidContinuum/1.0 (research; contact@orchidcontinuum.org)'
        })
    
    def fetch_batch(self, offset=0, limit=100):
        """Fetch a batch of images. Returns list of image records."""
        raise NotImplementedError
    
    def get_next_offset(self, current_offset, batch_size, total_available):
        """Get next offset for pagination."""
        return current_offset + batch_size


class GBIFAdapter(SourceAdapter):
    """GBIF data source adapter."""
    
    name = "GBIF"
    base_url = "https://api.gbif.org/v1"
    
    # Orchidaceae family key in GBIF
    ORCHIDACEAE_FAMILY_KEY = 7689
    
    def __init__(self):
        super().__init__()
        self.countries = [
            'US', 'BR', 'CO', 'EC', 'PE', 'MX', 'AU', 'MY', 'ID', 'PH',
            'TH', 'VN', 'IN', 'CN', 'JP', 'TW', 'CR', 'PA', 'VE', 'BO',
            'PY', 'AR', 'CL', 'ZA', 'MG', 'KE', 'TZ', 'UG', 'NG', 'CM',
            'GB', 'DE', 'FR', 'ES', 'IT', 'NL', 'BE', 'AT', 'CH', 'PL',
            'CZ', 'SE', 'NO', 'FI', 'DK', 'IE', 'PT', 'GR', 'RU', 'UA',
            'NZ', 'PG', 'FJ', 'NC', 'SG', 'HK', 'KR', 'MM', 'LA', 'KH',
            'BD', 'NP', 'LK', 'BT', 'GY', 'SR', 'TT', 'JM', 'CU', 'DO',
            'HT', 'GT', 'HN', 'NI', 'SV', 'BZ', 'GF', 'PR', 'VI', 'GP'
        ]
        self.current_country_idx = random.randint(0, len(self.countries) - 1)
        self.country_offsets = defaultdict(int)
    
    def fetch_batch(self, offset=0, limit=100):
        """Fetch orchid images from GBIF."""
        country = self.countries[self.current_country_idx]
        actual_offset = self.country_offsets[country]
        
        try:
            url = f"{self.base_url}/occurrence/search"
            params = {
                'familyKey': self.ORCHIDACEAE_FAMILY_KEY,
                'mediaType': 'StillImage',
                'country': country,
                'hasCoordinate': 'true',
                'limit': limit,
                'offset': actual_offset
            }
            
            response = self.session.get(url, params=params, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            
            results = data.get('results', [])
            end_of_records = data.get('endOfRecords', True)
            
            # Update offset for this country
            self.country_offsets[country] += limit
            
            # Move to next country if exhausted
            if end_of_records or not results:
                self.current_country_idx = (self.current_country_idx + 1) % len(self.countries)
                self.country_offsets[country] = 0
            
            # Parse results
            images = []
            for record in results:
                media = record.get('media', [])
                for m in media:
                    if m.get('type') == 'StillImage' and m.get('identifier'):
                        images.append({
                            'source': 'GBIF',
                            'image_url': m.get('identifier'),
                            'genus': record.get('genus'),
                            'species': record.get('specificEpithet'),
                            'scientific_name': record.get('scientificName'),
                            'gbif_key': str(record.get('key')),
                            'latitude': record.get('decimalLatitude'),
                            'longitude': record.get('decimalLongitude'),
                            'country': record.get('country'),
                            'country_code': record.get('countryCode'),
                            'state_province': record.get('stateProvince'),
                            'locality': record.get('locality'),
                            'observation_date': record.get('eventDate'),
                            'observer': record.get('recordedBy'),
                            'institution': record.get('institutionCode'),
                            'license': m.get('license'),
                            'rights_holder': m.get('rightsHolder')
                        })
            
            return images
            
        except Exception as e:
            logger.warning(f"GBIF fetch error: {e}")
            # Move to next country on error
            self.current_country_idx = (self.current_country_idx + 1) % len(self.countries)
            return []


class INaturalistAdapter(SourceAdapter):
    """iNaturalist data source adapter."""
    
    name = "iNaturalist"
    base_url = "https://api.inaturalist.org/v1"
    
    # Orchidaceae taxon ID in iNaturalist
    ORCHIDACEAE_TAXON_ID = 47217
    
    def __init__(self):
        super().__init__()
        self.page = 1
        self.quality_grades = ['research', 'needs_id']
        self.current_quality_idx = 0
    
    def fetch_batch(self, offset=0, limit=100):
        """Fetch orchid images from iNaturalist."""
        quality = self.quality_grades[self.current_quality_idx]
        
        try:
            url = f"{self.base_url}/observations"
            params = {
                'taxon_id': self.ORCHIDACEAE_TAXON_ID,
                'photos': 'true',
                'quality_grade': quality,
                'per_page': limit,
                'page': self.page,
                'order': 'desc',
                'order_by': 'created_at'
            }
            
            response = self.session.get(url, params=params, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            
            results = data.get('results', [])
            total = data.get('total_results', 0)
            
            # Update pagination
            self.page += 1
            if self.page * limit >= total or not results:
                self.page = 1
                self.current_quality_idx = (self.current_quality_idx + 1) % len(self.quality_grades)
            
            # Parse results
            images = []
            for obs in results:
                taxon = obs.get('taxon', {})
                photos = obs.get('photos', [])
                
                for photo in photos:
                    url = photo.get('url', '').replace('square', 'original')
                    if url:
                        # Parse genus/species from taxon name
                        name_parts = taxon.get('name', '').split()
                        genus = name_parts[0] if name_parts else None
                        species = name_parts[1] if len(name_parts) > 1 else None
                        
                        images.append({
                            'source': 'iNaturalist',
                            'image_url': url,
                            'genus': genus,
                            'species': species,
                            'scientific_name': taxon.get('name'),
                            'latitude': obs.get('location', '').split(',')[0] if obs.get('location') else None,
                            'longitude': obs.get('location', '').split(',')[1] if obs.get('location') and ',' in obs.get('location', '') else None,
                            'country': obs.get('place_guess'),
                            'observation_date': obs.get('observed_on'),
                            'observer': obs.get('user', {}).get('login'),
                            'license': photo.get('license_code'),
                            'rights_holder': photo.get('attribution')
                        })
            
            return images
            
        except Exception as e:
            logger.warning(f"iNaturalist fetch error: {e}")
            self.page = 1
            return []


class IDigBioAdapter(SourceAdapter):
    """iDigBio data source adapter."""
    
    name = "iDigBio"
    base_url = "https://search.idigbio.org/v2"
    
    def __init__(self):
        super().__init__()
        self.offset = 0
    
    def fetch_batch(self, offset=0, limit=100):
        """Fetch orchid images from iDigBio."""
        try:
            url = f"{self.base_url}/search/records"
            params = {
                'rq': json.dumps({'family': 'Orchidaceae', 'hasImage': True}),
                'limit': limit,
                'offset': self.offset
            }
            
            response = self.session.get(url, params=params, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            
            items = data.get('items', [])
            
            # Update offset
            self.offset += limit
            if not items:
                self.offset = 0
            
            # Parse results
            images = []
            for item in items:
                record = item.get('data', {})
                indexTerms = item.get('indexTerms', {})
                
                media_records = indexTerms.get('mediarecords', [])
                if not media_records:
                    continue
                
                # Get media URL
                for media_id in media_records[:1]:  # Just first image
                    media_url = f"https://api.idigbio.org/v2/media/{media_id}?size=fullsize"
                    
                    # Parse genus/species
                    sci_name = record.get('dwc:scientificName', '')
                    parts = sci_name.split()
                    genus = parts[0] if parts else None
                    species = parts[1] if len(parts) > 1 else None
                    
                    images.append({
                        'source': 'iDigBio',
                        'image_url': media_url,
                        'genus': genus or record.get('dwc:genus'),
                        'species': species or record.get('dwc:specificEpithet'),
                        'scientific_name': sci_name,
                        'latitude': indexTerms.get('geopoint', {}).get('lat'),
                        'longitude': indexTerms.get('geopoint', {}).get('lon'),
                        'country': record.get('dwc:country'),
                        'state_province': record.get('dwc:stateProvince'),
                        'locality': record.get('dwc:locality'),
                        'institution': record.get('dwc:institutionCode'),
                        'catalog_number': record.get('dwc:catalogNumber')
                    })
            
            return images
            
        except Exception as e:
            logger.warning(f"iDigBio fetch error: {e}")
            self.offset = 0
            return []


class ALAAdapter(SourceAdapter):
    """Atlas of Living Australia data source adapter."""
    
    name = "ALA"
    base_url = "https://biocache-ws.ala.org.au/ws"
    
    def __init__(self):
        super().__init__()
        self.start_index = 0
    
    def fetch_batch(self, offset=0, limit=100):
        """Fetch orchid images from ALA."""
        try:
            url = f"{self.base_url}/occurrences/search"
            params = {
                'q': 'family:Orchidaceae',
                'fq': 'multimedia:Image',
                'pageSize': limit,
                'startIndex': self.start_index,
                'facet': 'false'
            }
            
            response = self.session.get(url, params=params, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            
            occurrences = data.get('occurrences', [])
            total = data.get('totalRecords', 0)
            
            # Update offset
            self.start_index += limit
            if self.start_index >= total or not occurrences:
                self.start_index = 0
            
            # Parse results
            images = []
            for occ in occurrences:
                image_url = occ.get('largeImageUrl') or occ.get('smallImageUrl')
                if not image_url:
                    continue
                
                images.append({
                    'source': 'ALA',
                    'image_url': image_url,
                    'genus': occ.get('genus'),
                    'species': occ.get('species'),
                    'scientific_name': occ.get('scientificName'),
                    'latitude': occ.get('decimalLatitude'),
                    'longitude': occ.get('decimalLongitude'),
                    'country': 'Australia',
                    'state_province': occ.get('stateProvince'),
                    'locality': occ.get('locality'),
                    'observation_date': occ.get('eventDate'),
                    'institution': occ.get('institutionCode'),
                    'license': occ.get('license')
                })
            
            return images
            
        except Exception as e:
            logger.warning(f"ALA fetch error: {e}")
            self.start_index = 0
            return []


class FluidHarvester:
    """Main harvester that dynamically switches between sources."""
    
    def __init__(self):
        self.taxonomy_cache = TaxonomyCache()
        self.adapters = {
            'GBIF': GBIFAdapter(),
            'iNaturalist': INaturalistAdapter(),
            'iDigBio': IDigBioAdapter(),
            'ALA': ALAAdapter()
        }
        
        # Performance tracking
        self.source_stats = defaultdict(lambda: {
            'fetched': 0,
            'saved': 0,
            'errors': 0,
            'last_fetch_time': 0,
            'images_per_second': 0
        })
        
        # Track seen URLs to avoid duplicates
        self.seen_urls = set()
        self.load_recent_urls()
        
        # Current source
        self.current_source = 'GBIF'
        self.last_source_switch = time.time()
        
        # Stats
        self.total_saved = 0
        self.start_time = time.time()
    
    def load_recent_urls(self):
        """Load recently seen URLs to avoid duplicates."""
        logger.info("Loading recent URLs from database...")
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT image_url FROM orchid_images 
                WHERE created_at > NOW() - INTERVAL '24 hours'
            """)
            self.seen_urls = {row[0] for row in cur.fetchall()}
            logger.info(f"Loaded {len(self.seen_urls)} recent URLs")
        finally:
            release_connection(conn)
    
    def get_best_source(self):
        """Determine which source is performing best."""
        if time.time() - self.last_source_switch < MIN_SOURCE_SWITCH_INTERVAL:
            return self.current_source
        
        # Calculate performance scores
        scores = {}
        for source, stats in self.source_stats.items():
            if stats['fetched'] > 0:
                # Score based on save rate and speed
                save_rate = stats['saved'] / max(stats['fetched'], 1)
                speed = stats['images_per_second']
                error_penalty = 1 - (stats['errors'] / max(stats['fetched'], 1))
                scores[source] = save_rate * speed * error_penalty
            else:
                # Give unexplored sources a chance
                scores[source] = 0.5
        
        if scores:
            best = max(scores, key=lambda x: scores[x])
            if best != self.current_source:
                logger.info(f"Switching from {self.current_source} to {best} (score: {scores[best]:.2f})")
                self.current_source = best
                self.last_source_switch = time.time()
        
        return self.current_source
    
    def save_batch(self, images):
        """Save a batch of images to the database."""
        if not images:
            return 0
        
        conn = get_connection()
        saved = 0
        
        try:
            cur = conn.cursor()
            
            for img in images:
                # Skip if already seen
                if img['image_url'] in self.seen_urls:
                    continue
                
                # Validate taxonomy (uses cache, no DB call)
                taxonomy_id = self.taxonomy_cache.validate_and_get_id(
                    img.get('genus'),
                    img.get('species')
                )
                
                if not taxonomy_id:
                    continue
                
                # Parse coordinates
                try:
                    lat = float(img.get('latitude')) if img.get('latitude') else None
                    lon = float(img.get('longitude')) if img.get('longitude') else None
                except (ValueError, TypeError):
                    lat, lon = None, None
                
                # Insert image
                try:
                    cur.execute("""
                        INSERT INTO orchid_images (
                            taxonomy_id, image_url, image_source, gbif_occurrence_key,
                            latitude, longitude, country, country_code, state_province,
                            locality, observation_date, observer_name, institution_code,
                            image_license, image_rights_holder, created_at
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
                        )
                        ON CONFLICT (image_url) DO NOTHING
                    """, (
                        taxonomy_id,
                        img['image_url'],
                        img['source'],
                        img.get('gbif_key'),
                        lat,
                        lon,
                        img.get('country'),
                        img.get('country_code'),
                        img.get('state_province'),
                        img.get('locality'),
                        img.get('observation_date'),
                        img.get('observer'),
                        img.get('institution'),
                        img.get('license'),
                        img.get('rights_holder')
                    ))
                    
                    if cur.rowcount > 0:
                        saved += 1
                        self.seen_urls.add(img['image_url'])
                        
                except psycopg2.Error as e:
                    logger.debug(f"Insert error: {e}")
                    conn.rollback()
                    continue
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"Batch save error: {e}")
            conn.rollback()
        finally:
            release_connection(conn)
        
        return saved
    
    def run_cycle(self):
        """Run one harvesting cycle."""
        source = self.get_best_source()
        adapter = self.adapters[source]
        
        start = time.time()
        
        # Fetch batch
        images = adapter.fetch_batch(limit=BATCH_SIZE)
        fetch_time = time.time() - start
        
        # Update stats
        self.source_stats[source]['fetched'] += len(images)
        self.source_stats[source]['last_fetch_time'] = fetch_time
        
        if not images:
            self.source_stats[source]['errors'] += 1
            return 0
        
        # Save batch
        saved = self.save_batch(images)
        
        total_time = time.time() - start
        self.source_stats[source]['saved'] += saved
        self.source_stats[source]['images_per_second'] = saved / max(total_time, 0.1)
        
        self.total_saved += saved
        
        return saved
    
    def run(self):
        """Main harvesting loop."""
        logger.info(f"Starting Fluid Harvester {WORKER_ID}")
        logger.info(f"Sources: {list(self.adapters.keys())}")
        
        # Initialize taxonomy cache
        self.taxonomy_cache.refresh()
        
        cycle = 0
        last_status = time.time()
        
        while True:
            try:
                cycle += 1
                saved = self.run_cycle()
                
                # Log status every 60 seconds
                if time.time() - last_status > 60:
                    elapsed = time.time() - self.start_time
                    rate = self.total_saved / (elapsed / 3600)
                    
                    logger.info(f"=== STATUS ===")
                    logger.info(f"Total saved: {self.total_saved:,} images")
                    logger.info(f"Rate: {rate:.0f} images/hour")
                    logger.info(f"Current source: {self.current_source}")
                    
                    for source, stats in self.source_stats.items():
                        if stats['fetched'] > 0:
                            logger.info(f"  {source}: {stats['saved']}/{stats['fetched']} saved ({stats['images_per_second']:.1f}/sec)")
                    
                    last_status = time.time()
                
                # Small delay between cycles
                time.sleep(0.1)
                
            except KeyboardInterrupt:
                logger.info("Shutting down...")
                break
            except Exception as e:
                logger.error(f"Cycle error: {e}")
                time.sleep(5)


def main():
    harvester = FluidHarvester()
    harvester.run()


if __name__ == '__main__':
    main()
