#!/usr/bin/env python3
"""
COMPATIBLE MASSIVE-SCALE ORCHID DOWNLOADER
Works with existing Orchid Continuum database schema
Target: Millions of images from EOL, GBIF, ALA
"""
import os
import time
import requests
from pathlib import Path
from datetime import datetime
import psycopg2
import json

DATABASE_URL = os.environ.get('DATABASE_URL')
OUT_DIR = Path("attached_assets/orchid_images")
OUT_DIR.mkdir(parents=True, exist_ok=True)

session = requests.Session()
session.headers.update({'User-Agent': 'OrchidContinuum/1.0'})

class CompatibleDownloader:
    def __init__(self):
        self.downloaded = 0
        self.db_conn = None
        self.genus_stats = {}
        
    def connect_db(self):
        try:
            self.db_conn = psycopg2.connect(DATABASE_URL)
            print("✅ Database connected")
            return True
        except Exception as e:
            print(f"❌ DB error: {e}")
            return False
    
    def get_taxonomy_id(self, genus, species):
        """Get or create taxonomy ID"""
        try:
            cursor = self.db_conn.cursor()
            
            # Try to find existing taxonomy
            cursor.execute("""
                SELECT id FROM orchid_taxonomy 
                WHERE genus = %s AND species = %s
                LIMIT 1
            """, (genus, species))
            
            result = cursor.fetchone()
            if result:
                return result[0]
            
            # If not found, try just genus
            cursor.execute("""
                SELECT id FROM orchid_taxonomy 
                WHERE genus = %s
                LIMIT 1
            """, (genus,))
            
            result = cursor.fetchone()
            return result[0] if result else None
            
        except:
            return None
    
    def download_eol_batch(self, batch_size=10000):
        """Download batch from EOL"""
        print(f"\n🌍 Downloading {batch_size:,} images from EOL...")
        print("(5.8M total available)\n")
        
        # EOL TraitBank API for Orchidaceae
        offset = 0
        limit = 100
        
        while self.downloaded < batch_size:
            try:
                # Search EOL for orchid pages
                url = "https://eol.org/api/search/1.0.json"
                params = {
                    'q': 'Orchidaceae',
                    'page': (offset // 30) + 1,
                    'exact': False
                }
                
                resp = session.get(url, params=params, timeout=30)
                if resp.status_code != 200:
                    print(f"  ⚠️ EOL returned {resp.status_code}")
                    break
                
                data = resp.json()
                results = data.get('results', [])
                
                if not results:
                    break
                
                print(f"📄 Processing batch {offset//limit + 1}...")
                
                for item in results:
                    taxon_id = item.get('id')
                    if not taxon_id:
                        continue
                    
                    # Get taxon page with images
                    page_url = f"https://eol.org/api/pages/1.0/{taxon_id}.json"
                    page_params = {
                        'images_per_page': 25,
                        'images_page': 1,
                        'videos': 0,
                        'sounds': 0,
                        'maps': 0,
                        'text': 0,
                        'details': True,
                        'taxonomy': True
                    }
                    
                    try:
                        page_resp = session.get(page_url, params=page_params, timeout=15)
                        if page_resp.status_code != 200:
                            continue
                        
                        page_data = page_resp.json()
                        sci_name = page_data.get('scientificName', '')
                        
                        # Parse genus/species
                        parts = sci_name.split()
                        genus = parts[0] if len(parts) > 0 else 'Unknown'
                        species = ' '.join(parts[:2]) if len(parts) > 1 else genus
                        
                        # Get taxonomy ID
                        tax_id = self.get_taxonomy_id(genus, species)
                        
                        # Track genus stats
                        if genus not in self.genus_stats:
                            self.genus_stats[genus] = 0
                        
                        # Process images
                        for obj in page_data.get('dataObjects', []):
                            if obj.get('dataType') != 'http://purl.org/dc/dcmitype/StillImage':
                                continue
                            
                            img_url = obj.get('eolMediaURL') or obj.get('mediaURL')
                            if not img_url:
                                continue
                            
                            # Download image
                            try:
                                img_resp = session.get(img_url, timeout=15, stream=True)
                                if img_resp.status_code == 200:
                                    eol_id = obj.get('identifier', f"eol_{self.downloaded}")
                                    filename = f"eol_{self.downloaded}_{genus}.jpg"
                                    filepath = OUT_DIR / filename
                                    
                                    with open(filepath, 'wb') as f:
                                        for chunk in img_resp.iter_content(8192):
                                            f.write(chunk)
                                    
                                    # Insert to database
                                    cursor = self.db_conn.cursor()
                                    cursor.execute("""
                                        INSERT INTO orchid_images 
                                        (taxonomy_id, image_url, image_source, image_license,
                                         eol_data_object_id, local_path, download_status)
                                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                                        ON CONFLICT DO NOTHING
                                    """, (
                                        tax_id,
                                        img_url,
                                        'EOL',
                                        obj.get('license', 'CC-BY'),
                                        str(eol_id),
                                        str(filepath),
                                        'downloaded'
                                    ))
                                    self.db_conn.commit()
                                    
                                    self.downloaded += 1
                                    self.genus_stats[genus] += 1
                                    
                                    if self.downloaded % 100 == 0:
                                        print(f"  ✅ {self.downloaded:,} images | {len(self.genus_stats)} genera")
                                    
                                    if self.downloaded >= batch_size:
                                        break
                                        
                            except Exception as e:
                                continue
                        
                        if self.downloaded >= batch_size:
                            break
                            
                    except Exception as e:
                        continue
                    
                    time.sleep(0.2)
                
                if self.downloaded >= batch_size:
                    break
                
                offset += limit
                time.sleep(2)
                
            except Exception as e:
                print(f"  ⚠️ Batch error: {e}")
                offset += limit
                continue
        
        # Save stats
        stats_file = OUT_DIR / "download_stats.json"
        with open(stats_file, 'w') as f:
            json.dump({
                'downloaded': self.downloaded,
                'genera_count': len(self.genus_stats),
                'genus_stats': self.genus_stats,
                'timestamp': datetime.now().isoformat()
            }, f, indent=2)
        
        print(f"\n✅ Downloaded {self.downloaded:,} images")
        print(f"✅ Covered {len(self.genus_stats)} genera")
        print(f"📊 Stats saved to: {stats_file}")
    
    def run(self):
        print("="*80)
        print("🌺 COMPATIBLE MASSIVE-SCALE DOWNLOADER")
        print("="*80)
        print("Target: Millions from EOL (5.8M) + GBIF (2.4M) + ALA (297K)")
        print("="*80)
        
        if not self.connect_db():
            print("❌ Cannot proceed")
            return
        
        # Download first batch (10K images)
        self.download_eol_batch(batch_size=10000)
        
        if self.db_conn:
            self.db_conn.close()
        
        print("\n" + "="*80)
        print("🎉 BATCH COMPLETE!")
        print("="*80)

if __name__ == "__main__":
    downloader = CompatibleDownloader()
    downloader.run()
