#!/usr/bin/env python3
"""
Priority Image Collector - Focuses on Julius AI identified gaps
"""
import os
import psycopg2
import requests
import time
from datetime import datetime

DATABASE_URL = os.environ.get('DATABASE_URL')

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def get_gbif_images(genus, species, limit=5):
    """Get images from GBIF for specific orchid"""
    try:
        # Search for species in GBIF
        search_url = f"https://api.gbif.org/v1/species/match"
        params = {'genus': genus, 'species': species}
        response = requests.get(search_url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            usage_key = data.get('usageKey')
            
            if usage_key:
                # Get images
                media_url = f"https://api.gbif.org/v1/species/{usage_key}/media"
                media_response = requests.get(media_url, timeout=10)
                
                if media_response.status_code == 200:
                    media_data = media_response.json()
                    images = [item.get('identifier') for item in media_data.get('results', [])[:limit] if item.get('type') == 'StillImage']
                    return images
        
        return []
    except Exception as e:
        log(f"GBIF error: {e}")
        return []

def get_inaturalist_images(genus, species, limit=3):
    """Get images from iNaturalist"""
    try:
        search_name = f"{genus} {species}"
        url = "https://api.inaturalist.org/v1/observations"
        params = {
            'taxon_name': search_name,
            'quality_grade': 'research',
            'photos': 'true',
            'per_page': limit,
            'order': 'desc',
            'order_by': 'votes'
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            images = []
            for obs in data.get('results', []):
                if obs.get('photos'):
                    photo_url = obs['photos'][0].get('url', '').replace('square', 'medium')
                    if photo_url:
                        images.append(photo_url)
            return images
        
        return []
    except Exception as e:
        log(f"iNaturalist error: {e}")
        return []

def collect_priority_images():
    """Collect images for priority genera"""
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Get high-priority orchids needing images
    cursor.execute("""
        SELECT o.id, o.genus, o.species, o.scientific_name, MAX(eq.priority) as priority
        FROM orchid_record o
        JOIN enrichment_queue eq ON o.genus = eq.genus
        WHERE o.validation_status = 'approved'
        AND o.image_url IS NULL
        AND eq.enrichment_type = 'image_collection'
        AND eq.status = 'pending'
        GROUP BY o.id, o.genus, o.species, o.scientific_name
        ORDER BY priority DESC, o.id
        LIMIT 20
    """)
    
    orchids = cursor.fetchall()
    
    if not orchids:
        log("No priority orchids found needing images")
        cursor.close()
        conn.close()
        return
    
    log(f"📸 Found {len(orchids)} priority orchids needing images")
    
    collected_count = 0
    
    for orchid_id, genus, species, scientific_name, priority in orchids:
        log(f"Collecting images for: {scientific_name}")
        
        # Try GBIF first
        gbif_images = get_gbif_images(genus, species)
        
        # Try iNaturalist
        inat_images = get_inaturalist_images(genus, species)
        
        all_images = gbif_images + inat_images
        
        if all_images:
            # Store in external_images JSONB field
            cursor.execute("""
                UPDATE orchid_record
                SET external_images = %s,
                    image_url = %s,
                    updated_at = NOW()
                WHERE id = %s
            """, (
                str(all_images),
                all_images[0],  # Use first image as primary
                orchid_id
            ))
            
            conn.commit()
            collected_count += 1
            log(f"✅ Added {len(all_images)} images for {scientific_name}")
        else:
            log(f"⚠️ No images found for {scientific_name}")
        
        time.sleep(1)  # Rate limiting
    
    # Update enrichment queue
    cursor.execute("""
        UPDATE enrichment_queue
        SET status = 'in_progress', updated_at = NOW()
        WHERE enrichment_type = 'image_collection'
        AND status = 'pending'
    """)
    conn.commit()
    
    cursor.close()
    conn.close()
    
    log(f"✅ Batch complete! Collected images for {collected_count}/{len(orchids)} orchids")

if __name__ == "__main__":
    log("🚀 Priority Image Collector Starting...")
    collect_priority_images()
