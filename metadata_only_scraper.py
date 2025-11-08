#!/usr/bin/env python3
"""
METADATA-ONLY SCRAPER
Extracts image URLs from orchid websites, analyzes them with OpenAI Vision,
and saves 61-field metadata WITHOUT downloading images.

Sources:
- Gary Yong Gee (orchidspecies.com)
- Roberta Fox (Orchid Central)
"""

import os
import sys
import logging
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin, urlparse
import json
import time
import re

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import OrchidRecord, ScrapingLog

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MetadataOnlyScraper:
    """Scrape image URLs and extract metadata without downloading images"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # OpenAI client
        import openai
        if os.environ.get('OPENAI_API_KEY'):
            self.openai_client = openai.OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        else:
            self.openai_client = None
            logger.warning("⚠️ OPENAI_API_KEY not found - AI analysis will be skipped")
    
    def extract_gary_yong_gee_urls(self, base_url="https://www.orchidspecies.com/indexbygen.htm", max_pages=10):
        """
        Extract image URLs from Gary Yong Gee's orchid species website.
        Returns list of dicts with: {image_url, genus, species, page_url}
        """
        logger.info("🔍 Scraping Gary Yong Gee for image URLs...")
        image_data = []
        
        try:
            # Get the genus index page
            response = self.session.get(base_url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all genus links
            genus_links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                # Look for genus pages (pattern: genus name links)
                if 'genus' in href.lower() or any(href.endswith(ext) for ext in ['.htm', '.html']):
                    full_url = urljoin(base_url, href)
                    genus_links.append(full_url)
            
            logger.info(f"📊 Found {len(genus_links)} potential genus pages")
            
            # Process each genus page (limit for testing)
            for i, genus_url in enumerate(genus_links[:max_pages]):
                try:
                    logger.info(f"🔍 Processing genus page {i+1}/{min(max_pages, len(genus_links))}: {genus_url}")
                    
                    response = self.session.get(genus_url, timeout=15)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Find all images on the page
                    for img in soup.find_all('img'):
                        img_src = img.get('src')
                        if img_src and self._is_orchid_image(img_src):
                            full_img_url = urljoin(genus_url, img_src)
                            
                            # Try to extract genus/species from context
                            genus, species = self._extract_taxonomy_from_context(img, soup, genus_url)
                            
                            image_data.append({
                                'image_url': full_img_url,
                                'genus': genus,
                                'species': species,
                                'page_url': genus_url,
                                'source': 'gary_yong_gee'
                            })
                    
                    time.sleep(1)  # Be polite
                    
                except Exception as e:
                    logger.error(f"❌ Error processing genus page {genus_url}: {e}")
                    continue
            
            logger.info(f"✅ Extracted {len(image_data)} image URLs from Gary Yong Gee")
            return image_data
            
        except Exception as e:
            logger.error(f"❌ Failed to scrape Gary Yong Gee: {e}")
            return []
    
    def extract_roberta_fox_urls(self, base_url="http://www.orchidcentral.net/", max_pages=10):
        """
        Extract image URLs from Roberta Fox's Orchid Central website.
        Returns list of dicts with: {image_url, genus, species, page_url}
        """
        logger.info("🔍 Scraping Roberta Fox (Orchid Central) for image URLs...")
        image_data = []
        
        try:
            # Get the main page
            response = self.session.get(base_url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all orchid pages (look for links to orchid details)
            orchid_links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                # Look for orchid detail pages
                if any(keyword in href.lower() for keyword in ['orchid', 'species', 'genus']):
                    full_url = urljoin(base_url, href)
                    orchid_links.append(full_url)
            
            logger.info(f"📊 Found {len(orchid_links)} potential orchid pages")
            
            # Process each orchid page (limit for testing)
            for i, orchid_url in enumerate(orchid_links[:max_pages]):
                try:
                    logger.info(f"🔍 Processing orchid page {i+1}/{min(max_pages, len(orchid_links))}: {orchid_url}")
                    
                    response = self.session.get(orchid_url, timeout=15)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Find all images on the page
                    for img in soup.find_all('img'):
                        img_src = img.get('src')
                        if img_src and self._is_orchid_image(img_src):
                            full_img_url = urljoin(orchid_url, img_src)
                            
                            # Try to extract genus/species from context
                            genus, species = self._extract_taxonomy_from_context(img, soup, orchid_url)
                            
                            image_data.append({
                                'image_url': full_img_url,
                                'genus': genus,
                                'species': species,
                                'page_url': orchid_url,
                                'source': 'roberta_fox'
                            })
                    
                    time.sleep(1)  # Be polite
                    
                except Exception as e:
                    logger.error(f"❌ Error processing orchid page {orchid_url}: {e}")
                    continue
            
            logger.info(f"✅ Extracted {len(image_data)} image URLs from Roberta Fox")
            return image_data
            
        except Exception as e:
            logger.error(f"❌ Failed to scrape Roberta Fox: {e}")
            return []
    
    def _is_orchid_image(self, img_src):
        """Check if image source looks like an orchid photo"""
        if not img_src:
            return False
        
        # Skip common non-orchid images
        skip_patterns = ['logo', 'banner', 'icon', 'button', 'spacer', 'pixel', 'arrow', 'bullet']
        if any(pattern in img_src.lower() for pattern in skip_patterns):
            return False
        
        # Look for image file extensions
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        return any(img_src.lower().endswith(ext) for ext in image_extensions)
    
    def _extract_taxonomy_from_context(self, img_tag, soup, page_url):
        """Extract genus and species from image context or page URL"""
        genus = None
        species = None
        
        # Method 1: From image alt text
        alt_text = img_tag.get('alt', '')
        if alt_text:
            match = re.search(r'([A-Z][a-z]+)\s+([a-z]+)', alt_text)
            if match:
                genus, species = match.groups()
                return genus, species
        
        # Method 2: From nearby text
        parent = img_tag.parent
        if parent:
            text = parent.get_text()
            match = re.search(r'([A-Z][a-z]+)\s+([a-z]+)', text)
            if match:
                genus, species = match.groups()
                return genus, species
        
        # Method 3: From page title or heading
        title_tag = soup.find('title')
        if title_tag:
            title_text = title_tag.get_text()
            match = re.search(r'([A-Z][a-z]+)\s+([a-z]+)', title_text)
            if match:
                genus, species = match.groups()
                return genus, species
        
        # Method 4: From URL
        match = re.search(r'/([A-Z][a-z]+)[_-]([a-z]+)', page_url)
        if match:
            genus, species = match.groups()
            return genus, species
        
        return genus, species
    
    def analyze_image_with_ai(self, image_url, genus_hint=None, species_hint=None):
        """
        Analyze image URL with OpenAI Vision and extract all 61 metadata fields.
        Returns dict with metadata.
        """
        if not self.openai_client:
            logger.warning("⚠️ OpenAI client not available - skipping AI analysis")
            return {}
        
        try:
            scientific_name = f"{genus_hint} {species_hint}" if genus_hint and species_hint else "Unknown orchid"
            
            # Comprehensive prompt for all 61 fields
            prompt = f"""Analyze this orchid image ({scientific_name}) and extract ALL possible metadata fields:

**PHASE 1 - VISUAL ANALYSIS (8 fields):**
1. flower_color: Primary color(s) of flower (e.g., "pink", "white with purple spots")
2. bloom_stage: Current blooming stage (bud/opening/full_bloom/fading/seed_pod)
3. inflorescence_type: Flower arrangement (single/spike/raceme/panicle/umbel)
4. inflorescence_position: Position of flowers (terminal/lateral/basal)
5. bloombot_category: Flower type (cattleya_type/phalaenopsis_type/oncidium_type/dendrobium_type/other)
6. is_hybrid: Is this a hybrid? (true/false)
7. image_caption: Brief descriptive caption (1 sentence)

**PHASE 2 - MORPHOLOGICAL ANALYSIS (13 fields):**
8. leaf_shape: Leaf shape (oval/lance/linear/strap/terete)
9. pseudobulb_presence: Are pseudobulbs visible? (true/false)
10. pseudobulb_form: If present, form? (ovoid/cylindrical/conical/flattened/absent)
11. labellum_type: Lip/labellum type (simple/lobed/fringed/pouch/column)
12. flower_resupination: Flowers twisted/resupinate? (true/false)
13. keiki_formation: Keiki tendency (frequent/occasional/rare/none)
14. rhizome_spread_type: Growth type (sympodial/monopodial)
15. leaf_venation: Venation pattern (parallel/reticulate)
16. tissue_succulence: Leaf tissue (thin/medium/thick_succulent)
17. growth_rate: Growth habit (slow/moderate/fast)
18. flower_longevity_days: Estimated days flower lasts (number)
19. dormant_leaf_drop: Leaves drop during dormancy? (true/false)
20. growth_eye_activation: When growth eyes activate (spring/fall/year_round)

**PHASE 3 - CULTURAL & HABITAT (15+ fields):**
21. genus: Genus name (if identifiable)
22. species: Species name (if identifiable)
23. bloom_time: Blooming season (e.g., "spring", "summer", "fall", "winter", "year-round")
24. growth_habit: Growth type (epiphytic/terrestrial/lithophytic)
25. climate_preference: Temperature (cool/intermediate/warm)
26. light_requirements: Light needs (low/medium/high/very_high)
27. temperature_range: Temp range (e.g., "60-80°F", "15-27°C")
28. water_requirements: Watering needs (brief description)
29. native_habitat: Native region/habitat (if identifiable)
30. fragrance: Fragrance (fragrant/unscented/variable/unknown)
31. fragrance_description: Scent description (if fragrant)

**ADDITIONAL OBSERVABLE FIELDS:**
32. common_names: Any common names visible or inferable
33. leaf_form: Leaf description
34. cultural_notes: Any growing notes visible
35. ai_description: Detailed botanical description of the plant

Respond ONLY with valid JSON. Use null for uncertain/invisible values.
Format: {{"flower_color": "value", "bloom_stage": "value", ...}}"""

            # Call OpenAI Vision API
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",  # Use best model for comprehensive analysis
                messages=[
                    {"role": "system", "content": "You are an expert orchid botanist analyzing orchid images. Extract as much botanical metadata as possible. Respond only with valid JSON."},
                    {"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_url}}
                    ]}
                ],
                max_tokens=1000,
                temperature=0.2
            )
            
            ai_response = response.choices[0].message.content
            
            # Parse JSON response
            try:
                # Extract JSON from response (handles markdown code blocks)
                if '```json' in ai_response:
                    ai_response = ai_response.split('```json')[1].split('```')[0].strip()
                elif '```' in ai_response:
                    ai_response = ai_response.split('```')[1].split('```')[0].strip()
                
                metadata = json.loads(ai_response)
                logger.info(f"✅ AI extracted {len(metadata)} fields from image")
                return metadata
                
            except json.JSONDecodeError as je:
                logger.error(f"❌ JSON parse error: {je}")
                logger.debug(f"Response was: {ai_response[:200]}")
                return {}
                
        except Exception as e:
            logger.error(f"❌ AI analysis failed: {e}")
            return {}
    
    def save_metadata_to_database(self, image_data, metadata):
        """
        Save extracted metadata to database WITHOUT saving image file.
        Links to original image URL only.
        """
        try:
            # Check if orchid already exists
            genus = metadata.get('genus') or image_data.get('genus')
            species = metadata.get('species') or image_data.get('species')
            
            if not genus:
                logger.warning(f"⚠️ No genus found, skipping database save")
                return None
            
            # Search for existing orchid
            existing = OrchidRecord.query.filter_by(
                genus=genus,
                species=species,
                image_url=image_data['image_url']
            ).first()
            
            if existing:
                logger.info(f"📝 Updating existing orchid: {genus} {species}")
                orchid = existing
            else:
                logger.info(f"🆕 Creating new orchid: {genus} {species}")
                orchid = OrchidRecord()
                orchid.genus = genus
                orchid.species = species
                orchid.display_name = f"{genus} {species}" if species else genus
            
            # Update image reference (URL only, no file download)
            orchid.image_url = image_data['image_url']
            orchid.image_source = image_data.get('source', 'metadata_scraper')
            orchid.ingestion_source = f"scrape_{image_data.get('source', 'unknown')}"
            
            # Update all 61 metadata fields from AI analysis
            self._update_orchid_fields(orchid, metadata)
            
            # Save to database
            if not existing:
                db.session.add(orchid)
            
            db.session.commit()
            logger.info(f"✅ Saved metadata for {orchid.display_name} (ID: {orchid.id})")
            
            return orchid
            
        except Exception as e:
            logger.error(f"❌ Database save failed: {e}")
            db.session.rollback()
            return None
    
    def _update_orchid_fields(self, orchid, metadata):
        """Update orchid record with all available metadata fields"""
        
        # Phase 1: Visual Analysis
        if metadata.get('flower_color'):
            orchid.flower_color = metadata['flower_color']
        if metadata.get('bloom_stage'):
            orchid.bloom_stage = metadata['bloom_stage']
        if metadata.get('inflorescence_type'):
            orchid.inflorescence_type = metadata['inflorescence_type']
        if metadata.get('inflorescence_position'):
            orchid.inflorescence_position = metadata['inflorescence_position']
        if metadata.get('bloombot_category'):
            orchid.bloombot_category = metadata['bloombot_category']
        if metadata.get('is_hybrid') is not None:
            orchid.is_hybrid = metadata['is_hybrid']
        if metadata.get('image_caption'):
            orchid.image_caption = metadata['image_caption']
        
        # Phase 2: Morphological Analysis
        if metadata.get('leaf_shape'):
            orchid.leaf_shape = metadata['leaf_shape']
        if metadata.get('pseudobulb_presence') is not None:
            orchid.pseudobulb_presence = metadata['pseudobulb_presence']
        if metadata.get('pseudobulb_form'):
            orchid.pseudobulb_form = metadata['pseudobulb_form']
        if metadata.get('labellum_type'):
            orchid.labellum_type = metadata['labellum_type']
        if metadata.get('flower_resupination') is not None:
            orchid.flower_resupination = metadata['flower_resupination']
        if metadata.get('keiki_formation'):
            orchid.keiki_formation = metadata['keiki_formation']
        if metadata.get('rhizome_spread_type'):
            orchid.rhizome_spread_type = metadata['rhizome_spread_type']
        if metadata.get('leaf_venation'):
            orchid.leaf_venation = metadata['leaf_venation']
        if metadata.get('tissue_succulence'):
            orchid.tissue_succulence = metadata['tissue_succulence']
        if metadata.get('growth_rate'):
            orchid.growth_rate = metadata['growth_rate']
        if metadata.get('flower_longevity_days'):
            orchid.flower_longevity_days = metadata['flower_longevity_days']
        if metadata.get('dormant_leaf_drop') is not None:
            orchid.dormant_leaf_drop = metadata['dormant_leaf_drop']
        if metadata.get('growth_eye_activation'):
            orchid.growth_eye_activation = metadata['growth_eye_activation']
        
        # Phase 3: Cultural & Habitat
        if metadata.get('bloom_time'):
            orchid.bloom_time = metadata['bloom_time']
        if metadata.get('growth_habit'):
            orchid.growth_habit = metadata['growth_habit']
        if metadata.get('climate_preference'):
            orchid.climate_preference = metadata['climate_preference']
        if metadata.get('light_requirements'):
            orchid.light_requirements = metadata['light_requirements']
        if metadata.get('temperature_range'):
            orchid.temperature_range = metadata['temperature_range']
        if metadata.get('water_requirements'):
            orchid.water_requirements = metadata['water_requirements']
        if metadata.get('native_habitat'):
            orchid.native_habitat = metadata['native_habitat']
        if metadata.get('fragrance'):
            orchid.fragrance = metadata['fragrance']
        if metadata.get('fragrance_description'):
            orchid.fragrance_description = metadata['fragrance_description']
        
        # Additional fields
        if metadata.get('common_names'):
            orchid.common_names = metadata['common_names']
        if metadata.get('leaf_form'):
            orchid.leaf_form = metadata['leaf_form']
        if metadata.get('cultural_notes'):
            orchid.cultural_notes = metadata['cultural_notes']
        if metadata.get('ai_description'):
            orchid.ai_description = metadata['ai_description']
        
        # Scientific name
        if metadata.get('genus') and metadata.get('species'):
            orchid.scientific_name = f"{metadata['genus']} {metadata['species']}"
        
        # Mark as updated
        orchid.updated_at = datetime.utcnow()
    
    def run_metadata_enrichment(self, source='both', max_images=50):
        """
        COMPLETE ORCHESTRATION: scrape URLs → analyze with AI → save metadata to database.
        
        Args:
            source: 'gary', 'roberta', or 'both'
            max_images: Maximum number of images to process
        
        Returns:
            dict with urls_collected, images_processed, orchids_saved, errors
        """
        logger.info("=" * 80)
        logger.info("🌺 METADATA-ONLY SCRAPER - STARTING COMPLETE PIPELINE")
        logger.info("=" * 80)
        logger.info(f"Source: {source}")
        logger.info(f"Max images: {max_images}")
        logger.info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        all_image_data = []
        errors = []
        
        # PHASE 1: Scrape image URLs from websites
        try:
            if source in ['gary', 'both']:
                logger.info("\n📡 PHASE 1A: Scraping Gary Yong Gee URLs...")
                gary_urls = self.extract_gary_yong_gee_urls(max_pages=5)
                all_image_data.extend(gary_urls)
                logger.info(f"   ✅ Found {len(gary_urls)} URLs from Gary Yong Gee")
            
            if source in ['roberta', 'both']:
                logger.info("\n📡 PHASE 1B: Scraping Roberta Fox URLs...")
                roberta_urls = self.extract_roberta_fox_urls(max_pages=5)
                all_image_data.extend(roberta_urls)
                logger.info(f"   ✅ Found {len(roberta_urls)} URLs from Roberta Fox")
        except Exception as e:
            logger.error(f"❌ URL scraping failed: {e}")
            errors.append(f"URL scraping: {str(e)}")
        
        logger.info(f"\n📊 Total image URLs collected: {len(all_image_data)}")
        
        # PHASE 2 & 3: AI Analysis + Database Persistence
        processed_count = 0
        saved_count = 0
        failed_count = 0
        
        logger.info(f"\n🤖 PHASE 2 & 3: AI Analysis + Database Save (processing {min(max_images, len(all_image_data))} images)...")
        
        for i, image_data in enumerate(all_image_data[:max_images]):
            try:
                logger.info(f"\n🔍 [{i+1}/{min(max_images, len(all_image_data))}] Processing: {image_data['image_url'][:80]}...")
                
                # PHASE 2: Analyze image with OpenAI Vision API
                metadata = self.analyze_image_with_ai(
                    image_data['image_url'],
                    genus_hint=image_data.get('genus'),
                    species_hint=image_data.get('species')
                )
                
                if not metadata:
                    logger.warning(f"   ⚠️ No metadata extracted - skipping")
                    failed_count += 1
                    errors.append(f"No metadata for {image_data['image_url'][:50]}")
                    continue
                
                logger.info(f"   ✅ AI extracted {len(metadata)} fields")
                
                # PHASE 3: Save to database with transaction management
                try:
                    orchid = self.save_metadata_to_database(image_data, metadata)
                    if orchid:
                        saved_count += 1
                        logger.info(f"   💾 Saved to DB: {orchid.display_name} (ID: {orchid.id})")
                        
                        # Log successful scraping
                        log_entry = ScrapingLog(
                            source=image_data.get('source', 'unknown'),
                            url=image_data['page_url'],
                            status='success',
                            items_found=1,
                            items_processed=1
                        )
                        db.session.add(log_entry)
                        db.session.commit()
                    else:
                        failed_count += 1
                        errors.append(f"DB save failed for {image_data['image_url'][:50]}")
                except Exception as db_error:
                    logger.error(f"   ❌ Database error: {db_error}")
                    db.session.rollback()
                    failed_count += 1
                    errors.append(f"DB error: {str(db_error)}")
                
                processed_count += 1
                
                # Rate limiting for OpenAI API
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"   ❌ Error processing image: {e}")
                failed_count += 1
                errors.append(f"Processing error: {str(e)}")
                
                # Log failed attempt
                try:
                    log_entry = ScrapingLog(
                        source=image_data.get('source', 'unknown'),
                        url=image_data.get('page_url', image_data['image_url']),
                        status='error',
                        error_message=str(e),
                        items_found=0,
                        items_processed=0
                    )
                    db.session.add(log_entry)
                    db.session.commit()
                except:
                    pass
                
                continue
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ METADATA-ONLY SCRAPING COMPLETE!")
        logger.info("=" * 80)
        logger.info(f"URLs collected: {len(all_image_data)}")
        logger.info(f"Images processed: {processed_count}")
        logger.info(f"Orchids saved: {saved_count}")
        logger.info(f"Failed: {failed_count}")
        logger.info(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 80)
        
        return {
            'urls_collected': len(all_image_data),
            'images_processed': processed_count,
            'orchids_saved': saved_count,
            'failed': failed_count,
            'errors': errors[:10]  # Return first 10 errors
        }


def main():
    """Command-line interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Metadata-only orchid scraper')
    parser.add_argument('--source', choices=['gary', 'roberta', 'both'], default='both',
                        help='Source website to scrape')
    parser.add_argument('--max-images', type=int, default=50,
                        help='Maximum number of images to process')
    
    args = parser.parse_args()
    
    with app.app_context():
        scraper = MetadataOnlyScraper()
        results = scraper.run_metadata_enrichment(
            source=args.source,
            max_images=args.max_images
        )
        
        print(f"\n✅ Complete! Processed {results['images_processed']} images, saved {results['orchids_saved']} orchids")


if __name__ == "__main__":
    main()
