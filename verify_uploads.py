#!/usr/bin/env python3
"""
Verify what's actually in the Google Shared Drive
"""

import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Load credentials
creds_json = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON')
creds_dict = json.loads(creds_json)

credentials = service_account.Credentials.from_service_account_info(
    creds_dict,
    scopes=['https://www.googleapis.com/auth/drive']
)

# Build Drive service
service = build('drive', 'v3', credentials=credentials)

SHARED_DRIVE_ID = '0ACirEfOT4qC_Uk9PVA'

print("🔍 Checking Shared Drive contents...\n")

try:
    # List ALL files in the shared drive
    results = service.files().list(
        q=f"'{SHARED_DRIVE_ID}' in parents",
        spaces='drive',
        fields='files(id, name, mimeType, parents)',
        supportsAllDrives=True,
        includeItemsFromAllDrives=True,
        corpora='drive',
        driveId=SHARED_DRIVE_ID
    ).execute()
    
    files = results.get('files', [])
    
    print(f"📁 Found {len(files)} items in Shared Drive root:\n")
    
    for file in files:
        print(f"   {file['name']}")
        print(f"      Type: {file['mimeType']}")
        print(f"      ID: {file['id']}")
        
        # If it's a folder, check inside
        if file['mimeType'] == 'application/vnd.google-apps.folder':
            folder_results = service.files().list(
                q=f"'{file['id']}' in parents",
                spaces='drive',
                fields='files(id, name)',
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
                pageSize=10
            ).execute()
            
            folder_files = folder_results.get('files', [])
            print(f"      Contains: {len(folder_files)} files")
            if folder_files:
                for ff in folder_files[:5]:
                    print(f"         - {ff['name']}")
        print()
    
    if not files:
        print("❌ Shared Drive is completely empty!")
        print("\nPossible issues:")
        print("1. Files are being uploaded elsewhere")
        print("2. Permission issue with service account")
        print("3. Wrong Shared Drive ID")
        
except Exception as e:
    print(f"❌ Error: {e}")
