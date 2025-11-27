#!/usr/bin/env python3
"""
ECUAGENERA COMPREHENSIVE SCRAPER
Comprehensive scraper for collecting real orchid data and images from Ecuagenera.com
Targets three genera: Cattleya, Zygopetalum, and Sarcochilus
Uses O(1) taxonomy lookup via taxonomy_mapper for database integration

Features:
- Modular design avoiding Flask/database dependencies
- Comprehensive data extraction for species names, descriptions, images
- Intelligent image downloading with organization
- JSON export compatible with existing system
- Progress tracking and error handling
- Rate limiting and polite scraping
- O(1) taxonomy matching for database integration
"""

import requests
import time
import logging
import json
import os
import re
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from dataclasses import dataclass, asdict, field

from taxonomy_mapper import attach_record_to_taxonomy, lookup_taxon, batch_lookup_taxa

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class OrchidData:
    genus: str = ""
    species_name: str = ""
    hybrid_name: str = ""
    common_name: str = ""
    description: str = ""
    image_urls: List[str] = field(default_factory=list)
    image_files: List[str] = field(default_factory=list)
    price: str = ""
    availability: str = ""
    growing_info: str = ""
    botanical_features: List[str] = field(default_factory=list)
    flower_size: str = ""
    flowering_season: str = ""
    fragrance: str = ""
    origin: str = ""
    source: str = "Ecuagenera"
    source_url: str = ""
    scrape_date: str = ""
    
    def __post_init__(self):
        if not self.scrape_date:
            self.scrape_date = datetime.now().isoformat()


@dataclass
class ScrapingStats:
    genus: str = ""
    total_found: int = 0
    processed: int = 0
    images_downloaded: int = 0
    errors: int = 0
    start_time: Optional[datetime] = None
    
    def __post_init__(self):
        if self.start_time is None:
            self.start_time = datetime.now()
    
    @property
    def elapsed_time(self) -> float:
        if self.start_time is None:
            return 0.0
        return (datetime.now() - self.start_time).total_seconds()


class EcuaGeneraComprehensiveScraper:
    
    def __init__(self, 
                 base_url: str = "https://ecuagenera.com",
                 image_folder: str = "ecuagenera_images",
                 data_folder: str = "ecuagenera_data",
                 request_delay: float = 2.0,
                 max_retries: int = 3,
                 max_items_per_genus: int = 50):
        self.base_url = base_url
        self.image_folder = image_folder
        self.data_folder = data_folder
        self.request_delay = request_delay
        self.max_retries = max_retries
        self.max_items_per_genus = max_items_per_genus
        
        os.makedirs(self.image_folder, exist_ok=True)
        os.makedirs(self.data_folder, exist_ok=True)
        
        self.target_genera = ['cattleya', 'zygopetalum', 'sarcochilus']
        for genus in self.target_genera:
            os.makedirs(os.path.join(self.image_folder, genus), exist_ok=True)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none'
        })
        
        self.stats: Dict[str, ScrapingStats] = {}
        for genus in self.target_genera:
            self.stats[genus] = ScrapingStats(genus=genus)
        
        logger.info(f"Ecuagenera Comprehensive Scraper initialized with O(1) taxonomy lookup")
        logger.info(f"Images: {self.image_folder}, Data: {self.data_folder}")
        logger.info(f"Target: {self.max_items_per_genus} items per genus")

    def scrape_all_genera(self) -> Dict[str, List[Dict]]:
        logger.info("Starting comprehensive Ecuagenera scraping")
        logger.info("Target genera: Cattleya, Zygopetalum, Sarcochilus")
        
        results: Dict[str, List[Dict]] = {}
        
        for genus in self.target_genera:
            logger.info(f"\n{'='*60}")
            logger.info(f"Starting {genus.title()} collection")
            logger.info(f"{'='*60}")
            
            genus_data = self.scrape_genus(genus)
            results[genus] = genus_data
            
            self.save_genus_data(genus, genus_data)
            
            stats = self.stats[genus]
            logger.info(f"{genus.title()} complete: {len(genus_data)} items in {stats.elapsed_time:.1f}s")
            
            time.sleep(5)
        
        self.generate_summary_report(results)
        
        return results

    def scrape_genus(self, genus: str) -> List[Dict]:
        collection_url = f"{self.base_url}/collections/{genus}"
        
        logger.info(f"Scraping {genus} from: {collection_url}")
        
        genus_data: List[Dict] = []
        page = 1
        
        while len(genus_data) < self.max_items_per_genus:
            page_url = f"{collection_url}?page={page}" if page > 1 else collection_url
            
            logger.info(f"Processing page {page} for {genus}")
            
            try:
                response = self.session.get(page_url, timeout=30)
                
                if response.status_code != 200:
                    logger.warning(f"Failed to access page {page}: {response.status_code}")
                    break
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                products = self.extract_products_from_page(soup, genus, page_url)
                
                if not products:
                    logger.info(f"No more products found on page {page}")
                    break
                
                for product in products:
                    if len(genus_data) >= self.max_items_per_genus:
                        break
                    
                    orchid_data = self.process_product(product, genus)
                    if orchid_data:
                        genus_data.append(asdict(orchid_data))
                        self.stats[genus].processed += 1
                        
                        logger.info(f"{genus.title()} #{len(genus_data)}: {orchid_data.species_name or orchid_data.hybrid_name}")
                
                page += 1
                time.sleep(self.request_delay)
                
            except Exception as e:
                logger.error(f"Error processing page {page} for {genus}: {str(e)}")
                self.stats[genus].errors += 1
                break
        
        logger.info(f"{genus.title()} collection complete: {len(genus_data)} items")
        return genus_data

    def extract_products_from_page(self, soup: BeautifulSoup, genus: str, page_url: str) -> List[Any]:
        products: List[Any] = []
        
        selectors = [
            '.product-item',
            '.grid-product__content',
            '.product-card', 
            '.collection-product',
            '[data-product-id]',
            '.product',
            '[class*="product"]'
        ]
        
        for selector in selectors:
            found_products = soup.select(selector)
            if found_products:
                products.extend(found_products)
                logger.info(f"Found {len(found_products)} products using selector: {selector}")
                break
        
        if not products:
            product_links = soup.find_all('a', href=re.compile(r'/products/'))
            products = [link.parent for link in product_links if link.parent]
            logger.info(f"Fallback: Found {len(products)} product containers from links")
        
        return products

    def process_product(self, product_element: Any, genus: str) -> Optional[OrchidData]:
        try:
            orchid = OrchidData()
            orchid.genus = genus.title()
            
            name_selectors = [
                '.product-item__title',
                '.grid-product__title',
                '.product__title',
                '.product-title',
                'h2', 'h3', '.title',
                '[class*="title"]'
            ]
            
            name = self.extract_text_by_selectors(product_element, name_selectors)
            if name:
                orchid.species_name, orchid.hybrid_name = self.parse_orchid_name(name, genus)
                orchid.common_name = name
            
            desc_selectors = [
                '.product-item__description',
                '.grid-product__meta',
                '.product__description',
                '.description',
                'p'
            ]
            
            orchid.description = self.extract_text_by_selectors(product_element, desc_selectors)
            
            price_selectors = [
                '.price',
                '.product-item__price',
                '.grid-product__price',
                '[class*="price"]'
            ]
            
            orchid.price = self.extract_text_by_selectors(product_element, price_selectors)
            
            link_element = product_element.find('a', href=True)
            if link_element:
                product_url = urljoin(self.base_url, link_element['href'])
                orchid.source_url = product_url
                
                self.extract_detailed_info(orchid, product_url)
            
            self.extract_product_images(product_element, orchid, genus)
            
            orchid.botanical_features = self.extract_botanical_features(orchid.description)
            
            return orchid
            
        except Exception as e:
            logger.error(f"Error processing product: {str(e)}")
            return None

    def extract_text_by_selectors(self, element: Any, selectors: List[str]) -> str:
        for selector in selectors:
            found = element.select_one(selector)
            if found:
                return found.get_text(strip=True)
        return ""

    def parse_orchid_name(self, name: str, genus: str) -> Tuple[str, str]:
        name = name.strip()
        
        if '×' in name or '(' in name:
            return "", name
        
        if name.lower().startswith(genus.lower()):
            return name, ""
        
        return f"{genus.title()} {name}", ""

    def extract_detailed_info(self, orchid: OrchidData, product_url: str):
        try:
            time.sleep(1)
            response = self.session.get(product_url, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                detail_selectors = [
                    '.product-single__description',
                    '.product__description',
                    '.product-description',
                    '[class*="description"]'
                ]
                
                detailed_desc = self.extract_text_by_selectors(soup, detail_selectors)
                if detailed_desc and len(detailed_desc) > len(orchid.description):
                    orchid.description = detailed_desc
                
                growing_keywords = ['care', 'growing', 'cultivation', 'temperature', 'humidity', 'light']
                for keyword in growing_keywords:
                    elements = soup.find_all(string=re.compile(keyword, re.I))
                    if elements:
                        for elem in elements[:2]:
                            parent = elem.parent
                            if parent:
                                text = parent.get_text(strip=True)
                                if len(text) > 50:
                                    orchid.growing_info += text + " "
                
                self.extract_additional_metadata(soup, orchid)
                
        except Exception as e:
            logger.warning(f"Could not extract detailed info from {product_url}: {str(e)}")

    def extract_additional_metadata(self, soup: BeautifulSoup, orchid: OrchidData):
        try:
            spec_sections = soup.find_all(['div', 'section'], class_=re.compile(r'spec|detail|info', re.I))
            
            for section in spec_sections:
                text = section.get_text(strip=True).lower()
                
                size_match = re.search(r'(\d+\.?\d*)\s*(cm|inch|in)', text)
                if size_match and not orchid.flower_size:
                    orchid.flower_size = size_match.group(0)
                
                season_keywords = ['spring', 'summer', 'autumn', 'winter', 'fall']
                for season in season_keywords:
                    if season in text and not orchid.flowering_season:
                        orchid.flowering_season = season.title()
                        break
                
                if 'fragrant' in text or 'scent' in text:
                    orchid.fragrance = "Fragrant"
                
                country_keywords = ['ecuador', 'colombia', 'peru', 'brazil', 'costa rica']
                for country in country_keywords:
                    if country in text and not orchid.origin:
                        orchid.origin = country.title()
                        break
                        
        except Exception as e:
            logger.warning(f"Error extracting additional metadata: {str(e)}")

    def extract_product_images(self, product_element: Any, orchid: OrchidData, genus: str):
        try:
            img_elements = product_element.find_all('img')
            
            for img in img_elements:
                src = img.get('src') or img.get('data-src') or img.get('data-original')
                if not src:
                    continue
                
                if any(skip in src.lower() for skip in ['logo', 'icon', 'cart', 'star']):
                    continue
                
                image_url = urljoin(self.base_url, src)
                orchid.image_urls.append(image_url)
            
            for idx, image_url in enumerate(orchid.image_urls[:3]):
                filename = self.download_image(image_url, genus, orchid, idx)
                if filename:
                    orchid.image_files.append(filename)
                    self.stats[genus].images_downloaded += 1
                    
        except Exception as e:
            logger.warning(f"Error extracting images: {str(e)}")

    def download_image(self, image_url: str, genus: str, orchid: OrchidData, index: int) -> Optional[str]:
        try:
            base_name = (orchid.species_name or orchid.hybrid_name or orchid.common_name or "unknown").lower()
            base_name = re.sub(r'[^\w\s-]', '', base_name)
            base_name = re.sub(r'[-\s]+', '_', base_name)
            
            parsed_url = urlparse(image_url)
            ext = os.path.splitext(parsed_url.path)[1] or '.jpg'
            
            filename = f"{genus}_{base_name}_{index:02d}{ext}"
            filepath = os.path.join(self.image_folder, genus, filename)
            
            if os.path.exists(filepath):
                logger.info(f"Image exists: {filename}")
                return filename
            
            time.sleep(0.5)
            response = self.session.get(image_url, timeout=30)
            
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                logger.info(f"Downloaded: {filename} ({len(response.content)} bytes)")
                return filename
            else:
                logger.warning(f"Failed to download image: {response.status_code}")
                return None
                
        except Exception as e:
            logger.warning(f"Error downloading image from {image_url}: {str(e)}")
            return None

    def extract_botanical_features(self, description: str) -> List[str]:
        if not description:
            return []
        
        features = []
        text = description.lower()
        
        botanical_terms = {
            'sepals': ['sepal', 'sepals'],
            'petals': ['petal', 'petals'],
            'labellum': ['labellum', 'lip'],
            'column': ['column', 'gynostemium'],
            'pseudobulb': ['pseudobulb', 'pseudobulbs'],
            'inflorescence': ['inflorescence', 'spike', 'raceme'],
            'leaves': ['leaves', 'leaf', 'foliage'],
            'fragrance': ['fragrant', 'scented', 'perfumed', 'aromatic'],
            'texture': ['waxy', 'crystalline', 'velvety', 'glossy']
        }
        
        for feature, keywords in botanical_terms.items():
            if any(keyword in text for keyword in keywords):
                features.append(feature.title())
        
        return list(set(features))

    def save_to_database(self, genus_data: Dict[str, List[Dict]]) -> Dict[str, Dict[str, int]]:
        """
        Save scraped data to database using O(1) taxonomy_mapper.
        Uses attach_record_to_taxonomy for each orchid record.
        """
        all_results: Dict[str, Dict[str, int]] = {}
        
        for genus, orchids in genus_data.items():
            results = {'attached': 0, 'failed': 0, 'images_saved': 0}
            
            for orchid in orchids:
                scientific_name = orchid.get('species_name') or f"{genus.title()} {orchid.get('hybrid_name', '')}"
                
                record = {
                    'scientific_name': scientific_name,
                    'genus': orchid.get('genus', genus.title()),
                    'species': orchid.get('hybrid_name', ''),
                    'source': orchid.get('source', 'Ecuagenera'),
                    'description': orchid.get('description', ''),
                    'origin': orchid.get('origin', '')
                }
                
                for img_url in orchid.get('image_urls', []):
                    result = attach_record_to_taxonomy(record, img_url)
                    
                    if result.get('attached'):
                        results['attached'] += 1
                        results['images_saved'] += 1
                        logger.info(f"Attached {scientific_name} image to taxonomy_id {result['taxonomy_id']}")
                    else:
                        results['failed'] += 1
                        logger.warning(f"Failed to attach {scientific_name}: {result.get('reason')}")
            
            all_results[genus] = results
            logger.info(f"{genus.title()} database save: {results}")
        
        return all_results

    def save_genus_data(self, genus: str, data: List[Dict]):
        filename = f"ecuagenera_{genus}_data.json"
        filepath = os.path.join(self.data_folder, filename)
        
        export_data = {
            "metadata": {
                "genus": genus.title(),
                "total_items": len(data),
                "scrape_date": datetime.now().isoformat(),
                "source": "Ecuagenera.com",
                "scraper_version": "2.0 (O(1) taxonomy)",
                "stats": asdict(self.stats[genus])
            },
            "orchids": data
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(data)} {genus} records to {filename}")

    def generate_summary_report(self, results: Dict[str, List[Dict]]):
        report = {
            "scraping_summary": {
                "total_genera": len(results),
                "scrape_date": datetime.now().isoformat(),
                "scraper": "Ecuagenera Comprehensive Scraper v2.0 (O(1) taxonomy)"
            },
            "genera_stats": {},
            "totals": {
                "total_orchids": 0,
                "total_images": 0,
                "total_errors": 0
            }
        }
        
        for genus, data in results.items():
            stats = self.stats[genus]
            genus_stats = {
                "items_collected": len(data),
                "images_downloaded": stats.images_downloaded,
                "errors": stats.errors,
                "processing_time": stats.elapsed_time,
                "success_rate": (len(data) / max(1, len(data) + stats.errors)) * 100
            }
            
            report["genera_stats"][genus] = genus_stats
            report["totals"]["total_orchids"] += len(data)
            report["totals"]["total_images"] += stats.images_downloaded
            report["totals"]["total_errors"] += stats.errors
        
        report_path = os.path.join(self.data_folder, "ecuagenera_scraping_summary.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self.print_summary_report(report)
        
        logger.info(f"Summary report saved to: ecuagenera_scraping_summary.json")

    def print_summary_report(self, report: Dict):
        logger.info("\n" + "="*80)
        logger.info("ECUAGENERA SCRAPING SUMMARY REPORT")
        logger.info("="*80)
        logger.info(f"Date: {report['scraping_summary']['scrape_date']}")
        logger.info(f"Scraper: {report['scraping_summary']['scraper']}")
        logger.info("")
        
        for genus, stats in report['genera_stats'].items():
            logger.info(f"{genus.title()}:")
            logger.info(f"  Items: {stats['items_collected']}")
            logger.info(f"  Images: {stats['images_downloaded']}")
            logger.info(f"  Errors: {stats['errors']}")
            logger.info(f"  Success Rate: {stats['success_rate']:.1f}%")
            logger.info(f"  Time: {stats['processing_time']:.1f}s")
        
        logger.info("")
        logger.info("TOTALS:")
        logger.info(f"  Total Orchids: {report['totals']['total_orchids']}")
        logger.info(f"  Total Images: {report['totals']['total_images']}")
        logger.info(f"  Total Errors: {report['totals']['total_errors']}")
        logger.info("="*80)


def main():
    scraper = EcuaGeneraComprehensiveScraper(
        max_items_per_genus=50,
        request_delay=2.0
    )
    
    results = scraper.scrape_all_genera()
    
    total_orchids = sum(len(data) for data in results.values())
    logger.info(f"\nScraping complete! Total orchids collected: {total_orchids}")


if __name__ == "__main__":
    main()
