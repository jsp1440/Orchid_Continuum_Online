#!/usr/bin/env python3
"""
iNaturalist Orchid Image Downloader
Downloads CC-licensed orchid photos from iNaturalist API
Target: 100,000+ images covering 15,000-20,000 species
"""

import requests
import json
import time
import os
from datetime import datetime
from urllib.parse import urlparse
import csv

class iNaturalistDownloader:
    def __init__(self):
        self.base_url = "https://api.inaturalist.org/v1"
        self.output_dir = "inaturalist_downloads"
        self.csv_file = "inaturalist_orchid_metadata.csv"
        self.downloaded_count = 0
        self.species_set = set()
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize CSV
        self.init_csv()
    
    def init_csv(self):
        """Initialize CSV file with headers"""
        with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'observation_id', 'species', 'genus', 'family', 
                'common_name', 'quality_grade', 'license',
                'image_url', 'image_filename', 'latitude', 'longitude',
                'location', 'country', 'observed_on', 'user',
                'num_identification_agreements', 'captive'
            ])
        print(f"✅ Created {self.csv_file}")
    
    def search_orchid_observations(self, page=1, per_page=200):
        """
        Search for orchid observations with photos
        
        Quality filters:
        - research: community-identified to species level
        - photos: true (only observations with photos)
        - license: CC-BY, CC-BY-NC, CC0 (allows use with attribution)
        - iconic_taxa: Plantae
        - taxon_id: 47170 (Orchidaceae family)
        """
        params = {
            'taxon_id': 47217,  # Orchidaceae family (CORRECTED)
            'quality_grade': 'research',  # Community-verified
            'photos': 'true',
            'license': 'cc-by,cc-by-nc,cc-by-sa,cc-by-nd,cc0',  # Creative Commons only
            'per_page': per_page,
            'page': page,
            'order': 'desc',
            'order_by': 'created_at'
        }
        
        response = requests.get(f"{self.base_url}/observations", params=params)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ API Error {response.status_code}: {response.text}")
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
        """Process single observation and download images"""
        obs_id = obs['id']
        
        # Get taxonomic info
        taxon = obs.get('taxon', {})
        species = taxon.get('name', 'Unknown')
        rank = taxon.get('rank', '')
        
        # Only process species-level identifications
        if rank != 'species':
            return 0
        
        # Get genus and family
        ancestors = taxon.get('ancestors', [])
        genus = None
        family = None
        for ancestor in ancestors:
            if ancestor.get('rank') == 'genus':
                genus = ancestor.get('name')
            if ancestor.get('rank') == 'family':
                family = ancestor.get('name')
        
        # Get location info
        lat = obs.get('geojson', {}).get('coordinates', [None, None])[1]
        lon = obs.get('geojson', {}).get('coordinates', [None, None])[0]
        location = obs.get('place_guess', '')
        
        # Get observation metadata
        quality = obs.get('quality_grade', '')
        observed_on = obs.get('observed_on', '')
        user = obs.get('user', {}).get('login', '')
        captive = obs.get('captive', False)
        num_agreements = obs.get('num_identification_agreements', 0)
        
        # Process photos
        photos = obs.get('photos', [])
        images_downloaded = 0
        
        for idx, photo in enumerate(photos):
            # Get license
            license_code = photo.get('license_code', 'unknown')
            
            # Get large image URL (original or large)
            image_url = photo.get('url', '').replace('square', 'original')
            if not image_url:
                continue
            
            # Create filename
            safe_species = species.replace(' ', '_').replace('/', '-')
            filename = f"inat_{obs_id}_{safe_species}_{idx+1}.jpg"
            
            # Download image
            print(f"  📥 Downloading: {species} (obs {obs_id}, photo {idx+1}/{len(photos)})")
            if self.download_image(image_url, filename):
                # Write metadata to CSV
                with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        obs_id, species, genus, family,
                        taxon.get('preferred_common_name', ''),
                        quality, license_code, image_url, filename,
                        lat, lon, location, 
                        obs.get('place_guess', '').split(',')[-1].strip() if obs.get('place_guess') else '',
                        observed_on, user, num_agreements, captive
                    ])
                
                images_downloaded += 1
                self.downloaded_count += 1
                self.species_set.add(species)
                
                # Rate limiting
                time.sleep(0.1)
        
        return images_downloaded
    
    def download_batch(self, max_pages=500, start_page=1):
        """
        Download orchid observations in batches
        
        Args:
            max_pages: Maximum number of pages to download (200 obs/page = 100,000 images max)
            start_page: Starting page number (for resuming)
        """
        print("\n" + "="*70)
        print("🌺 iNaturalist Orchid Downloader")
        print("="*70)
        print(f"Target: {max_pages} pages × 200 observations = {max_pages * 200:,} max observations")
        print(f"Starting from page {start_page}")
        print("="*70 + "\n")
        
        for page in range(start_page, start_page + max_pages):
            print(f"\n📄 Processing page {page}/{start_page + max_pages - 1}...")
            
            # Fetch observations
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
            
            # Process each observation
            page_images = 0
            for obs in results:
                images = self.process_observation(obs)
                page_images += images
            
            print(f"\n  ✅ Page {page} complete: {page_images} images downloaded")
            print(f"  📊 Total progress: {self.downloaded_count:,} images, {len(self.species_set):,} species")
            
            # Rate limiting between pages
            time.sleep(1)
            
            # Save checkpoint every 10 pages
            if page % 10 == 0:
                print(f"\n💾 Checkpoint: {self.downloaded_count:,} images, {len(self.species_set):,} species")
                print(f"   Resume from page {page + 1} if needed")
        
        print("\n" + "="*70)
        print("🎉 Download Complete!")
        print("="*70)
        print(f"✅ Downloaded: {self.downloaded_count:,} images")
        print(f"✅ Species covered: {len(self.species_set):,}")
        print(f"✅ Images saved to: {self.output_dir}/")
        print(f"✅ Metadata saved to: {self.csv_file}")
        print("="*70 + "\n")


if __name__ == "__main__":
    downloader = iNaturalistDownloader()
    
    # Download configuration
    # Start small for testing, then scale up
    downloader.download_batch(
        max_pages=1,  # TEST: Just 1 page first (~200 observations)
        start_page=1
    )
    
    # After testing works, change to:
    # downloader.download_batch(max_pages=500, start_page=1)  # Full download
    
    # To resume from page 50: downloader.download_batch(max_pages=450, start_page=50)
