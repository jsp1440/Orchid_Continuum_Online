#!/usr/bin/env python3
"""
Fix invalid Flickr URLs by replacing them with real GBIF occurrence images
"""

import requests
from app import app, db
from models import OrchidRecord
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_gbif_image_url(genus: str, species: str) -> str | None:
    """Fetch a real image URL from GBIF for the given species"""
    try:
        # Search GBIF occurrences with images
        url = "https://api.gbif.org/v1/occurrence/search"
        params = {
            'scientificName': f"{genus} {species}",
            'mediaType': 'StillImage',
            'hasCoordinate': 'true',
            'limit': 10
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Extract first available image URL
        if data.get('results'):
            for result in data['results']:
                media = result.get('media', [])
                for m in media:
                    if m.get('type') == 'StillImage' and m.get('identifier'):
                        image_url = m['identifier']
                        # Validate it's a real URL
                        if image_url.startswith('http') and any(ext in image_url.lower() for ext in ['.jpg', '.jpeg', '.png']):
                            logger.info(f"  ✅ Found GBIF image: {image_url[:80]}...")
                            return image_url
        
        logger.warning(f"  ❌ No GBIF images found for {genus} {species}")
        return None
        
    except Exception as e:
        logger.error(f"  ❌ GBIF lookup failed for {genus} {species}: {e}")
        return None

def fix_invalid_flickr_urls():
    """Fix all invalid Flickr URLs in the database"""
    with app.app_context():
        # Find all records with invalid Flickr URLs
        invalid_records = OrchidRecord.query.filter(
            OrchidRecord.image_url.like('https://flickr.com/%'),
            ~OrchidRecord.image_url.like('%staticflickr.com%')
        ).all()
        
        logger.info(f"🔍 Found {len(invalid_records)} records with invalid Flickr URLs")
        
        # Group by species to avoid duplicate GBIF lookups
        species_images = {}
        fixed_count = 0
        removed_count = 0
        
        for record in invalid_records:
            species_key = f"{record.genus} {record.species}"
            
            # Check if we already looked up this species
            if species_key not in species_images:
                logger.info(f"🔎 Looking up: {species_key}")
                species_images[species_key] = get_gbif_image_url(record.genus, record.species)
            
            # Update the record
            new_url = species_images[species_key]
            if new_url:
                logger.info(f"  ✏️  Updating ID {record.id}: {record.display_name}")
                record.image_url = new_url
                fixed_count += 1
            else:
                logger.info(f"  🗑️  Removing invalid URL from ID {record.id}: {record.display_name}")
                record.image_url = None
                removed_count += 1
        
        # Commit changes
        db.session.commit()
        
        logger.info(f"\n✅ URL Fix Complete!")
        logger.info(f"   Fixed with GBIF images: {fixed_count}")
        logger.info(f"   Removed (no images found): {removed_count}")
        logger.info(f"   Total updated: {len(invalid_records)}")
        
        return fixed_count, removed_count

if __name__ == "__main__":
    print("🔧 Fixing invalid Flickr URLs...\n")
    fixed, removed = fix_invalid_flickr_urls()
    print(f"\n🎉 Done! Fixed {fixed} URLs, removed {removed} invalid URLs")
