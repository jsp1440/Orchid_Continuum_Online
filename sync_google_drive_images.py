#!/usr/bin/env python3
"""
Sync Google Drive Images to Database
Connects 1,000+ Google Drive images to existing orchid records
"""

import os
import sys
import json
import requests
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Google Drive folder ID from user
GDRIVE_FOLDER_ID = "1aPJ6fzPCP6PdjCciPggpoxl9ZCCN7opy"

def get_drive_service():
    """Get Google Drive service using service account credentials"""
    try:
        from googleapiclient.discovery import build
        from google.oauth2.service_account import Credentials
        
        # Try to get service account credentials
        service_account_json = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON')
        if not service_account_json:
            logger.error("❌ GOOGLE_SERVICE_ACCOUNT_JSON not found in environment")
            return None
        
        credentials_info = json.loads(service_account_json)
        credentials = Credentials.from_service_account_info(
            credentials_info,
            scopes=['https://www.googleapis.com/auth/drive.readonly']
        )
        
        service = build('drive', 'v3', credentials=credentials)
        logger.info("✅ Google Drive service initialized with service account")
        return service
        
    except ImportError as e:
        logger.error(f"❌ Missing required libraries: {e}")
        logger.info("Install with: pip install google-api-python-client google-auth")
        return None
    except Exception as e:
        logger.error(f"❌ Failed to initialize Google Drive service: {e}")
        return None

def list_drive_files(drive_service, folder_id, page_token=None):
    """List all files from a Google Drive folder using service account"""
    try:
        query = f"'{folder_id}' in parents and trashed=false"
        fields = 'nextPageToken, files(id, name, mimeType, size, createdTime, thumbnailLink, webViewLink)'
        
        results = drive_service.files().list(
            q=query,
            pageSize=1000,
            fields=fields,
            pageToken=page_token,
            orderBy='name'
        ).execute()
        
        return results
    except Exception as e:
        logger.error(f"❌ Failed to list Drive files: {e}")
        return None

def get_all_drive_files_recursive(drive_service, folder_id, depth=0):
    """Recursively get ALL files from folder and subfolders"""
    all_files = []
    folders_to_process = [(folder_id, depth)]
    
    while folders_to_process:
        current_folder_id, current_depth = folders_to_process.pop(0)
        indent = "  " * current_depth
        
        page_token = None
        while True:
            data = list_drive_files(drive_service, current_folder_id, page_token)
            if not data:
                break
            
            files = data.get('files', [])
            
            for file in files:
                if file.get('mimeType') == 'application/vnd.google-apps.folder':
                    # Found a subfolder - add to processing queue
                    logger.info(f"{indent}📁 Found subfolder: {file['name']}")
                    folders_to_process.append((file['id'], current_depth + 1))
                elif file.get('mimeType', '').startswith('image/'):
                    # Found an image - add to results
                    all_files.append(file)
                    logger.debug(f"{indent}🖼️  {file['name']}")
            
            logger.info(f"{indent}📥 Fetched {len(files)} items from current folder (total images: {len(all_files)})")
            
            page_token = data.get('nextPageToken')
            if not page_token:
                break
    
    return all_files

def get_all_drive_files(drive_service, folder_id):
    """Get ALL files from folder (handles pagination) - wrapper for backward compatibility"""
    return get_all_drive_files_recursive(drive_service, folder_id)

def parse_filename(filename):
    """
    Parse orchid filename to extract genus and species
    Examples:
      "Cattleya walkeriana.jpg" -> ("Cattleya", "walkeriana")
      "Phalaenopsis_stuartiana.JPG" -> ("Phalaenopsis", "stuartiana")
      "Dendrobium nobile 'Virginalis'.jpg" -> ("Dendrobium", "nobile")
    """
    # Remove file extension
    name_without_ext = os.path.splitext(filename)[0]
    
    # Replace underscores with spaces
    name_clean = name_without_ext.replace('_', ' ')
    
    # Split on spaces
    parts = name_clean.split()
    
    if len(parts) >= 2:
        genus = parts[0].strip().capitalize()
        species = parts[1].strip().lower()
        return genus, species
    
    return None, None

def sync_images_to_database():
    """Main sync function"""
    logger.info("🌸 Starting Google Drive → Database Sync")
    logger.info(f"📁 Folder ID: {GDRIVE_FOLDER_ID}")
    
    # Get Drive service
    drive_service = get_drive_service()
    if not drive_service:
        return False
    
    # Get all files from Google Drive
    logger.info("📥 Fetching files from Google Drive (including subfolders)...")
    drive_files = get_all_drive_files(drive_service, GDRIVE_FOLDER_ID)
    
    if not drive_files:
        logger.error("❌ No files found or API error")
        return False
    
    logger.info(f"✅ Found {len(drive_files)} files in Google Drive")
    
    # Filter to image files only
    image_files = [
        f for f in drive_files 
        if f.get('mimeType', '').startswith('image/')
    ]
    logger.info(f"🖼️  {len(image_files)} are images")
    
    # Connect to database
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        logger.error("❌ DATABASE_URL not found")
        return False
    
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Analyze what we have
        stats = {
            'total_images': len(image_files),
            'matched': 0,
            'updated': 0,
            'no_match': 0,
            'errors': 0
        }
        
        logger.info("🔍 Matching images to database records...")
        
        for img in image_files:
            file_id = img['id']
            filename = img['name']
            
            # Parse filename
            genus, species = parse_filename(filename)
            
            if not genus or not species:
                logger.debug(f"⚠️  Skipped {filename} - couldn't parse genus/species")
                stats['no_match'] += 1
                continue
            
            # Try to find matching record in database
            cursor.execute("""
                SELECT id, display_name, scientific_name, genus, species, google_drive_id
                FROM orchid_record
                WHERE LOWER(genus) = LOWER(%s) AND LOWER(species) = LOWER(%s)
                LIMIT 1
            """, (genus, species))
            
            record = cursor.fetchone()
            
            if record:
                stats['matched'] += 1
                
                # Only update if not already linked
                if not record['google_drive_id']:
                    cursor.execute("""
                        UPDATE orchid_record
                        SET google_drive_id = %s
                        WHERE id = %s
                    """, (file_id, record['id']))
                    stats['updated'] += 1
                    logger.info(f"✅ Linked: {filename} → {record['display_name'] or record['scientific_name']}")
                else:
                    logger.debug(f"⏭️  Already linked: {filename}")
            else:
                stats['no_match'] += 1
                logger.debug(f"⚠️  No match for: {filename} ({genus} {species})")
        
        # Commit changes
        conn.commit()
        
        # Print summary
        logger.info("\n" + "="*60)
        logger.info("📊 SYNC SUMMARY")
        logger.info("="*60)
        logger.info(f"Total images in Google Drive: {stats['total_images']}")
        logger.info(f"Matched to database records: {stats['matched']}")
        logger.info(f"Database records updated: {stats['updated']}")
        logger.info(f"No database match: {stats['no_match']}")
        logger.info(f"Errors: {stats['errors']}")
        logger.info("="*60)
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Database error: {e}")
        return False

if __name__ == '__main__':
    success = sync_images_to_database()
    sys.exit(0 if success else 1)
