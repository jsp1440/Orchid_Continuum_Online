#!/usr/bin/env python3
"""
Wikimedia Commons Orchid Image Downloader - Mac Version
Downloads ~100,000 high-quality orchid images from Wikimedia Commons

FEATURES:
- All CC-licensed (free to use)
- High-resolution professional photography
- Historical botanical illustrations (1700s-1900s)
- Multi-language descriptions

SETUP (one time):
    pip3 install requests

USAGE:
    python3 EASY_Mac_Wikimedia_Downloader.py

The script will:
- Create folder: ~/orchid_downloads/wikimedia_commons/
- Download images with metadata
- Save data to: wikimedia_orchids.csv
"""

import requests
import time
import os
import csv
from pathlib import Path
import urllib.parse

class WikimediaDownloader:
    def __init__(self):
        # Create folder in user's home directory
        home = str(Path.home())
        self.base_dir = os.path.join(home, "orchid_downloads")
        self.output_dir = os.path.join(self.base_dir, "wikimedia_commons")
        self.csv_file = os.path.join(self.base_dir, "wikimedia_orchids.csv")
        
        self.api_url = "https://commons.wikimedia.org/w/api.php"
        self.downloaded_count = 0
        self.species_set = set()
        
        # Auto-create directories
        os.makedirs(self.output_dir, exist_ok=True)
        
        print(f"\n✅ Created folder: {self.base_dir}")
        print(f"✅ Images will save to: {self.output_dir}")
        print(f"✅ Data will save to: {self.csv_file}\n")
        
        self.init_csv()
    
    def init_csv(self):
        """Initialize CSV with image metadata"""
        with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'page_id', 'title', 'filename', 'description',
                'date_uploaded', 'uploader', 'author', 'source',
                'license', 'license_url', 'categories',
                'width', 'height', 'size_bytes', 'mime_type',
                'image_url', 'thumbnail_url', 'commons_url',
                'extracted_species', 'extracted_genus'
            ])
        print(f"✅ Created: {self.csv_file}")
    
    def search_images(self, query, limit=500, continue_token=None):
        """Search Wikimedia Commons for orchid images"""
        params = {
            'action': 'query',
            'format': 'json',
            'generator': 'search',
            'gsrsearch': query,
            'gsrnamespace': '6',  # File namespace
            'gsrlimit': min(limit, 500),  # Max 500 per request
            'prop': 'imageinfo|categories',
            'iiprop': 'url|size|mime|extmetadata|user|timestamp',
            'iiurlwidth': 500,  # Thumbnail width
            'cllimit': 'max'
        }
        
        if continue_token:
            params.update(continue_token)
        
        # Add User-Agent header to avoid 403 errors
        headers = {
            'User-Agent': 'OrchidDownloader/1.0 (Educational/Research Project)'
        }
        
        try:
            response = requests.get(self.api_url, params=params, headers=headers, timeout=30)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ API Error {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Request failed: {e}")
            return None
    
    def download_image(self, url, filename):
        """Download image file"""
        try:
            headers = {
                'User-Agent': 'OrchidDownloader/1.0 (Educational/Research Project)'
            }
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                filepath = os.path.join(self.output_dir, filename)
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                return True
            return False
        except:
            return False
    
    def extract_species_from_title(self, title):
        """Try to extract species name from filename"""
        # Common patterns: "Genus species - description.jpg"
        import re
        
        # Remove "File:" prefix
        title = title.replace('File:', '')
        
        # Look for scientific name pattern (Genus species)
        pattern = r'([A-Z][a-z]+)\s+([a-z]+)'
        match = re.search(pattern, title)
        
        if match:
            genus = match.group(1)
            species = f"{genus} {match.group(2)}"
            return genus, species
        
        return '', ''
    
    def process_image(self, page):
        """Process and download a single image"""
        page_id = page.get('pageid', '')
        title = page.get('title', '')
        
        imageinfo = page.get('imageinfo', [])
        if not imageinfo:
            return False
        
        info = imageinfo[0]
        
        # Get metadata
        img_url = info.get('url', '')
        thumb_url = info.get('thumburl', '')
        width = info.get('width', 0)
        height = info.get('height', 0)
        size = info.get('size', 0)
        mime = info.get('mime', '')
        uploader = info.get('user', '')
        timestamp = info.get('timestamp', '')
        
        # Get extended metadata
        extmeta = info.get('extmetadata', {})
        description = extmeta.get('ImageDescription', {}).get('value', '')
        author = extmeta.get('Artist', {}).get('value', '')
        source = extmeta.get('Credit', {}).get('value', '')
        license_name = extmeta.get('LicenseShortName', {}).get('value', '')
        license_url = extmeta.get('LicenseUrl', {}).get('value', '')
        
        # Get categories
        categories = []
        for cat in page.get('categories', []):
            cat_title = cat.get('title', '').replace('Category:', '')
            categories.append(cat_title)
        categories_str = '|'.join(categories)
        
        # Extract species info
        genus, species = self.extract_species_from_title(title)
        
        # Generate filename
        safe_title = title.replace('File:', '').replace('/', '_').replace('\\', '_')
        if len(safe_title) > 100:
            safe_title = safe_title[:100]
        filename = f"{page_id}_{safe_title}"
        if not filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
            filename += '.jpg'
        
        # Download image
        print(f"  📥 {title[:60]}...", end='\r')
        
        if self.download_image(img_url, filename):
            # Save to CSV
            with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    page_id, title, filename, description,
                    timestamp, uploader, author, source,
                    license_name, license_url, categories_str,
                    width, height, size, mime,
                    img_url, thumb_url,
                    f"https://commons.wikimedia.org/wiki/{urllib.parse.quote(title)}",
                    species, genus
                ])
            
            self.downloaded_count += 1
            if species:
                self.species_set.add(species)
            
            time.sleep(0.2)  # Be nice to Wikimedia servers
            return True
        
        return False
    
    def run(self, max_images=100000):
        """Main download loop"""
        print("\n" + "="*70)
        print("📚 Wikimedia Commons Orchid Downloader")
        print("="*70)
        print(f"🎯 Target: {max_images:,} orchid images")
        print("📸 Source: High-quality CC-licensed photos + historical illustrations")
        print("="*70 + "\n")
        
        # Search queries to try
        queries = [
            'Orchidaceae',
            'Orchid flower',
            'Orchid species',
            'Orchidaceae species'
        ]
        
        for query_idx, query in enumerate(queries):
            print(f"\n🔍 Query {query_idx + 1}/{len(queries)}: '{query}'")
            
            continue_token = None
            batch = 1
            
            while self.downloaded_count < max_images:
                print(f"\n  📄 Batch {batch} (Total: {self.downloaded_count:,} images, {len(self.species_set):,} species)")
                
                data = self.search_images(query, limit=500, continue_token=continue_token)
                
                if not data:
                    print("  ⚠️ No data returned")
                    break
                
                pages = data.get('query', {}).get('pages', {})
                if not pages:
                    print("  ✅ No more results for this query")
                    break
                
                # Process batch
                batch_count = 0
                for page_id, page in pages.items():
                    if self.process_image(page):
                        batch_count += 1
                    
                    if self.downloaded_count >= max_images:
                        print(f"\n  🎯 Reached target: {max_images:,} images")
                        break
                
                print(f"  ✅ Batch complete: +{batch_count} images")
                
                # Check for continuation
                if 'continue' not in data:
                    print("  ✅ No more results")
                    break
                
                continue_token = data['continue']
                batch += 1
                time.sleep(2)
            
            if self.downloaded_count >= max_images:
                break
        
        print("\n" + "="*70)
        print("🎉 DOWNLOAD COMPLETE!")
        print("="*70)
        print(f"✅ Downloaded: {self.downloaded_count:,} images")
        print(f"✅ Species identified: {len(self.species_set):,}")
        print(f"📁 Images: {self.output_dir}")
        print(f"📊 Data: {self.csv_file}")
        print("="*70 + "\n")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("📚 WELCOME TO WIKIMEDIA COMMONS DOWNLOADER")
    print("="*70)
    print("This will download orchid images to:")
    print("  ~/orchid_downloads/wikimedia_commons/")
    print("\nFeatures:")
    print("  • All CC-licensed (free to use)")
    print("  • High-resolution professional photography")
    print("  • Historical botanical illustrations")
    print("\nTarget: ~100,000 images")
    print("Estimated time: 4-6 hours")
    print("Estimated storage: 10-20 GB")
    print("="*70)
    
    input("\nPress Enter to start downloading, or Ctrl+C to exit...")
    
    downloader = WikimediaDownloader()
    downloader.run(max_images=100000)
