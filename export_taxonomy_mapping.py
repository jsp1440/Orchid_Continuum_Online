#!/usr/bin/env python3
"""
Export EOL Page ID to Taxonomy ID mapping from database
"""
import os
import csv
import psycopg2

print("📊 Exporting EOL → Taxonomy mapping from database...")

# Connect to database
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

# Export all EOL page IDs with taxonomy mappings
query = """
SELECT eol_page_id, id as taxonomy_id, genus, species 
FROM orchid_taxonomy 
WHERE eol_page_id IS NOT NULL
ORDER BY eol_page_id
"""

cur.execute(query)
rows = cur.fetchall()

# Write to CSV
with open('eol_taxonomy_mapping.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['eol_page_id', 'taxonomy_id', 'genus', 'species'])
    writer.writerows(rows)

print(f"✅ Exported {len(rows):,} mappings to eol_taxonomy_mapping.csv")

cur.close()
conn.close()
