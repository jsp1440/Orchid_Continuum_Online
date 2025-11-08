#!/usr/bin/env python3
"""
EMERGENCY: Query EOL API to get taxonomy for all 95,000 images
Get the REAL data before URLs expire: genus, species, location, dates
"""

import os
import requests
import time
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import json

DATABASE_URL = os.environ.get('DATABASE_URL')

# EOL API endpoint
EOL_API_BASE = "https://eol.org/api"

class EOLTaxonomyFetcher:
    def __init__(self):
        self.db_conn = psycopg2.connect(DATABASE_URL)
        self.fetched = 0
        self.failed = 0
        self.start_time = time.time()
    
    def get_page_taxonomy(self, page_id):
        """Query EOL API for taxonomy data for a page_id"""
        try:
            # EOL API endpoint for page data
            url = f"{EOL_API_BASE}/pages/1.0/{page_id}.json"
            
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Extract taxonomy
            taxonomy = {
                'page_id': page_id,
                'scientific_name': data.get('scientificName'),
                'canonical_name': None,
                'genus': None,
                'species': None,
                'family': None,
                'common_names': [],
                'data_objects': []
            }
            
            # Parse scientific name
            if taxonomy['scientific_name']:
                parts = taxonomy['scientific_name'].split()
                if len(parts) >= 1:
                    taxonomy['genus'] = parts[0]
                if len(parts) >= 2:
                    taxonomy['species'] = parts[1]
            
            # Get common names
            if 'vernacularNames' in data:
                taxonomy['common_names'] = [
                    vn.get('vernacularName') 
                    for vn in data['vernacularNames'][:5]
                ]
            
            # Get taxonomy hierarchy
            if 'taxonConcepts' in data and data['taxonConcepts']:
                tc = data['taxonConcepts'][0]
                taxonomy['canonical_name'] = tc.get('canonicalForm')
                
                # Get family from ancestry
                if 'ancestry' in tc:
                    for anc in tc['ancestry']:
                        if anc.get('taxonRank') == 'family':
                            taxonomy['family'] = anc.get('scientificName')
            
            # Get data objects (images) with metadata
            if 'dataObjects' in data:
                for obj in data['dataObjects']:
                    if obj.get('dataType') == 'http://purl.org/dc/dcmitype/StillImage':
                        img_data = {
                            'source': obj.get('source'),
                            'eol_media_url': obj.get('eolMediaURL'),
                            'thumbnail': obj.get('eolThumbnailURL'),
                            'location': obj.get('location'),
                            'rights_holder': obj.get('rightsHolder'),
                            'license': obj.get('license'),
                            'created': obj.get('created'),
                            'description': obj.get('description')
                        }
                        taxonomy['data_objects'].append(img_data)
            
            return taxonomy
            
        except Exception as e:
            print(f"  Error fetching page {page_id}: {e}")
            return None
    
    def update_database(self, eol_id, taxonomy_data):
        """Update eol_images table with taxonomy data"""
        try:
            cursor = self.db_conn.cursor()
            
            # Add columns if they don't exist
            cursor.execute("""
                ALTER TABLE eol_images 
                ADD COLUMN IF NOT EXISTS scientific_name TEXT,
                ADD COLUMN IF NOT EXISTS genus TEXT,
                ADD COLUMN IF NOT EXISTS species TEXT,
                ADD COLUMN IF NOT EXISTS family TEXT,
                ADD COLUMN IF NOT EXISTS common_names TEXT,
                ADD COLUMN IF NOT EXISTS taxonomy_data JSONB
            """)
            
            # Update the record
            cursor.execute("""
                UPDATE eol_images 
                SET scientific_name = %s,
                    genus = %s,
                    species = %s,
                    family = %s,
                    common_names = %s,
                    taxonomy_data = %s
                WHERE id = %s
            """, (
                taxonomy_data.get('scientific_name'),
                taxonomy_data.get('genus'),
                taxonomy_data.get('species'),
                taxonomy_data.get('family'),
                ','.join(taxonomy_data.get('common_names', [])),
                json.dumps(taxonomy_data),
                eol_id
            ))
            
            self.db_conn.commit()
            cursor.close()
            return True
            
        except Exception as e:
            print(f"  Error updating database: {e}")
            return False
    
    def process_all_images(self, limit=None):
        """Fetch taxonomy for all EOL images"""
        cursor = self.db_conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT id, page_id
            FROM eol_images
            WHERE page_id IS NOT NULL
            AND (scientific_name IS NULL OR scientific_name = '')
            ORDER BY id
        """
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query)
        images = cursor.fetchall()
        total = len(images)
        
        print(f"\n{'='*80}")
        print(f"FETCHING TAXONOMY FOR {total:,} EOL IMAGES")
        print(f"{'='*80}\n")
        
        unique_pages = {}  # Cache to avoid duplicate API calls
        
        for idx, img in enumerate(images, 1):
            page_id = img['page_id']
            
            # Check cache first
            if page_id in unique_pages:
                taxonomy = unique_pages[page_id]
            else:
                taxonomy = self.get_page_taxonomy(page_id)
                if taxonomy:
                    unique_pages[page_id] = taxonomy
                time.sleep(0.5)  # Rate limiting
            
            if taxonomy:
                if self.update_database(img['id'], taxonomy):
                    self.fetched += 1
            else:
                self.failed += 1
            
            # Progress every 10 images
            if idx % 10 == 0:
                elapsed = time.time() - self.start_time
                rate = idx / elapsed if elapsed > 0 else 0
                eta_hours = (total - idx) / rate / 3600 if rate > 0 else 0
                
                print(f"Progress: {idx:,}/{total:,} ({idx/total*100:.1f}%) | "
                      f"Rate: {rate:.2f}/sec | ETA: {eta_hours:.2f}h | "
                      f"✓{self.fetched:,} ✗{self.failed:,} | "
                      f"Unique pages: {len(unique_pages):,}")
        
        cursor.close()
        
        print(f"\n{'='*80}")
        print(f"TAXONOMY FETCH COMPLETE")
        print(f"{'='*80}")
        print(f"Fetched: {self.fetched:,}")
        print(f"Failed: {self.failed:,}")
        print(f"Unique pages: {len(unique_pages):,}")
        print(f"Time: {(time.time() - self.start_time)/3600:.2f} hours")

def main():
    print("="*80)
    print("EMERGENCY EOL TAXONOMY FETCH")
    print("Getting REAL taxonomy data before it's lost")
    print("="*80)
    print(f"Started: {datetime.now()}\n")
    
    fetcher = EOLTaxonomyFetcher()
    
    # Start with test of 100 images
    print("Testing with first 100 images...")
    fetcher.process_all_images(limit=100)
    
    print("\n✓ Test complete. Check results in database.")
    print("\nTo process all 95,000, change limit to None and run again.")

if __name__ == '__main__':
    main()
