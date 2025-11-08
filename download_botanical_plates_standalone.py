"""
Standalone Botanical Plates & Herbarium Sheets Downloader
Downloads from Wikimedia Commons with full attribution
Saves directly to PostgreSQL database
"""
import requests
import time
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
import re

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Database connection from environment
DATABASE_URL = os.environ.get('DATABASE_URL')


def get_bloombuilder_species():
    """Get all BloomBuilder species from database"""
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("SELECT id, genus, species, common_name FROM bloombuilder_species ORDER BY genus, species")
    species_list = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return species_list


def search_wikimedia_commons(search_term, limit=10, image_type="botanical illustration"):
    """Search Wikimedia Commons for botanical images"""
    url = "https://commons.wikimedia.org/w/api.php"
    
    if image_type == "botanical illustration":
        query = f"{search_term} botanical illustration OR botanical plate OR Curtis botanical magazine"
    else:
        query = f"{search_term} herbarium specimen OR herbarium sheet"
    
    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": query,
        "gsrnamespace": "6",
        "gsrlimit": limit,
        "prop": "imageinfo",
        "iiprop": "url|size|extmetadata|timestamp",
        "iiurlwidth": "1200"
    }
    
    # Required User-Agent header for Wikimedia API
    headers = {
        "User-Agent": "OrchidContinuum/1.0 (https://orchid-continuum.replit.app; contact@orchidcontinuum.org) Python/requests"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        images = []
        if "query" in data and "pages" in data["query"]:
            for page_id, page in data["query"]["pages"].items():
                if "imageinfo" in page:
                    info = page["imageinfo"][0]
                    metadata = info.get("extmetadata", {})
                    
                    artist = metadata.get("Artist", {}).get("value", "Unknown")
                    credit = metadata.get("Credit", {}).get("value", "")
                    license_short = metadata.get("LicenseShortName", {}).get("value", "CC-BY-SA")
                    date_time = metadata.get("DateTimeOriginal", {}).get("value", "")
                    
                    # Clean HTML tags from artist name
                    artist_clean = re.sub(r'<[^>]+>', '', artist)
                    
                    image_data = {
                        "title": page.get("title", "").replace("File:", ""),
                        "url": info.get("url", ""),
                        "thumb_url": info.get("thumburl", ""),
                        "artist": artist_clean[:200],
                        "license": license_short,
                        "date": date_time,
                        "source_url": f"https://commons.wikimedia.org/wiki/{page.get('title', '')}"
                    }
                    images.append(image_data)
        
        logger.info(f"  Found {len(images)} images for '{search_term}' ({image_type})")
        return images
        
    except Exception as e:
        logger.error(f"  Error searching Wikimedia: {e}")
        return []


def save_to_database(conn, image_data, genus, species_epithet, image_source_type):
    """Save image to orchid_images table"""
    cursor = conn.cursor()
    
    try:
        # Check if already exists
        cursor.execute(
            "SELECT id FROM orchid_images WHERE image_url = %s",
            (image_data['url'],)
        )
        
        if cursor.fetchone():
            logger.info(f"    ⏭️  Already exists: {image_data['title'][:50]}...")
            cursor.close()
            return False
        
        # Insert new image
        cursor.execute("""
            INSERT INTO orchid_images (
                image_url, image_source, genus_name, species_epithet,
                observer_name, institution_code, source_url, license_info
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            image_data['url'],
            image_source_type,
            genus,
            species_epithet,
            image_data['artist'],
            'Wikimedia Commons',
            image_data['source_url'],
            image_data['license']
        ))
        
        conn.commit()
        logger.info(f"    ✅ Saved: {image_data['title'][:60]}")
        cursor.close()
        return True
        
    except Exception as e:
        conn.rollback()
        logger.error(f"    ❌ Error saving: {e}")
        cursor.close()
        return False


def download_all():
    """Main download function"""
    logger.info("=" * 70)
    logger.info("🌺 BOTANICAL PLATE & HERBARIUM SHEET DOWNLOADER")
    logger.info("=" * 70)
    logger.info("Source: Wikimedia Commons")
    logger.info("Attribution: Full credit preserved for all images")
    logger.info("=" * 70)
    
    # Get species list
    species_list = get_bloombuilder_species()
    logger.info(f"\n📋 Found {len(species_list)} BloomBuilder species")
    
    # Connect to database
    conn = psycopg2.connect(DATABASE_URL)
    
    total_plates = 0
    total_herbarium = 0
    
    for species in species_list:
        scientific_name = f"{species['genus']} {species['species']}"
        logger.info(f"\n{'─' * 70}")
        logger.info(f"🔍 {scientific_name}")
        logger.info(f"{'─' * 70}")
        
        # Download botanical illustrations
        logger.info("  📖 Searching for botanical illustrations...")
        illustrations = search_wikimedia_commons(
            scientific_name,
            limit=8,
            image_type="botanical illustration"
        )
        
        for img in illustrations:
            if save_to_database(conn, img, species['genus'], species['species'], "Botanical Illustration - Wikimedia"):
                total_plates += 1
            time.sleep(0.3)
        
        # Download herbarium sheets
        logger.info("  🌿 Searching for herbarium sheets...")
        herbarium = search_wikimedia_commons(
            scientific_name,
            limit=8,
            image_type="herbarium"
        )
        
        for img in herbarium:
            if save_to_database(conn, img, species['genus'], species['species'], "Herbarium Sheet - Wikimedia"):
                total_herbarium += 1
            time.sleep(0.3)
        
        time.sleep(1)  # Rate limiting between species
    
    conn.close()
    
    # Print summary
    logger.info(f"\n{'=' * 70}")
    logger.info(f"✅ DOWNLOAD COMPLETE!")
    logger.info(f"{'=' * 70}")
    logger.info(f"🎨 Botanical Illustrations: {total_plates} new images")
    logger.info(f"🌿 Herbarium Sheets: {total_herbarium} new images")
    logger.info(f"📊 Total New Images: {total_plates + total_herbarium}")
    logger.info(f"{'=' * 70}")
    
    # Database summary
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT image_source, COUNT(*) as count
        FROM orchid_images
        GROUP BY image_source
        ORDER BY count DESC
    """)
    
    logger.info("\n📊 DATABASE SUMMARY:")
    for row in cursor.fetchall():
        logger.info(f"  {row[0]}: {row[1]} images")
    
    cursor.close()
    conn.close()


if __name__ == "__main__":
    download_all()
