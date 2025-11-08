#!/usr/bin/env python3
"""Simple GBIF Image Downloader - Working Version"""
import os
import requests
import psycopg2
from datetime import datetime

DATABASE_URL = os.environ.get("DATABASE_URL")

def search_gbif_image(scientific_name):
    """Search GBIF for images"""
    try:
        url = "https://api.gbif.org/v1/occurrence/search"
        response = requests.get(url, params={
            'scientificName': scientific_name,
            'mediaType': 'StillImage',
            'limit': 5
        }, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            for result in data.get('results', []):
                if 'media' in result:
                    for media in result['media']:
                        if media.get('type') == 'StillImage':
                            return media.get('identifier'), result.get('key')
        return None, None
    except:
        return None, None

def main():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Post start message
    cur.execute("""
        INSERT INTO julius_communication (message_from, message_type, subject, message)
        VALUES ('gbif_image_downloader', 'status_update', '🖼️ GBIF Image Download Started', 
                'Searching GBIF for orchid images...')
    """)
    conn.commit()
    
    # Get orchids needing images (wild species only, limit 30 for speed)
    cur.execute("""
        SELECT id, scientific_name
        FROM orchid_record
        WHERE image_url IS NULL
          AND species IS NOT NULL 
          AND species != ''
          AND scientific_name NOT LIKE '%×%'
        LIMIT 30
    """)
    
    orchids = cur.fetchall()
    print(f"Found {len(orchids)} orchids needing images")
    
    downloaded = 0
    for orchid_id, scientific_name in orchids:
        print(f"Searching GBIF for: {scientific_name}")
        image_url, gbif_key = search_gbif_image(scientific_name)
        
        if image_url:
            # Update database
            cur.execute("""
                UPDATE orchid_record
                SET image_url = %s,
                    image_source = 'GBIF',
                    image_attribution = %s
                WHERE id = %s
            """, (image_url, f'GBIF Occurrence {gbif_key}', orchid_id))
            
            # Log to dashboard
            cur.execute("""
                INSERT INTO julius_communication (message_from, message_type, subject, message)
                VALUES ('gbif_image_downloader', 'result', %s, %s)
            """, (
                f'✅ Image Downloaded: {scientific_name}',
                f'Found GBIF image: {image_url[:60]}...'
            ))
            
            conn.commit()
            downloaded += 1
            print(f"  ✅ Downloaded image")
        else:
            print(f"  ❌ No image found")
    
    # Final message
    cur.execute("""
        INSERT INTO julius_communication (message_from, message_type, subject, message)
        VALUES ('gbif_image_downloader', 'result', %s, %s)
    """, (
        f'✅ GBIF Download Complete: {downloaded} Images',
        f'Downloaded {downloaded} images from GBIF for orchids without images.'
    ))
    conn.commit()
    
    print(f"DONE! Downloaded {downloaded} images")
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
