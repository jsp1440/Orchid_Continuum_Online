#!/usr/bin/env python3
"""
Test if service account can access Google Shared Drives
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

print("🔍 Checking Shared Drive access...\n")

try:
    # List all shared drives the service account has access to
    results = service.drives().list(pageSize=10).execute()
    drives = results.get('drives', [])
    
    if not drives:
        print("❌ No Shared Drives found")
        print("   The service account doesn't have access to any Shared Drives yet")
        print("\n✅ TO FIX: Share the Shared Drive with:")
        print("   google-service-account@orchid-photo-studio.iam.gserviceaccount.com")
    else:
        print(f"✅ Found {len(drives)} Shared Drive(s):\n")
        for drive in drives:
            print(f"   📁 Name: {drive['name']}")
            print(f"      ID: {drive['id']}")
            print()
        
        print("🎉 SUCCESS! Service account has Shared Drive access!")
        print("\nYou can now use these Shared Drive IDs for uploading images.")
        
except Exception as e:
    print(f"❌ Error: {e}")
