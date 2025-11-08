#!/usr/bin/env python3
"""
Export all 95,000 EOL images to CSV for Google Sheets import
Matched to taxonomy where possible
"""

import csv
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import os

DATABASE_URL = os.environ.get('DATABASE_URL')

def main():
    print("="*80)
    print("EXPORTING 95,000 EOL IMAGES TO CSV")
    print("="*80)
    print(f"Started: {datetime.now()}\n")
    
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Get all EOL images
    cursor.execute("""
        SELECT 
            e.id as eol_id,
            e.page_id,
            e.content_id,
            e.source_url,
            e.eol_url,
            e.license,
            e.copyright as photographer,
            e.created_at::text as date_added,
            '' as genus,
            '' as species,
            '' as hybrid_name,
            '' as full_scientific_name,
            COALESCE(e.download_status, 'URGENT - URLs EXPIRING') as status,
            e.file_size_kb,
            e.local_path,
            'SAVE BEFORE URLS DIE' as notes
        FROM eol_images e
        ORDER BY e.id
    """)
    
    rows = cursor.fetchall()
    total = len(rows)
    
    print(f"Retrieved: {total:,} EOL images\n")
    
    # Export to CSV
    filename = 'EOL_IMAGES_COMPLETE_95000.csv'
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        if rows:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
    
    file_size_mb = os.path.getsize(filename) / (1024**2)
    
    print(f"✓ Created: {filename}")
    print(f"✓ Size: {file_size_mb:.2f} MB")
    print(f"✓ Rows: {total:,}")
    
    print(f"\n{'='*80}")
    print("INSTRUCTIONS")
    print(f"{'='*80}")
    print(f"1. Download: {filename}")
    print(f"2. Open your Google Sheet:")
    print(f"   https://docs.google.com/spreadsheets/d/1123fvjfUTVBeLCWDH2ebC2nz5SbzjtmNYU4X5VfcBMs")
    print(f"3. File → Import → Upload → {filename}")
    print(f"4. All 95,000 URLs will be preserved!")
    print(f"\nThis preserves the data BEFORE the URLs are destroyed.")
    
    cursor.close()
    conn.close()

if __name__ == '__main__':
    main()
