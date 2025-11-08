#!/usr/bin/env python3
"""
Step 4: Import Chris Howard + Roberta Fox images from Google Drive
Imports images with basic taxonomy matching (genus/species/hybrid names only)
Full 54-field metadata will be added later from EOL/GBIF bulk imports
"""
import os
import sys
import psycopg2
import requests
import re
from datetime import datetime
import json
from urllib.parse import quote

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Google Drive folder with Chris Howard + Roberta Fox images
GDRIVE_FOLDER_ID = '12oAfJ5ikrMv-vC5Srh5Gg5Ll3we9tU35'

def get_db():
    return psycopg2.connect(os.environ['DATABASE_URL'])

def load_synonyms_and_abbreviations():
    """Load genus abbreviations and synonyms from database."""
    print("📚 Loading synonyms and abbreviations...")
    
    conn = get_db()
    cur = conn.cursor()
    
    # Get all taxonomy with synonyms
    cur.execute("""
        SELECT 
            id, 
            scientific_name, 
            genus, 
            species,
            synonyms,
            synonyms_json
        FROM orchid_taxonomy
        WHERE scientific_name IS NOT NULL
    """)
    
    # Build lookup dictionaries
    name_to_id = {}
    abbrev_to_genus = {}
    
    for tax_id, sci_name, genus, species, synonyms, synonyms_json in cur.fetchall():
        # Add scientific name
        name_to_id[sci_name.lower().strip()] = tax_id
        
        # Add genus + species
        if genus and species:
            name_to_id[f"{genus} {species}".lower().strip()] = tax_id
        
        # Add synonyms from text field
        if synonyms:
            for syn in synonyms.split(','):
                syn = syn.strip()
                if syn:
                    name_to_id[syn.lower()] = tax_id
        
        # Add synonyms from JSON field
        if synonyms_json:
            try:
                syn_list = json.loads(synonyms_json) if isinstance(synonyms_json, str) else synonyms_json
                for syn in syn_list:
                    if isinstance(syn, dict):
                        syn_name = syn.get('name', '')
                    else:
                        syn_name = str(syn)
                    if syn_name:
                        name_to_id[syn_name.lower().strip()] = tax_id
            except:
                pass
        
        # Common abbreviations
        if genus:
            # First 3-4 letters
            abbrev_to_genus[genus[:3].lower()] = genus
            abbrev_to_genus[genus[:4].lower()] = genus
            # Common patterns
            if '.' in genus:
                parts = genus.split('.')
                abbrev_to_genus[parts[0].lower()] = genus
    
    cur.close()
    conn.close()
    
    print(f"✅ Loaded {len(name_to_id):,} name variations")
    print(f"✅ Loaded {len(abbrev_to_genus):,} genus abbreviations")
    
    return name_to_id, abbrev_to_genus

def parse_orchid_name_from_filename(filename, abbrev_to_genus):
    """
    Extract orchid name from filename.
    Handles patterns like:
    - Phal amabilis.jpg
    - Cattleya labiata.jpg
    - Dendrobium nobile var album.jpg
    - Paph rothschildianum.jpg
    """
    if not filename:
        return None
    
    # Remove file extension
    name = os.path.splitext(filename)[0]
    
    # Clean up common patterns
    name = name.replace('_', ' ').replace('-', ' ')
    name = re.sub(r'\d+', '', name)  # Remove numbers
    name = re.sub(r'[^a-zA-Z\s×.×]', '', name)  # Keep only letters, spaces, hybrid markers
    name = ' '.join(name.split())  # Normalize spaces
    
    if not name:
        return None
    
    parts = name.split()
    if len(parts) < 2:
        return None
    
    genus_part = parts[0]
    species_part = parts[1] if len(parts) > 1 else ''
    
    # Try to expand abbreviation
    genus_lower = genus_part.lower()
    if genus_lower in abbrev_to_genus:
        full_genus = abbrev_to_genus[genus_lower]
    else:
        full_genus = genus_part.capitalize()
    
    # Build scientific name
    if species_part:
        scientific_name = f"{full_genus} {species_part.lower()}"
    else:
        scientific_name = full_genus
    
    return scientific_name

def detect_hybrid_type(name):
    """Detect if name is hybrid or intergeneric."""
    if not name:
        return False, False
    
    is_hybrid = '×' in name or ' x ' in name.lower() or '×' in name
    
    # Check for intergeneric (multiple capitals in first word)
    parts = name.split()
    if len(parts) > 0:
        first_word = parts[0]
        capital_count = sum(1 for c in first_word if c.isupper())
        is_intergeneric = capital_count > 1
    else:
        is_intergeneric = False
    
    return is_hybrid, is_intergeneric

def get_folder_file_list(folder_id):
    """
    Get list of image files from Google Drive folder.
    Uses public access via embeddedfolderview.
    """
    print(f"📂 Accessing Google Drive folder: {folder_id}")
    
    url = f'https://drive.google.com/embeddedfolderview?id={folder_id}'
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        html = response.text
        
        # Extract file IDs and names
        # Pattern: file/d/{file_id}/view or similar
        file_pattern = r'file/d/([a-zA-Z0-9_-]{25,40})'
        file_ids = re.findall(file_pattern, html)
        
        # Try to extract filenames from HTML
        # This is approximate - might need adjustment
        name_pattern = r'title="([^"]+\.(jpg|jpeg|png|JPG|JPEG|PNG))"'
        filenames = re.findall(name_pattern, html)
        
        files = []
        for file_id in set(file_ids):
            # Build public URL
            image_url = f'https://drive.google.com/uc?export=view&id={file_id}'
            files.append({
                'id': file_id,
                'url': image_url,
                'name': None  # We'll extract from URL or skip
            })
        
        print(f"✅ Found {len(files)} potential image files")
        return files
        
    except Exception as e:
        print(f"❌ Error accessing folder: {e}")
        print(f"\n💡 TIP: Make sure folder is publicly viewable")
        print(f"   Right-click folder → Share → Anyone with the link can view")
        return []

def match_name_to_taxonomy(scientific_name, name_to_id):
    """Match scientific name to taxonomy ID."""
    if not scientific_name:
        return None
    
    # Try exact match
    name_lower = scientific_name.lower().strip()
    if name_lower in name_to_id:
        return name_to_id[name_lower]
    
    # Try without author
    name_parts = name_lower.split()
    if len(name_parts) >= 2:
        genus_species = f"{name_parts[0]} {name_parts[1]}"
        if genus_species in name_to_id:
            return name_to_id[genus_species]
    
    return None

def import_images_from_folder(files, name_to_id, abbrev_to_genus, photographer='Unknown', source='Google Drive'):
    """Import images from Google Drive file list."""
    print(f"\n📥 Importing images...")
    print(f"   Note: Without filenames, images will be imported with generic names")
    print(f"   You can update names manually or via spreadsheet later")
    
    conn = get_db()
    cur = conn.cursor()
    
    imported = 0
    matched = 0
    unmatched = []
    skipped_no_name = 0
    
    for idx, file_info in enumerate(files, 1):
        file_id = file_info['id']
        image_url = file_info['url']
        filename = file_info.get('name')
        
        # Skip if no filename (we can't extract species name)
        if not filename:
            skipped_no_name += 1
            continue
        
        # Extract orchid name from filename
        scientific_name = parse_orchid_name_from_filename(filename, abbrev_to_genus)
        
        if not scientific_name:
            continue
        
        # Match to taxonomy
        taxonomy_id = match_name_to_taxonomy(scientific_name, name_to_id)
        
        if not taxonomy_id:
            unmatched.append(scientific_name)
            continue
        
        matched += 1
        
        # Check if already exists
        cur.execute(
            "SELECT 1 FROM orchid_images WHERE image_url = %s",
            (image_url,)
        )
        if cur.fetchone():
            continue
        
        # Detect hybrid type
        is_hybrid, is_intergeneric = detect_hybrid_type(scientific_name)
        
        # Build metadata
        metadata = {
            'import_source': 'Google Drive Bulk Import',
            'import_date': datetime.now().isoformat(),
            'original_filename': filename,
            'file_id': file_id
        }
        
        # Insert image (MINIMAL FIELDS - metadata will come from EOL/GBIF later)
        try:
            cur.execute("""
                INSERT INTO orchid_images (
                    taxonomy_id, image_url, image_source, image_rights_holder,
                    is_hybrid, is_intergeneric,
                    image_description, media_metadata, downloaded_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                taxonomy_id,
                image_url,
                source,
                photographer,
                is_hybrid,
                is_intergeneric,
                f'{scientific_name} - {photographer}',
                json.dumps(metadata),
                datetime.now()
            ))
            imported += 1
            
            if imported % 50 == 0:
                conn.commit()
                print(f"   ✅ Imported {imported} / Matched {matched} / Processed {idx}/{len(files)}")
                
        except Exception as e:
            print(f"   ⚠️  Error importing {scientific_name}: {e}")
            continue
    
    conn.commit()
    cur.close()
    conn.close()
    
    print(f"\n{'='*80}")
    print(f"✅ IMPORT COMPLETE")
    print(f"{'='*80}")
    print(f"  Files processed: {len(files)}")
    print(f"  Skipped (no filename): {skipped_no_name}")
    print(f"  Matched to taxonomy: {matched}")
    print(f"  Images imported: {imported}")
    print(f"  Unmatched: {len(unmatched)}")
    
    if unmatched:
        print(f"\n⚠️  Sample unmatched names (top 20):")
        for name in unmatched[:20]:
            print(f"    - {name}")
    
    return imported, matched

def main():
    print("=" * 80)
    print("GOOGLE DRIVE IMAGE IMPORTER")
    print("Chris Howard + Roberta Fox Collections")
    print("=" * 80)
    print()
    
    # Load synonyms and abbreviations
    name_to_id, abbrev_to_genus = load_synonyms_and_abbreviations()
    
    # Get file list from Google Drive
    files = get_folder_file_list(GDRIVE_FOLDER_ID)
    
    if not files:
        print("\n❌ No files found in folder")
        print("\n💡 MANUAL OPTION:")
        print("   1. Open folder in browser")
        print("   2. List image filenames")
        print("   3. Create CSV with: filename, photographer, source")
        return
    
    # Import images
    imported, matched = import_images_from_folder(
        files, 
        name_to_id, 
        abbrev_to_genus,
        photographer='Chris Howard / Roberta Fox',
        source='Google Drive Collection'
    )
    
    print()
    print("=" * 80)
    print("✅ GOOGLE DRIVE IMPORT COMPLETE")
    print("=" * 80)
    print()
    print("Next step: Run bulk EOL import to add 54 metadata fields")
    print("  python bulk_eol_import/2_import_images_and_traits.py")

if __name__ == '__main__':
    main()
