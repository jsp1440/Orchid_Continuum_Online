#!/usr/bin/env python3
"""
iNaturalist COMPLETE Orchid Data Downloader
Captures 52+ fields: taxonomy, ecology, habitat, geography, metadata
Target: 100,000+ images with full ecological and taxonomic data
"""

import requests
import json
import time
import os
from datetime import datetime
import csv

class iNaturalistCompleteDownloader:
    def __init__(self):
        self.base_url = "https://api.inaturalist.org/v1"
        self.output_dir = "inaturalist_complete"
        self.csv_file = "inaturalist_orchids_52_fields.csv"
        self.downloaded_count = 0
        self.species_set = set()
        
        os.makedirs(self.output_dir, exist_ok=True)
        self.init_csv()
    
    def init_csv(self):
        """Initialize CSV with 52+ comprehensive fields"""
        with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                # OBSERVATION IDENTIFIERS
                'observation_id', 'uuid', 'observation_url', 'created_at', 'updated_at',
                
                # TAXONOMIC HIERARCHY (Kingdom → Species)
                'kingdom', 'phylum', 'class', 'order', 'family', 'subfamily', 'tribe',
                'genus', 'species', 'subspecies', 'variety',
                'taxon_id', 'taxon_rank', 'taxon_rank_level', 'ancestry', 'common_name',
                
                # ECOLOGICAL STATUS
                'native', 'introduced', 'endemic', 'threatened', 'extinct', 'captive',
                
                # GEOGRAPHIC DATA
                'latitude', 'longitude', 'positional_accuracy', 'location_description',
                'country', 'state_province', 'county', 'place_guess',
                'elevation_meters', 'coordinate_uncertainty',
                
                # OBSERVATION METADATA
                'observed_on', 'observed_time', 'time_zone', 'quality_grade',
                'num_identification_agreements', 'num_identification_disagreements',
                'identifications_count', 'community_taxon_match',
                
                # OBSERVER DATA
                'observer_username', 'observer_id',
                
                # PHOTO DATA
                'photo_count', 'image_url', 'image_filename', 'photo_license',
                'photo_attribution',
                
                # EXTERNAL LINKS
                'wikipedia_url', 'observations_count_species',
                
                # HABITAT/ECOLOGY NOTES
                'description', 'tags', 'annotations'
            ])
        print(f"✅ Created {self.csv_file} with 52+ fields")
    
    def parse_taxonomy(self, taxon):
        """Extract complete taxonomic hierarchy"""
        taxonomy = {
            'kingdom': '', 'phylum': '', 'class': '', 'order': '',
            'family': '', 'subfamily': '', 'tribe': '', 'genus': '',
            'species': '', 'subspecies': '', 'variety': ''
        }
        
        # Get ancestors for hierarchy
        ancestors = taxon.get('ancestors', [])
        for ancestor in ancestors:
            rank = ancestor.get('rank', '').lower()
            name = ancestor.get('name', '')
            if rank in taxonomy:
                taxonomy[rank] = name
        
        # Current taxon
        current_rank = taxon.get('rank', '').lower()
        current_name = taxon.get('name', '')
        if current_rank in taxonomy:
            taxonomy[current_rank] = current_name
        
        return taxonomy
    
    def get_place_names(self, obs):
        """Extract geographic place names"""
        place_guess = obs.get('place_guess', '')
        parts = [p.strip() for p in place_guess.split(',')]
        
        country = parts[-1] if len(parts) > 0 else ''
        state = parts[-2] if len(parts) > 1 else ''
        county = parts[-3] if len(parts) > 2 else ''
        
        return country, state, county
    
    def search_orchid_observations(self, page=1, per_page=200):
        """Search for orchid observations with all data"""
        params = {
            'taxon_id': 47217,  # Orchidaceae family
            'quality_grade': 'research',
            'photos': 'true',
            'license': 'cc-by,cc-by-nc,cc-by-sa,cc-by-nd,cc0',
            'per_page': per_page,
            'page': page,
            'order': 'desc',
            'order_by': 'created_at'
        }
        
        response = requests.get(f"{self.base_url}/observations", params=params)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ API Error {response.status_code}")
            return None
    
    def download_image(self, url, filename):
        """Download single image"""
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                filepath = os.path.join(self.output_dir, filename)
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                return True
            return False
        except Exception as e:
            print(f"  ⚠️ Download error: {e}")
            return False
    
    def process_observation(self, obs):
        """Process observation with ALL 52+ fields"""
        obs_id = obs['id']
        uuid = obs.get('uuid', '')
        obs_url = obs.get('uri', '')
        
        # Timestamps
        created_at = obs.get('created_at', '')
        updated_at = obs.get('updated_at', '')
        
        # Get taxon info
        taxon = obs.get('taxon', {})
        if not taxon or taxon.get('rank') != 'species':
            return 0  # Only species-level
        
        # Parse full taxonomic hierarchy
        taxonomy = self.parse_taxonomy(taxon)
        
        # Taxon metadata
        taxon_id = taxon.get('id', '')
        taxon_rank = taxon.get('rank', '')
        taxon_rank_level = taxon.get('rank_level', '')
        ancestry = taxon.get('ancestry', '')
        common_name = taxon.get('preferred_common_name', '')
        
        # Ecological status
        native = taxon.get('native', '')
        introduced = taxon.get('introduced', '')
        endemic = taxon.get('endemic', '')
        threatened = taxon.get('threatened', '')
        extinct = taxon.get('extinct', '')
        captive = obs.get('captive', False)
        
        # Geographic data
        geojson = obs.get('geojson', {})
        coords = geojson.get('coordinates', [None, None])
        lon, lat = coords[0], coords[1]
        
        positional_accuracy = obs.get('positional_accuracy', '')
        public_accuracy = obs.get('public_positional_accuracy', '')
        location_desc = obs.get('place_guess', '')
        country, state, county = self.get_place_names(obs)
        
        # Observation metadata
        observed_on = obs.get('observed_on', '')
        time_observed = obs.get('time_observed_at', '')
        time_zone = obs.get('observed_time_zone', '')
        quality_grade = obs.get('quality_grade', '')
        
        # Community identification data
        num_agreements = obs.get('num_identification_agreements', 0)
        num_disagreements = obs.get('identification_disagreements_count', 0)
        idents_count = len(obs.get('identifications', []))
        most_agree = obs.get('identifications_most_agree', False)
        
        # Observer
        user = obs.get('user', {})
        observer_username = user.get('login', '')
        observer_id = user.get('id', '')
        
        # Description and notes
        description = obs.get('description', '')
        tags = ','.join(obs.get('tags', []))
        annotations = json.dumps(obs.get('annotations', []))
        
        # Wikipedia
        wikipedia_url = taxon.get('wikipedia_url', '')
        obs_count = taxon.get('observations_count', 0)
        
        # Process photos
        photos = obs.get('photos', [])
        images_downloaded = 0
        
        for idx, photo in enumerate(photos):
            license_code = photo.get('license_code', '')
            attribution = photo.get('attribution', '')
            image_url = photo.get('url', '').replace('square', 'original')
            
            if not image_url:
                continue
            
            # Create filename
            safe_species = taxonomy['species'].replace(' ', '_').replace('/', '-')
            filename = f"inat_{obs_id}_{safe_species}_{idx+1}.jpg"
            
            # Download image
            print(f"  📥 {taxonomy['species']} (obs {obs_id}, photo {idx+1}/{len(photos)})")
            
            if self.download_image(image_url, filename):
                # Write complete metadata to CSV
                with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        # OBSERVATION IDENTIFIERS
                        obs_id, uuid, obs_url, created_at, updated_at,
                        
                        # TAXONOMIC HIERARCHY
                        taxonomy['kingdom'], taxonomy['phylum'], taxonomy['class'],
                        taxonomy['order'], taxonomy['family'], taxonomy['subfamily'],
                        taxonomy['tribe'], taxonomy['genus'], taxonomy['species'],
                        taxonomy['subspecies'], taxonomy['variety'],
                        taxon_id, taxon_rank, taxon_rank_level, ancestry, common_name,
                        
                        # ECOLOGICAL STATUS
                        native, introduced, endemic, threatened, extinct, captive,
                        
                        # GEOGRAPHIC DATA
                        lat, lon, positional_accuracy, location_desc,
                        country, state, county, location_desc,
                        '', public_accuracy,  # elevation placeholder, uncertainty
                        
                        # OBSERVATION METADATA
                        observed_on, time_observed, time_zone, quality_grade,
                        num_agreements, num_disagreements, idents_count, most_agree,
                        
                        # OBSERVER DATA
                        observer_username, observer_id,
                        
                        # PHOTO DATA
                        len(photos), image_url, filename, license_code, attribution,
                        
                        # EXTERNAL LINKS
                        wikipedia_url, obs_count,
                        
                        # HABITAT/ECOLOGY NOTES
                        description, tags, annotations
                    ])
                
                images_downloaded += 1
                self.downloaded_count += 1
                self.species_set.add(taxonomy['species'])
                
                time.sleep(0.1)  # Rate limiting
        
        return images_downloaded
    
    def download_batch(self, max_pages=500, start_page=1):
        """Download orchid observations with complete data"""
        print("\n" + "="*70)
        print("🌺 iNaturalist COMPLETE Orchid Data Downloader")
        print("="*70)
        print(f"📊 52+ fields: taxonomy, ecology, habitat, geography, metadata")
        print(f"🎯 Target: {max_pages} pages × 200 obs = {max_pages * 200:,} observations")
        print(f"🚀 Starting from page {start_page}")
        print("="*70 + "\n")
        
        for page in range(start_page, start_page + max_pages):
            print(f"\n📄 Processing page {page}/{start_page + max_pages - 1}...")
            
            data = self.search_orchid_observations(page=page, per_page=200)
            
            if not data:
                print("❌ Failed to fetch data. Stopping.")
                break
            
            results = data.get('results', [])
            total_results = data.get('total_results', 0)
            
            if not results:
                print("✅ No more results. Download complete!")
                break
            
            print(f"  Found {len(results)} observations (total available: {total_results:,})")
            
            page_images = 0
            for obs in results:
                images = self.process_observation(obs)
                page_images += images
            
            print(f"\n  ✅ Page {page}: {page_images} images")
            print(f"  📊 Total: {self.downloaded_count:,} images, {len(self.species_set):,} species")
            
            time.sleep(1)
            
            if page % 10 == 0:
                print(f"\n💾 Checkpoint: Resume from page {page + 1} if needed")
        
        print("\n" + "="*70)
        print("🎉 Download Complete!")
        print("="*70)
        print(f"✅ Images: {self.downloaded_count:,}")
        print(f"✅ Species: {len(self.species_set):,}")
        print(f"✅ Data: {self.output_dir}/")
        print(f"✅ CSV: {self.csv_file} (52+ fields)")
        print("="*70 + "\n")


if __name__ == "__main__":
    downloader = iNaturalistCompleteDownloader()
    
    # TEST: 1 page first
    downloader.download_batch(max_pages=1, start_page=1)
    
    # FULL DOWNLOAD: Uncomment after testing
    # downloader.download_batch(max_pages=500, start_page=1)
