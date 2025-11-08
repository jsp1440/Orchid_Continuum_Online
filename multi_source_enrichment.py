#!/usr/bin/env python3
"""
Multi-source orchid enrichment: POWO → Andy's → Ecuagenera → IOSPE
"""
import os
import time
import logging
import requests
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

DATABASE_URL = os.environ.get('DATABASE_URL')
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

class MultiSourceEnricher:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0 (Research Bot)'})
        self.stats = {'powo': 0, 'andys': 0, 'ecuagenera': 0, 'iospe': 0, 'failed': 0}
    
    def check_powo(self, genus, species):
        """Check Plants of the World Online"""
        try:
            # POWO API endpoint
            url = f"https://powo.science.kew.org/api/1/search"
            params = {'q': f"{genus} {species}", 'f': 'species'}
            
            response = self.session.get(url, params=params, timeout=10)
            time.sleep(1)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('results'):
                    result = data['results'][0]
                    return {
                        'source': 'POWO',
                        'name': result.get('name'),
                        'author': result.get('author'),
                        'family': result.get('family'),
                        'distribution': result.get('distribution')
                    }
        except Exception as e:
            logger.debug(f"POWO error: {e}")
        return None
    
    def check_andys_orchids(self, genus, species):
        """Check Andy's Orchids catalog"""
        try:
            # Andy's Orchids search
            search_term = f"{genus}+{species}".replace(' ', '+')
            url = f"https://andysorchids.com/search?q={search_term}"
            
            response = self.session.get(url, timeout=10)
            time.sleep(1)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for product listings
                products = soup.find_all('div', class_='product-item')
                if products:
                    product = products[0]
                    img = product.find('img')
                    
                    if img and img.get('src'):
                        return {
                            'source': "Andy's Orchids",
                            'image_url': img['src'],
                            'product_url': url
                        }
        except Exception as e:
            logger.debug(f"Andy's error: {e}")
        return None
    
    def check_ecuagenera(self, genus, species):
        """Check Ecuagenera catalog"""
        try:
            search_term = f"{genus} {species}"
            url = f"https://www.ecuagenera.com/search?q={search_term}"
            
            response = self.session.get(url, timeout=10)
            time.sleep(1)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for product images
                products = soup.find_all('div', class_='product')
                if products:
                    product = products[0]
                    img = product.find('img')
                    
                    if img and img.get('src'):
                        return {
                            'source': 'Ecuagenera',
                            'image_url': img['src'],
                            'product_url': url
                        }
        except Exception as e:
            logger.debug(f"Ecuagenera error: {e}")
        return None
    
    def check_iospe(self, genus, species):
        """Check Internet Orchid Species Photo Encyclopedia"""
        try:
            # IOSPE format: genus/species pages
            genus_lower = genus.lower()
            species_lower = species.lower()
            url = f"http://www.orchidspecies.com/{genus_lower}/{genus_lower}_{species_lower}.htm"
            
            response = self.session.get(url, timeout=10)
            time.sleep(1)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for images
                imgs = soup.find_all('img')
                for img in imgs:
                    src = img.get('src', '')
                    if genus_lower in src.lower() or species_lower in src.lower():
                        full_url = f"http://www.orchidspecies.com/{genus_lower}/{src}"
                        return {
                            'source': 'IOSPE',
                            'image_url': full_url,
                            'page_url': url
                        }
        except Exception as e:
            logger.debug(f"IOSPE error: {e}")
        return None
    
    def enrich_orchid(self, orchid_id, genus, species, scientific_name, db_session):
        """Try all sources in order"""
        logger.info(f"[{orchid_id}] {scientific_name}")
        
        # Try POWO first (authoritative taxonomy)
        data = self.check_powo(genus, species)
        if data:
            self.stats['powo'] += 1
            logger.info(f"  ✅ POWO: {data.get('family', 'Found')}")
            db_session.execute(
                text("UPDATE orchid_record SET data_source = :source WHERE id = :id"),
                {'id': orchid_id, 'source': 'POWO'}
            )
            db_session.commit()
            return True
        
        # Try Andy's Orchids (images + availability)
        data = self.check_andys_orchids(genus, species)
        if data:
            self.stats['andys'] += 1
            logger.info(f"  ✅ Andy's Orchids: Image found")
            db_session.execute(
                text("""UPDATE orchid_record 
                       SET image_url = :url, image_source = :source 
                       WHERE id = :id AND image_url IS NULL"""),
                {'id': orchid_id, 'url': data['image_url'], 'source': "Andy's Orchids"}
            )
            db_session.commit()
            return True
        
        # Try Ecuagenera
        data = self.check_ecuagenera(genus, species)
        if data:
            self.stats['ecuagenera'] += 1
            logger.info(f"  ✅ Ecuagenera: Image found")
            db_session.execute(
                text("""UPDATE orchid_record 
                       SET image_url = :url, image_source = :source 
                       WHERE id = :id AND image_url IS NULL"""),
                {'id': orchid_id, 'url': data['image_url'], 'source': 'Ecuagenera'}
            )
            db_session.commit()
            return True
        
        # Try IOSPE
        data = self.check_iospe(genus, species)
        if data:
            self.stats['iospe'] += 1
            logger.info(f"  ✅ IOSPE: Image found")
            db_session.execute(
                text("""UPDATE orchid_record 
                       SET image_url = :url, image_source = :source 
                       WHERE id = :id AND image_url IS NULL"""),
                {'id': orchid_id, 'url': data['image_url'], 'source': 'IOSPE'}
            )
            db_session.commit()
            return True
        
        self.stats['failed'] += 1
        logger.info(f"  ❌ Not found in any source")
        return False
    
    def process_batch(self, limit=50):
        """Process batch of orchids without GBIF matches"""
        db_session = Session()
        try:
            result = db_session.execute(text("""
                SELECT id, genus, species, scientific_name
                FROM orchid_record
                WHERE gbif_species_key IS NULL
                  AND genus IS NOT NULL
                  AND species IS NOT NULL
                  AND LENGTH(species) > 2
                ORDER BY id
                LIMIT :limit
            """), {'limit': limit})
            
            orchids = result.fetchall()
            for orchid in orchids:
                self.enrich_orchid(orchid.id, orchid.genus, orchid.species, 
                                 orchid.scientific_name, db_session)
            
            return len(orchids)
        finally:
            db_session.close()
    
    def run(self):
        """Run multi-source enrichment"""
        logger.info("="*70)
        logger.info("🌍 MULTI-SOURCE ENRICHMENT")
        logger.info("Sources: POWO → Andy's → Ecuagenera → IOSPE")
        logger.info("="*70)
        
        batch_num = 0
        while batch_num < 10:  # Limit to 10 batches for now
            batch_num += 1
            logger.info(f"\nBatch {batch_num}:")
            processed = self.process_batch(50)
            
            if processed == 0:
                break
        
        # Summary
        logger.info("\n" + "="*70)
        logger.info("✅ ENRICHMENT SUMMARY")
        logger.info(f"POWO: {self.stats['powo']}")
        logger.info(f"Andy's Orchids: {self.stats['andys']}")
        logger.info(f"Ecuagenera: {self.stats['ecuagenera']}")
        logger.info(f"IOSPE: {self.stats['iospe']}")
        logger.info(f"Not found: {self.stats['failed']}")
        logger.info("="*70)

if __name__ == "__main__":
    enricher = MultiSourceEnricher()
    enricher.run()
