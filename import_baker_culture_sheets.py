#!/usr/bin/env python3
"""
Baker Culture Sheets Importer - Structured Database Version
Imports Charles & Margaret Baker's orchid culture data into structured tables
Source: https://orchidculture.com/COD/FREE/
"""
import os
import sys
import psycopg2
import requests
from bs4 import BeautifulSoup
import re
import time
import json
from datetime import datetime

DATABASE_URL = os.environ.get('DATABASE_URL')

class BakerCultureImporter:
    def __init__(self):
        self.base_url = "https://orchidculture.com/COD/FREE/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; OrchidBot/1.0; Educational/Research)'
        })
        self.conn = psycopg2.connect(DATABASE_URL)
        self.cur = self.conn.cursor()
        
        self.stats = {'processed': 0, 'errors': 0, 'skipped': 0}
        
    def import_all_culture_sheets(self, limit=None):
        """Import all available Baker culture sheets"""
        print("="*70)
        print("🌺 BAKER CULTURE SHEETS IMPORTER")
        print("="*70)
        print(f"Source: {self.base_url}")
        print()
        
        try:
            # Get index page
            response = self.session.get(self.base_url, timeout=15)
            if response.status_code != 200:
                print(f"❌ Failed to access Baker index: {response.status_code}")
                return self.stats
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all culture sheet links (FS*.html pattern)
            culture_links = []
            for link in soup.find_all('a', href=re.compile(r'FS\d+\.html')):
                href = link.get('href')
                if href:
                    full_url = f"{self.base_url}{href}"
                    species_text = link.get_text().strip()
                    culture_links.append((full_url, species_text))
            
            total = len(culture_links)
            if limit:
                culture_links = culture_links[:limit]
                total = limit
            
            print(f"📋 Found {len(culture_links)} culture sheets to import")
            print()
            
            # Process each culture sheet
            for i, (url, species_text) in enumerate(culture_links, 1):
                try:
                    print(f"[{i}/{total}] {species_text}")
                    
                    # Check if already imported
                    self.cur.execute("""
                        SELECT id FROM baker_culture_sheets 
                        WHERE scientific_name = %s
                    """, (species_text,))
                    
                    if self.cur.fetchone():
                        print(f"   ⏭️  Already imported")
                        self.stats['skipped'] += 1
                        continue
                    
                    # Scrape culture sheet
                    culture_data = self.scrape_culture_sheet(url, species_text)
                    
                    if culture_data:
                        # Save to database
                        self.save_culture_sheet(culture_data)
                        self.stats['processed'] += 1
                        print(f"   ✅ Imported successfully")
                    else:
                        print(f"   ⚠️  No data extracted")
                        self.stats['errors'] += 1
                    
                    # Be respectful to server
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"   ❌ Error: {str(e)[:100]}")
                    self.stats['errors'] += 1
                    continue
            
            print()
            print("="*70)
            print("📊 IMPORT COMPLETE")
            print("="*70)
            print(f"✅ Imported: {self.stats['processed']}")
            print(f"⏭️  Skipped: {self.stats['skipped']}")
            print(f"❌ Errors: {self.stats['errors']}")
            print("="*70)
            
        finally:
            self.cur.close()
            self.conn.close()
        
        return self.stats
    
    def scrape_culture_sheet(self, url, species_name):
        """Scrape individual Baker culture sheet"""
        try:
            response = self.session.get(url, timeout=15)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Parse species name
            genus, species = self.parse_species_name(species_name)
            
            # Extract data from the page
            text_content = soup.get_text()
            
            data = {
                'scientific_name': species_name,
                'genus': genus,
                'species': species,
                'source_url': url,
                'raw_html': str(soup)[:5000],  # Keep first 5000 chars
            }
            
            # Extract structured data
            data.update(self.extract_origin_data(text_content))
            data.update(self.extract_temperature_data(text_content))
            data.update(self.extract_light_data(text_content))
            data.update(self.extract_water_humidity_data(text_content))
            data.update(self.extract_cultural_data(text_content))
            
            # Calculate data quality score
            data['quality_score'] = self.calculate_quality_score(data)
            
            return data
            
        except Exception as e:
            print(f"      Error scraping: {str(e)[:50]}")
            return None
    
    def parse_species_name(self, name):
        """Parse genus and species from scientific name"""
        parts = name.strip().split()
        genus = parts[0] if parts else ''
        species = parts[1] if len(parts) > 1 else ''
        return genus, species
    
    def extract_origin_data(self, text):
        """Extract geographic origin data"""
        data = {}
        
        # Look for elevation patterns
        elev_match = re.search(r'(\d+)-(\d+)\s*(?:m|meters)', text, re.IGNORECASE)
        if elev_match:
            data['elevation_min'] = int(elev_match.group(1))
            data['elevation_max'] = int(elev_match.group(2))
        
        # Look for climate zones
        if re.search(r'tropical|equatorial', text, re.IGNORECASE):
            data['climate_zone'] = 'tropical'
        elif re.search(r'subtropical', text, re.IGNORECASE):
            data['climate_zone'] = 'subtropical'
        elif re.search(r'temperate', text, re.IGNORECASE):
            data['climate_zone'] = 'temperate'
        
        return data
    
    def extract_temperature_data(self, text):
        """Extract temperature requirements"""
        data = {}
        
        # Look for temperature patterns (e.g., "75-85°F")
        temp_patterns = re.findall(r'(\d+)-(\d+)\s*°?[Ff]', text)
        if len(temp_patterns) >= 2:
            # Assume first is day, second is night
            data['temp_day_min'] = int(temp_patterns[0][0])
            data['temp_day_max'] = int(temp_patterns[0][1])
            if len(temp_patterns) > 1:
                data['temp_night_min'] = int(temp_patterns[1][0])
                data['temp_night_max'] = int(temp_patterns[1][1])
        
        return data
    
    def extract_light_data(self, text):
        """Extract light requirements"""
        data = {}
        
        # Look for footcandle values
        fc_match = re.search(r'(\d+,?\d*)-(\d+,?\d*)\s*(?:foot-?candles?|fc)', text, re.IGNORECASE)
        if fc_match:
            data['light_min'] = int(fc_match.group(1).replace(',', ''))
            data['light_max'] = int(fc_match.group(2).replace(',', ''))
        
        # Classify light level
        if 'bright' in text.lower():
            data['light_level'] = 'bright'
        elif 'shade' in text.lower():
            data['light_level'] = 'shade'
        elif 'medium' in text.lower():
            data['light_level'] = 'medium'
        
        return data
    
    def extract_water_humidity_data(self, text):
        """Extract water and humidity requirements"""
        data = {}
        
        # Humidity percentages
        hum_match = re.search(r'(\d+)-(\d+)%', text)
        if hum_match:
            data['humidity_min'] = int(hum_match.group(1))
            data['humidity_max'] = int(hum_match.group(2))
        
        return data
    
    def extract_cultural_data(self, text):
        """Extract additional cultural information"""
        data = {}
        
        # Check for rest period
        if re.search(r'rest period|dormancy', text, re.IGNORECASE):
            data['rest_period'] = True
        
        # Check for mounting
        if re.search(r'mount|mounted', text, re.IGNORECASE):
            data['mounting'] = True
        
        # Check for fragrance
        if re.search(r'fragrant|scent|perfume', text, re.IGNORECASE):
            data['fragrance'] = True
        
        return data
    
    def calculate_quality_score(self, data):
        """Calculate data quality score (0-100)"""
        score = 0
        fields_to_check = [
            'elevation_min', 'climate_zone', 'temp_day_min', 'temp_night_min',
            'light_level', 'humidity_min', 'fragrance'
        ]
        
        for field in fields_to_check:
            if data.get(field):
                score += 14  # ~100/7 fields
        
        return min(score, 100)
    
    def save_culture_sheet(self, data):
        """Save culture sheet to database"""
        # Get taxonomy_id
        self.cur.execute("""
            SELECT id FROM orchid_taxonomy 
            WHERE scientific_name = %s
            LIMIT 1
        """, (data['scientific_name'],))
        
        result = self.cur.fetchone()
        taxonomy_id = result[0] if result else None
        
        # Insert Baker culture sheet
        self.cur.execute("""
            INSERT INTO baker_culture_sheets (
                taxonomy_id, genus, species, scientific_name,
                native_elevation_min, native_elevation_max, climate_zone,
                temp_summer_day_min, temp_summer_day_max,
                temp_summer_night_min, temp_summer_night_max,
                light_level, light_footcandles_min, light_footcandles_max,
                humidity_min, humidity_max,
                rest_period_required, mounting_recommended, fragrance,
                source_url, raw_data, data_quality_score, scraped_at
            ) VALUES (
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s
            )
        """, (
            taxonomy_id, data['genus'], data['species'], data['scientific_name'],
            data.get('elevation_min'), data.get('elevation_max'), data.get('climate_zone'),
            data.get('temp_day_min'), data.get('temp_day_max'),
            data.get('temp_night_min'), data.get('temp_night_max'),
            data.get('light_level'), data.get('light_min'), data.get('light_max'),
            data.get('humidity_min'), data.get('humidity_max'),
            data.get('rest_period', False), data.get('mounting', False), data.get('fragrance', False),
            data['source_url'], json.dumps({'raw_html': data.get('raw_html', '')}), 
            data.get('quality_score', 0), datetime.now()
        ))
        
        self.conn.commit()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Import Baker culture sheets')
    parser.add_argument('--limit', type=int, help='Limit number of sheets to import (for testing)')
    args = parser.parse_args()
    
    importer = BakerCultureImporter()
    importer.import_all_culture_sheets(limit=args.limit)
