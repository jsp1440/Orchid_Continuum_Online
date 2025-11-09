#!/usr/bin/env python3
"""
Backfill taxonomy_id for existing Baker culture sheets
"""
import os
import psycopg2
import re

DATABASE_URL = os.environ.get('DATABASE_URL')

def clean_species_name(name):
    """Clean up species name"""
    # Remove newlines, extra whitespace
    cleaned = ' '.join(name.strip().split())
    # Remove author citations
    cleaned = re.sub(r'\([^)]+\)', '', cleaned).strip()
    cleaned = re.sub(r'\s+[A-Z][a-z]+\.?$', '', cleaned).strip()
    return cleaned

def backfill_taxonomy_ids():
    """Update Baker culture sheets with taxonomy_ids"""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    print("="*70)
    print("🔗 BACKFILLING BAKER TAXONOMY IDS")
    print("="*70)
    
    # Get all Baker records without taxonomy_id
    cur.execute("""
        SELECT id, scientific_name, genus, species
        FROM baker_culture_sheets
        WHERE taxonomy_id IS NULL
    """)
    
    records = cur.fetchall()
    print(f"📋 Found {len(records)} records to process")
    print()
    
    stats = {'matched': 0, 'unmatched': 0, 'cleaned': 0}
    
    for baker_id, orig_name, genus, species in records:
        # Clean the scientific name
        clean_name = clean_species_name(orig_name)
        
        if clean_name != orig_name:
            # Update scientific_name to cleaned version
            cur.execute("""
                UPDATE baker_culture_sheets
                SET scientific_name = %s
                WHERE id = %s
            """, (clean_name, baker_id))
            stats['cleaned'] += 1
        
        taxonomy_id = None
        
        # Try exact match on scientific name
        cur.execute("""
            SELECT id FROM orchid_taxonomy
            WHERE scientific_name = %s
            LIMIT 1
        """, (clean_name,))
        result = cur.fetchone()
        
        if result:
            taxonomy_id = result[0]
        elif genus and species:
            # Try genus + species match
            cur.execute("""
                SELECT id FROM orchid_taxonomy
                WHERE genus = %s AND species = %s
                LIMIT 1
            """, (genus, species))
            result = cur.fetchone()
            if result:
                taxonomy_id = result[0]
        
        if taxonomy_id:
            # Update taxonomy_id
            cur.execute("""
                UPDATE baker_culture_sheets
                SET taxonomy_id = %s
                WHERE id = %s
            """, (taxonomy_id, baker_id))
            print(f"✅ {clean_name} → taxonomy_id={taxonomy_id}")
            stats['matched'] += 1
        else:
            print(f"⚠️  {clean_name} → no match")
            stats['unmatched'] += 1
    
    conn.commit()
    cur.close()
    conn.close()
    
    print()
    print("="*70)
    print("📊 BACKFILL COMPLETE")
    print("="*70)
    print(f"✅ Matched: {stats['matched']}")
    print(f"🧹 Cleaned: {stats['cleaned']}")
    print(f"⚠️  Unmatched: {stats['unmatched']}")
    print("="*70)

if __name__ == '__main__':
    backfill_taxonomy_ids()
