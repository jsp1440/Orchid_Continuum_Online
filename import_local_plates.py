"""
Import the botanical plates downloaded this weekend
From attached_assets/botanical_illustrations and attached_assets/orchid_images
"""
import os
import glob
import psycopg2
from pathlib import Path

DATABASE_URL = os.environ.get('DATABASE_URL')

# Find all botanical plate images
plate_paths = []
plate_paths.extend(glob.glob('attached_assets/botanical_illustrations/*.jpg'))
plate_paths.extend(glob.glob('attached_assets/orchid_images/*.jpg'))

print("=" * 70)
print(f"🎨 IMPORTING {len(plate_paths)} BOTANICAL PLATES")
print("=" * 70)

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

imported = 0
for path in plate_paths:
    filename = Path(path).name
    
    # Determine source and metadata from filename
    if 'reichenbachia' in filename.lower():
        source = 'Reichenbachia - Orchids Illustrated and Described'
        artist = 'F. Sander'
    elif 'lindenia' in filename.lower():
        source = 'Lindenia - Iconographie des Orchidées'
        artist = 'L. Linden'
    else:
        source = 'Historical Botanical Illustration'
        artist = 'Unknown'
    
    # Create file URL (Replit hosted)
    file_url = f"/attached_assets/{path.split('attached_assets/')[1]}"
    
    try:
        cursor.execute("""
            INSERT INTO orchid_images (
                image_url, local_path, image_source, image_type,
                image_rights_holder, image_license, image_description
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        """, (
            file_url,
            path,
            source,
            'botanical_plate',
            artist,
            'Public Domain',
            f'Historical botanical plate from {source}'
        ))
        
        if cursor.rowcount > 0:
            conn.commit()
            imported += 1
            print(f"  ✅ {imported}. {filename}")
        
    except Exception as e:
        conn.rollback()
        print(f"  ❌ Error with {filename}: {e}")

cursor.close()
conn.close()

print("\n" + "=" * 70)
print(f"✅ IMPORTED {imported} BOTANICAL PLATES")
print("=" * 70)
