"""
Download Botanical Plates and Herbarium Sheets from Wikimedia Commons
Saves to orchid_images table with full attribution
"""
import requests
import time
from app import app, db
from models import OrchidImage, BloomBuilderSpecies
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def search_wikimedia_commons(search_term, limit=20, image_type="botanical illustration"):
    """
    Search Wikimedia Commons for botanical illustrations or herbarium sheets
    """
    url = "https://commons.wikimedia.org/w/api.php"
    
    # Enhanced search query
    if image_type == "botanical illustration":
        query = f"{search_term} botanical illustration OR botanical plate OR Curtis botanical"
    else:
        query = f"{search_term} herbarium specimen"
    
    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": query,
        "gsrnamespace": "6",  # File namespace
        "gsrlimit": limit,
        "prop": "imageinfo",
        "iiprop": "url|size|extmetadata|timestamp",
        "iiurlwidth": "1200"
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        images = []
        if "query" in data and "pages" in data["query"]:
            for page_id, page in data["query"]["pages"].items():
                if "imageinfo" in page:
                    info = page["imageinfo"][0]
                    metadata = info.get("extmetadata", {})
                    
                    # Extract attribution data
                    artist = metadata.get("Artist", {}).get("value", "Unknown")
                    credit = metadata.get("Credit", {}).get("value", "")
                    license_short = metadata.get("LicenseShortName", {}).get("value", "")
                    date_time = metadata.get("DateTimeOriginal", {}).get("value", "")
                    description = metadata.get("ImageDescription", {}).get("value", "")
                    
                    # Clean up artist name (remove HTML tags)
                    import re
                    artist_clean = re.sub(r'<[^>]+>', '', artist)
                    
                    image_data = {
                        "title": page.get("title", "").replace("File:", ""),
                        "url": info.get("url", ""),
                        "thumb_url": info.get("thumburl", ""),
                        "width": info.get("width", 0),
                        "height": info.get("height", 0),
                        "artist": artist_clean[:200],
                        "credit": credit[:500] if credit else "",
                        "license": license_short,
                        "date": date_time,
                        "description": description[:1000] if description else "",
                        "source_url": f"https://commons.wikimedia.org/wiki/{page.get('title', '')}",
                        "timestamp": info.get("timestamp", "")
                    }
                    images.append(image_data)
        
        logger.info(f"Found {len(images)} images for '{search_term}' ({image_type})")
        return images
        
    except Exception as e:
        logger.error(f"Error searching Wikimedia: {e}")
        return []


def save_to_database(image_data, species_name, image_type="Botanical Illustration"):
    """
    Save image to orchid_images table with full attribution
    """
    try:
        # Parse species name
        parts = species_name.split()
        genus = parts[0] if len(parts) > 0 else ""
        species_epithet = parts[1] if len(parts) > 1 else ""
        
        # Check if already exists
        existing = OrchidImage.query.filter_by(
            image_url=image_data['url']
        ).first()
        
        if existing:
            logger.info(f"Image already exists: {image_data['title'][:50]}")
            return False
        
        # Create new record
        new_image = OrchidImage(
            image_url=image_data['url'],
            image_source=image_type,
            genus_name=genus,
            species_epithet=species_epithet,
            observer_name=image_data['artist'],
            institution_code="Wikimedia Commons",
            source_url=image_data['source_url'],
            license_info=image_data['license'],
            locality=image_data.get('credit', '')[:200],
            observation_date=None,  # Botanical plates don't have observation dates
            latitude=None,
            longitude=None
        )
        
        db.session.add(new_image)
        db.session.commit()
        
        logger.info(f"✅ Saved: {image_data['title'][:60]}")
        return True
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error saving image: {e}")
        return False


def download_for_bloombuilder_species(limit_per_species=10):
    """
    Download botanical plates for all 25 BloomBuilder pilot species
    """
    with app.app_context():
        species_list = BloomBuilderSpecies.query.all()
        
        logger.info(f"Starting download for {len(species_list)} species")
        
        total_saved = 0
        for species in species_list:
            scientific_name = f"{species.genus} {species.species}"
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing: {scientific_name}")
            logger.info(f"{'='*60}")
            
            # Download botanical illustrations
            logger.info("Searching for botanical illustrations...")
            illustrations = search_wikimedia_commons(
                scientific_name, 
                limit=limit_per_species,
                image_type="botanical illustration"
            )
            
            for img in illustrations:
                if save_to_database(img, scientific_name, "Botanical Illustration"):
                    total_saved += 1
                time.sleep(0.5)  # Rate limiting
            
            # Download herbarium sheets
            logger.info("Searching for herbarium sheets...")
            herbarium = search_wikimedia_commons(
                scientific_name,
                limit=limit_per_species,
                image_type="herbarium"
            )
            
            for img in herbarium:
                if save_to_database(img, scientific_name, "Herbarium Sheet - Wikimedia"):
                    total_saved += 1
                time.sleep(0.5)  # Rate limiting
            
            time.sleep(1)  # Pause between species
        
        logger.info(f"\n{'='*60}")
        logger.info(f"✅ COMPLETE: Saved {total_saved} new images to database")
        logger.info(f"{'='*60}")
        
        # Print summary
        from sqlalchemy import func
        summary = db.session.query(
            OrchidImage.image_source,
            func.count(OrchidImage.id)
        ).group_by(OrchidImage.image_source).all()
        
        logger.info("\nDatabase Summary:")
        for source, count in summary:
            logger.info(f"  {source}: {count} images")


if __name__ == "__main__":
    print("🌺 Botanical Plate & Herbarium Sheet Downloader")
    print("=" * 60)
    print("This will download images from Wikimedia Commons for")
    print("all 25 BloomBuilder species with full attribution.")
    print("=" * 60)
    
    download_for_bloombuilder_species(limit_per_species=10)
