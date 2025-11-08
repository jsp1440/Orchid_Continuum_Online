#!/usr/bin/env python3
"""
Export Orchid Continuum database to Google Sheets
Handles large datasets with batching and rate limiting
"""
import os
import sys
import json
import time
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from app import app, db
from models import OrchidRecord
from sqlalchemy import func

# Google Sheets configuration
SPREADSHEET_ID = "1UQZj4ZaA7cWnU0SozR4_qReWNOm0V9xz"
BATCH_SIZE = 500  # Rows per API call (Google recommends < 1000)
RATE_LIMIT_DELAY = 1  # Seconds between API calls to avoid hitting quotas

# Core fields to export (most important for Julius and metadata tracking)
EXPORT_FIELDS = [
    'id', 'display_name', 'scientific_name', 'genus', 'species', 'author',
    'common_names', 'taxonomy_id', 'is_hybrid', 'grex_name', 
    'region', 'native_habitat', 'country', 'state_province',
    'decimal_latitude', 'decimal_longitude', 'elevation_m',
    'growth_habit', 'climate_preference', 'bloom_time', 'flower_color',
    'is_flowering', 'flower_count', 'fragrance',
    'image_url', 'photographer', 'image_source', 'image_attribution',
    'gbif_taxon_key', 'gbif_occurrence_key', 'eol_page_id',
    'inaturalist_observation_id', 'data_source', 'ingestion_source',
    'ai_description', 'ai_confidence', 'created_at', 'updated_at'
]

def get_sheets_service():
    """Initialize Google Sheets API service"""
    creds_json = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON')
    if not creds_json:
        raise ValueError("GOOGLE_SERVICE_ACCOUNT_JSON not found in environment")
    
    creds_dict = json.loads(creds_json)
    creds = service_account.Credentials.from_service_account_info(
        creds_dict,
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    
    return build('sheets', 'v4', credentials=creds)

def export_orchids_batch(offset=0, limit=None, test_mode=False):
    """
    Export orchid records to Google Sheets in batches
    
    Args:
        offset: Starting row offset
        limit: Maximum number of rows to export (None = all)
        test_mode: If True, only export first 100 rows for testing
    """
    with app.app_context():
        # Count total records
        total_count = db.session.query(func.count(OrchidRecord.id)).scalar()
        print(f"\n🌺 Orchid Continuum → Google Sheets Export")
        print(f"=" * 60)
        print(f"📊 Total records in database: {total_count:,}")
        
        if test_mode:
            limit = 100
            print(f"🧪 TEST MODE: Exporting first {limit} records")
        elif limit:
            print(f"📋 Export limit: {limit:,} records")
        else:
            print(f"📋 Exporting ALL records")
        
        print(f"🔢 Fields per record: {len(EXPORT_FIELDS)}")
        print(f"=" * 60 + "\n")
        
        # Get sheets service
        try:
            service = get_sheets_service()
            print("✅ Connected to Google Sheets API")
        except Exception as e:
            print(f"❌ Failed to connect to Google Sheets: {e}")
            return
        
        # Prepare header row
        header_row = [EXPORT_FIELDS]
        
        # Write header
        try:
            body = {'values': header_row}
            service.spreadsheets().values().update(
                spreadsheetId=SPREADSHEET_ID,
                range='Sheet1!A1',
                valueInputOption='RAW',
                body=body
            ).execute()
            print("✅ Header row written\n")
        except HttpError as e:
            print(f"❌ Failed to write header: {e}")
            return
        
        # Export data in batches
        current_offset = offset
        exported_count = 0
        batch_num = 1
        
        while True:
            # Determine batch size
            if limit:
                remaining = limit - exported_count
                current_batch_size = min(BATCH_SIZE, remaining)
                if current_batch_size <= 0:
                    break
            else:
                current_batch_size = BATCH_SIZE
            
            # Query batch
            query = db.session.query(OrchidRecord).order_by(OrchidRecord.id)
            batch = query.offset(current_offset).limit(current_batch_size).all()
            
            if not batch:
                break
            
            # Convert to rows
            rows = []
            for record in batch:
                row = []
                for field in EXPORT_FIELDS:
                    value = getattr(record, field, None)
                    
                    # Handle special data types
                    if isinstance(value, datetime):
                        row.append(value.isoformat() if value else '')
                    elif isinstance(value, bool):
                        row.append('TRUE' if value else 'FALSE')
                    elif value is None:
                        row.append('')
                    else:
                        row.append(str(value))
                
                rows.append(row)
            
            # Write batch to sheets
            try:
                start_row = 2 + current_offset  # +2 because: header row + 1-indexed
                end_row = start_row + len(rows) - 1
                range_name = f'Sheet1!A{start_row}:AK{end_row}'
                
                body = {'values': rows}
                service.spreadsheets().values().update(
                    spreadsheetId=SPREADSHEET_ID,
                    range=range_name,
                    valueInputOption='RAW',
                    body=body
                ).execute()
                
                exported_count += len(rows)
                current_offset += len(rows)
                
                progress = (exported_count / (limit or total_count)) * 100
                print(f"✅ Batch {batch_num}: Exported {len(rows)} rows (Total: {exported_count:,} / {progress:.1f}%)")
                
                batch_num += 1
                
                # Rate limiting
                time.sleep(RATE_LIMIT_DELAY)
                
            except HttpError as e:
                print(f"❌ Batch {batch_num} failed: {e}")
                break
        
        print(f"\n{'=' * 60}")
        print(f"🎉 Export Complete!")
        print(f"📊 Total exported: {exported_count:,} records")
        print(f"🔗 View: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
        print(f"{'=' * 60}\n")

if __name__ == '__main__':
    # Check for test mode flag
    test_mode = '--test' in sys.argv or '-t' in sys.argv
    
    # Check for limit flag
    limit = None
    for arg in sys.argv:
        if arg.startswith('--limit='):
            limit = int(arg.split('=')[1])
    
    export_orchids_batch(test_mode=test_mode, limit=limit)
