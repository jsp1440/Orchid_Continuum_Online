"""
Categorize all 106,717 images into proper types with metadata
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.environ.get('DATABASE_URL')

print("=" * 70)
print("📋 CATEGORIZING IMAGES BY TYPE")
print("=" * 70)

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor(cursor_factory=RealDictCursor)

# 1. Categorize Tropicos herbarium sheets
print("\n1️⃣  Categorizing Tropicos Herbarium Sheets...")
cursor.execute("""
    UPDATE orchid_images 
    SET image_type = 'herbarium_sheet'
    WHERE image_source = 'Tropicos - Missouri Botanical Garden'
    AND image_type IS NULL
""")
herbarium_count = cursor.rowcount
conn.commit()
print(f"   ✅ {herbarium_count:,} herbarium sheets categorized")

# 2. Categorize BHL botanical plates (from EOL)
print("\n2️⃣  Categorizing Botanical Plates (BHL)...")
cursor.execute("""
    UPDATE orchid_images 
    SET image_type = 'botanical_plate'
    WHERE image_source = 'EOL - Botanical Illustration'
    AND image_rights_holder = 'Biodiversity Heritage Library'
    AND image_type IS NULL
""")
plates_count = cursor.rowcount
conn.commit()
print(f"   ✅ {plates_count:,} botanical plates categorized")

# 3. Categorize GBIF living photos
print("\n3️⃣  Categorizing GBIF Living Photos...")
cursor.execute("""
    UPDATE orchid_images 
    SET image_type = 'living_photo'
    WHERE image_source = 'GBIF'
    AND image_type IS NULL
""")
gbif_count = cursor.rowcount
conn.commit()
print(f"   ✅ {gbif_count:,} GBIF photos categorized")

# 4. Categorize remaining EOL images as living photos
print("\n4️⃣  Categorizing EOL Field Photos...")
cursor.execute("""
    UPDATE orchid_images 
    SET image_type = 'living_photo'
    WHERE image_source = 'EOL - Botanical Illustration'
    AND image_rights_holder != 'Biodiversity Heritage Library'
    AND image_type IS NULL
""")
eol_photos_count = cursor.rowcount
conn.commit()
print(f"   ✅ {eol_photos_count:,} EOL field photos categorized")

# 5. Extract year from locality field for plates
print("\n5️⃣  Extracting years from metadata...")
cursor.execute("""
    UPDATE orchid_images 
    SET collection_year = CAST(
        SUBSTRING(locality FROM 'Year: ([0-9]{4})')
        AS INTEGER
    )
    WHERE image_type = 'botanical_plate'
    AND locality LIKE '%Year:%'
    AND collection_year IS NULL
""")
year_count = cursor.rowcount
conn.commit()
print(f"   ✅ {year_count:,} years extracted")

# 6. Extract plate numbers
print("\n6️⃣  Extracting plate numbers...")
cursor.execute("""
    UPDATE orchid_images 
    SET plate_number = SUBSTRING(locality FROM 'Page ([^(]+)')
    WHERE image_type = 'botanical_plate'
    AND locality LIKE '%Page%'
    AND plate_number IS NULL
""")
plate_num_count = cursor.rowcount
conn.commit()
print(f"   ✅ {plate_num_count:,} plate numbers extracted")

# Final summary
print("\n" + "=" * 70)
print("📊 CATEGORIZATION COMPLETE")
print("=" * 70)

cursor.execute("""
    SELECT 
        image_type,
        COUNT(*) as count,
        COUNT(DISTINCT taxonomy_id) as species_count
    FROM orchid_images
    GROUP BY image_type
    ORDER BY count DESC
""")

for row in cursor.fetchall():
    img_type = row['image_type'] or 'uncategorized'
    print(f"\n{img_type.upper().replace('_', ' ')}")
    print(f"  Images: {row['count']:,}")
    print(f"  Species: {row['species_count']:,}")

# Show sample metadata for each type
print("\n" + "=" * 70)
print("📋 SAMPLE METADATA")
print("=" * 70)

# Herbarium sample
print("\n🔬 HERBARIUM SHEET SAMPLE:")
cursor.execute("""
    SELECT 
        observer_name as collector,
        institution_code,
        locality,
        image_license
    FROM orchid_images
    WHERE image_type = 'herbarium_sheet'
    AND observer_name IS NOT NULL
    LIMIT 1
""")
sample = cursor.fetchone()
if sample:
    print(f"  Collector: {sample['collector']}")
    print(f"  Institution: {sample['institution_code']}")
    print(f"  Locality: {sample['locality'][:60]}...")
    print(f"  License: {sample['license']}")

# Botanical plate sample
print("\n🎨 BOTANICAL PLATE SAMPLE:")
cursor.execute("""
    SELECT 
        image_rights_holder as artist,
        collection_year,
        plate_number,
        image_license
    FROM orchid_images
    WHERE image_type = 'botanical_plate'
    AND collection_year IS NOT NULL
    LIMIT 1
""")
sample = cursor.fetchone()
if sample:
    print(f"  Artist: {sample['artist']}")
    print(f"  Year: {sample['collection_year']}")
    print(f"  Plate: {sample['plate_number']}")
    print(f"  License: {sample['license']}")

# Living photo sample
print("\n📸 LIVING PHOTO SAMPLE:")
cursor.execute("""
    SELECT 
        observer_name as photographer,
        country,
        image_license
    FROM orchid_images
    WHERE image_type = 'living_photo'
    AND observer_name IS NOT NULL
    LIMIT 1
""")
sample = cursor.fetchone()
if sample:
    print(f"  Photographer: {sample['photographer']}")
    print(f"  Country: {sample['country']}")
    print(f"  License: {sample['license']}")

print("\n" + "=" * 70)

cursor.close()
conn.close()
