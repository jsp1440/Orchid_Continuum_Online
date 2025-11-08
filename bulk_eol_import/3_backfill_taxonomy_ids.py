#!/usr/bin/env python3
"""
Step 3: Backfill taxonomy_id for images that have eol_page_id but no taxonomy_id
This fixes the 84% of images that weren't linked to orchid_taxonomy
"""
import json
import os
import psycopg2

MAPPING_FILE = 'bulk_eol_import/eol_taxonomy_mapping.json'

def get_db():
    return psycopg2.connect(os.environ['DATABASE_URL'])

def load_mapping():
    """Load EOL taxonomy mapping."""
    print(f"📋 Loading EOL taxonomy mapping...")
    
    with open(MAPPING_FILE, 'r') as f:
        mapping = json.load(f)
    
    # Convert to page_id → taxonomy_id lookup
    page_to_tax = {}
    for tax_id, info in mapping.items():
        page_id = str(info['eol_page_id'])
        page_to_tax[page_id] = int(tax_id)
    
    print(f"✅ Loaded {len(page_to_tax):,} page_id → taxonomy_id mappings")
    return page_to_tax

def backfill_taxonomy_ids(page_to_tax):
    """Backfill taxonomy_id for images with eol_page_id but no taxonomy_id."""
    print(f"\n🔄 Backfilling taxonomy_id for orphaned images...")
    
    conn = get_db()
    cur = conn.cursor()
    
    # Count orphaned images
    cur.execute("""
        SELECT COUNT(*) 
        FROM orchid_images 
        WHERE eol_page_id IS NOT NULL 
        AND taxonomy_id IS NULL
    """)
    orphaned_count = cur.fetchone()[0]
    print(f"   Found {orphaned_count:,} images with eol_page_id but no taxonomy_id")
    
    if orphaned_count == 0:
        print("   ✅ No orphaned images to backfill!")
        return
    
    # Backfill using mapping
    updated = 0
    batch_size = 1000
    
    # Get all orphaned eol_page_ids
    cur.execute("""
        SELECT DISTINCT eol_page_id 
        FROM orchid_images 
        WHERE eol_page_id IS NOT NULL 
        AND taxonomy_id IS NULL
    """)
    
    orphaned_pages = [row[0] for row in cur.fetchall()]
    print(f"   Processing {len(orphaned_pages):,} unique page_ids...")
    
    for page_id in orphaned_pages:
        if page_id in page_to_tax:
            taxonomy_id = page_to_tax[page_id]
            
            cur.execute("""
                UPDATE orchid_images 
                SET taxonomy_id = %s 
                WHERE eol_page_id = %s 
                AND taxonomy_id IS NULL
            """, (taxonomy_id, page_id))
            
            updated += cur.rowcount
            
            if updated % batch_size == 0:
                conn.commit()
                print(f"   Updated {updated:,} images...")
    
    conn.commit()
    print(f"✅ Backfilled taxonomy_id for {updated:,} images!")
    
    # Show new stats
    cur.execute("""
        SELECT 
            COUNT(*) as total_images,
            COUNT(DISTINCT taxonomy_id) as unique_species,
            ROUND(AVG(CASE WHEN taxonomy_id IS NOT NULL THEN 1 ELSE 0 END) * 100, 2) as pct_with_taxonomy
        FROM orchid_images
    """)
    
    row = cur.fetchone()
    print(f"\n📊 Updated Database Stats:")
    print(f"   Total images: {row[0]:,}")
    print(f"   Unique species: {row[1]:,}")
    print(f"   % with taxonomy: {row[2]}%")
    
    cur.close()
    conn.close()

if __name__ == '__main__':
    print("=" * 80)
    print("TAXONOMY ID BACKFILL")
    print("Linking orphaned images to orchid_taxonomy")
    print("=" * 80)
    print()
    
    page_to_tax = load_mapping()
    backfill_taxonomy_ids(page_to_tax)
    
    print()
    print("=" * 80)
    print("✅ BACKFILL COMPLETE!")
    print("=" * 80)
