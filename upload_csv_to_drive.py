#!/usr/bin/env python3
"""
Upload the taxonomy CSV directly to Google Shared Drive
"""

import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Load credentials
creds_json = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON')
creds_dict = json.loads(creds_json)

credentials = service_account.Credentials.from_service_account_info(
    creds_dict,
    scopes=['https://www.googleapis.com/auth/drive']
)

# Build Drive service
drive_service = build('drive', 'v3', credentials=credentials)

SHARED_DRIVE_ID = '0ACirEfOT4qC_Uk9PVA'
CSV_FILE = 'ORCHID_TAXONOMY_WITH_IMAGES.csv'

print("📤 Uploading CSV to your Shared Drive...\n")

# Upload file
file_metadata = {
    'name': 'Orchid Taxonomy with Images (35,320 species)',
    'parents': [SHARED_DRIVE_ID],
    'mimeType': 'text/csv'
}

media = MediaFileUpload(
    CSV_FILE,
    mimetype='text/csv',
    resumable=True
)

file = drive_service.files().create(
    body=file_metadata,
    media_body=media,
    fields='id, webViewLink',
    supportsAllDrives=True
).execute()

print(f"✅ Uploaded successfully!")
print(f"\nFile ID: {file['id']}")
print(f"View URL: {file['webViewLink']}")

# Share with domain
print("\n🔓 Sharing with fcosorchids.org domain...")

permission = {
    'type': 'domain',
    'role': 'writer',
    'domain': 'fcosorchids.org'
}

drive_service.permissions().create(
    fileId=file['id'],
    body=permission,
    supportsAllDrives=True,
    sendNotificationEmail=False
).execute()

print("✅ Shared!")

print("\n" + "="*60)
print("🎉 DONE!")
print("="*60)
print("The CSV is now in your Shared Drive!")
print(f"\nGo to: https://drive.google.com/drive/folders/{SHARED_DRIVE_ID}")
print("You'll see: 'Orchid Taxonomy with Images (35,320 species)'")
print("\nRight-click it → Open with → Google Sheets")
print("="*60)
