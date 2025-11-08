#!/usr/bin/env python3
"""
Comprehensive Trait Data Enrichment System
==========================================
Captures COMPLETE structured trait data from GBIF + iNaturalist

GBIF Data Captured:
- Distribution geography (countries, regions)
- Elevation range (min/max meters)
- Occurrence coordinates  
- Basis of record
- Dataset information

iNaturalist Data Captured:
- Observation photos (URLs, licenses)
- Phenology (flowering times)
- Conservation status
- Community identification data
"""

import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor, Json
import requests

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ComprehensiveGBIFEnricher:
    """Enhanced GBIF integration capturing ALL distribution and occurrence data"""
    
    def __init__(self):
        self.base_url = "https://api.gbif.org/v1"
        
    def get_comprehensive_species_data(self, scientific_name: str) -> Optional[Dict]:
        """Get COMPLETE GBIF data including distribution and elevation"""
        try:
            # Match species
            response = requests.get(
                f"{self.base_url}/species/match",
                params={'name': scientific_name, 'verbose': True},
                timeout=10
            )
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            species_key = data.get('usageKey')
            
            if not species_key:
                return None
            
            # Get occurrence data with distribution
            occ_response = requests.get(
                f"{self.base_url}/occurrence/search",
                params={
                    'taxonKey': species_key,
                    'limit': 100,  # Get sample occurrences for distribution analysis
                    'hasCoordinate': True
                },
                timeout=15
            )
            
            distribution_data = {
                'countries': [],
                'elevation_range': {'min': None, 'max': None},
                'coordinates': [],
                'basis_of_record': [],
                'occurrence_count': 0
            }
            
            if occ_response.status_code == 200:
                occ_data = occ_response.json()
                distribution_data['occurrence_count'] = occ_data.get('count', 0)
                
                # Extract distribution details
                countries = set()
                elevations = []
                bases = set()
                
                for occurrence in occ_data.get('results', []):
                    # Countries
                    if occurrence.get('country'):
                        countries.add(occurrence['country'])
                    
                    # Elevation
                    if occurrence.get('elevation'):
                        elevations.append(occurrence['elevation'])
                    
                    # Coordinates (sample)
                    if len(distribution_data['coordinates']) < 10:
                        if occurrence.get('decimalLatitude') and occurrence.get('decimalLongitude'):
                            distribution_data['coordinates'].append({
                                'lat': occurrence['decimalLatitude'],
                                'lon': occurrence['decimalLongitude'],
                                'country': occurrence.get('country'),
                                'locality': occurrence.get('locality')
                            })
                    
                    # Basis of record
                    if occurrence.get('basisOfRecord'):
                        bases.add(occurrence['basisOfRecord'])
                
                distribution_data['countries'] = sorted(list(countries))
                distribution_data['basis_of_record'] = sorted(list(bases))
                
                if elevations:
                    distribution_data['elevation_range'] = {
                        'min': min(elevations),
                        'max': max(elevations)
                    }
            
            return {
                'gbif_species_key': species_key,
                'scientific_name': data.get('scientificName'),
                'taxonomic_status': data.get('taxonomicStatus'),
                'kingdom': data.get('kingdom'),
                'family': data.get('family'),
                'genus': data.get('genus'),
                'distribution': distribution_data
            }
            
        except Exception as e:
            logger.error(f"GBIF error for {scientific_name}: {e}")
            return None


class ComprehensiveiNatEnricher:
    """Enhanced iNaturalist integration capturing ALL observation and phenology data"""
    
    def __init__(self):
        self.base_url = "https://api.inaturalist.org/v1"
        
    def get_comprehensive_taxon_data(self, scientific_name: str) -> Optional[Dict]:
        """Get COMPLETE iNaturalist data including photos and phenology"""
        try:
            # Get taxon
            response = requests.get(
                f"{self.base_url}/taxa",
                params={'q': scientific_name, 'rank': 'species'},
                timeout=10
            )
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            results = data.get('results', [])
            
            if not results:
                return None
            
            taxon = results[0]
            taxon_id = taxon.get('id')
            
            # Get observations for phenology
            obs_response = requests.get(
                f"{self.base_url}/observations",
                params={
                    'taxon_id': taxon_id,
                    'per_page': 50,
                    'order_by': 'votes',
                    'photos': True
                },
                timeout=15
            )
            
            observation_data = {
                'total_observations': 0,
                'photos': [],
                'phenology': {
                    'flowering_months': [],
                    'observed_in_countries': []
                },
                'quality_grades': {}
            }
            
            if obs_response.status_code == 200:
                obs_data = obs_response.json()
                observation_data['total_observations'] = obs_data.get('total_results', 0)
                
                # Extract photos and phenology
                months = []
                countries = set()
                quality = {}
                
                for obs in obs_data.get('results', []):
                    # Photos
                    if len(observation_data['photos']) < 20:  # Limit to 20 photos
                        for photo in obs.get('photos', []):
                            if len(observation_data['photos']) >= 20:
                                break
                            observation_data['photos'].append({
                                'url': photo.get('url'),
                                'attribution': photo.get('attribution'),
                                'license_code': photo.get('license_code')
                            })
                    
                    # Phenology - flowering months
                    if obs.get('observed_on'):
                        try:
                            month = int(obs['observed_on'].split('-')[1])
                            months.append(month)
                        except:
                            pass
                    
                    # Geographic distribution
                    if obs.get('place_guess'):
                        countries.add(obs['place_guess'].split(',')[0])
                    
                    # Quality grades
                    qg = obs.get('quality_grade', 'unknown')
                    quality[qg] = quality.get(qg, 0) + 1
                
                # Calculate phenology
                if months:
                    from collections import Counter
                    month_counts = Counter(months)
                    observation_data['phenology']['flowering_months'] = [
                        {'month': m, 'count': c} 
                        for m, c in sorted(month_counts.most_common())
                    ]
                
                observation_data['phenology']['observed_in_countries'] = sorted(list(countries))[:10]
                observation_data['quality_grades'] = quality
            
            # Get FULL conservation_status object (not just status label)
            conservation_obj = taxon.get('conservation_status')  # This is the complete object
            
            return {
                'inaturalist_taxon_id': taxon_id,
                'wikipedia_url': taxon.get('wikipedia_url'),
                'conservation_status_full': conservation_obj,  # Store complete conservation object
                'iconic_taxon': taxon.get('iconic_taxon_name'),
                'observations': observation_data
            }
            
        except Exception as e:
            logger.error(f"iNaturalist error for {scientific_name}: {e}")
            return None


class ComprehensiveEnrichment:
    """Comprehensive enrichment system storing ALL structured data"""
    
    def __init__(self):
        self.db_url = os.environ.get('DATABASE_URL')
        self.gbif = ComprehensiveGBIFEnricher()
        self.inat = ComprehensiveiNatEnricher()
        self.batch_size = 50
        self.progress_file = 'comprehensive_enrichment_progress.json'
        
    def get_progress(self) -> Dict:
        """Load progress"""
        if os.path.exists(self.progress_file):
            with open(self.progress_file, 'r') as f:
                return json.load(f)
        return {
            'last_processed_id': 0,
            'total_processed': 0,
            'gbif_enriched': 0,
            'inat_enriched': 0,
            'errors': 0,
            'started_at': datetime.now().isoformat()
        }
    
    def save_progress(self, progress: Dict):
        """Save progress"""
        progress['last_updated'] = datetime.now().isoformat()
        with open(self.progress_file, 'w') as f:
            json.dump(progress, f, indent=2)
    
    def get_orchids_to_enrich(self, last_id: int, limit: int) -> List[Dict]:
        """Get orchids to enrich"""
        conn = psycopg2.connect(self.db_url)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT id, scientific_name
            FROM orchid_record
            WHERE id > %s
            AND scientific_name IS NOT NULL
            AND scientific_name != ''
            ORDER BY id ASC
            LIMIT %s
        """, (last_id, limit))
        
        orchids = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return [dict(o) for o in orchids]
    
    def update_orchid_comprehensive(self, orchid_id: int, gbif_data: Optional[Dict], inat_data: Optional[Dict]) -> bool:
        """Update with COMPREHENSIVE structured data"""
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            
            updates = []
            params = []
            
            if gbif_data:
                dist = gbif_data.get('distribution', {})
                
                updates.extend([
                    "gbif_species_key = %s",
                    "taxonomic_status = %s",
                    "gbif_distribution = %s",
                    "elevation_m = %s",
                    "gbif_last_synced_at = NOW()"
                ])
                
                # Store elevation (use max as representative)
                elevation = None
                if dist.get('elevation_range', {}).get('max'):
                    elevation = dist['elevation_range']['max']
                
                params.extend([
                    gbif_data.get('gbif_species_key'),
                    gbif_data.get('taxonomic_status'),
                    Json(dist),  # Store full distribution as JSONB
                    elevation
                ])
            
            if inat_data:
                obs = inat_data.get('observations', {})
                
                updates.extend([
                    "inaturalist_observation_id = %s",
                    "external_images = %s",
                    "trait_confidence = %s",
                    "data_origin = %s",
                    "inaturalist_last_updated = NOW()"
                ])
                
                # Store ALL iNaturalist data as structured JSONB
                
                # Photos with full metadata
                photos_json = obs.get('photos', [])
                
                # Store COMPLETE conservation_status object (status, authority, place, assessment date, etc.)
                # This is the full object from iNaturalist taxon endpoint
                conservation_full = inat_data.get('conservation_status_full')  # Complete conservation metadata
                
                trait_data = {
                    'phenology': obs.get('phenology', {}),
                    'quality_grades': obs.get('quality_grades', {}),
                    'total_observations': obs.get('total_observations', 0),
                    'conservation_status': conservation_full,  # Store FULL conservation object with all metadata
                    'wikipedia_url': inat_data.get('wikipedia_url')
                }
                
                # Source tracking in data_origin JSONB
                origin_data = {
                    'inaturalist_taxon_id': inat_data.get('inaturalist_taxon_id'),
                    'last_updated': datetime.now().isoformat(),
                    'source': 'iNaturalist API v1'
                }
                
                params.extend([
                    inat_data.get('inaturalist_taxon_id'),
                    Json(photos_json) if photos_json else None,
                    Json(trait_data),  # Store phenology + quality grades
                    Json(origin_data)  # Store source metadata
                ])
            
            if updates:
                updates.append("updated_at = NOW()")
                params.append(orchid_id)
                
                query = f"UPDATE orchid_record SET {', '.join(updates)} WHERE id = %s"
                cursor.execute(query, params)
            
            conn.commit()
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Update error for orchid {orchid_id}: {e}")
            return False
    
    def enrich_batch(self, orchids: List[Dict], progress: Dict) -> Dict:
        """Enrich batch with comprehensive data"""
        
        for orchid in orchids:
            orchid_id = orchid['id']
            scientific_name = orchid['scientific_name']
            
            try:
                logger.info(f"🔄 {scientific_name} (ID: {orchid_id})")
                
                # Get comprehensive GBIF data
                gbif_data = self.gbif.get_comprehensive_species_data(scientific_name)
                if gbif_data:
                    dist = gbif_data.get('distribution', {})
                    progress['gbif_enriched'] += 1
                    logger.info(f"  ✅ GBIF: {dist.get('occurrence_count', 0)} occ, {len(dist.get('countries', []))} countries, elev: {dist.get('elevation_range', {})}")
                
                time.sleep(0.5)
                
                # Get comprehensive iNat data  
                inat_data = self.inat.get_comprehensive_taxon_data(scientific_name)
                if inat_data:
                    obs = inat_data.get('observations', {})
                    progress['inat_enriched'] += 1
                    logger.info(f"  ✅ iNat: {obs.get('total_observations', 0)} obs, {len(obs.get('photos', []))} photos")
                
                # Update with comprehensive data
                if gbif_data or inat_data:
                    self.update_orchid_comprehensive(orchid_id, gbif_data, inat_data)
                
                progress['total_processed'] += 1
                progress['last_processed_id'] = orchid_id
                
                if progress['total_processed'] % 10 == 0:
                    self.save_progress(progress)
                    logger.info(f"📊 Progress: {progress['total_processed']} processed, {progress['gbif_enriched']} GBIF, {progress['inat_enriched']} iNat")
                
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ Error: {e}")
                progress['errors'] += 1
                progress['last_processed_id'] = orchid_id
                progress['total_processed'] += 1
        
        return progress
    
    def run(self):
        """Run comprehensive enrichment"""
        
        logger.info("=" * 80)
        logger.info("🚀 COMPREHENSIVE TRAIT DATA ENRICHMENT")
        logger.info("   Capturing: Distribution, Elevation, Photos, Phenology")
        logger.info("=" * 80)
        
        progress = self.get_progress()
        logger.info(f"📊 Resuming from ID: {progress['last_processed_id']}")
        
        conn = psycopg2.connect(self.db_url)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM orchid_record WHERE scientific_name IS NOT NULL")
        result = cursor.fetchone()
        total = result[0] if result else 0
        cursor.close()
        conn.close()
        
        logger.info(f"📊 Total orchids: {total}")
        
        while True:
            orchids = self.get_orchids_to_enrich(progress['last_processed_id'], self.batch_size)
            
            if not orchids:
                logger.info("✅ Complete!")
                break
            
            logger.info(f"📦 Processing batch of {len(orchids)}...")
            progress = self.enrich_batch(orchids, progress)
            self.save_progress(progress)
        
        logger.info("=" * 80)
        logger.info("🎉 ENRICHMENT COMPLETE!")
        logger.info(f"✅ GBIF: {progress['gbif_enriched']} (distribution, elevation)")
        logger.info(f"✅ iNat: {progress['inat_enriched']} (photos, phenology)")
        logger.info(f"📊 Total: {progress['total_processed']}")
        logger.info("=" * 80)
        
        return progress


def main():
    enrichment = ComprehensiveEnrichment()
    enrichment.run()


if __name__ == "__main__":
    main()
