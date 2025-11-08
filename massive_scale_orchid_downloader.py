#!/usr/bin/env python3
"""
MASSIVE-SCALE ORCHID IMAGE DOWNLOADER
Target: 5.8M EOL + 2.4M GBIF + 297K ALA = 8.5+ Million Images
Statistical coverage across all ~800 orchid genera
"""
import os
import sys
import time
import requests
import zipfile
import json
from PIL import Image
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import psycopg2
from psycopg2.extras import execute_batch

# Database connection
DATABASE_URL = os.environ.get('DATABASE_URL')

# Output directory
OUT_DIR = Path("attached_assets/orchid_images")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Statistics file for genus-level tracking
STATS_FILE = OUT_DIR / "genus_coverage_stats.json"

session = requests.Session()
session.headers.update({'User-Agent': 'OrchidContinuum/1.0 (Educational Research)'})

class MassiveScaleDownloader:
    def __init__(self):
        self.downloaded_count = 0
        self.genus_stats = defaultdict(int)  # Track images per genus
        self.species_stats = defaultdict(int)  # Track images per species
        self.db_conn = None
        self.batch_size = 1000
        self.pending_imports = []
        
    def connect_db(self):
        """Connect to PostgreSQL"""
        try:
            self.db_conn = psycopg2.connect(DATABASE_URL)
            print("✅ Database connected")
            
            # Create comprehensive table
            cursor = self.db_conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS orchid_images (
                    id SERIAL PRIMARY KEY,
                    filename VARCHAR(255) UNIQUE,
                    source VARCHAR(100),
                    genus VARCHAR(255),
                    species VARCHAR(255),
                    full_name VARCHAR(500),
                    url TEXT,
                    thumbnail_url TEXT,
                    gbif_id VARCHAR(100),
                    eol_id VARCHAR(100),
                    ala_id VARCHAR(100),
                    collector VARCHAR(255),
                    date_observed VARCHAR(100),
                    location TEXT,
                    latitude FLOAT,
                    longitude FLOAT,
                    book_title VARCHAR(255),
                    author VARCHAR(255),
                    illustrator VARCHAR(255),
                    year INTEGER,
                    plate_number INTEGER,
                    license VARCHAR(100),
                    image_type VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(filename)
                );
                
                CREATE INDEX IF NOT EXISTS idx_genus ON orchid_images(genus);
                CREATE INDEX IF NOT EXISTS idx_species ON orchid_images(species);
                CREATE INDEX IF NOT EXISTS idx_source ON orchid_images(source);
            """)
            self.db_conn.commit()
            return True
        except Exception as e:
            print(f"❌ Database error: {e}")
            return False
    
    def save_genus_stats(self):
        """Save genus-level statistics for analysis"""
        stats = {
            'last_updated': datetime.now().isoformat(),
            'total_images': self.downloaded_count,
            'total_genera': len(self.genus_stats),
            'total_species': len(self.species_stats),
            'genus_coverage': dict(self.genus_stats),
            'species_coverage': dict(self.species_stats),
            'genera_with_10plus': sum(1 for count in self.genus_stats.values() if count >= 10),
            'genera_with_50plus': sum(1 for count in self.genus_stats.values() if count >= 50),
            'genera_with_100plus': sum(1 for count in self.genus_stats.values() if count >= 100)
        }
        
        with open(STATS_FILE, 'w') as f:
            json.dump(stats, f, indent=2)
        
        return stats
    
    def batch_import_to_db(self, force=False):
        """Batch import to database for efficiency"""
        if not self.pending_imports or (not force and len(self.pending_imports) < self.batch_size):
            return
        
        try:
            cursor = self.db_conn.cursor()
            
            insert_sql = """
                INSERT INTO orchid_images 
                (filename, source, genus, species, full_name, url, thumbnail_url, 
                 gbif_id, eol_id, ala_id, collector, date_observed, location, 
                 latitude, longitude, book_title, author, illustrator, year, 
                 plate_number, license, image_type)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (filename) DO NOTHING
            """
            
            execute_batch(cursor, insert_sql, self.pending_imports)
            self.db_conn.commit()
            
            imported = len(self.pending_imports)
            self.pending_imports = []
            
            if imported > 0 and imported % 5000 == 0:
                print(f"  💾 Batch imported {imported:,} records")
                
        except Exception as e:
            print(f"  ⚠️ Batch import error: {e}")
            self.db_conn.rollback()
            self.pending_imports = []
    
    def download_eol_images(self, max_records=100000):
        """Download from Encyclopedia of Life (5.8M available)"""
        print("\n" + "="*80)
        print("🌍 EOL - Encyclopedia of Life")
        print("="*80)
        print(f"Available: 5,800,000+ orchid images")
        print(f"Downloading: {max_records:,} images (statistically representative sample)")
        print("="*80 + "\n")
        
        page = 1
        per_page = 500
        
        while self.downloaded_count < max_records:
            try:
                # EOL API v3 - taxon pages for Orchidaceae
                url = "https://eol.org/api/search/1.0.json"
                params = {
                    'q': 'Orchidaceae',
                    'page': page,
                    'exact': False,
                    'filter_by_taxon_concept_id': '',
                    'filter_by_hierarchy_entry_id': '',
                    'filter_by_string': '',
                    'cache_ttl': ''
                }
                
                resp = session.get(url, params=params, timeout=30)
                if resp.status_code != 200:
                    print(f"  ⚠️ EOL API page {page} returned {resp.status_code}")
                    break
                
                data = resp.json()
                results = data.get('results', [])
                
                if not results:
                    break
                
                print(f"📄 Page {page} - Processing {len(results)} taxa...")
                
                for taxon in results:
                    # Get detailed taxon data with images
                    taxon_id = taxon.get('id')
                    if not taxon_id:
                        continue
                    
                    detail_url = f"https://eol.org/api/pages/1.0/{taxon_id}.json"
                    detail_params = {
                        'images_per_page': 50,
                        'images_page': 1,
                        'videos_per_page': 0,
                        'sounds_per_page': 0,
                        'maps_per_page': 0,
                        'texts_per_page': 0,
                        'details': True,
                        'common_names': False,
                        'synonyms': False,
                        'references': False,
                        'taxonomy': True
                    }
                    
                    try:
                        detail_resp = session.get(detail_url, params=detail_params, timeout=15)
                        if detail_resp.status_code != 200:
                            continue
                        
                        detail_data = detail_resp.json()
                        
                        # Extract taxonomy
                        sci_name = detail_data.get('scientificName', 'Unknown')
                        genus = sci_name.split()[0] if ' ' in sci_name else 'Unknown'
                        species = sci_name if ' ' in sci_name else 'Unknown'
                        
                        # Process images
                        data_objects = detail_data.get('dataObjects', [])
                        for obj in data_objects:
                            if obj.get('dataType') != 'http://purl.org/dc/dcmitype/StillImage':
                                continue
                            
                            img_url = obj.get('eolMediaURL') or obj.get('mediaURL')
                            thumb_url = obj.get('eolThumbnailURL')
                            
                            if not img_url:
                                continue
                            
                            # Download image
                            try:
                                img_resp = session.get(img_url, timeout=15, stream=True)
                                if img_resp.status_code == 200:
                                    eol_id = obj.get('identifier', self.downloaded_count)
                                    filename = f"eol_{eol_id}.jpg"
                                    filepath = OUT_DIR / filename
                                    
                                    # Save image
                                    with open(filepath, 'wb') as f:
                                        for chunk in img_resp.iter_content(chunk_size=8192):
                                            f.write(chunk)
                                    
                                    # Track statistics
                                    self.genus_stats[genus] += 1
                                    self.species_stats[species] += 1
                                    self.downloaded_count += 1
                                    
                                    # Queue for database import
                                    self.pending_imports.append((
                                        filename, 'EOL', genus, species, sci_name,
                                        img_url, thumb_url, None, str(eol_id), None,
                                        obj.get('rightsHolder'), None, obj.get('location'),
                                        None, None, None, None, None, None, None,
                                        obj.get('license', 'CC-BY'), 'photograph'
                                    ))
                                    
                                    # Batch import every 1000 images
                                    self.batch_import_to_db()
                                    
                                    if self.downloaded_count % 500 == 0:
                                        print(f"  ✅ Downloaded: {self.downloaded_count:,} | Genera: {len(self.genus_stats)}")
                                        self.save_genus_stats()
                                    
                                    if self.downloaded_count >= max_records:
                                        break
                                        
                            except Exception as e:
                                continue
                        
                        if self.downloaded_count >= max_records:
                            break
                            
                    except Exception as e:
                        continue
                    
                    time.sleep(0.1)  # Rate limiting
                
                if self.downloaded_count >= max_records:
                    break
                
                page += 1
                time.sleep(2)
                
            except Exception as e:
                print(f"  ⚠️ Page {page} error: {e}")
                page += 1
                continue
        
        # Final batch import
        self.batch_import_to_db(force=True)
        stats = self.save_genus_stats()
        
        print(f"\n✅ EOL Complete:")
        print(f"   Images: {self.downloaded_count:,}")
        print(f"   Genera: {stats['total_genera']}")
        print(f"   Species: {stats['total_species']}")
    
    def run(self):
        """Run massive-scale download"""
        print("="*80)
        print("🌺 MASSIVE-SCALE ORCHID IMAGE DOWNLOADER")
        print("="*80)
        print("Target: 8.5+ Million Images")
        print("Mission: Complete statistical coverage of all orchid genera")
        print("="*80)
        
        if not self.connect_db():
            print("❌ Cannot proceed without database")
            return
        
        # Start with EOL (largest dataset)
        self.download_eol_images(max_records=100000)  # Start with 100K
        
        print("\n" + "="*80)
        print("🎉 BATCH COMPLETE!")
        print("="*80)
        final_stats = self.save_genus_stats()
        print(f"✅ Total images: {final_stats['total_images']:,}")
        print(f"✅ Genera covered: {final_stats['total_genera']:,}")
        print(f"✅ Species covered: {final_stats['total_species']:,}")
        print(f"✅ Genera with 10+ images: {final_stats['genera_with_10plus']:,}")
        print(f"✅ Genera with 50+ images: {final_stats['genera_with_50plus']:,}")
        print(f"✅ Genera with 100+ images: {final_stats['genera_with_100plus']:,}")
        print("="*80)
        
        if self.db_conn:
            self.db_conn.close()


if __name__ == "__main__":
    downloader = MassiveScaleDownloader()
    downloader.run()
