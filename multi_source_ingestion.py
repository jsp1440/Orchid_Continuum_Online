#!/usr/bin/env python3
"""
Multi-Source Orchid Image Ingestion System
Fetches from: GBIF, iNaturalist, POWO, Tropicos, Australian databases, EOL
Goal: 2,000,000 orchid images
"""
import os
import json
import time
import requests
import psycopg2
from datetime import datetime

# API Configuration
INATURALIST_API = "https://api.inaturalist.org/v1"
GBIF_API = "https://api.gbif.org/v1"
EOL_API = "https://eol.org/api"
TROPICOS_API = "https://services.tropicos.org/Name"
POWO_API = "https://powo.science.kew.org/api/1"

# Orchid family taxon IDs
ORCHIDACEAE_TAXON_IDS = {
    'inaturalist': 47170,  # Orchidaceae family ID on iNaturalist
    'gbif': 7505,  # Orchidaceae family key on GBIF
}

class MultiSourceIngestion:
    def __init__(self):
        self.db_conn = psycopg2.connect(os.environ['DATABASE_URL'])
        self.stats = {
            'inaturalist': 0,
            'gbif': 0,
            'eol': 0,
            'tropicos': 0,
            'powo': 0,
            'total': 0
        }
    
    def fetch_inaturalist_observations(self, page=1, per_page=200):
        """
        Fetch orchid observations with photos from iNaturalist
        Returns up to 200 observations per page (iNat limit)
        """
        print(f"\n📸 Fetching iNaturalist orchids (page {page})...")
        
        params = {
            'taxon_id': ORCHIDACEAE_TAXON_IDS['inaturalist'],
            'photos': 'true',
            'quality_grade': 'research',  # Only verified observations
            'page': page,
            'per_page': per_page,
            'order': 'desc',
            'order_by': 'created_at'
        }
        
        try:
            response = requests.get(
                f"{INATURALIST_API}/observations",
                params=params,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            observations = data.get('results', [])
            total_results = data.get('total_results', 0)
            
            print(f"✅ Found {len(observations)} observations (total available: {total_results:,})")
            return observations, total_results
        except Exception as e:
            print(f"❌ iNaturalist error: {e}")
            return [], 0
    
    def extract_inaturalist_images(self, observation):
        """Extract image URLs from iNaturalist observation"""
        images = []
        photos = observation.get('photos', [])
        taxon = observation.get('taxon', {})
        
        for photo in photos:
            images.append({
                'source': 'iNaturalist',
                'occurrence_key': str(observation.get('id')),
                'image_url': photo.get('url', '').replace('square', 'original'),  # Get full resolution
                'scientific_name': taxon.get('name', ''),
                'genus': taxon.get('name', '').split()[0] if taxon.get('name') else '',
                'species': taxon.get('name', '').split()[1] if len(taxon.get('name', '').split()) > 1 else '',
                'latitude': observation.get('location', '').split(',')[0] if observation.get('location') else None,
                'longitude': observation.get('location', '').split(',')[1] if observation.get('location') else None,
                'photographer': observation.get('user', {}).get('login', ''),
                'license': photo.get('license_code', 'CC-BY-NC'),
                'observed_on': observation.get('observed_on')
            })
        
        return images
    
    def fetch_gbif_genus(self, genus, limit=100):
        """Fetch GBIF occurrences for a specific genus"""
        print(f"\n🌍 Fetching GBIF: {genus}...")
        
        try:
            response = requests.get(
                f"{GBIF_API}/occurrence/search",
                params={
                    'genus': genus,
                    'mediaType': 'StillImage',
                    'hasCoordinate': 'true',
                    'limit': limit
                },
                timeout=30
            )
            response.raise_for_status()
            results = response.json().get('results', [])
            print(f"✅ Found {len(results)} GBIF occurrences")
            return results
        except Exception as e:
            print(f"❌ GBIF error: {e}")
            return []
    
    def insert_to_staging(self, records, source_table='staging_gbif_images'):
        """Insert records to staging table"""
        if not records:
            return 0
        
        cur = self.db_conn.cursor()
        inserted = 0
        
        for record in records:
            try:
                metadata = {
                    'scientific_name': record.get('scientific_name'),
                    'genus': record.get('genus'),
                    'species': record.get('species'),
                    'latitude': record.get('latitude'),
                    'longitude': record.get('longitude'),
                    'photographer': record.get('photographer'),
                    'source': record.get('source'),
                    'observed_on': record.get('observed_on')
                }
                
                cur.execute("""
                    INSERT INTO staging_gbif_images 
                    (occurrence_key, image_url, media_json, license, created_at)
                    SELECT %s, %s, %s, %s, %s
                    WHERE NOT EXISTS (
                        SELECT 1 FROM staging_gbif_images WHERE image_url = %s
                    )
                    AND NOT EXISTS (
                        SELECT 1 FROM orchid_images WHERE image_url = %s
                    )
                """, (
                    record.get('occurrence_key'),
                    record.get('image_url'),
                    json.dumps(metadata),
                    record.get('license'),
                    datetime.now(),
                    record.get('image_url'),
                    record.get('image_url')
                ))
                
                if cur.rowcount > 0:
                    inserted += 1
            except Exception as e:
                print(f"   ⚠️  Insert error: {e}")
                self.db_conn.rollback()
                continue
        
        self.db_conn.commit()
        return inserted
    
    def run_inaturalist_batch(self, pages=5):
        """Run iNaturalist ingestion for multiple pages"""
        print("\n" + "=" * 70)
        print("📸 iNaturalist Ingestion (Research Grade Orchids)")
        print("=" * 70)
        
        total_inserted = 0
        
        for page in range(1, pages + 1):
            observations, total_available = self.fetch_inaturalist_observations(page)
            
            if not observations:
                break
            
            all_images = []
            for obs in observations:
                images = self.extract_inaturalist_images(obs)
                all_images.extend(images)
            
            inserted = self.insert_to_staging(all_images)
            total_inserted += inserted
            self.stats['inaturalist'] += inserted
            
            print(f"   ✅ Page {page}: {inserted} new images added")
            
            time.sleep(1)  # Rate limiting
        
        print(f"\n📊 iNaturalist Total: {total_inserted} new images")
        return total_inserted
    
    def run_gbif_batch(self, genera_list, limit_per_genus=100):
        """Run GBIF ingestion for multiple genera"""
        print("\n" + "=" * 70)
        print("🌍 GBIF Ingestion (Multiple Genera)")
        print("=" * 70)
        
        total_inserted = 0
        
        for genus in genera_list:
            occurrences = self.fetch_gbif_genus(genus, limit_per_genus)
            
            all_images = []
            for occ in occurrences:
                media = occ.get('media', [])
                for item in media:
                    if item.get('type') == 'StillImage':
                        all_images.append({
                            'source': 'GBIF',
                            'occurrence_key': str(occ.get('key')),
                            'image_url': item.get('identifier'),
                            'scientific_name': occ.get('scientificName', ''),
                            'genus': occ.get('genus', ''),
                            'species': occ.get('species', ''),
                            'latitude': occ.get('decimalLatitude'),
                            'longitude': occ.get('decimalLongitude'),
                            'photographer': occ.get('recordedBy', ''),
                            'license': item.get('license', ''),
                            'observed_on': occ.get('eventDate')
                        })
            
            if all_images:
                inserted = self.insert_to_staging(all_images)
                total_inserted += inserted
                self.stats['gbif'] += inserted
                print(f"   ✅ {genus}: {inserted} new images")
            
            time.sleep(1)
        
        print(f"\n📊 GBIF Total: {total_inserted} new images")
        return total_inserted
    
    def print_summary(self):
        """Print ingestion summary"""
        total = sum(self.stats.values())
        
        print("\n" + "=" * 70)
        print("📊 INGESTION SUMMARY")
        print("=" * 70)
        print(f"   iNaturalist: {self.stats['inaturalist']:,} images")
        print(f"   GBIF: {self.stats['gbif']:,} images")
        print(f"   EOL: {self.stats['eol']:,} images")
        print(f"   Tropicos: {self.stats['tropicos']:,} images")
        print(f"   POWO: {self.stats['powo']:,} images")
        print(f"   ─" * 35)
        print(f"   TOTAL: {total:,} NEW images added")
        print("=" * 70 + "\n")
    
    def close(self):
        self.db_conn.close()

def main():
    print("\n🌺 Multi-Source Orchid Ingestion System")
    print("🎯 Goal: 2,000,000 orchid images")
    print("=" * 70)
    
    system = MultiSourceIngestion()
    
    # Run iNaturalist (biggest source - 1.4M+ orchid observations!)
    system.run_inaturalist_batch(pages=10)  # 10 pages = ~2000 images
    
    # Run GBIF for major genera
    major_genera = [
        'Epidendrum', 'Pleurothallis', 'Bulbophyllum', 'Lepanthes',
        'Maxillaria', 'Stelis', 'Masdevallia', 'Habenaria'
    ]
    system.run_gbif_batch(major_genera, limit_per_genus=50)
    
    # Print summary
    system.print_summary()
    system.close()

if __name__ == '__main__':
    main()
