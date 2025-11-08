import csv
import os
import psycopg2

# Get database URL
db_url = os.environ.get('DATABASE_URL')
if not db_url:
    print("DATABASE_URL not set")
    exit(1)

# Parse connection string
# Format: postgres://user:pass@host/dbname or postgresql://...
from urllib.parse import urlparse
result = urlparse(db_url)
username = result.username
password = result.password
database = result.path[1:]
hostname = result.hostname
port = result.port or 5432

# Connect
conn = psycopg2.connect(
    database=database,
    user=username,
    password=password,
    host=hostname,
    port=port
)
cur = conn.cursor()

print("Importing BloomBuilder species data...")

with open('attached_assets/bloombuilder/BloomBuilder_Species_Index.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    count = 0
    
    for row in reader:
        # Check if exists
        cur.execute("SELECT id FROM bloombuilder_species WHERE species = %s", (row['species'],))
        if cur.fetchone():
            print(f"  Skipping {row['species']} (already exists)")
            continue
        
        # Insert
        cur.execute("""
            INSERT INTO bloombuilder_species 
            (species, genus, family, herbarium_url, photo_url, diagram_url, 
             source_reference, profile_type, habitat, distribution, pollinators,
             ecological_notes, conservation_status, evolutionary_notes, external_links, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            row['species'], row['genus'], row['family'],
            row['herbarium_url'] or None, row['photo_url'] or None, row['diagram_url'] or None,
            row['source_reference'] or None, row['profile_type'],
            row['habitat'] or None, row['distribution'] or None, row['pollinators'] or None,
            row['ecological_notes'] or None, row['conservation_status'] or None,
            row['evolutionary_notes'] or None, row['external_links'] or None,
            row['notes'] or None
        ))
        count += 1
        print(f"  Added: {row['species']}")

conn.commit()
cur.close()
conn.close()

print(f"\n✅ Imported {count} species successfully!")
