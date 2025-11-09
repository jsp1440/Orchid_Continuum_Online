#!/usr/bin/env python3
"""
ZENODO CSV WORKER - Import 5.6M Images from Local CSV Files
============================================================
Imports images from Zenodo EOL dataset (1.4GB, 58 CSV files)
NO API CALLS - reads directly from downloaded CSV files

Sources include:
- Biodiversity Heritage Library (BHL)
- Flickr museums and herbaria
- Encyclopedia of Life (EOL)
- And many more

Run: python workers/zenodo_csv_worker.py zenodo-1
"""
import os, sys, time, psycopg2, csv, glob
from psycopg2 import pool

WORKER_ID = sys.argv[1] if len(sys.argv) > 1 else "zenodo-1"
ZENODO_DIR = "external_databases/zenodo_data"
BATCH_SIZE = 1000  # Insert 1000 images at a time
MAX_IMAGES_PER_PAGE = 200  # Limit per EOL page to avoid spam

pool_obj = pool.SimpleConnectionPool(minconn=1, maxconn=3, dsn=os.environ.get('DATABASE_URL'))
stats = {'added': 0, 'duplicates': 0, 'errors': 0, 'start': time.time(), 'current_file': '', 'files_processed': 0}

def get_conn():
    return pool_obj.getconn()

def put_conn(c):
    pool_obj.putconn(c)

def get_source_from_url(source_url):
    """Determine image source from URL"""
    url_lower = source_url.lower()
    
    if 'biodivlibrary' in url_lower or 'biodiversitylibrary' in url_lower:
        return 'BHL - Biodiversity Heritage Library'
    elif 'flickr.com' in url_lower:
        return 'Flickr - Museums & Herbaria'
    elif 'inaturalist' in url_lower:
        return 'iNaturalist'
    elif 'wikimedia' in url_lower:
        return 'Wikimedia Commons'
    elif 'eol.org' in url_lower:
        return 'EOL - Encyclopedia of Life'
    else:
        return 'Zenodo Dataset'

def check_page_image_count(conn, eol_page_id):
    """Check how many images we already have for this EOL page"""
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) FROM orchid_images 
        WHERE media_metadata->>'eol_page_id' = %s
    """, (str(eol_page_id),))
    count = cur.fetchone()[0]
    return count

def process_csv_file(csv_path):
    """Process a single Zenodo CSV file"""
    c = get_conn()
    
    try:
        batch = []
        line_count = 0
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                line_count += 1
                
                try:
                    eol_content_id = row.get('EOL content ID', '').strip()
                    eol_page_id = row.get('EOL page ID', '').strip()
                    source_url = row.get('Medium Source URL', '').strip()
                    eol_url = row.get('EOL Full-Size Copy URL', '').strip()
                    license_name = row.get('License Name', '').strip()
                    copyright_owner = row.get('Copyright Owner', '').strip()
                    
                    # Skip if no valid URLs
                    if not eol_url or not eol_page_id:
                        continue
                    
                    # Check if we already have too many images for this page
                    if line_count % 100 == 0:  # Check every 100 rows to avoid too many queries
                        current_count = check_page_image_count(c, eol_page_id)
                        if current_count >= MAX_IMAGES_PER_PAGE:
                            continue
                    
                    # Determine source
                    image_source = get_source_from_url(source_url)
                    
                    # Prepare metadata
                    metadata = {
                        'eol_page_id': eol_page_id,
                        'eol_content_id': eol_content_id,
                        'source_url': source_url,
                        'license': license_name,
                        'copyright_owner': copyright_owner
                    }
                    
                    batch.append((
                        None,  # taxonomy_id (NULL for now - will match later)
                        eol_url,
                        image_source,
                        'illustration',  # type
                        None,  # country
                        None, None,  # lat/long
                        license_name or 'Unknown',
                        copyright_owner,
                        metadata
                    ))
                    
                    # Insert batch when full
                    if len(batch) >= BATCH_SIZE:
                        insert_batch(c, batch)
                        batch = []
                        
                except Exception as e:
                    stats['errors'] += 1
                    if stats['errors'] < 5:  # Only print first few errors
                        print(f"[{WORKER_ID}] Row error: {str(e)[:100]}")
                    continue
        
        # Insert remaining batch
        if batch:
            insert_batch(c, batch)
        
        stats['files_processed'] += 1
        print(f"[{WORKER_ID}] ✅ Processed {csv_path}: {line_count} rows, {stats['added']} total saved")
        
    except Exception as e:
        print(f"[{WORKER_ID}] ❌ File error {csv_path}: {e}")
        stats['errors'] += 1
    finally:
        put_conn(c)

def insert_batch(conn, batch):
    """Insert a batch of images"""
    if not batch:
        return
    
    cur = conn.cursor()
    import json
    
    try:
        # Insert images one by one (simpler and more reliable)
        inserted = 0
        
        for item in batch:
            taxonomy_id, image_url, image_source, image_type, country, lat, lon, license, rights_holder, metadata = item
            
            try:
                sql = """
                INSERT INTO orchid_images (
                    taxonomy_id, image_url, image_source, image_type,
                    country, latitude, longitude, image_license, 
                    rights_holder, media_metadata, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                ON CONFLICT (image_url) DO NOTHING
                """
                
                cur.execute(sql, (
                    taxonomy_id,
                    image_url,
                    image_source,
                    image_type,
                    country,
                    lat,
                    lon,
                    license,
                    rights_holder,
                    json.dumps(metadata)
                ))
                
                if cur.rowcount > 0:
                    inserted += 1
                    
            except Exception as e:
                # Skip this image on error
                continue
        
        conn.commit()
        
        stats['added'] += inserted
        stats['duplicates'] += (len(batch) - inserted)
        
        # Print progress every 10,000 images
        if stats['added'] % 10000 < BATCH_SIZE:
            elapsed = time.time() - stats['start']
            rate = stats['added'] / (elapsed / 60)
            print(f"[{WORKER_ID}] Progress: {stats['added']:,} images saved ({rate:.1f}/min), {stats['duplicates']:,} duplicates, {stats['files_processed']} files")
        
    except Exception as e:
        conn.rollback()
        stats['errors'] += 1
        print(f"[{WORKER_ID}] Batch insert error: {str(e)[:200]}")

def main():
    print(f"📊 ZENODO CSV WORKER: {WORKER_ID}")
    print(f"📁 Reading from: {ZENODO_DIR}")
    
    # Find all CSV files
    csv_files = sorted(glob.glob(f"{ZENODO_DIR}/media_manifest_*.csv"))
    
    if not csv_files:
        print(f"❌ No CSV files found in {ZENODO_DIR}")
        return
    
    print(f"📋 Found {len(csv_files)} CSV files to process")
    print(f"🎯 Target: 5.6 MILLION images from BHL, Flickr, museums, herbaria, etc.\n")
    
    # Process each CSV file
    for csv_path in csv_files:
        stats['current_file'] = csv_path
        process_csv_file(csv_path)
        time.sleep(0.5)  # Brief pause between files
    
    # Final stats
    elapsed = time.time() - stats['start']
    rate = stats['added'] / (elapsed / 60) if elapsed > 0 else 0
    
    print(f"\n{'='*80}")
    print(f"🎉 ZENODO IMPORT COMPLETE!")
    print(f"{'='*80}")
    print(f"✅ Images saved: {stats['added']:,}")
    print(f"⏭️  Duplicates skipped: {stats['duplicates']:,}")
    print(f"❌ Errors: {stats['errors']:,}")
    print(f"📁 Files processed: {stats['files_processed']}/{len(csv_files)}")
    print(f"⏱️  Time: {elapsed/60:.1f} minutes")
    print(f"📈 Rate: {rate:.1f} images/minute")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()
