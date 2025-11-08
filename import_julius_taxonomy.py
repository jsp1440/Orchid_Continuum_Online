#!/usr/bin/env python3
"""
Import Julius's taxonomy results back into the database
Run this AFTER Julius delivers julius_taxonomy_results.csv
"""
import os
import csv
import psycopg2

print("🌺 IMPORTING JULIUS TAXONOMY RESULTS")
print("=" * 70)

# Check if Julius's file exists
if not os.path.exists('julius_taxonomy_results.csv'):
    print("❌ ERROR: julius_taxonomy_results.csv not found!")
    print("   Waiting for Julius to deliver the results...")
    exit(1)

# Load Julius's taxonomy data
taxonomy_data = []
with open('julius_taxonomy_results.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        taxonomy_data.append(row)

print(f"📊 Loaded {len(taxonomy_data):,} species from Julius\n")

# Connect to database
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

# Insert taxonomy
inserted = 0
updated = 0
failed = 0

print("💾 Importing into orchid_taxonomy table...")

for i, row in enumerate(taxonomy_data, 1):
    try:
        eol_page_id = row['eol_page_id']
        scientific_name = row['scientific_name']
        genus = row['genus']
        species = row['species']
        family = row.get('family', 'Orchidaceae')
        
        # Insert or update (using scientific_name as unique key)
        cur.execute("""
            INSERT INTO orchid_taxonomy (
                eol_page_id, genus, species, family, scientific_name, created_at
            ) VALUES (%s, %s, %s, %s, %s, NOW())
            ON CONFLICT (scientific_name) DO UPDATE 
            SET eol_page_id = EXCLUDED.eol_page_id,
                genus = EXCLUDED.genus,
                species = EXCLUDED.species,
                family = EXCLUDED.family,
                updated_at = NOW()
            RETURNING (xmax = 0) AS inserted
        """, (eol_page_id, genus, species, family, scientific_name))
        
        result = cur.fetchone()
        if result and result[0]:
            inserted += 1
        else:
            updated += 1
        
        conn.commit()
        
        if i % 100 == 0:
            print(f"   Progress: {i}/{len(taxonomy_data)} (✅ {inserted} new | 🔄 {updated} updated)")
        
    except Exception as e:
        failed += 1
        print(f"   ⚠️  Failed: {row.get('eol_page_id', 'unknown')} - {e}")
        conn.rollback()

print()
print("=" * 70)
print(f"✅ IMPORT COMPLETE!")
print(f"   New species added: {inserted}")
print(f"   Existing updated: {updated}")
print(f"   Failed: {failed}")

# Now link the unmapped images to their taxonomy
print()
print("🔗 Linking images to taxonomy...")

cur.execute("""
    UPDATE orchid_images oi
    SET taxonomy_id = ot.id
    FROM orchid_taxonomy ot
    WHERE oi.eol_page_id::text = ot.eol_page_id
    AND oi.taxonomy_id IS NULL
""")

linked = cur.rowcount
conn.commit()

print(f"   ✅ Linked {linked:,} images to taxonomy")

# Final stats
cur.execute("SELECT COUNT(*) FROM orchid_taxonomy")
result = cur.fetchone()
total_species = result[0] if result else 0

cur.execute("SELECT COUNT(*) FROM orchid_images")
result = cur.fetchone()
total_images = result[0] if result else 0

cur.execute("SELECT COUNT(DISTINCT taxonomy_id) FROM orchid_images WHERE taxonomy_id IS NOT NULL")
result = cur.fetchone()
species_with_images = result[0] if result else 0

cur.execute("SELECT COUNT(*) FROM orchid_images WHERE taxonomy_id IS NULL")
result = cur.fetchone()
unmapped_images = result[0] if result else 0

print()
print("📊 FINAL DATABASE STATS:")
print(f"   Total species in taxonomy: {total_species:,}")
print(f"   Total images: {total_images:,}")
print(f"   Species with images: {species_with_images:,}")
print(f"   Unmapped images: {unmapped_images:,}")
print()

coverage_pct = (species_with_images / 33494) * 100  # 33,494 = total known orchids
print(f"🎉 ORCHID COVERAGE: {coverage_pct:.1f}% of all known orchid species!")

cur.close()
conn.close()
