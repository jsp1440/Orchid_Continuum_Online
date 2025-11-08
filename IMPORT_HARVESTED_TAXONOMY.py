#!/usr/bin/env python3
"""
IMPORT EXTERNALLY HARVESTED EOL TAXONOMY
Run this in Replit AFTER Mac/Julius provides the taxonomy CSV

Validates against 7,439 verified species before importing
"""

import os
import csv
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

DATABASE_URL = os.environ.get('DATABASE_URL')

def import_taxonomy(harvested_csv):
    """
    Import externally harvested taxonomy with validation
    
    Args:
        harvested_csv: CSV from Mac/Julius with columns:
                      page_id,scientific_name,genus,species,family,common_names
    """
    
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    print("="*80)
    print("IMPORTING EXTERNALLY HARVESTED EOL TAXONOMY")
    print("="*80)
    print(f"Started: {datetime.now()}\n")
    
    # Load verified taxonomy for validation
    print("📚 Loading verified taxonomy for validation...")
    cursor.execute("""
        SELECT DISTINCT genus, species, scientific_name
        FROM orchid_taxonomy
        WHERE genus IS NOT NULL
    """)
    verified = cursor.fetchall()
    
    # Create verification sets
    verified_genera = {v['genus'].lower() for v in verified if v['genus']}
    verified_species = {
        (v['genus'].lower(), v['species'].lower()) 
        for v in verified 
        if v['genus'] and v['species']
    }
    verified_names = {v['scientific_name'].lower() for v in verified if v['scientific_name']}
    
    print(f"✓ Loaded {len(verified_genera):,} verified genera")
    print(f"✓ Loaded {len(verified_species):,} verified species")
    print(f"✓ Loaded {len(verified_names):,} verified scientific names\n")
    
    # Read harvested taxonomy
    print(f"📖 Reading {harvested_csv}...")
    with open(harvested_csv, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    total = len(rows)
    print(f"✓ Loaded {total:,} harvested records\n")
    
    # Import with validation
    print("🔬 Importing with validation...")
    imported = 0
    skipped_no_data = 0
    skipped_unverified = 0
    
    for idx, row in enumerate(rows, 1):
        page_id = row.get('page_id')
        sci_name = row.get('scientific_name', '').strip()
        genus = row.get('genus', '').strip()
        species = row.get('species', '').strip()
        family = row.get('family', '').strip()
        common_names = row.get('common_names', '').strip()
        
        # Skip if no data
        if not sci_name or not genus:
            skipped_no_data += 1
            continue
        
        # Validate against verified taxonomy
        is_verified = False
        if sci_name.lower() in verified_names:
            is_verified = True
        elif genus.lower() in verified_genera:
            if not species or (genus.lower(), species.lower()) in verified_species:
                is_verified = True
        
        if not is_verified:
            skipped_unverified += 1
            continue
        
        # Import to database
        try:
            cursor.execute("""
                UPDATE eol_images
                SET scientific_name = %s,
                    genus = %s,
                    species = %s,
                    family = %s,
                    common_names = %s
                WHERE page_id = %s
            """, (sci_name, genus, species, family, common_names, page_id))
            
            if cursor.rowcount > 0:
                imported += 1
                if imported % 1000 == 0:
                    conn.commit()
                    print(f"  Progress: {imported:,} imported ({idx:,}/{total:,} processed)")
        
        except Exception as e:
            print(f"  Error importing page_id {page_id}: {e}")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    # Final summary
    print(f"\n{'='*80}")
    print(f"IMPORT COMPLETE")
    print(f"{'='*80}")
    print(f"Total records processed: {total:,}")
    print(f"Successfully imported: {imported:,}")
    print(f"Skipped (no data): {skipped_no_data:,}")
    print(f"Skipped (unverified): {skipped_unverified:,}")
    print(f"Import rate: {imported/total*100:.1f}%")
    
    # Verification
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN scientific_name IS NOT NULL THEN 1 END) as with_names
        FROM eol_images
    """)
    stats = cursor.fetchone()
    cursor.close()
    conn.close()
    
    print(f"\n✓ Database now has {stats[1]:,}/{stats[0]:,} images with taxonomy")
    print(f"  ({stats[1]/stats[0]*100:.1f}% complete)")

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 IMPORT_HARVESTED_TAXONOMY.py <harvested_csv>")
        print("\nExample:")
        print("  python3 IMPORT_HARVESTED_TAXONOMY.py eol_taxonomy_harvested.csv")
        sys.exit(1)
    
    import_taxonomy(sys.argv[1])
