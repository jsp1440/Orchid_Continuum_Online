#!/usr/bin/env python3
"""
Bulk Import EOL URLs into orchid_images table
Uses batch inserts for performance (1000 rows at a time)
"""
import os
import csv
import psycopg2
from psycopg2.extras import execute_batch

print("🌺 BULK IMPORTING EOL URLs TO DATABASE")
print("=" * 70)

# Connect to database
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

# Read the extracted URLs
urls_data = []
with open('orchid_eol_urls.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        urls_data.append(row)

print(f"📊 Loaded {len(urls_data):,} URLs from CSV\n")

# Prepare batch insert
# Only insert if we have a valid taxonomy_id
insert_query = """
INSERT INTO orchid_images (
    taxonomy_id,
    image_url,
    image_source,
    image_license,
    eol_page_id,
    eol_content_id,
    copyright_owner,
    created_at
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, NOW()
)
"""

# Prepare all rows (allow NULL taxonomy_id for now)
valid_rows = []
skipped_no_taxonomy = 0

for row in urls_data:
    taxonomy_id = row.get('taxonomy_id', '').strip()
    
    # Convert taxonomy_id to int or None
    tax_id_value = int(taxonomy_id) if taxonomy_id and taxonomy_id != 'None' else None
    
    if tax_id_value is None:
        skipped_no_taxonomy += 1
    
    valid_rows.append((
        tax_id_value,
        row['image_url'],
        row['image_source'],
        row['image_license'],
        row['eol_page_id'],
        row.get('eol_content_id', ''),
        row.get('copyright_owner', '')
    ))

print(f"✅ {len(valid_rows):,} URLs ready to import")
print(f"⚠️  {skipped_no_taxonomy:,} URLs skipped (no taxonomy mapping)")
print()

# Batch insert (1000 at a time for performance)
print("💾 Inserting into database...")
batch_size = 1000
total_inserted = 0
total_skipped_duplicates = 0

try:
    for i in range(0, len(valid_rows), batch_size):
        batch = valid_rows[i:i+batch_size]
        
        # Insert each row individually to handle duplicates gracefully
        for row_data in batch:
            try:
                cur.execute(insert_query, row_data)
                total_inserted += 1
            except psycopg2.errors.UniqueViolation:
                # Duplicate URL - skip it
                total_skipped_duplicates += 1
                conn.rollback()
                continue
            except Exception:
                # Other error - rollback and continue
                conn.rollback()
                continue
        
        # Commit every batch
        conn.commit()
        
        # Show progress every 10k rows
        if (total_inserted + total_skipped_duplicates) % 10000 == 0:
            print(f"   ✓ Processed {total_inserted + total_skipped_duplicates:,} rows (inserted: {total_inserted:,}, skipped: {total_skipped_duplicates:,})...")
    
    conn.commit()
    print(f"\n✅ Successfully inserted {total_inserted:,} new image URLs!")
    print(f"⚠️  Skipped {total_skipped_duplicates:,} duplicate URLs")
    
except Exception as e:
    conn.rollback()
    print(f"❌ Error during import: {e}")
    raise
finally:
    cur.close()
    conn.close()

print("\n📊 Verifying import...")
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

# Count total images
cur.execute("SELECT COUNT(*) FROM orchid_images")
total_images = cur.fetchone()[0]

# Count unique species
cur.execute("SELECT COUNT(DISTINCT taxonomy_id) FROM orchid_images WHERE taxonomy_id IS NOT NULL")
unique_species = cur.fetchone()[0]

# Count by source
cur.execute("""
    SELECT image_source, COUNT(*) 
    FROM orchid_images 
    GROUP BY image_source 
    ORDER BY COUNT(*) DESC
""")
by_source = cur.fetchall()

print(f"\n🎉 DATABASE TOTALS:")
print(f"   Total images: {total_images:,}")
print(f"   Unique species: {unique_species:,}")
print(f"\n📈 Images by source:")
for source, count in by_source:
    print(f"   {source}: {count:,}")

cur.close()
conn.close()

print(f"\n✅ IMPORT COMPLETE!")
