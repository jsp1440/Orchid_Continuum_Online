#!/usr/bin/env python3
"""
EMERGENCY: Download ALL 95,000 EOL images NOW before URLs die
Match to taxonomy and prepare for Google Drive upload
"""

import os
import sys
import time
import requests
import psycopg2
from psycopg2.extras import RealDictCursor
from pathlib import Path
from datetime import datetime
import concurrent.futures
from urllib.parse import urlparse

DATABASE_URL = os.environ.get('DATABASE_URL')

# Local storage (Replit has ~10GB)
STORAGE_DIR = Path('/tmp/eol_orchid_rescue')
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

class EOLRescue:
    def __init__(self):
        self.db_conn = psycopg2.connect(DATABASE_URL)
        self.downloaded = 0
        self.failed = 0
        self.start_time = time.time()
    
    def download_single_image(self, image_data):
        """Download one image and save locally"""
        try:
            eol_id = image_data['id']
            page_id = image_data['page_id']
            url = image_data['source_url']
            
            # Create filename
            ext = Path(urlparse(url).path).suffix or '.jpg'
            filename = f"eol_{page_id}_{eol_id}{ext}"
            filepath = STORAGE_DIR / filename
            
            # Skip if exists
            if filepath.exists():
                return {'status': 'exists', 'path': str(filepath), 'id': eol_id}
            
            # Download
            response = requests.get(url, timeout=30, stream=True)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Update database
            cursor = self.db_conn.cursor()
            cursor.execute("""
                UPDATE eol_images 
                SET local_path = %s,
                    download_status = 'downloaded',
                    uploaded_at = NOW(),
                    file_size_kb = %s
                WHERE id = %s
            """, (str(filepath), filepath.stat().st_size // 1024, eol_id))
            self.db_conn.commit()
            cursor.close()
            
            return {'status': 'downloaded', 'path': str(filepath), 'id': eol_id}
            
        except Exception as e:
            return {'status': 'failed', 'error': str(e), 'id': image_data.get('id')}
    
    def get_images_to_download(self):
        """Get all EOL images that need downloading"""
        cursor = self.db_conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT id, page_id, source_url
            FROM eol_images
            WHERE source_url IS NOT NULL
            AND (download_status IS NULL OR download_status != 'downloaded')
            ORDER BY id
        """)
        images = cursor.fetchall()
        cursor.close()
        return images
    
    def download_all_parallel(self, max_workers=20):
        """Download all images using parallel workers"""
        images = self.get_images_to_download()
        total = len(images)
        
        print(f"\n{'='*80}")
        print(f"DOWNLOADING {total:,} EOL IMAGES")
        print(f"Storage: {STORAGE_DIR}")
        print(f"Workers: {max_workers}")
        print(f"{'='*80}\n")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self.download_single_image, img): img for img in images}
            
            for idx, future in enumerate(concurrent.futures.as_completed(futures), 1):
                result = future.result()
                
                if result['status'] == 'downloaded':
                    self.downloaded += 1
                elif result['status'] == 'failed':
                    self.failed += 1
                
                # Progress every 100 images
                if idx % 100 == 0:
                    elapsed = time.time() - self.start_time
                    rate = idx / elapsed
                    eta_hours = (total - idx) / rate / 3600
                    storage_gb = sum(f.stat().st_size for f in STORAGE_DIR.glob('*')) / (1024**3)
                    
                    print(f"Progress: {idx:,}/{total:,} ({idx/total*100:.1f}%) | "
                          f"Rate: {rate:.1f}/sec | ETA: {eta_hours:.1f}h | "
                          f"Storage: {storage_gb:.2f}GB | "
                          f"✓{self.downloaded:,} ✗{self.failed:,}")
        
        return self.downloaded, self.failed
    
    def match_to_taxonomy(self):
        """Match EOL images to orchid taxonomy"""
        print(f"\n{'='*80}")
        print("MATCHING IMAGES TO TAXONOMY")
        print(f"{'='*80}\n")
        
        cursor = self.db_conn.cursor()
        
        # This will be complex - EOL page_id needs to match to species
        # For now, just create the linkage table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS eol_taxonomy_links (
                id SERIAL PRIMARY KEY,
                eol_image_id INTEGER REFERENCES eol_images(id),
                taxonomy_id INTEGER REFERENCES orchid_taxonomy(id),
                confidence FLOAT,
                matched_by VARCHAR(50),
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        print("✓ Created taxonomy linkage table")
        print("  (Actual matching requires EOL page_id → species lookup)")
        
        self.db_conn.commit()
        cursor.close()
    
    def create_upload_manifest(self):
        """Create manifest for bulk Google Drive upload"""
        cursor = self.db_conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT 
                e.id,
                e.page_id,
                e.local_path,
                e.license,
                e.copyright as photographer,
                e.file_size_kb
            FROM eol_images e
            WHERE e.local_path IS NOT NULL
            ORDER BY e.id
        """)
        
        rows = cursor.fetchall()
        
        import csv
        manifest_file = 'EOL_UPLOAD_MANIFEST.csv'
        with open(manifest_file, 'w', newline='', encoding='utf-8') as f:
            if rows:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
        
        print(f"\n✓ Created upload manifest: {manifest_file}")
        print(f"  Total files: {len(rows):,}")
        
        cursor.close()
        return manifest_file

def main():
    print("="*80)
    print("EMERGENCY EOL IMAGE RESCUE")
    print("DOWNLOADING 95,000 IMAGES BEFORE URLS ARE DESTROYED")
    print("="*80)
    print(f"Started: {datetime.now()}\n")
    
    rescue = EOLRescue()
    
    # Download everything
    downloaded, failed = rescue.download_all_parallel(max_workers=20)
    
    elapsed = time.time() - rescue.start_time
    storage_gb = sum(f.stat().st_size for f in STORAGE_DIR.glob('*')) / (1024**3)
    
    print(f"\n{'='*80}")
    print("DOWNLOAD COMPLETE")
    print(f"{'='*80}")
    print(f"Downloaded: {downloaded:,}")
    print(f"Failed: {failed:,}")
    print(f"Time: {elapsed/3600:.2f} hours")
    print(f"Storage: {storage_gb:.2f} GB")
    print(f"Location: {STORAGE_DIR}")
    
    # Match to taxonomy
    rescue.match_to_taxonomy()
    
    # Create manifest
    rescue.create_upload_manifest()
    
    print(f"\n{'='*80}")
    print("IMAGES SAVED! Next: Upload to YOUR Google Drive")
    print(f"{'='*80}\n")

if __name__ == '__main__':
    main()
