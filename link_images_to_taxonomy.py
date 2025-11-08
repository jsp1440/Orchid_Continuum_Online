"""
Link images to orchid_taxonomy and extract metadata
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import re

DATABASE_URL = os.environ.get('DATABASE_URL')

print("=" * 70)
print("🔗 LINKING IMAGES TO TAXONOMY")
print("=" * 70)

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor(cursor_factory=RealDictCursor)

# Link images to taxonomy via image_description field
print("\n1️⃣  Linking images to taxonomy via scientific names...")
cursor.execute("""
    UPDATE orchid_images oi
    SET taxonomy_id = ot.id
    FROM orchid_taxonomy ot
    WHERE oi.taxonomy_id IS NULL
    AND oi.image_description IS NOT NULL
    AND ot.scientific_name = TRIM(
        REGEXP_REPLACE(oi.image_description, ' - .*$', '')
    )
""")
linked_count = cursor.rowcount
conn.commit()
print(f"   ✅ Linked {linked_count:,} images to taxonomy")

# Detect hybrids (× symbol or 'x' between names)
print("\n2️⃣  Detecting hybrid orchids...")
cursor.execute("""
    UPDATE orchid_images
    SET is_hybrid = TRUE
    WHERE (
        image_description LIKE '%×%' OR
        image_description LIKE '% x %' OR
        image_description ~* '[A-Z][a-z]+ x [A-Z][a-z]+'
    )
    AND is_hybrid = FALSE
""")
hybrid_count = cursor.rowcount
conn.commit()
print(f"   ✅ Detected {hybrid_count:,} hybrid images")

# Detect intergeneric hybrids (two different genus names)
print("\n3️⃣  Detecting intergeneric hybrids...")
cursor.execute("""
    UPDATE orchid_images
    SET is_intergeneric = TRUE
    WHERE image_description ~* '^[A-Z][a-z]+ara|^[A-Z][a-z]+opsis|phrag|catt'
    AND is_intergeneric = FALSE
""")
intergen_count = cursor.rowcount
conn.commit()
print(f"   ✅ Detected {intergen_count:,} intergeneric images")

# Extract geographic origin from country field
print("\n4️⃣  Extracting geographic origins...")
cursor.execute("""
    UPDATE orchid_images
    SET geographic_origin = country
    WHERE country IS NOT NULL
    AND geographic_origin IS NULL
""")
geo_count = cursor.rowcount
conn.commit()
print(f"   ✅ Set {geo_count:,} geographic origins")

# Final statistics
print("\n" + "=" * 70)
print("📊 IMAGE CATEGORIZATION SUMMARY")
print("=" * 70)

cursor.execute("""
    SELECT 
        image_type,
        COUNT(*) as total_images,
        COUNT(DISTINCT taxonomy_id) FILTER (WHERE taxonomy_id IS NOT NULL) as linked_species,
        COUNT(*) FILTER (WHERE is_hybrid = TRUE) as hybrids,
        COUNT(*) FILTER (WHERE geographic_origin IS NOT NULL) as with_location
    FROM orchid_images
    GROUP BY image_type
    ORDER BY total_images DESC
""")

for row in cursor.fetchall():
    img_type = row['image_type'] or 'unknown'
    print(f"\n{'  ' + img_type.upper().replace('_', ' ')}")
    print(f"    Total: {row['total_images']:,} images")
    print(f"    Linked to species: {row['linked_species']:,}")
    print(f"    Hybrids: {row['hybrids']:,}")
    print(f"    With location: {row['with_location']:,}")

print("\n" + "=" * 70)

cursor.close()
conn.close()
