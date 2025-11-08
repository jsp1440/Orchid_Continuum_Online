#!/usr/bin/env python3
"""
EMERGENCY EOL IMAGE DOWNLOAD
Downloads all 95,000 EOL images before URLs are destroyed
Saves to local storage with proper filenames
"""

import os
import sys
import time
import requests
from pathlib import Path
from urllib.parse import urlparse
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

# Database connection
DATABASE_URL = os.environ.get('DATABASE_URL')

# Create storage directory
STORAGE_DIR = Path('static/eol_images')
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

def download_image(url, image_id, page_id):
    """Download a single image and return local path"""
    try:
        # Create filename from image_id and URL
        ext = Path(urlparse(url).path).suffix or '.jpg'
        filename = f"eol_{page_id}_{image_id}{ext}"
        filepath = STORAGE_DIR / filename
        
        # Skip if already downloaded
        if filepath.exists():
            return str(filepath)
        
        # Download with timeout
        response = requests.get(url, timeout=30, stream=True)
        response.raise_for_status()
        
        # Save to file
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return str(filepath)
    
    except Exception as e:
        print(f"ERROR downloading {url}: {e}")
        return None

def main():
    print("=" * 80)
    print("EMERGENCY EOL IMAGE DOWNLOAD")
    print("=" * 80)
    print(f"Started: {datetime.now()}")
    print(f"Storage: {STORAGE_DIR.absolute()}")
    print()
    
    # Connect to database
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Get total count
    cursor.execute("SELECT COUNT(*) as total FROM eol_images WHERE source_url IS NOT NULL")
    total = cursor.fetchone()['total']
    print(f"Total EOL images to download: {total:,}")
    print()
    
    # Process in batches
    batch_size = 100
    downloaded = 0
    failed = 0
    skipped = 0
    
    cursor.execute("""
        SELECT id, page_id, source_url, eol_url 
        FROM eol_images 
        WHERE source_url IS NOT NULL
        ORDER BY id
    """)
    
    start_time = time.time()
    
    for row in cursor:
        image_id = row['id']
        page_id = row['page_id']
        url = row['source_url']
        
        # Try to download
        local_path = download_image(url, image_id, page_id)
        
        if local_path:
            # Update database with local path
            update_cursor = conn.cursor()
            update_cursor.execute("""
                UPDATE eol_images 
                SET local_path = %s 
                WHERE id = %s
            """, (local_path, image_id))
            conn.commit()
            update_cursor.close()
            
            downloaded += 1
            
            # Progress update every 100 images
            if downloaded % 100 == 0:
                elapsed = time.time() - start_time
                rate = downloaded / elapsed if elapsed > 0 else 0
                eta_seconds = (total - downloaded) / rate if rate > 0 else 0
                eta_hours = eta_seconds / 3600
                
                print(f"✓ {downloaded:,}/{total:,} ({downloaded/total*100:.1f}%) | "
                      f"Rate: {rate:.1f}/sec | ETA: {eta_hours:.1f} hours | "
                      f"Failed: {failed}")
        else:
            failed += 1
    
    # Final summary
    elapsed = time.time() - start_time
    print()
    print("=" * 80)
    print("DOWNLOAD COMPLETE")
    print("=" * 80)
    print(f"Total images: {total:,}")
    print(f"Downloaded: {downloaded:,}")
    print(f"Failed: {failed:,}")
    print(f"Time elapsed: {elapsed/3600:.2f} hours")
    print(f"Storage used: {sum(f.stat().st_size for f in STORAGE_DIR.glob('*'))/(1024**3):.2f} GB")
    print()
    
    cursor.close()
    conn.close()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDownload interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
