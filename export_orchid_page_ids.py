"""
Export EOL Page IDs from current database
This creates the file needed for mac_filter_eol_orchids.py
"""
import psycopg2
import os

DATABASE_URL = os.environ.get('DATABASE_URL')

print("📤 Exporting EOL Page IDs from database...")

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

# Get all unique EOL data object IDs (content IDs act as page references)
cursor.execute("""
    SELECT DISTINCT eol_data_object_id 
    FROM orchid_images 
    WHERE eol_data_object_id IS NOT NULL 
    AND eol_data_object_id != ''
    AND image_source LIKE '%EOL%'
    ORDER BY eol_data_object_id
""")

page_ids = [row[0] for row in cursor.fetchall()]

cursor.close()
conn.close()

# Write to file
with open('orchid_eol_page_ids.txt', 'w') as f:
    for page_id in page_ids:
        f.write(f"{page_id}\n")

print(f"✅ Exported {len(page_ids):,} EOL page IDs to: orchid_eol_page_ids.txt")
print()
print("NEXT STEPS:")
print("1. Download this file to your Mac")
print("2. Place it in the same folder as the EOL manifest files")
print("3. Run: python3 mac_filter_eol_orchids.py")
