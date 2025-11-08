#!/usr/bin/env python3
"""
Step 2: Bulk import EOL images with trait enrichment
Uses mapping from Step 1 to import images and traits for all orchids
"""
import csv
import json
import os
import sys
import psycopg2
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

MAPPING_FILE = 'bulk_eol_import/eol_taxonomy_mapping.json'
IMAGE_CSV_DIR = 'external_databases/zenodo_data'
TRAITS_CSV = 'external_databases/eol_traitbank/trait_bank/traits.csv'
BATCH_SIZE = 1000

def get_db():
    return psycopg2.connect(os.environ['DATABASE_URL'])

def load_mapping():
    """Load EOL taxonomy mapping."""
    print(f"📋 Loading EOL taxonomy mapping...")
    
    if not os.path.exists(MAPPING_FILE):
        print(f"❌ Mapping file not found: {MAPPING_FILE}")
        print(f"   Run Step 1 first: python bulk_eol_import/1_map_eol_pages.py")
        sys.exit(1)
    
    with open(MAPPING_FILE, 'r') as f:
        mapping = json.load(f)
    
    # Convert string keys back to int
    mapping = {int(k): v for k, v in mapping.items()}
    
    print(f"✅ Loaded {len(mapping):,} taxonomy mappings")
    return mapping

def build_page_id_index(mapping):
    """Build reverse index: eol_page_id → taxonomy_info."""
    print(f"\n🔍 Building EOL page_id index...")
    
    page_index = {}
    for tax_id, info in mapping.items():
        page_id = info['eol_page_id']
        page_index[page_id] = {
            'taxonomy_id': tax_id,
            **info
        }
    
    print(f"✅ Indexed {len(page_index):,} EOL page_ids")
    return page_index

def load_traits_by_page_id():
    """Load all orchid traits indexed by EOL page_id."""
    print(f"\n🌿 Loading traits from EOL TraitBank...")
    
    if not os.path.exists(TRAITS_CSV):
        print(f"⚠️  Traits file not found: {TRAITS_CSV}")
        print(f"   Continuing without traits...")
        return {}
    
    traits_by_page = {}
    
    with open(TRAITS_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        count = 0
        for row in reader:
            page_id = row.get('page_id', '').strip()
            
            if not page_id:
                continue
            
            if page_id not in traits_by_page:
                traits_by_page[page_id] = []
            
            # Extract trait info
            predicate = row.get('predicate', '').split('/')[-1] if row.get('predicate') else 'unknown'
            measurement = row.get('measurement', '')
            literal = row.get('literal', '')
            units = row.get('units', '')
            
            trait_value = literal if literal else measurement
            if units:
                trait_value = f"{trait_value} {units}"
            
            if trait_value:
                traits_by_page[page_id].append({
                    'category': predicate,
                    'value': trait_value,
                    'eol_trait_id': row.get('eol_pk', '')
                })
            
            count += 1
            if count % 100000 == 0:
                print(f"   Processed {count:,} trait records...")
    
    print(f"✅ Loaded traits for {len(traits_by_page):,} species")
    return traits_by_page

def import_images_batch(page_index, traits_by_page, limit_species=None):
    """Import images from CSV files in batches."""
    print(f"\n📥 Importing images from EOL CSV files...")
    
    # Get list of CSV files
    csv_files = sorted([
        f for f in os.listdir(IMAGE_CSV_DIR)
        if f.startswith('media_manifest_') and f.endswith('.csv')
    ])
    
    print(f"   Found {len(csv_files)} CSV files to process")
    
    conn = get_db()
    cur = conn.cursor()
    
    total_images = 0
    total_species = 0
    images_batch = []
    processed_species = set()
    
    for csv_idx, csv_file in enumerate(csv_files, 1):
        csv_path = os.path.join(IMAGE_CSV_DIR, csv_file)
        
        print(f"\n[{csv_idx}/{len(csv_files)}] Processing: {csv_file}")
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                content_id = row.get('EOL content ID', '').strip()
                page_id = row.get('EOL page ID', '').strip()
                source_url = row.get('Medium Source URL', '').strip()
                eol_url = row.get('EOL Full-Size Copy URL', '').strip()
                license_name = row.get('License Name', '').strip()
                copyright_owner = row.get('Copyright Owner', '').strip()
                
                # Check if this page_id matches an orchid
                if page_id not in page_index:
                    continue
                
                orchid_info = page_index[page_id]
                tax_id = orchid_info['taxonomy_id']
                
                # Check if already exists
                cur.execute(
                    "SELECT 1 FROM orchid_images WHERE eol_content_id = %s",
                    (content_id,)
                )
                if cur.fetchone():
                    continue
                
                # Prefer EOL hosted URL (more reliable)
                image_url = eol_url if eol_url else source_url
                
                if not image_url:
                    continue
                
                # Get traits for this page_id
                traits = traits_by_page.get(page_id, [])
                
                # Build eol_metadata JSONB
                eol_metadata = {
                    'zenodo_source': 'https://zenodo.org/records/17210269',
                    'eol_page_id': page_id,
                    'eol_content_id': content_id,
                    'traits': traits,
                    'import_date': datetime.now().isoformat()
                }
                
                # Add to batch
                images_batch.append({
                    'taxonomy_id': tax_id,
                    'eol_content_id': content_id,
                    'eol_page_id': page_id,
                    'image_url': image_url,
                    'image_license': license_name,
                    'copyright_owner': copyright_owner,
                    'image_source': 'EOL-Zenodo',
                    'is_hybrid': orchid_info['is_hybrid'],
                    'is_intergeneric': orchid_info['is_intergeneric'],
                    'eol_metadata': json.dumps(eol_metadata)
                })
                
                processed_species.add(tax_id)
                
                # Insert batch when full
                if len(images_batch) >= BATCH_SIZE:
                    insert_images_batch(cur, images_batch)
                    total_images += len(images_batch)
                    total_species = len(processed_species)
                    
                    print(f"   ✅ Imported {total_images:,} images for {total_species:,} species")
                    
                    images_batch = []
                    conn.commit()
                
                # Limit check
                if limit_species and len(processed_species) >= limit_species:
                    print(f"\n⚠️  Reached limit of {limit_species} species")
                    break
            
            if limit_species and len(processed_species) >= limit_species:
                break
    
    # Insert remaining batch
    if images_batch:
        insert_images_batch(cur, images_batch)
        total_images += len(images_batch)
        conn.commit()
    
    cur.close()
    conn.close()
    
    print(f"\n✅ Image import complete!")
    print(f"   Total images: {total_images:,}")
    print(f"   Total species: {len(processed_species):,}")
    
    return total_images, len(processed_species)

def insert_images_batch(cur, images_batch):
    """Insert batch of images into database."""
    for img in images_batch:
        try:
            cur.execute("""
                INSERT INTO orchid_images (
                    taxonomy_id, eol_content_id, eol_page_id, image_url,
                    image_license, copyright_owner, image_source,
                    is_hybrid, is_intergeneric,
                    image_description, eol_metadata, downloaded_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (eol_content_id) DO NOTHING
            """, (
                img['taxonomy_id'],
                img['eol_content_id'],
                img['eol_page_id'],
                img['image_url'],
                img['image_license'],
                img['copyright_owner'],
                img['image_source'],
                img['is_hybrid'],
                img['is_intergeneric'],
                'Encyclopedia of Life (Zenodo bulk import)',
                img['eol_metadata'],
                datetime.now()
            ))
        except Exception as e:
            # Skip duplicates or errors
            continue

def main():
    print("=" * 80)
    print("BULK EOL IMPORT - Images + Traits")
    print("=" * 80)
    print()
    
    # Check for command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Bulk import EOL images and traits')
    parser.add_argument('--test', action='store_true', help='Test mode: process only 100 species')
    parser.add_argument('--limit', type=int, help='Limit number of species to process')
    args = parser.parse_args()
    
    if args.limit:
        limit = args.limit
        print(f"\n⚠️  LIMIT MODE: Processing {limit} species")
    elif args.test:
        limit = 100
        print("\n⚠️  TEST MODE: Processing 100 species")
    else:
        limit = None
        print("\n🚀 FULL MODE: Processing all species")
    
    print()
    
    # Load mapping
    mapping = load_mapping()
    page_index = build_page_id_index(mapping)
    
    # Load all traits into memory (indexed by page_id)
    traits_by_page = load_traits_by_page_id()
    
    # Import images with traits embedded in eol_metadata
    total_images, total_species = import_images_batch(page_index, traits_by_page, limit_species=limit)
    
    print()
    print("=" * 80)
    print("✅ BULK IMPORT COMPLETE!")
    print("=" * 80)
    print(f"\nResults:")
    print(f"  Images imported: {total_images:,}")
    print(f"  Species enriched: {total_species:,}")
    print(f"  Traits stored in eol_metadata JSONB field")
    print()

if __name__ == '__main__':
    main()
