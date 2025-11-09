#!/usr/bin/env python3
"""
AOS Culture Sheets Importer - Structured Database Version  
Imports American Orchid Society culture sheets into structured tables
Source: https://www.aos.org/orchid-care/care-sheets
"""
import os
import psycopg2
import requests
from bs4 import BeautifulSoup
import time
import json
from datetime import datetime

DATABASE_URL = os.environ.get('DATABASE_URL')

class AOSCultureImporter:
    def __init__(self):
        self.base_url = "https://www.aos.org"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; OrchidBot/1.0; Educational/Research)'
        })
        self.conn = psycopg2.connect(DATABASE_URL)
        self.cur = self.conn.cursor()
        
        # AOS culture sheets (genus-level)
        self.culture_sheets = [
            ('Angraecum', '/orchid-care/care-sheets/angraecum-culture-sheet'),
            ('Bulbophyllum', '/orchid-care/care-sheets/bulbophyllum-culture-sheet'),
            ('Catasetum', '/orchid-care/care-sheets/catasetum-culture-sheet'),
            ('Cattleya', '/orchid-care/care-sheets/cattleya-culture-sheet'),
            ('Coelogyne', '/orchid-care/care-sheets/coelogyne-culture-sheet'),
            ('Cymbidium', '/orchid-care/care-sheets/cymbidium-culture-sheet'),
            ('Dendrobium', '/orchid-care/care-sheets/dendrobium-culture-sheet'),
            ('Gongora', '/orchid-care/care-sheets/gongora-culture-sheet'),
            ('Habenaria', '/orchid-care/care-sheets/habenaria-culture-sheet'),
            ('Lycaste', '/orchid-care/care-sheets/lycaste-culture-sheet'),
            ('Masdevallia', '/orchid-care/care-sheets/masdevallia-culture-sheet'),
            ('Miltonia', '/orchid-care/care-sheets/miltonia-culture-sheet'),
            ('Miltoniopsis', '/orchid-care/care-sheets/miltoniopsis-culture-sheet'),
            ('Oncidium', '/orchid-care/care-sheets/oncidium-culture-sheet'),
            ('Paphiopedilum', '/orchid-care/care-sheets/paphiopedilum-culture-sheet'),
            ('Phalaenopsis', '/orchid-care/care-sheets/phalaenopsis-culture-sheet'),
            ('Stanhopea', '/orchid-care/care-sheets/stanhopea-culture-sheet'),
            ('Tolumnia', '/orchid-care/care-sheets/tolumnia-culture-sheet'),
            ('Vanda', '/orchid-care/care-sheets/vanda-culture-sheet')
        ]
        
        self.stats = {'processed': 0, 'skipped': 0, 'errors': 0}
    
    def import_all_culture_sheets(self):
        """Import all AOS culture sheets"""
        print("="*70)
        print("🇺🇸 AOS CULTURE SHEETS IMPORTER")
        print("="*70)
        print(f"Source: {self.base_url}/orchid-care/care-sheets")
        print(f"📚 Genus-level culture sheets: {len(self.culture_sheets)}")
        print()
        
        try:
            for i, (genus, url_path) in enumerate(self.culture_sheets, 1):
                try:
                    print(f"[{i}/{len(self.culture_sheets)}] {genus}")
                    
                    # Check if already imported
                    self.cur.execute("""
                        SELECT id FROM aos_culture_sheets 
                        WHERE genus = %s
                    """, (genus,))
                    
                    if self.cur.fetchone():
                        print(f"   ⏭️  Already imported")
                        self.stats['skipped'] += 1
                        continue
                    
                    # Scrape culture sheet
                    culture_data = self.scrape_culture_sheet(genus, url_path)
                    
                    if culture_data:
                        self.save_culture_sheet(culture_data)
                        self.stats['processed'] += 1
                        print(f"   ✅ Imported successfully")
                    else:
                        print(f"   ⚠️  No data extracted")
                        self.stats['errors'] += 1
                    
                    # Be respectful to AOS servers
                    time.sleep(2)
                    
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
    
    def scrape_culture_sheet(self, genus, url_path):
        """Scrape individual AOS culture sheet"""
        full_url = self.base_url + url_path
        
        try:
            response = self.session.get(full_url, timeout=15)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove nav, header, footer elements
            for element in soup.find_all(['nav', 'header', 'footer', 'aside']):
                element.decompose()
            
            # Find main content container using semantic selectors
            main_content = soup.find('main')
            if not main_content:
                main_content = soup.find('article')
            if not main_content:
                main_content = soup.find('section', role='main')
            if not main_content:
                # Fallback: use body if no semantic container found
                main_content = soup.find('body')
            
            if not main_content:
                return None
            
            # Extract sections by heading (H2/H3)
            sections = self.extract_sections_by_heading(main_content)
            full_text = main_content.get_text()
            
            data = {
                'genus': genus,
                'source_url': full_url,
                'light_requirements': sections.get('light', sections.get('lighting')),
                'temperature_requirements': sections.get('temperature', sections.get('temperatures')),
                'water_requirements': sections.get('water', sections.get('watering')),
                'humidity_requirements': sections.get('humidity'),
                'fertilizer_requirements': sections.get('fertilizer', sections.get('fertilizing')),
                'potting_requirements': sections.get('potting', sections.get('repotting')),
                'special_notes': sections.get('problems', sections.get('notes', sections.get('cultural notes'))),
                'raw_html': str(soup)[:3000]
            }
            
            # Classify temperature category
            if 'cool' in full_text.lower():
                data['temp_category'] = 'cool'
            elif 'warm' in full_text.lower():
                data['temp_category'] = 'warm'
            else:
                data['temp_category'] = 'intermediate'
            
            # Classify light level
            if 'bright' in full_text.lower() or 'high' in full_text.lower():
                data['light_level'] = 'bright'
            elif 'shade' in full_text.lower() or 'low' in full_text.lower():
                data['light_level'] = 'low'
            else:
                data['light_level'] = 'medium'
            
            return data
            
        except Exception as e:
            print(f"      Error scraping: {str(e)[:50]}")
            return None
    
    def extract_sections_by_heading(self, container):
        """Extract content by H2/H3 headings"""
        sections = {}
        current_heading = None
        current_content = []
        
        # Walk through all direct children
        for element in container.find_all(['h1', 'h2', 'h3', 'p']):
            if element.name in ['h1', 'h2', 'h3']:
                # Save previous section if exists
                if current_heading:
                    sections[current_heading.lower()] = ' '.join(current_content).strip()[:500]
                # Start new section
                current_heading = element.get_text().strip()
                current_content = []
            elif element.name == 'p' and current_heading:
                # Add paragraph to current section
                text = element.get_text().strip()
                if text:
                    current_content.append(text)
        
        # Save final section
        if current_heading:
            sections[current_heading.lower()] = ' '.join(current_content).strip()[:500]
        
        return sections
    
    def save_culture_sheet(self, data):
        """Save AOS culture sheet to database"""
        # Get taxonomy_id for genus
        self.cur.execute("""
            SELECT id FROM orchid_taxonomy 
            WHERE genus = %s
            LIMIT 1
        """, (data['genus'],))
        
        result = self.cur.fetchone()
        taxonomy_id = result[0] if result else None
        
        # Insert AOS culture sheet
        self.cur.execute("""
            INSERT INTO aos_culture_sheets (
                taxonomy_id, genus,
                light_requirements, light_level,
                temperature_requirements, temp_category,
                water_requirements,
                humidity_requirements,
                fertilizer_requirements,
                potting_requirements,
                special_notes,
                source_url, raw_data, scraped_at
            ) VALUES (
                %s, %s,
                %s, %s,
                %s, %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s, %s, %s
            )
        """, (
            taxonomy_id, data['genus'],
            data.get('light_requirements'), data.get('light_level'),
            data.get('temperature_requirements'), data.get('temp_category'),
            data.get('water_requirements'),
            data.get('humidity_requirements'),
            data.get('fertilizer_requirements'),
            data.get('potting_requirements'),
            data.get('special_notes'),
            data['source_url'], json.dumps({'raw_html': data.get('raw_html', '')}),
            datetime.now()
        ))
        
        self.conn.commit()


if __name__ == '__main__':
    importer = AOSCultureImporter()
    importer.import_all_culture_sheets()
