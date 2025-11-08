#!/usr/bin/env python3
"""
Export complete taxonomy with images to CSV
Ready to upload to Google Sheets
"""

import os
import csv
import psycopg2
from psycopg2.extras import RealDictCursor

# Connect to database
db_conn = psycopg2.connect(os.environ.get('DATABASE_URL'))

print("🌺 EXPORTING ORCHID TAXONOMY WITH IMAGES\n")

print("🔍 Loading complete taxonomy data...")

with db_conn.cursor(cursor_factory=RealDictCursor) as cur:
    # Get all taxonomy with aggregated image data
    cur.execute("""
        SELECT 
            ot.scientific_name,
            ot.genus,
            ot.species,
            ot.subspecies,
            ot.variety,
            ot.author,
            ot.family,
            ot.order,
            ot.class,
            ot.common_names,
            ot.taxonomic_status,
            ot.iucn_red_list_category,
            ot.gbif_taxon_key,
            ot.eol_page_id,
            COUNT(DISTINCT oi.id) as total_images,
            COUNT(DISTINCT CASE WHEN oi.google_drive_url IS NOT NULL THEN oi.id END) as uploaded_images,
            STRING_AGG(DISTINCT oi.country, '; ') FILTER (WHERE oi.country IS NOT NULL) as countries_found,
            STRING_AGG(DISTINCT CONCAT(
                COALESCE(oi.country, 'Unknown'),
                ' | ',
                COALESCE(oi.observation_date::text, 'No date'),
                ' | ',
                COALESCE(oi.observer_name, 'Unknown observer'),
                ' | ',
                COALESCE(oi.google_drive_url, oi.image_url)
            ), ' || ') as image_details
        FROM orchid_taxonomy ot
        LEFT JOIN orchid_images oi ON ot.id = oi.taxonomy_id
        GROUP BY ot.id, ot.scientific_name, ot.genus, ot.species, ot.subspecies, 
                 ot.variety, ot.author, ot.family,
                 ot.order, ot.class, ot.common_names, ot.taxonomic_status,
                 ot.iucn_red_list_category, ot.gbif_taxon_key, ot.eol_page_id
        ORDER BY ot.family, ot.genus, ot.species
    """)
    
    species_data = cur.fetchall()

print(f"✅ Found {len(species_data)} species\n")

# Write to CSV
csv_file = 'ORCHID_TAXONOMY_WITH_IMAGES.csv'

print(f"💾 Writing to {csv_file}...")

with open(csv_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    
    # Header
    writer.writerow([
        'Scientific Name',
        'Genus',
        'Species',
        'Subspecies',
        'Variety',
        'Author',
        'Family',
        'Order',
        'Class',
        'Common Names',
        'Status',
        'IUCN Category',
        'GBIF ID',
        'EOL ID',
        'Total Images',
        'Uploaded to Drive',
        'Countries Found',
        'Image Details (Name | Country | Date | Observer | URL)'
    ])
    
    # Data rows
    for sp in species_data:
        writer.writerow([
            sp['scientific_name'] or '',
            sp['genus'] or '',
            sp['species'] or '',
            sp['subspecies'] or '',
            sp['variety'] or '',
            sp['author'] or '',
            sp['family'] or '',
            sp['order'] or '',
            sp['class'] or '',
            sp['common_names'] or '',
            sp['taxonomic_status'] or '',
            sp['iucn_red_list_category'] or '',
            sp['gbif_taxon_key'] or '',
            sp['eol_page_id'] or '',
            sp['total_images'],
            sp['uploaded_images'],
            sp['countries_found'] or '',
            sp['image_details'] or ''
        ])

print(f"✅ Exported {len(species_data)} rows")

# Statistics
total_species_with_images = sum(1 for sp in species_data if sp['total_images'] > 0)
total_images = sum(sp['total_images'] for sp in species_data)
uploaded = sum(sp['uploaded_images'] for sp in species_data)

print("\n" + "="*60)
print("📊 SUMMARY")
print("="*60)
print(f"Total species in database: {len(species_data)}")
print(f"Species with images: {total_species_with_images}")
print(f"Total images: {total_images}")
print(f"Uploaded to Google Drive: {uploaded}")
print(f"\nCSV file: {csv_file}")
print(f"Size: {os.path.getsize(csv_file) / 1024 / 1024:.2f} MB")
print("="*60)
print("\n✅ Ready to upload to Google Sheets!")
print("   1. Download this CSV file from Replit")
print("   2. Upload to Google Sheets in your Shared Drive")
print("   3. All taxonomy + images organized!")

db_conn.close()
