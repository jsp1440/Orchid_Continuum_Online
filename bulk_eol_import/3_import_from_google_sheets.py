#!/usr/bin/env python3
"""
Step 3: Import existing matched images from Google Sheets
Imports Roberta Fox, Chris Howard, and other curated collections
"""
import os
import sys
import psycopg2
import csv
import requests
from datetime import datetime
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Google Drive file IDs from your links
SHEETS_FILE_ID = '14EtrNTceyo2ujNKCsy5XH9lWaJ3YsBmF'
SHARED_FOLDER_ID = '1VtKUMeQr_bAH6wpp37gsz3ecfwX1yS75'

def get_db():
    return psycopg2.connect(os.environ['DATABASE_URL'])

def download_sheet_as_csv(file_id):
    """Download Google Sheet as CSV"""
    print(f"📥 Downloading Google Sheet: {file_id}")
    
    # Export as CSV
    url = f'https://docs.google.com/spreadsheets/d/{file_id}/export?format=csv'
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Save to temp file
        csv_path = f'bulk_eol_import/google_sheet_{file_id}.csv'
        with open(csv_path, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ Downloaded to: {csv_path}")
        return csv_path
        
    except Exception as e:
        print(f"❌ Failed to download sheet: {e}")
        print(f"\n💡 TIP: Make sure the sheet is publicly viewable!")
        print(f"   File → Share → Anyone with the link can view")
        return None

def detect_hybrid_type(scientific_name):
    """Detect if name is hybrid or intergeneric."""
    if not scientific_name:
        return False, False
    
    name = scientific_name.strip()
    is_hybrid = '×' in name or ' x ' in name.lower()
    
    # Check for intergeneric (multiple genus names)
    parts = name.replace('×', '').strip().split()
    if len(parts) > 0:
        first_word = parts[0]
        capital_count = sum(1 for c in first_word if c.isupper())
        is_intergeneric = capital_count > 1
    else:
        is_intergeneric = False
    
    return is_hybrid, is_intergeneric

def match_species_to_taxonomy(scientific_name):
    """Match scientific name to taxonomy_id in database."""
    if not scientific_name:
        return None
    
    conn = get_db()
    cur = conn.cursor()
    
    # Try exact match first
    cur.execute("""
        SELECT id FROM orchid_taxonomy
        WHERE LOWER(scientific_name) = LOWER(%s)
        LIMIT 1
    """, (scientific_name.strip(),))
    
    result = cur.fetchone()
    
    if result:
        taxonomy_id = result[0]
    else:
        # Try genus + species match
        parts = scientific_name.strip().split()
        if len(parts) >= 2:
            genus = parts[0]
            species = parts[1]
            
            cur.execute("""
                SELECT id FROM orchid_taxonomy
                WHERE LOWER(genus) = LOWER(%s)
                  AND LOWER(species) = LOWER(%s)
                LIMIT 1
            """, (genus, species))
            
            result = cur.fetchone()
            taxonomy_id = result[0] if result else None
        else:
            taxonomy_id = None
    
    cur.close()
    conn.close()
    
    return taxonomy_id

def import_from_csv(csv_path):
    """Import images from Google Sheets CSV."""
    print(f"\n📊 Processing CSV: {csv_path}")
    
    if not os.path.exists(csv_path):
        print(f"❌ File not found: {csv_path}")
        return 0, 0
    
    conn = get_db()
    cur = conn.cursor()
    
    total_rows = 0
    imported = 0
    matched = 0
    unmatched = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        # Try to detect headers
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        
        print(f"\n📋 Detected columns: {headers}")
        
        # Try to identify key columns (flexible matching)
        sci_name_col = None
        image_url_col = None
        photographer_col = None
        source_col = None
        
        for col in headers:
            col_lower = col.lower()
            if 'scientific' in col_lower or 'species' in col_lower or 'name' in col_lower:
                sci_name_col = col
            if 'image' in col_lower and 'url' in col_lower:
                image_url_col = col
            if 'photo' in col_lower or 'image' in col_lower:
                if not image_url_col:
                    image_url_col = col
            if 'photograph' in col_lower or 'credit' in col_lower:
                photographer_col = col
            if 'source' in col_lower:
                source_col = col
        
        print(f"\n🔍 Column mapping:")
        print(f"  Scientific name: {sci_name_col}")
        print(f"  Image URL: {image_url_col}")
        print(f"  Photographer: {photographer_col}")
        print(f"  Source: {source_col}")
        
        if not sci_name_col or not image_url_col:
            print(f"\n❌ Could not identify required columns!")
            print(f"   Need: scientific name + image URL")
            return 0, 0
        
        for row in reader:
            total_rows += 1
            
            scientific_name = row.get(sci_name_col, '').strip()
            image_url = row.get(image_url_col, '').strip()
            photographer = row.get(photographer_col, '').strip() if photographer_col else ''
            source = row.get(source_col, '').strip() if source_col else 'Google Sheets Import'
            
            if not scientific_name or not image_url:
                continue
            
            # Match to taxonomy
            taxonomy_id = match_species_to_taxonomy(scientific_name)
            
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
                'import_source': 'Google Sheets',
                'import_date': datetime.now().isoformat(),
                'photographer': photographer,
                'original_source': source
            }
            
            # Insert image
            try:
                cur.execute("""
                    INSERT INTO orchid_images (
                        taxonomy_id, image_url, image_source, image_rights_holder,
                        is_hybrid, is_intergeneric, image_description,
                        media_metadata, downloaded_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    taxonomy_id,
                    image_url,
                    source,
                    photographer,
                    is_hybrid,
                    is_intergeneric,
                    f'Imported from Google Sheets: {scientific_name}',
                    json.dumps(metadata),
                    datetime.now()
                ))
                imported += 1
                
                if imported % 100 == 0:
                    conn.commit()
                    print(f"   ✅ Imported {imported} images ({matched} matched / {total_rows} total)")
                    
            except Exception as e:
                print(f"   ⚠️  Error importing {scientific_name}: {e}")
                continue
    
    conn.commit()
    cur.close()
    conn.close()
    
    print(f"\n{'='*80}")
    print(f"✅ IMPORT COMPLETE")
    print(f"{'='*80}")
    print(f"  Total rows: {total_rows}")
    print(f"  Matched to taxonomy: {matched}")
    print(f"  Images imported: {imported}")
    print(f"  Unmatched species: {len(unmatched)}")
    
    if unmatched:
        print(f"\n⚠️  Top 20 unmatched species:")
        for species in unmatched[:20]:
            print(f"    - {species}")
    
    return imported, matched

def main():
    print("=" * 80)
    print("GOOGLE SHEETS IMAGE IMPORTER")
    print("Importing curated collections (Roberta Fox, Chris Howard, etc.)")
    print("=" * 80)
    print()
    
    # Download the sheet
    csv_path = download_sheet_as_csv(SHEETS_FILE_ID)
    
    if not csv_path:
        print("\n❌ Could not download Google Sheet")
        print("\n💡 ALTERNATIVE: Export the sheet manually as CSV and save to:")
        print(f"   bulk_eol_import/google_sheet_manual.csv")
        
        # Check for manual CSV
        manual_path = 'bulk_eol_import/google_sheet_manual.csv'
        if os.path.exists(manual_path):
            print(f"\n✅ Found manual CSV: {manual_path}")
            csv_path = manual_path
        else:
            print(f"\n❌ Manual CSV not found")
            sys.exit(1)
    
    # Import from CSV
    imported, matched = import_from_csv(csv_path)
    
    print()
    print("=" * 80)
    print("✅ IMPORT SESSION COMPLETE")
    print("=" * 80)

if __name__ == '__main__':
    main()
