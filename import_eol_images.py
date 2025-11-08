"""
Import EOL images from CSV to database
"""
import csv
import os
import psycopg2
from psycopg2.extras import execute_batch

DATABASE_URL = os.environ.get('DATABASE_URL')

print("=" * 70)
print("📥 IMPORTING EOL IMAGES FROM CSV")
print("=" * 70)

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

# Read CSV
total = 0
imported = 0
skipped = 0

with open('EOL_IMAGES_COMPLETE_95000.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    
    batch = []
    for row in reader:
        total += 1
        
        # Get EOL URL (column is 'eol_url')
        image_url = row.get('eol_url') or row.get('source_url')
        if not image_url or not image_url.startswith('http'):
            skipped += 1
            continue
        
        # Prepare data
        batch.append((
            image_url,
            'EOL - Botanical Illustration',
            row.get('full_scientific_name') or f"{row.get('genus','')} {row.get('species','')}".strip(),
            row.get('page_id'),
            row.get('photographer'),
            row.get('license'),
            row.get('notes','')
        ))
        
        # Batch insert every 1000
        if len(batch) >= 1000:
            try:
                execute_batch(cursor, """
                    INSERT INTO orchid_images (
                        image_url, image_source, image_description,
                        eol_data_object_id, image_rights_holder,
                        image_license, locality
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, batch)
                conn.commit()
                imported += len(batch)
                print(f"✅ Imported {imported:,} images...")
                batch = []
            except Exception as e:
                print(f"❌ Batch error: {e}")
                conn.rollback()
                batch = []
    
    # Insert remaining
    if batch:
        try:
            execute_batch(cursor, """
                INSERT INTO orchid_images (
                    image_url, image_source, image_description,
                    eol_data_object_id, image_rights_holder,
                    image_license, locality
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, batch)
            conn.commit()
            imported += len(batch)
        except Exception as e:
            print(f"❌ Final batch error: {e}")
            conn.rollback()

cursor.close()
conn.close()

print("=" * 70)
print(f"✅ IMPORT COMPLETE")
print(f"📊 Total rows: {total:,}")
print(f"✅ Imported: {imported:,}")
print(f"⏭️  Skipped: {skipped:,}")
print("=" * 70)
