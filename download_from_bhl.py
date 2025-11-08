"""
Download Botanical Plates from Biodiversity Heritage Library (BHL)
BHL has thousands of high-quality botanical illustrations with full attribution
Much more reliable than Wikimedia Commons for historical botanical plates
"""
import requests
import time
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

DATABASE_URL = os.environ.get('DATABASE_URL')
BHL_API_BASE = "https://www.biodiversitylibrary.org/api3"


def get_bloombuilder_species():
    """Get all BloomBuilder species"""
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT id, genus, species FROM bloombuilder_species ORDER BY genus, species")
    species_list = cursor.fetchall()
    cursor.close()
    conn.close()
    return species_list


def search_bhl_for_species(scientific_name, limit=15):
    """
    Search BHL for botanical illustrations of a species
    BHL API is free and doesn't require authentication
    """
    url = f"{BHL_API_BASE}?op=PublicationSearchAdvanced&searchterm={scientific_name}&searchtype=F&format=json"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        results = []
        if data.get("Status") == "ok" and data.get("Result"):
            items = data["Result"][:limit]
            
            for item in items:
                title_id = item.get("TitleID")
                if title_id:
                    # Get pages with illustrations
                    pages = get_bhl_item_pages(title_id, scientific_name)
                    results.extend(pages[:3])  # Max 3 per publication
                    
                    if len(results) >= limit:
                        break
                    time.sleep(0.3)
        
        logger.info(f"  Found {len(results)} BHL illustrations")
        return results[:limit]
        
    except Exception as e:
        logger.error(f"  Error searching BHL: {e}")
        return []


def get_bhl_item_pages(title_id, scientific_name):
    """Get illustrated pages from a BHL title"""
    url = f"{BHL_API_BASE}?op=GetPageMetadata&titleid={title_id}&pages=t&names=t&format=json"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        illustrated_pages = []
        if data.get("Status") == "ok" and data.get("Result"):
            pages = data["Result"]
            
            for page in pages:
                # Only get illustrated pages
                if page.get("Illustrated") == "true":
                    page_id = page.get("PageID")
                    page_url = f"https://www.biodiversitylibrary.org/page/{page_id}"
                    image_url = f"https://www.biodiversitylibrary.org/pagethumb/{page_id},400"
                    
                    # Get publication info
                    pub_title = page.get("Volume", "")
                    year = page.get("Year", "")
                    
                    illustrated_pages.append({
                        "page_id": page_id,
                        "url": page_url,
                        "image_url": image_url,
                        "publication": pub_title[:200],
                        "year": year,
                        "page_number": page.get("PageNumbers", "")
                    })
        
        return illustrated_pages
        
    except Exception as e:
        logger.error(f"  Error getting BHL pages: {e}")
        return []


def save_to_database(conn, image_data, genus, species_epithet):
    """Save BHL image to database"""
    cursor = conn.cursor()
    
    try:
        # Check if exists
        cursor.execute("SELECT id FROM orchid_images WHERE image_url = %s", (image_data['image_url'],))
        if cursor.fetchone():
            logger.info(f"    ⏭️  Exists: Page {image_data['page_number']}")
            cursor.close()
            return False
        
        # Get or create taxonomy entry
        scientific_name = f"{genus} {species_epithet}"
        cursor.execute("""
            SELECT id FROM orchid_taxonomy 
            WHERE scientific_name = %s
            LIMIT 1
        """, (scientific_name,))
        
        taxonomy_row = cursor.fetchone()
        taxonomy_id = taxonomy_row[0] if taxonomy_row else None
        
        # Insert image with correct schema
        cursor.execute("""
            INSERT INTO orchid_images (
                image_url, image_source, taxonomy_id,
                observer_name, institution_code, 
                image_description, locality, 
                image_license
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            image_data['image_url'],
            'BHL Botanical Illustration',
            taxonomy_id,
            image_data['publication'][:200],
            'Biodiversity Heritage Library',
            f"{scientific_name} - Historical botanical plate",
            f"Page {image_data['page_number']} ({image_data['year']})",
            'Public Domain'
        ))
        
        conn.commit()
        logger.info(f"    ✅ {image_data['publication'][:45]}... ({image_data['year']})")
        cursor.close()
        return True
        
    except Exception as e:
        conn.rollback()
        logger.error(f"    ❌ Error: {e}")
        cursor.close()
        return False


def download_all():
    """Download BHL botanical plates for all species"""
    logger.info("=" * 70)
    logger.info("🌺 BHL BOTANICAL ILLUSTRATION DOWNLOADER")
    logger.info("=" * 70)
    logger.info("Source: Biodiversity Heritage Library (BHL)")
    logger.info("License: Public Domain historical botanical plates")
    logger.info("=" * 70)
    
    species_list = get_bloombuilder_species()
    logger.info(f"\n📋 Found {len(species_list)} BloomBuilder species\n")
    
    conn = psycopg2.connect(DATABASE_URL)
    total_saved = 0
    
    for species in species_list:
        scientific_name = f"{species['genus']} {species['species']}"
        logger.info(f"{'─' * 70}")
        logger.info(f"🔍 {scientific_name}")
        logger.info(f"{'─' * 70}")
        
        # Search BHL
        illustrations = search_bhl_for_species(scientific_name, limit=10)
        
        for img in illustrations:
            if save_to_database(conn, img, species['genus'], species['species']):
                total_saved += 1
            time.sleep(0.3)
        
        time.sleep(1)
    
    conn.close()
    
    logger.info(f"\n{'=' * 70}")
    logger.info(f"✅ DOWNLOAD COMPLETE!")
    logger.info(f"{'=' * 70}")
    logger.info(f"🎨 BHL Botanical Illustrations: {total_saved} new images")
    logger.info(f"{'=' * 70}")
    
    # Summary
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT image_source, COUNT(*) 
        FROM orchid_images 
        GROUP BY image_source 
        ORDER BY COUNT(*) DESC
    """)
    
    logger.info("\n📊 DATABASE SUMMARY:")
    for row in cursor.fetchall():
        logger.info(f"  {row[0]}: {row[1]} images")
    
    cursor.close()
    conn.close()


if __name__ == "__main__":
    download_all()
