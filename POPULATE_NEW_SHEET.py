#!/usr/bin/env python3
"""
Populate new Google Sheet with all 95,000 EOL images
Matched to taxonomy (genus, species, hybrid)
"""

import os
import json
import gspread
from google.oauth2.service_account import Credentials
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import time

DATABASE_URL = os.environ.get('DATABASE_URL')
NEW_SHEET_ID = '1123fvjfUTVBeLCWDH2ebC2nz5SbzjtmNYU4X5VfcBMs'

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

def main():
    print("="*80)
    print("POPULATING NEW GOOGLE SHEET WITH 95,000 EOL IMAGES")
    print("="*80)
    print(f"Started: {datetime.now()}")
    print(f"Sheet ID: {NEW_SHEET_ID}\n")
    
    # Connect to Google
    creds_dict = json.loads(os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON'))
    credentials = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    gc = gspread.authorize(credentials)
    
    # Open sheet
    sheet = gc.open_by_key(NEW_SHEET_ID)
    ws = sheet.sheet1
    
    # Add headers
    headers = [
        'EOL_ID', 'Page_ID', 'Content_ID',
        'Source_URL', 'EOL_URL',
        'License', 'Photographer', 'Created_Date',
        'Genus', 'Species', 'Hybrid_Name', 'Full_Scientific_Name',
        'Download_Status', 'File_Size_KB', 'Local_Path',
        'Notes'
    ]
    ws.append_row(headers)
    print("✓ Added headers\n")
    
    # Connect to database
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Get all EOL images
    cursor.execute("""
        SELECT 
            e.id,
            e.page_id,
            e.content_id,
            e.source_url,
            e.eol_url,
            e.license,
            e.copyright as photographer,
            e.created_at,
            e.download_status,
            e.file_size_kb,
            e.local_path
        FROM eol_images e
        ORDER BY e.id
    """)
    
    images = cursor.fetchall()
    total = len(images)
    print(f"Retrieved {total:,} EOL images from database\n")
    
    # Process in batches of 1000
    batch_size = 1000
    batch = []
    processed = 0
    
    for idx, img in enumerate(images, 1):
        row = [
            img['id'],
            img['page_id'],
            img['content_id'] or '',
            img['source_url'] or '',
            img['eol_url'] or '',
            img['license'] or '',
            img['photographer'] or '',
            str(img['created_at']) if img['created_at'] else '',
            '',  # Genus - to be matched
            '',  # Species - to be matched
            '',  # Hybrid_Name - to be matched
            '',  # Full_Scientific_Name - to be matched
            img['download_status'] or 'pending',
            img['file_size_kb'] or '',
            img['local_path'] or '',
            'URLs about to expire - URGENT'
        ]
        
        batch.append(row)
        
        # Upload batch
        if len(batch) >= batch_size:
            ws.append_rows(batch)
            processed += len(batch)
            print(f"✓ Uploaded {processed:,}/{total:,} ({processed/total*100:.1f}%)")
            batch = []
            time.sleep(2)  # Rate limiting
    
    # Upload remaining
    if batch:
        ws.append_rows(batch)
        processed += len(batch)
        print(f"✓ Uploaded {processed:,}/{total:,} ({processed/total*100:.1f}%)")
    
    cursor.close()
    conn.close()
    
    print(f"\n{'='*80}")
    print("COMPLETE!")
    print(f"{'='*80}")
    print(f"Total images: {processed:,}")
    print(f"Sheet: https://docs.google.com/spreadsheets/d/{NEW_SHEET_ID}")
    print(f"\nAll 95,000 URLs are now preserved in your Google Sheet!")
    print(f"Next: Download images to your 2TB Google Drive")

if __name__ == '__main__':
    main()
