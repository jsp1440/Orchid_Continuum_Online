"""
Automatically import images from uploaded ZIP file
Run this after user uploads orchid_images_*.zip
"""
import os
import glob
import zipfile
import psycopg2
from pathlib import Path

DATABASE_URL = os.environ.get('DATABASE_URL')

# Find uploaded zip files
zip_files = glob.glob('orchid_images_*.zip')

if not zip_files:
    print("❌ No orchid_images_*.zip file found")
    print("📤 Please upload the ZIP file from your Mac first")
    exit(1)

zip_file = zip_files[0]  # Use the first/newest one
print("=" * 70)
print(f"📦 EXTRACTING: {zip_file}")
print("=" * 70)

# Extract to temp directory
extract_dir = "temp_uploaded_images"
os.makedirs(extract_dir, exist_ok=True)

with zipfile.ZipFile(zip_file, 'r') as zip_ref:
    zip_ref.extractall(extract_dir)
    
# Find all images
image_files = []
for ext in ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG']:
    image_files.extend(glob.glob(f"{extract_dir}/**/{ext}", recursive=True))

print(f"\n✅ Extracted {len(image_files)} images\n")

# Categorize and import
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

categories = {
    'herbarium': 0,
    'plate': 0,
    'photo': 0
}

for img_path in image_files:
    filename = Path(img_path).name.lower()
    
    # Determine type based on filename patterns
    if any(x in filename for x in ['herbarium', 'specimen', 'sheet', 'tropicos']):
        image_type = 'herbarium_sheet'
        source = 'Herbarium Specimen'
        categories['herbarium'] += 1
    elif any(x in filename for x in ['plate', 'illustration', 'botanical', 'lindenia', 'reichenbachia', 'bhl']):
        image_type = 'botanical_plate'
        source = 'Historical Botanical Illustration'
        categories['plate'] += 1
    else:
        image_type = 'living_photo'
        source = 'Field Observation'
        categories['photo'] += 1
    
    # Create permanent path
    dest_dir = f"attached_assets/uploaded_images/{image_type}s"
    os.makedirs(dest_dir, exist_ok=True)
    
    dest_path = f"{dest_dir}/{filename}"
    
    # Move file
    os.rename(img_path, dest_path)
    
    # Insert to database
    try:
        cursor.execute("""
            INSERT INTO orchid_images (
                image_url, local_path, image_source, image_type,
                image_license, image_description
            ) VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        """, (
            f"/{dest_path}",
            dest_path,
            source,
            image_type,
            'User Uploaded',
            f'Uploaded from Mac - {filename}'
        ))
        
        if cursor.rowcount > 0:
            conn.commit()
            symbol = "🔬" if image_type == 'herbarium_sheet' else "🎨" if image_type == 'botanical_plate' else "📸"
            print(f"  {symbol} {filename}")
            
    except Exception as e:
        conn.rollback()
        print(f"  ❌ Error: {filename}: {e}")

cursor.close()
conn.close()

# Clean up
import shutil
shutil.rmtree(extract_dir)

print("\n" + "=" * 70)
print("✅ IMPORT COMPLETE")
print("=" * 70)
print(f"📸 Living Photos: {categories['photo']}")
print(f"🔬 Herbarium Sheets: {categories['herbarium']}")
print(f"🎨 Botanical Plates: {categories['plate']}")
print(f"📊 Total: {sum(categories.values())}")
print("=" * 70)

# Show updated totals
cursor = psycopg2.connect(DATABASE_URL).cursor()
cursor.execute("""
    SELECT 
        COUNT(*) FILTER (WHERE image_type = 'living_photo') as photos,
        COUNT(*) FILTER (WHERE image_type = 'herbarium_sheet') as herbarium,
        COUNT(*) FILTER (WHERE image_type = 'botanical_plate') as plates,
        COUNT(*) as total
    FROM orchid_images
""")
row = cursor.fetchone()
cursor.close()

print("\n📊 DATABASE TOTALS:")
print(f"  Photos: {row[0]:,}")
print(f"  Herbarium: {row[1]:,}")
print(f"  Plates: {row[2]:,}")
print(f"  TOTAL: {row[3]:,}")
print("=" * 70)
