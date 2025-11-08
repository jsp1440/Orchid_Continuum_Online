#!/usr/bin/env python3
"""
Simple standalone Google Sheets export - no Flask dependencies
"""
import os
import json
import time
import psycopg2
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SPREADSHEET_ID = "1UQZj4ZaA7cWnU0SozR4_qReWNOm0V9xz"
BATCH_SIZE = 500
RATE_LIMIT_DELAY = 1

EXPORT_FIELDS = [
    'id', 'display_name', 'scientific_name', 'genus', 'species',
    'region', 'country', 'decimal_latitude', 'decimal_longitude',
    'growth_habit', 'bloom_time', 'flower_color', 'is_flowering',
    'image_url', 'photographer', 'data_source', 'created_at'
]

def get_sheets_service():
    """Initialize Google Sheets API service"""
    creds_json = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON')
    if not creds_json:
        raise ValueError("GOOGLE_SERVICE_ACCOUNT_JSON not found")
    
    creds_dict = json.loads(creds_json)
    creds = service_account.Credentials.from_service_account_info(
        creds_dict,
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    
    return build('sheets', 'v4', credentials=creds)

def export_test_batch():
    """Export first 100 records as a test"""
    
    # Connect to database
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()
    
    print("\n🌺 Orchid Continuum → Google Sheets Test Export")
    print("=" * 60)
    
    # Count total
    cur.execute("SELECT COUNT(*) FROM orchid_record")
    total_count = cur.fetchone()[0]
    print(f"📊 Total records in database: {total_count:,}")
    print(f"🧪 TEST MODE: Exporting first 100 records\n")
    
    # Get sheets service
    service = get_sheets_service()
    print("✅ Connected to Google Sheets API\n")
    
    # Write header
    header_row = [EXPORT_FIELDS]
    body = {'values': header_row}
    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range='Sheet1!A1',
        valueInputOption='RAW',
        body=body
    ).execute()
    print("✅ Header row written\n")
    
    # Query data
    field_sql = ', '.join(EXPORT_FIELDS)
    cur.execute(f"SELECT {field_sql} FROM orchid_record ORDER BY id LIMIT 100")
    
    # Convert to rows
    rows = []
    for record in cur.fetchall():
        row = []
        for value in record:
            if value is None:
                row.append('')
            elif isinstance(value, bool):
                row.append('TRUE' if value else 'FALSE')
            else:
                row.append(str(value))
        rows.append(row)
    
    # Write to sheets
    body = {'values': rows}
    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range='Sheet1!A2',
        valueInputOption='RAW',
        body=body
    ).execute()
    
    print(f"✅ Exported {len(rows)} rows\n")
    print("=" * 60)
    print(f"🎉 Test Export Complete!")
    print(f"🔗 View: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
    print("=" * 60 + "\n")
    
    cur.close()
    conn.close()

if __name__ == '__main__':
    export_test_batch()
