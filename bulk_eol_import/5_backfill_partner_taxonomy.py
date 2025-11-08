#!/usr/bin/env python3
"""
Backfill taxonomy_id for partner collections using filename parsing
Fixes the 875 Roberta Fox images that were imported without taxonomy
"""
import re
import os
import psycopg2

# Expanded genus abbreviations (includes single-letter codes)
GENUS_ABBREVIATIONS = {
    # Single letter
    'C': 'Cattleya', 'C.': 'Cattleya',
    'L': 'Laelia', 'L.': 'Laelia',
    'V': 'Vanda', 'V.': 'Vanda',
    # Common abbreviations
    'Aca.': 'Acanthephippium',
    'Acia.': 'Acianthera',
    'Ada.': 'Ada',
    'Aer.': 'Aerangis',
    'Aergs.': 'Aerangis',
    'Ame.': 'Amesiella',
    'Anc.': 'Ancistrochilus',
    'Angcm.': 'Angraecum',
    'Bif.': 'Bifrenaria',
    'Blc.': 'Brassolaeliocattleya',
    'Brs.': 'Brassavola',
    'Bulb.': 'Bulbophyllum',
    'Cat.': 'Catasetum',
    'Catt.': 'Cattleya',
    'Coel.': 'Coelogyne',
    'Cyc.': 'Cycnoches',
    'Cym.': 'Cymbidium',
    'Cyp.': 'Cypripedium',
    'Den.': 'Dendrobium', 'Dend.': 'Dendrobium',
    'Enc.': 'Encyclia',
    'Epi.': 'Epidendrum',
    'Lc.': 'Laeliocattleya',
    'Lyc.': 'Lycaste',
    'Masd.': 'Masdevallia',
    'Max.': 'Maxillaria',
    'Milt.': 'Miltonia',
    'Onc.': 'Oncidium',
    'Paph.': 'Paphiopedilum',
    'Phal.': 'Phalaenopsis',
    'Pls.': 'Pleione',
    'Pot.': 'Potinara',
    'Rl.': 'Rhyncholaelia', 'Rl': 'Rhyncholaelia',
    'Rlc.': 'Rhyncholaeliocattleya',
    'Rhy.': 'Rhynchostylis',
    'Slc.': 'Sophrolaeliocattleya',
    'Stan.': 'Stanhopea',
    'Vanc.': 'Vanda',
    'Zyg.': 'Zygopetalum',
}

def get_db():
    return psycopg2.connect(os.environ['DATABASE_URL'])

def parse_genus_species_from_filename(filename):
    """Parse genus/species from various filename formats.
    
    Roberta Fox format: 1289_Epi villotae.jpg
    Chris Howard format: Aca. mantinianum_20.jpg
    Full name format: Rhyncholaelia digbyana.jpg
    """
    # Remove extension
    name = filename.rsplit('.', 1)[0]
    
    # Remove trailing _numbers or Tnumbers
    name = re.sub(r'[_T]\d+$', '', name)
    
    # Remove leading numbers (Roberta Fox format)
    name = re.sub(r'^\d+_?', '', name)
    
    # Check for hybrid markers
    is_hybrid = bool(re.search(r'[\(x×]|hybrid', name.lower()))
    
    # Remove parentheses
    name = re.sub(r'\([^)]+\)', '', name).strip()
    
    # Split into parts
    parts = name.split()
    
    if len(parts) < 2:
        return None, None, is_hybrid
    
    genus_part = parts[0]
    species_part = parts[1] if len(parts) > 1 else None
    
    # Expand abbreviation
    if genus_part in GENUS_ABBREVIATIONS:
        genus = GENUS_ABBREVIATIONS[genus_part]
    elif genus_part.rstrip('.') in GENUS_ABBREVIATIONS:
        genus = GENUS_ABBREVIATIONS[genus_part.rstrip('.')]
    else:
        genus = genus_part.capitalize()
    
    # Clean species
    if species_part:
        species = species_part.lower()
        # Remove special characters but keep hyphens
        species = re.sub(r'[^a-z-]', '', species)
    else:
        species = None
    
    return genus, species, is_hybrid

def find_taxonomy_id(genus, species):
    """Find taxonomy_id in orchid_taxonomy."""
    if not genus or not species:
        return None
    
    conn = get_db()
    cur = conn.cursor()
    
    # Exact match
    cur.execute("""
        SELECT id FROM orchid_taxonomy 
        WHERE genus = %s AND species = %s
        LIMIT 1
    """, (genus, species))
    
    row = cur.fetchone()
    if row:
        cur.close()
        conn.close()
        return row[0]
    
    # Case-insensitive
    cur.execute("""
        SELECT id FROM orchid_taxonomy 
        WHERE LOWER(genus) = LOWER(%s) AND LOWER(species) = LOWER(%s)
        LIMIT 1
    """, (genus, species))
    
    row = cur.fetchone()
    cur.close()
    conn.close()
    
    return row[0] if row else None

def backfill_partner_taxonomy():
    """Backfill taxonomy_id for partner collections."""
    print("=" * 80)
    print("PARTNER TAXONOMY BACKFILL")
    print("=" * 80)
    print()
    
    conn = get_db()
    cur = conn.cursor()
    
    # Get all partner images without taxonomy_id
    cur.execute("""
        SELECT id, alt_text, image_source
        FROM orchid_images
        WHERE (image_source LIKE '%Collection%' OR image_source LIKE '%Fox%' OR image_source LIKE '%Howard%')
        AND taxonomy_id IS NULL
        AND alt_text IS NOT NULL
    """)
    
    orphaned = cur.fetchall()
    print(f"📋 Found {len(orphaned)} partner images without taxonomy")
    print()
    
    updated = 0
    no_match = 0
    
    for image_id, filename, source in orphaned:
        genus, species, is_hybrid = parse_genus_species_from_filename(filename)
        
        if not genus or not species:
            no_match += 1
            continue
        
        taxonomy_id = find_taxonomy_id(genus, species)
        
        if taxonomy_id:
            cur.execute("""
                UPDATE orchid_images
                SET taxonomy_id = %s, is_hybrid = %s
                WHERE id = %s
            """, (taxonomy_id, is_hybrid, image_id))
            
            updated += 1
            
            if updated % 100 == 0:
                conn.commit()
                print(f"  ... Updated {updated} images")
        else:
            no_match += 1
    
    conn.commit()
    
    print()
    print(f"✅ Backfill complete!")
    print(f"   Updated: {updated}")
    print(f"   No match: {no_match}")
    
    # Show updated stats
    cur.execute("""
        SELECT 
            COUNT(*) as total_images,
            COUNT(DISTINCT taxonomy_id) as unique_species,
            COUNT(CASE WHEN taxonomy_id IS NOT NULL THEN 1 END) as images_with_taxonomy
        FROM orchid_images
    """)
    
    row = cur.fetchone()
    print()
    print("📊 Updated Database Stats:")
    print(f"   Total images: {row[0]:,}")
    print(f"   Unique species: {row[1]:,}")
    print(f"   Images with taxonomy: {row[2]:,} ({100*row[2]/row[0]:.1f}%)")
    
    # Show partner breakdown
    cur.execute("""
        SELECT image_source, 
               COUNT(*) as total,
               COUNT(CASE WHEN taxonomy_id IS NOT NULL THEN 1 END) as with_taxonomy
        FROM orchid_images
        WHERE image_source LIKE '%Collection%' OR image_source LIKE '%Fox%' OR image_source LIKE '%Howard%'
        GROUP BY image_source
        ORDER BY total DESC
    """)
    
    print()
    print("Partner Collections:")
    for source, total, with_tax in cur.fetchall():
        pct = 100 * with_tax / total if total > 0 else 0
        print(f"  {source}: {with_tax}/{total} ({pct:.1f}%)")
    
    cur.close()
    conn.close()
    
    print()
    print("=" * 80)

if __name__ == '__main__':
    backfill_partner_taxonomy()
