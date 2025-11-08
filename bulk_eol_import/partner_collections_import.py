#!/usr/bin/env python3
"""
Import partner collections from Google Drive
Standalone script - no Flask dependencies
"""
import re
import os
import psycopg2
import requests
from datetime import datetime

# Partner collection folders
PARTNER_FOLDERS = {
    'Roberta Fox': '1aPJ6fzPCP6PdjCciPggpoxl9ZCCN7opy',  # 53 files
    'Chris Howard Main': '1jQoQ9x-2f1ENZq7iVCgneAmoQIvc6xIS',
    'Chris Howard Shared 1': '1VtKUMeQr_bAH6wpp37gsz3ecfwX1yS75',
    'Chris Howard Shared 2': '12oAfJ5ikrMv-vC5Srh5Gg5Ll3we9tU35',
}

def get_db():
    return psycopg2.connect(os.environ['DATABASE_URL'])

def extract_species_from_filename(filename):
    """Extract genus and species from filename.
    
    Examples:
        Cattleya_bicolor.jpg → genus=Cattleya, species=bicolor
        Paphiopedilum hirsutissimum.JPG → genus=Paphiopedilum, species=hirsutissimum
        Dendrobium_x_hybrid.jpg → genus=Dendrobium, species=x hybrid (hybrid)
    """
    # Remove extension
    name = filename.rsplit('.', 1)[0]
    
    # Replace underscores with spaces
    name = name.replace('_', ' ')
    
    # Extract first two words (genus species)
    parts = name.split()
    
    if len(parts) >= 2:
        genus = parts[0].capitalize()
        species = parts[1].lower()
        
        # Check for hybrid marker
        is_hybrid = '×' in name or ' x ' in name.lower() or species == 'x'
        
        return genus, species, is_hybrid
    
    return None, None, False

def find_taxonomy_id(genus, species, is_hybrid=False):
    """Find taxonomy_id for a genus/species combination."""
    conn = get_db()
    cur = conn.cursor()
    
    # Try exact match first
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
    
    # Try case-insensitive match
    cur.execute("""
        SELECT id FROM orchid_taxonomy 
        WHERE LOWER(genus) = LOWER(%s) AND LOWER(species) = LOWER(%s)
        LIMIT 1
    """, (genus, species))
    
    row = cur.fetchone()
    cur.close()
    conn.close()
    
    return row[0] if row else None

def get_file_ids_from_folder(folder_id):
    """Extract Google Drive file IDs from a folder.
    
    Uses the embedded folder view to extract file IDs without auth.
    """
    print(f"  📁 Scanning folder {folder_id}...")
    
    try:
        url = f'https://drive.google.com/embeddedfolderview?id={folder_id}'
        response = requests.get(url, timeout=20)
        
        if response.status_code != 200:
            print(f"  ❌ Cannot access folder (status {response.status_code})")
            return []
        
        html = response.text
        
        # Extract file IDs using patterns
        patterns = [
            r'file/d/([a-zA-Z0-9_-]{25,35})',  # Direct file links
            r'id=([a-zA-Z0-9_-]{25,35})',      # ID parameters
        ]
        
        file_ids = set()
        for pattern in patterns:
            matches = re.findall(pattern, html)
            for match in matches:
                if len(match) >= 25 and match != folder_id:
                    file_ids.add(match)
        
        print(f"  ✅ Found {len(file_ids)} file IDs")
        return list(file_ids)
        
    except Exception as e:
        print(f"  ❌ Error scanning folder: {e}")
        return []

def import_partner_images():
    """Import images from all partner collections."""
    print("=" * 80)
    print("PARTNER COLLECTIONS IMPORT")
    print("=" * 80)
    print()
    
    conn = get_db()
    cur = conn.cursor()
    
    total_imported = 0
    total_skipped = 0
    stats_by_partner = {}
    
    for partner_name, folder_id in PARTNER_FOLDERS.items():
        print(f"\n🌸 Processing: {partner_name}")
        print(f"   Folder ID: {folder_id}")
        
        file_ids = get_file_ids_from_folder(folder_id)
        
        if not file_ids:
            print(f"  ⚠️  No files found in folder")
            continue
        
        imported = 0
        skipped = 0
        no_match = 0
        
        for file_id in file_ids:
            # Build image URL
            image_url = f'https://drive.google.com/uc?export=view&id={file_id}'
            
            # Check if already imported
            cur.execute("""
                SELECT id FROM orchid_images WHERE image_url = %s
            """, (image_url,))
            
            if cur.fetchone():
                skipped += 1
                continue
            
            # Try to extract species from file ID or use placeholder
            # For now, import without taxonomy_id - we'll backfill later
            
            try:
                cur.execute("""
                    INSERT INTO orchid_images (
                        image_url, image_source, wild_specimen, 
                        image_license, downloaded_at
                    )
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    image_url,
                    f'{partner_name} - Google Drive',
                    False,  # Partner photos are typically cultivated
                    'Private Collection',
                    datetime.now()
                ))
                
                imported += 1
                
                if imported % 50 == 0:
                    conn.commit()
                    print(f"    ... {imported} imported so far")
                    
            except Exception as e:
                print(f"  ❌ Error importing {file_id}: {e}")
                continue
        
        conn.commit()
        
        stats_by_partner[partner_name] = {
            'imported': imported,
            'skipped': skipped,
            'no_match': no_match
        }
        
        total_imported += imported
        total_skipped += skipped
        
        print(f"  ✅ {partner_name}: {imported} imported, {skipped} duplicates")
    
    cur.close()
    conn.close()
    
    print()
    print("=" * 80)
    print("✅ PARTNER IMPORT COMPLETE!")
    print("=" * 80)
    print(f"Total imported: {total_imported}")
    print(f"Total skipped: {total_skipped}")
    print()
    print("Partner breakdown:")
    for partner, stats in stats_by_partner.items():
        print(f"  {partner}: {stats['imported']} images")

if __name__ == '__main__':
    import_partner_images()
