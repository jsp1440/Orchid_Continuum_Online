#!/usr/bin/env python3
"""
Julius AI Helper Script - Add GBIF Data to Google Sheets
Usage: Julius can adapt this script to batch-upload GBIF orchid data
"""
import os
import json
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configuration
SPREADSHEET_ID = "1UQZj4ZaA7cWnU0SozR4_qReWNOm0V9xz"
SHEET_NAME = "Sheet1"
DRIVE_FOLDER_ID = "1jQoQ9x-2f1ENZq7iVCgneAmoQIvc6xIS"

# Column order (17 fields)
COLUMNS = [
    'id', 'display_name', 'scientific_name', 'genus', 'species',
    'region', 'country', 'decimal_latitude', 'decimal_longitude',
    'growth_habit', 'bloom_time', 'flower_color', 'is_flowering',
    'image_url', 'photographer', 'data_source', 'created_at'
]

def get_google_services():
    """Initialize Google Sheets and Drive APIs"""
    creds_json = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON')
    if not creds_json:
        raise ValueError("GOOGLE_SERVICE_ACCOUNT_JSON not found in environment")
    
    creds_dict = json.loads(creds_json)
    creds = service_account.Credentials.from_service_account_info(
        creds_dict,
        scopes=[
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
    )
    
    sheets_service = build('sheets', 'v4', credentials=creds)
    drive_service = build('drive', 'v3', credentials=creds)
    
    return sheets_service, drive_service

def get_next_id(sheets_service):
    """Get the next available ID by checking last row"""
    try:
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f'{SHEET_NAME}!A:A'
        ).execute()
        
        values = result.get('values', [])
        if len(values) > 1:  # Skip header row
            last_id = int(values[-1][0])
            return last_id + 1
        else:
            return 1
    except (HttpError, IndexError, ValueError):
        # If can't determine, start from 6000 (after existing 5915)
        return 6000

def upload_image_to_drive(drive_service, image_path, filename):
    """
    Upload image to Google Drive folder
    Returns shareable link
    """
    file_metadata = {
        'name': filename,
        'parents': [DRIVE_FOLDER_ID]
    }
    
    from googleapiclient.http import MediaFileUpload
    media = MediaFileUpload(image_path, resumable=True)
    
    file = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, webViewLink'
    ).execute()
    
    # Make file publicly accessible
    permission = {
        'type': 'anyone',
        'role': 'reader'
    }
    drive_service.permissions().create(
        fileId=file['id'],
        body=permission
    ).execute()
    
    return file['webViewLink']

def add_orchid_batch(sheets_service, orchid_records):
    """
    Add multiple orchid records to Google Sheets
    
    Args:
        sheets_service: Google Sheets API service
        orchid_records: List of dicts with orchid data
    
    Example record:
    {
        'display_name': 'Cattleya labiata',
        'scientific_name': 'Cattleya labiata Lindl.',
        'genus': 'Cattleya',
        'species': 'labiata',
        'region': 'South America',
        'country': 'Brazil',
        'decimal_latitude': -10.5,
        'decimal_longitude': -50.2,
        'growth_habit': 'epiphytic',
        'bloom_time': 'Fall',
        'flower_color': 'Pink/Purple',
        'is_flowering': True,
        'image_url': 'https://drive.google.com/...',
        'photographer': 'John Smith',
        'data_source': 'GBIF'
    }
    """
    
    # Get next available ID
    next_id = get_next_id(sheets_service)
    
    # Convert records to rows
    rows = []
    for i, record in enumerate(orchid_records):
        row = [
            next_id + i,
            record.get('display_name', ''),
            record.get('scientific_name', ''),
            record.get('genus', ''),
            record.get('species', ''),
            record.get('region', ''),
            record.get('country', ''),
            str(record.get('decimal_latitude', '')),
            str(record.get('decimal_longitude', '')),
            record.get('growth_habit', ''),
            record.get('bloom_time', ''),
            record.get('flower_color', ''),
            'TRUE' if record.get('is_flowering') else 'FALSE',
            record.get('image_url', ''),
            record.get('photographer', ''),
            record.get('data_source', 'GBIF'),
            datetime.now().isoformat()
        ]
        rows.append(row)
    
    # Append to sheet
    body = {'values': rows}
    result = sheets_service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=f'{SHEET_NAME}!A:Q',
        valueInputOption='RAW',
        insertDataOption='INSERT_ROWS',
        body=body
    ).execute()
    
    return result

# Example usage
if __name__ == '__main__':
    print("🌺 Julius AI - Google Sheets Helper")
    print("=" * 60)
    
    # Initialize services
    try:
        sheets_service, drive_service = get_google_services()
        print("✅ Connected to Google Sheets & Drive APIs\n")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        exit(1)
    
    # Example: Add test orchid records
    test_records = [
        {
            'display_name': 'Cattleya labiata',
            'scientific_name': 'Cattleya labiata Lindl.',
            'genus': 'Cattleya',
            'species': 'labiata',
            'region': 'South America',
            'country': 'Brazil',
            'decimal_latitude': -10.5,
            'decimal_longitude': -50.2,
            'growth_habit': 'epiphytic',
            'bloom_time': 'Fall',
            'flower_color': 'Pink/Purple',
            'is_flowering': True,
            'image_url': 'https://example.com/test-image.jpg',
            'photographer': 'Test Photographer',
            'data_source': 'GBIF'
        }
    ]
    
    print(f"📝 Adding {len(test_records)} test orchid(s)...\n")
    
    try:
        result = add_orchid_batch(sheets_service, test_records)
        print(f"✅ Successfully added {len(test_records)} orchid(s)!")
        print(f"📊 Updated range: {result.get('updates', {}).get('updatedRange')}")
        print(f"\n🔗 View sheet: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
    except HttpError as e:
        print(f"❌ Failed to add records: {e}")
    
    print("=" * 60)
