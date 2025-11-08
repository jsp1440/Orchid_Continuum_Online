#!/usr/bin/env python3
"""
FAST bulk import - uses PostgreSQL's COPY command for maximum speed
"""
import os
import csv
import psycopg2
from io import StringIO

print("🌺 FAST BULK IMPORT - EOL URLs")
print("=" * 70)

# Load CSV data
urls_data = []
with open('orchid_eol_urls.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        urls_data.append(row)

print(f"📊 Loaded {len(urls_data):,} URLs\n")

# Connect to database
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

# Prepare data for COPY command
copy_data = StringIO()
inserted = 0
skipped_no_taxonomy = 0

for row in urls_data:
    taxonomy_id = row.get('taxonomy_id', '').strip()
    tax_id_value = taxonomy_id if taxonomy_id and taxonomy_id != 'None' else '\\N'  # NULL in COPY format
    
    if tax_id_value == '\\N':
        skipped_no_taxonomy += 1
    
    # Escape strings for COPY
    image_url = row['image_url'].replace('\\', '\\\\').replace('\t', ' ')
    image_source = row['image_source'].replace('\\', '\\\\').replace('\t', ' ')
    image_license = row.get('image_license', '').replace('\\', '\\\\').replace('\t', ' ')
    eol_page_id = row.get('eol_page_id', '').replace('\\', '\\\\').replace('\t', ' ')
    eol_content_id = row.get('eol_content_id', '').replace('\\', '\\\\').replace('\t', ' ')
    copyright_owner = row.get('copyright_owner', '').replace('\\', '\\\\').replace('\t', ' ')
    
    # Format: taxonomy_id, image_url, image_source, image_license, eol_page_id, eol_content_id, copyright_owner, created_at
    copy_data.write(f"{tax_id_value}\t{image_url}\t{image_source}\t{image_license}\t{eol_page_id}\t{eol_content_id}\t{copyright_owner}\tNOW()\n")
    inserted += 1

copy_data.seek(0)

print(f"✅ {inserted:,} URLs prepared")
print(f"⚠️  {skipped_no_taxonomy:,} without taxonomy mapping")
print()

# Use COPY for ultra-fast bulk insert
print("💾 Bulk inserting via COPY command...")

try:
    # Create temp table to avoid duplicates
    cur.execute("""
        CREATE TEMP TABLE temp_eol_images (
            taxonomy_id INTEGER,
            image_url TEXT,
            image_source VARCHAR(100),
            image_license TEXT,
            eol_page_id VARCHAR(50),
            eol_content_id VARCHAR(50),
            copyright_owner TEXT,
            created_at TIMESTAMP
        )
    """)
    
    # COPY into temp table
    cur.copy_from(copy_data, 'temp_eol_images', columns=(
        'taxonomy_id', 'image_url', 'image_source', 'image_license',
        'eol_page_id', 'eol_content_id', 'copyright_owner', 'created_at'
    ))
    
    print(f"   ✓ Loaded into temp table")
    
    # Insert only non-duplicates
    cur.execute("""
        INSERT INTO orchid_images (
            taxonomy_id, image_url, image_source, image_license,
            eol_page_id, eol_content_id, copyright_owner, created_at
        )
        SELECT DISTINCT ON (image_url)
            taxonomy_id, image_url, image_source, image_license,
            eol_page_id, eol_content_id, copyright_owner, NOW()
        FROM temp_eol_images
        WHERE NOT EXISTS (
            SELECT 1 FROM orchid_images oi WHERE oi.image_url = temp_eol_images.image_url
        )
    """)
    
    rows_inserted = cur.rowcount
    conn.commit()
    
    print(f"   ✓ Inserted {rows_inserted:,} new URLs")
    print(f"   ✓ Skipped {inserted - rows_inserted:,} duplicates")
    
except Exception as e:
    conn.rollback()
    print(f"❌ Error: {e}")
    raise
finally:
    cur.close()
    conn.close()

# Verify
print("\n📊 Final Statistics:")
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

cur.execute("SELECT COUNT(*) FROM orchid_images")
total = cur.fetchone()[0]

cur.execute("SELECT COUNT(DISTINCT taxonomy_id) FROM orchid_images WHERE taxonomy_id IS NOT NULL")
species = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM orchid_images WHERE taxonomy_id IS NULL")
unmapped = cur.fetchone()[0]

print(f"   Total images: {total:,}")
print(f"   Mapped to species: {species:,}")
print(f"   Unmapped (pending taxonomy): {unmapped:,}")

cur.close()
conn.close()

print("\n✅ IMPORT COMPLETE!")
