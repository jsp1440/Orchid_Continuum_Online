#!/usr/bin/env python3
"""
Step 1: Map EOL page_ids to orchid taxonomy
Creates mapping: taxonomy_id → eol_page_id
"""
import csv
import json
import os
import sys
import psycopg2
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

TRAITBANK_PAGES = 'external_databases/eol_traitbank/trait_bank/pages.csv'
OUTPUT_MAPPING = 'bulk_eol_import/eol_taxonomy_mapping.json'

def get_db():
    return psycopg2.connect(os.environ['DATABASE_URL'])

def detect_hybrid_type(scientific_name):
    """Detect if name is hybrid or intergeneric."""
    name = scientific_name.strip()
    
    # Check for hybrid symbol
    is_hybrid = '×' in name or ' x ' in name.lower()
    
    # Check for intergeneric (multiple genus names before species)
    # Example: "Brassia × Miltonia" or "Brassidium"
    parts = name.replace('×', '').strip().split()
    
    # If first word is capitalized and contains multiple capital letters, likely intergeneric
    if len(parts) > 0:
        first_word = parts[0]
        # Count capital letters (more than 2 suggests compound genus)
        capital_count = sum(1 for c in first_word if c.isupper())
        is_intergeneric = capital_count > 1
    else:
        is_intergeneric = False
    
    return is_hybrid, is_intergeneric

def load_orchid_taxonomy():
    """Load all orchid species from database."""
    print("📋 Loading orchid taxonomy from database...")
    
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT id, scientific_name, genus, species
        FROM orchid_taxonomy
        WHERE scientific_name IS NOT NULL
        ORDER BY id
    """)
    
    orchids = {}
    taxonomy_info = {}
    
    for tax_id, sci_name, genus, species in cur.fetchall():
        # Normalize name for matching
        normalized = sci_name.lower().strip()
        orchids[normalized] = tax_id
        
        # Also try genus + species only
        if genus and species:
            alt_name = f"{genus} {species}".lower().strip()
            if alt_name not in orchids:
                orchids[alt_name] = tax_id
        
        # Store taxonomy info
        is_hybrid, is_intergeneric = detect_hybrid_type(sci_name)
        taxonomy_info[tax_id] = {
            'scientific_name': sci_name,
            'genus': genus,
            'species': species,
            'is_hybrid': is_hybrid,
            'is_intergeneric': is_intergeneric
        }
    
    cur.close()
    conn.close()
    
    print(f"✅ Loaded {len(taxonomy_info):,} orchid species")
    print(f"   {sum(1 for t in taxonomy_info.values() if t['is_hybrid']):,} hybrids detected")
    print(f"   {sum(1 for t in taxonomy_info.values() if t['is_intergeneric']):,} intergenerics detected")
    
    return orchids, taxonomy_info

def build_eol_mapping(orchids, taxonomy_info):
    """Match EOL page_ids to orchid taxonomy."""
    print(f"\n🔍 Matching EOL pages to orchid species...")
    print(f"   Reading: {TRAITBANK_PAGES}")
    
    if not os.path.exists(TRAITBANK_PAGES):
        print(f"❌ File not found: {TRAITBANK_PAGES}")
        return {}
    
    eol_mapping = {}  # taxonomy_id → eol_page_id
    matched_count = 0
    
    with open(TRAITBANK_PAGES, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            page_id = row.get('page_id', '').strip()
            canonical = row.get('canonical', '').strip().lower()
            
            if not page_id or not canonical:
                continue
            
            # Try to match canonical name
            if canonical in orchids:
                tax_id = orchids[canonical]
                
                # Only use first match (most specific)
                if tax_id not in eol_mapping:
                    eol_mapping[tax_id] = page_id
                    matched_count += 1
                    
                    if matched_count % 1000 == 0:
                        print(f"   Matched {matched_count:,} species...")
    
    print(f"✅ Matched {len(eol_mapping):,} orchid species to EOL page_ids")
    
    # Combine with taxonomy info
    full_mapping = {}
    for tax_id, page_id in eol_mapping.items():
        if tax_id in taxonomy_info:
            full_mapping[tax_id] = {
                'eol_page_id': page_id,
                **taxonomy_info[tax_id]
            }
    
    return full_mapping

def save_mapping(mapping):
    """Save mapping to JSON file."""
    os.makedirs('bulk_eol_import', exist_ok=True)
    
    # Convert int keys to strings for JSON
    json_mapping = {str(k): v for k, v in mapping.items()}
    
    with open(OUTPUT_MAPPING, 'w') as f:
        json.dump(json_mapping, f, indent=2)
    
    print(f"\n💾 Saved mapping to: {OUTPUT_MAPPING}")
    print(f"   {len(mapping):,} taxonomy_id → eol_page_id mappings")

def main():
    print("=" * 80)
    print("EOL PAGE ID MAPPER")
    print("Linking EOL data to orchid taxonomy")
    print("=" * 80)
    print()
    
    # Load orchid taxonomy
    orchids, taxonomy_info = load_orchid_taxonomy()
    
    # Build EOL mapping
    mapping = build_eol_mapping(orchids, taxonomy_info)
    
    # Save results
    save_mapping(mapping)
    
    print()
    print("=" * 80)
    print("✅ MAPPING COMPLETE!")
    print("=" * 80)
    
    # Stats
    stats = {
        'total_orchids': len(taxonomy_info),
        'matched_to_eol': len(mapping),
        'match_rate': f"{len(mapping)/len(taxonomy_info)*100:.1f}%",
        'hybrids': sum(1 for t in mapping.values() if t['is_hybrid']),
        'intergenerics': sum(1 for t in mapping.values() if t['is_intergeneric'])
    }
    
    print(f"\nStats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

if __name__ == '__main__':
    main()
