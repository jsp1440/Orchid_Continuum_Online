#!/usr/bin/env python3
"""
Wild Orchid Vision Analyzer
Directly analyzes images from Gary Yong Gee and Roberta Fox websites
WITHOUT downloading - uses AI Vision with direct URLs
"""

import os
import psycopg2
from openai import OpenAI
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
import re

DATABASE_URL = os.environ.get('DATABASE_URL')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

class WildOrchidCollector:
    """Collects and analyzes wild orchid images from partner websites"""
    
    def __init__(self):
        self.gary_base = "https://orchids.yonggee.name"
        self.roberta_base = "https://www.sfos.org/species-index-photo"
        self.collected_count = 0
        
    def scrape_gary_yong_gee_images(self):
        """Scrape image URLs from Gary Yong Gee's website"""
        log("🌺 Scraping Gary Yong Gee wild orchid images...")
        
        images_found = []
        
        try:
            # Try different genus pages
            genera = ['Cattleya', 'Dendrobium', 'Bulbophyllum', 'Pleurothallis', 'Epidendrum']
            
            for genus in genera:
                try:
                    url = f"{self.gary_base}/genus/{genus.lower()}"
                    response = requests.get(url, timeout=10)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Find all images
                        for img in soup.find_all('img'):
                            src = img.get('src')
                            if src and ('/images/' in src or '/photos/' in src or '/orchid' in src.lower()):
                                # Make absolute URL
                                if src.startswith('/'):
                                    full_url = f"{self.gary_base}{src}"
                                elif not src.startswith('http'):
                                    full_url = f"{self.gary_base}/{src}"
                                else:
                                    full_url = src
                                
                                # Get species name from context
                                species_name = self.extract_species_from_context(img, soup, genus)
                                
                                images_found.append({
                                    'url': full_url,
                                    'genus': genus,
                                    'species': species_name,
                                    'source': 'Gary Yong Gee',
                                    'photographer': 'Gary Yong Gee'
                                })
                                
                        log(f"  Found {len([i for i in images_found if i['genus'] == genus])} images for {genus}")
                        
                    time.sleep(1)
                    
                except Exception as e:
                    log(f"  Error with {genus}: {e}")
                    
        except Exception as e:
            log(f"Gary scraping error: {e}")
            
        return images_found
    
    def scrape_roberta_fox_images(self):
        """Scrape image URLs from Roberta Fox's SFOS photo index"""
        log("🌸 Scraping Roberta Fox wild orchid images...")
        
        images_found = []
        
        try:
            response = requests.get(self.roberta_base, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for orchid images with species names
                for img in soup.find_all('img'):
                    src = img.get('src')
                    alt = img.get('alt', '')
                    
                    if src and ('orchid' in alt.lower() or 'species' in src.lower()):
                        # Make absolute URL
                        if src.startswith('/'):
                            full_url = f"https://www.sfos.org{src}"
                        elif not src.startswith('http'):
                            full_url = f"https://www.sfos.org/{src}"
                        else:
                            full_url = src
                        
                        # Extract species from alt text or nearby text
                        genus, species = self.parse_species_name(alt)
                        
                        if genus:
                            images_found.append({
                                'url': full_url,
                                'genus': genus,
                                'species': species,
                                'source': 'Roberta Fox / SFOS',
                                'photographer': 'Roberta Fox'
                            })
                
                log(f"  Found {len(images_found)} Roberta Fox images")
                
        except Exception as e:
            log(f"Roberta Fox scraping error: {e}")
            
        return images_found
    
    def parse_species_name(self, text):
        """Extract genus and species from text"""
        if not text:
            return None, None
            
        # Look for pattern: Genus species
        match = re.search(r'([A-Z][a-z]+)\s+([a-z]+)', text)
        if match:
            return match.group(1), match.group(2)
            
        return None, None
    
    def extract_species_from_context(self, img_tag, soup, genus):
        """Extract species name from image context"""
        # Try alt text first
        alt = img_tag.get('alt', '')
        if alt:
            _, species = self.parse_species_name(alt)
            if species:
                return species
        
        # Try nearby text
        parent = img_tag.parent
        if parent:
            text = parent.get_text()
            _, species = self.parse_species_name(text)
            if species:
                return species
                
        return 'sp.'
    
    def analyze_image_with_vision(self, image_url):
        """Analyze orchid image using GPT-4 Vision"""
        if not client:
            return None
            
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """Analyze this WILD orchid photograph. Provide:
1. Flower colors, patterns, markings
2. Flower shape and structure (sepals, petals, lip)
3. Growth habitat visible (tree, rock, ground)
4. Unique identifying features
5. Estimated genus if possible

Focus on features useful for species identification. Keep concise, 3-4 sentences."""
                            },
                            {
                                "type": "image_url",
                                "image_url": {"url": image_url}
                            }
                        ]
                    }
                ],
                max_tokens=400
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            log(f"Vision API error: {e}")
            return None
    
    def save_to_database(self, image_data, ai_description):
        """Save wild orchid image to database"""
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        try:
            scientific_name = f"{image_data['genus']} {image_data['species']}"
            
            cursor.execute("""
                INSERT INTO orchid_record (
                    scientific_name, genus, species, 
                    image_url, photographer, image_source,
                    ai_description, validation_status,
                    created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                ON CONFLICT DO NOTHING
                RETURNING id
            """, (
                scientific_name,
                image_data['genus'],
                image_data['species'],
                image_data['url'],
                image_data['photographer'],
                image_data['source'],
                ai_description,
                'approved'
            ))
            
            result = cursor.fetchone()
            conn.commit()
            
            if result:
                self.collected_count += 1
                return result[0]
            
        except Exception as e:
            log(f"Database error: {e}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
            
        return None
    
    def run_collection_and_analysis(self):
        """Main collection and analysis workflow"""
        log("🚀 Starting wild orchid collection and analysis...")
        
        # Collect image URLs from both sources
        gary_images = self.scrape_gary_yong_gee_images()
        roberta_images = self.scrape_roberta_fox_images()
        
        all_images = gary_images + roberta_images
        
        log(f"📸 Total images found: {len(all_images)}")
        log(f"   Gary Yong Gee: {len(gary_images)}")
        log(f"   Roberta Fox: {len(roberta_images)}")
        
        # Analyze each image with AI Vision
        for idx, image_data in enumerate(all_images[:50], 1):  # Start with 50
            log(f"\n[{idx}/{len(all_images[:50])}] Analyzing: {image_data['genus']} {image_data['species']}")
            log(f"   Source: {image_data['source']}")
            log(f"   URL: {image_data['url'][:80]}...")
            
            ai_description = self.analyze_image_with_vision(image_data['url'])
            
            if ai_description:
                log(f"   AI: {ai_description[:100]}...")
                
                orchid_id = self.save_to_database(image_data, ai_description)
                
                if orchid_id:
                    log(f"   ✅ Saved to database (ID: {orchid_id})")
                else:
                    log(f"   ⚠️ Already exists in database")
            else:
                log(f"   ⚠️ AI analysis failed")
            
            time.sleep(2)  # Rate limiting
        
        log(f"\n✅ Collection complete! Added {self.collected_count} new wild orchid records")
        return self.collected_count

if __name__ == "__main__":
    collector = WildOrchidCollector()
    collector.run_collection_and_analysis()
