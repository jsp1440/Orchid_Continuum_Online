#!/usr/bin/env python3
"""
Create Google Sheet with 34,000 orchid species + images
Organized by taxonomy with all data
"""

import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Load Google credentials
creds_json = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON')
creds_dict = json.loads(creds_json)

credentials = service_account.Credentials.from_service_account_info(
    creds_dict,
    scopes=[
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
)

# Build services
sheets_service = build('sheets', 'v4', credentials=credentials)
drive_service = build('drive', 'v3', credentials=credentials)

# Connect to database
db_conn = psycopg2.connect(os.environ.get('DATABASE_URL'))

SHARED_DRIVE_ID = '0ACirEfOT4qC_Uk9PVA'

print("🌺 CREATING ORCHID TAXONOMY MASTER SHEET\n")

# Step 1: Create Google Sheet
print("📊 Creating Google Sheet...")

spreadsheet = {
    'properties': {
        'title': 'Orchid Continuum - Complete Taxonomy with Images'
    },
    'sheets': [{
        'properties': {
            'title': 'Orchid Species Database',
            'gridProperties': {
                'frozenRowCount': 1
            }
        }
    }]
}

sheet = sheets_service.spreadsheets().create(
    body=spreadsheet,
    fields='spreadsheetId'
).execute()

sheet_id = sheet['spreadsheetId']
print(f"✅ Created sheet: {sheet_id}")

# Step 2: Move to Shared Drive
print(f"📁 Moving to Shared Drive...")

drive_service.files().update(
    fileId=sheet_id,
    addParents=SHARED_DRIVE_ID,
    supportsAllDrives=True,
    fields='id, parents'
).execute()

print(f"✅ Moved to Orchid_Image_Archives")

# Step 3: Get taxonomy data with image counts
print("🔍 Loading taxonomy data...")

with db_conn.cursor(cursor_factory=RealDictCursor) as cur:
    cur.execute("""
        SELECT 
            ot.id,
            ot.scientific_name,
            ot.genus,
            ot.species,
            ot.author,
            ot.family,
            ot.order,
            ot.class,
            ot.common_names,
            ot.taxonomic_status,
            ot.iucn_red_list_category,
            COUNT(DISTINCT oi.id) as image_count,
            STRING_AGG(DISTINCT oi.country, ', ') as countries,
            STRING_AGG(DISTINCT oi.google_drive_url, '; ') as image_urls
        FROM orchid_taxonomy ot
        LEFT JOIN orchid_images oi ON ot.id = oi.taxonomy_id
        GROUP BY ot.id
        ORDER BY ot.family, ot.genus, ot.species
    """)
    
    species_data = cur.fetchall()

print(f"✅ Found {len(species_data)} species")

# Step 4: Prepare sheet data
print("📝 Formatting data...")

# Header row
headers = [
    'Scientific Name',
    'Genus',
    'Species',
    'Author',
    'Family',
    'Order',
    'Class',
    'Common Names',
    'Status',
    'IUCN Category',
    'Image Count',
    'Countries Found',
    'Image URLs'
]

# Data rows
rows = [headers]
for sp in species_data:
    row = [
        sp['scientific_name'] or '',
        sp['genus'] or '',
        sp['species'] or '',
        sp['author'] or '',
        sp['family'] or '',
        sp['order'] or '',
        sp['class'] or '',
        sp['common_names'] or '',
        sp['taxonomic_status'] or '',
        sp['iucn_red_list_category'] or '',
        str(sp['image_count']),
        sp['countries'] or '',
        sp['image_urls'] or ''
    ]
    rows.append(row)

print(f"✅ Prepared {len(rows)-1} rows")

# Step 5: Write to sheet (in batches of 10,000 rows)
print("💾 Writing to Google Sheet...")

BATCH_SIZE = 10000
for i in range(0, len(rows), BATCH_SIZE):
    batch = rows[i:i+BATCH_SIZE]
    
    range_name = f'Orchid Species Database!A{i+1}'
    
    body = {
        'values': batch
    }
    
    sheets_service.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range=range_name,
        valueInputOption='RAW',
        body=body
    ).execute()
    
    print(f"  ✅ Wrote rows {i+1}-{i+len(batch)}")

# Step 6: Format header
print("🎨 Formatting...")

requests = [
    {
        'repeatCell': {
            'range': {
                'sheetId': 0,
                'startRowIndex': 0,
                'endRowIndex': 1
            },
            'cell': {
                'userEnteredFormat': {
                    'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.4},
                    'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
                    'horizontalAlignment': 'CENTER'
                }
            },
            'fields': 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)'
        }
    },
    {
        'autoResizeDimensions': {
            'dimensions': {
                'sheetId': 0,
                'dimension': 'COLUMNS',
                'startIndex': 0,
                'endIndex': len(headers)
            }
        }
    }
]

sheets_service.spreadsheets().batchUpdate(
    spreadsheetId=sheet_id,
    body={'requests': requests}
).execute()

print("✅ Formatting applied")

# Step 7: Share with domain
print("🔓 Sharing with fcosorchids.org...")

permission = {
    'type': 'domain',
    'role': 'writer',
    'domain': 'fcosorchids.org'
}

drive_service.permissions().create(
    fileId=sheet_id,
    body=permission,
    supportsAllDrives=True,
    sendNotificationEmail=False
).execute()

print("✅ Shared with your domain")

# Done!
print("\n" + "="*60)
print("🎉 SUCCESS!")
print("="*60)
print(f"Total species: {len(species_data)}")
print(f"Google Sheet URL:")
print(f"https://docs.google.com/spreadsheets/d/{sheet_id}")
print("="*60)

db_conn.close()
