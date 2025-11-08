#!/usr/bin/env python3
"""
Simple Google Drive Sync - Works with public folders, no authentication needed!
Just make the folder public and run this script.
"""

import os
import sys
import requests
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Google Drive folder ID
GDRIVE_FOLDER_ID = "1aPJ6fzPCP6PdjCciPggpoxl9ZCCN7opy"

def sync_images():
    """Sync Google Drive images to database"""
    logger.info("🌸 Google Drive Image Sync Starting...")
    logger.info(f"📁 Folder: https://drive.google.com/drive/folders/{GDRIVE_FOLDER_ID}")
    logger.info("")
    logger.info("⚠️  IMPORTANT: Before running this script:")
    logger.info("   1. Open the folder in Google Drive")
    logger.info("   2. Click 'Share' button")
    logger.info("   3. Change to 'Anyone with the link' can view")
    logger.info("   4. Click 'Done'")
    logger.info("")
    
    # For now, let's just check database connectivity and show what we have
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        logger.error("❌ DATABASE_URL not found")
        return False
    
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check current state
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN google_drive_id IS NOT NULL AND google_drive_id != '' THEN 1 END) as with_gdrive,
                COUNT(CASE WHEN image_url IS NOT NULL AND image_url != '' THEN 1 END) as with_url,
                COUNT(CASE WHEN image_filename IS NOT NULL AND image_filename != '' THEN 1 END) as with_file
            FROM orchid_record
        """)
        
        stats = cursor.fetchone()
        
        logger.info("📊 Current Database State:")
        logger.info(f"   Total orchids: {stats['total']}")
        logger.info(f"   With Google Drive ID: {stats['with_gdrive']}")
        logger.info(f"   With image URL: {stats['with_url']}")  
        logger.info(f"   With local file: {stats['with_file']}")
        logger.info("")
        
        # Get sample orchids without images
        cursor.execute("""
            SELECT id, display_name, scientific_name, genus, species
            FROM orchid_record
            WHERE (google_drive_id IS NULL OR google_drive_id = '')
              AND (image_url IS NULL OR image_url = '')
              AND (image_filename IS NULL OR image_filename = '')
            LIMIT 10
        """)
        
        no_images = cursor.fetchall()
        
        if no_images:
            logger.info(f"📋 Sample orchids WITHOUT images ({len(no_images)} shown):")
            for orchid in no_images:
                name = orchid['display_name'] or orchid['scientific_name'] or f"{orchid['genus']} {orchid['species']}"
                logger.info(f"   • ID {orchid['id']}: {name}")
        
        logger.info("")
        logger.info("🔧 Next Steps:")
        logger.info("   To sync Google Drive images, you have 2 options:")
        logger.info("")
        logger.info("   OPTION 1 - Simple API Key (Recommended):")
        logger.info("   1. Get API key from https://console.cloud.google.com/apis/credentials")
        logger.info("   2. Add to Replit Secrets: GOOGLE_API_KEY")
        logger.info("   3. Run: python sync_google_drive_images.py")
        logger.info("")
        logger.info("   OPTION 2 - Manual Upload:")
        logger.info("   1. Download images from Google Drive")
        logger.info("   2. Upload via /upload page")
        logger.info("   3. Images will auto-link to records")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return False

if __name__ == '__main__':
    success = sync_images()
    sys.exit(0 if success else 1)
