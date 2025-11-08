#!/usr/bin/env python3
"""
Import partner photos with species name extraction from filenames
Standalone script - parses genus/species from Google Drive filenames
"""
import re
import os
import psycopg2
import requests
from datetime import datetime
from bs4 import BeautifulSoup

# Partner collection folders
PARTNER_FOLDERS = {
    'Roberta Fox': '1YqIWmIfaXSy_0_bAbvSG8EMQjAuNq0lj',
    'Chris Howard': '1dJ5AbZ_iEdX4-SgHVA3RB-306meBedBu',
}

# Common genus abbreviations in orchid photography
GENUS_ABBREVIATIONS = {
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
    'C.': 'Cattleya',
    'Cat.': 'Catasetum',
    'Catt.': 'Cattleya',
    'Coel.': 'Coelogyne',
    'Cyc.': 'Cycnoches',
    'Cym.': 'Cymbidium',
    'Cyp.': 'Cypripedium',
    'Den.': 'Dendrobium',
    'Dend.': 'Dendrobium',
    'Enc.': 'Encyclia',
    'Epi.': 'Epidendrum',
    'L.': 'Laelia',
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
    'Rlc.': 'Rhyncholaeliocattleya',
    'Rhy.': 'Rhynchostylis',
    'Slc.': 'Sophrolaeliocattleya',
    'Stan.': 'Stanhopea',
    'V.': 'Vanda',
    'Vanc.': 'Vanda',
    'Zyg.': 'Zygopetalum',
}

def get_db():
    return psycopg2.connect(os.environ['DATABASE_URL'])

def extract_filenames_from_folder(folder_id):
    """Extract filenames from Google Drive folder using embeddedfolderview."""
    print(f"  📁 Extracting filenames from folder {folder_id}...")
    
    try:
        url = f'https://drive.google.com/embeddedfolderview?id={folder_id}'
        response = requests.get(url, timeout=30)
        
        if response.status_code != 200:
            print(f"  ❌ Cannot access folder (status {response.status_code})")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all filename elements
        filenames = []
        for div in soup.find_all('div', class_='flip-entry-title'):
            filename = div.get_text(strip=True)
            if filename and (filename.endswith('.jpg') or filename.endswith('.JPG') or 
                           filename.endswith('.jpeg') or filename.endswith('.JPEG') or
                           filename.endswith('.png') or filename.endswith('.PNG')):
                filenames.append(filename)
        
        print(f"  ✅ Extracted {len(filenames)} filenames")
        return filenames
        
    except Exception as e:
        print(f"  ❌ Error extracting filenames: {e}")
        return []

def extract_file_ids_from_folder(folder_id):
    """Extract Google Drive file IDs from folder."""
    try:
        url = f'https://drive.google.com/embeddedfolderview?id={folder_id}'
        response = requests.get(url, timeout=30)
        
        if response.status_code != 200:
            return []
        
        html = response.text
        
        patterns = [
            r'file/d/([a-zA-Z0-9_-]{25,35})',
            r'id=([a-zA-Z0-9_-]{25,35})',
        ]
        
        file_ids = set()
        for pattern in patterns:
            matches = re.findall(pattern, html)
            for match in matches:
                if len(match) >= 25 and match != folder_id:
                    file_ids.add(match)
        
        return list(file_ids)
        
    except Exception as e:
        print(f"  ❌ Error extracting file IDs: {e}")
        return []

def parse_genus_species_from_filename(filename):
    """Parse genus and species from filename.
    
    Examples:
        Aca. mantinianum_20.jpg → genus=Acanthephippium, species=mantinianum
        Aer. crassifolia_413.jpg → genus=Aerangis, species=crassifolia
        Cattleya bicolor.jpg → genus=Cattleya, species=bicolor
        (Lyc. Cherish x Lyc. Shonan Bright)_1030.jpg → hybrid detected
    """
    # Remove extension
    name = filename.rsplit('.', 1)[0]
    
    # Remove trailing numbers like _20, _413, etc.
    name = re.sub(r'_\d+$', '', name)
    
    # Check for hybrid markers
    is_hybrid = bool(re.search(r'[\(x×]|hybrid', name.lower()))
    
    # Remove parentheses and content for hybrids
    name = re.sub(r'\([^)]+\)', '', name).strip()
    
    # Split into parts
    parts = name.split()
    
    if len(parts) < 2:
        return None, None, is_hybrid
    
    # Check if first part is abbreviation
    genus_part = parts[0]
    species_part = parts[1] if len(parts) > 1 else None
    
    # Expand abbreviation if found
    if genus_part in GENUS_ABBREVIATIONS:
        genus = GENUS_ABBREVIATIONS[genus_part]
    else:
        genus = genus_part.capitalize()
    
    # Clean species name
    if species_part:
        species = species_part.lower()
        # Remove special characters
        species = re.sub(r'[^a-z-]', '', species)
    else:
        species = None
    
    return genus, species, is_hybrid

def find_taxonomy_id(genus, species):
    """Find taxonomy_id for genus/species in orchid_taxonomy."""
    if not genus or not species:
        return None
    
    conn = get_db()
    cur = conn.cursor()
    
    # Try exact match
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
    
    # Try case-insensitive
    cur.execute("""
        SELECT id FROM orchid_taxonomy 
        WHERE LOWER(genus) = LOWER(%s) AND LOWER(species) = LOWER(%s)
        LIMIT 1
    """, (genus, species))
    
    row = cur.fetchone()
    cur.close()
    conn.close()
    
    return row[0] if row else None

def import_partner_photos():
    """Import photos from partner collections with filename parsing."""
    print("=" * 80)
    print("PARTNER PHOTO IMPORT WITH SPECIES DETECTION")
    print("=" * 80)
    print()
    
    conn = get_db()
    cur = conn.cursor()
    
    total_imported = 0
    total_matched = 0
    total_skipped = 0
    stats_by_partner = {}
    
    for partner_name, folder_id in PARTNER_FOLDERS.items():
        print(f"\n🌸 Processing: {partner_name}")
        print(f"   Folder ID: {folder_id}")
        
        # Extract filenames AND file IDs
        filenames = extract_filenames_from_folder(folder_id)
        file_ids = extract_file_ids_from_folder(folder_id)
        
        if not filenames or not file_ids:
            print(f"  ⚠️  No files found")
            continue
        
        # Match filenames to file IDs (assumes same order)
        if len(filenames) != len(file_ids):
            print(f"  ⚠️  Mismatch: {len(filenames)} names vs {len(file_ids)} IDs")
            # Use minimum to avoid index errors
            min_count = min(len(filenames), len(file_ids))
            filenames = filenames[:min_count]
            file_ids = file_ids[:min_count]
        
        imported = 0
        matched = 0
        skipped = 0
        
        for filename, file_id in zip(filenames, file_ids):
            # Build image URL
            image_url = f'https://drive.google.com/uc?export=view&id={file_id}'
            
            # Check if already imported
            cur.execute("SELECT id FROM orchid_images WHERE image_url = %s", (image_url,))
            if cur.fetchone():
                skipped += 1
                continue
            
            # Parse genus/species from filename
            genus, species, is_hybrid = parse_genus_species_from_filename(filename)
            
            # Find taxonomy_id
            taxonomy_id = None
            if genus and species:
                taxonomy_id = find_taxonomy_id(genus, species)
                if taxonomy_id:
                    matched += 1
            
            try:
                cur.execute("""
                    INSERT INTO orchid_images (
                        image_url, image_source, taxonomy_id, wild_specimen,
                        image_license, is_hybrid, alt_text, downloaded_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    image_url,
                    f'{partner_name} Collection',
                    taxonomy_id,
                    False,  # Cultivated
                    'Private Collection',
                    is_hybrid,
                    filename,  # Store original filename
                    datetime.now()
                ))
                
                imported += 1
                
                if imported % 50 == 0:
                    conn.commit()
                    print(f"    ... {imported} imported, {matched} matched to taxonomy")
                    
            except Exception as e:
                print(f"  ❌ Error importing {filename}: {e}")
                continue
        
        conn.commit()
        
        stats_by_partner[partner_name] = {
            'imported': imported,
            'matched': matched,
            'skipped': skipped
        }
        
        total_imported += imported
        total_matched += matched
        total_skipped += skipped
        
        print(f"  ✅ {partner_name}: {imported} imported, {matched} taxonomy matched, {skipped} duplicates")
    
    cur.close()
    conn.close()
    
    print()
    print("=" * 80)
    print("✅ PARTNER IMPORT COMPLETE!")
    print("=" * 80)
    print(f"Total imported: {total_imported}")
    print(f"Matched to taxonomy: {total_matched} ({100*total_matched/total_imported if total_imported else 0:.1f}%)")
    print(f"Total skipped: {total_skipped}")
    print()
    print("Partner breakdown:")
    for partner, stats in stats_by_partner.items():
        print(f"  {partner}:")
        print(f"    - {stats['imported']} images imported")
        print(f"    - {stats['matched']} matched to taxonomy")

if __name__ == '__main__':
    import_partner_photos()
