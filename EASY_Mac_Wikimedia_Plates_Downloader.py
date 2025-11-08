#!/usr/bin/env python3
"""
Wikimedia Commons Orchid Botanical Plates Downloader
Downloads historical botanical illustrations from Wikimedia Commons
Honors original botanists, illustrators, and contributing institutions
"""

import os
import requests
import json
import csv
import time
from datetime import datetime
from urllib.parse import quote

class WikimediaPlatesDownloader:
    def __init__(self):
        self.api_url = "https://commons.wikimedia.org/w/api.php"
        
        self.base_dir = os.path.expanduser("~/orchid_downloads")
        self.output_dir = os.path.join(self.base_dir, "wikimedia_plates")
        self.csv_file = os.path.join(self.base_dir, "wikimedia_plates_attribution.csv")
        
        self.downloaded_count = 0
        
    def setup(self):
        """Create directories and CSV file"""
        os.makedirs(self.output_dir, exist_ok=True)
        
        print(f"✅ Plates will save to: {self.output_dir}")
        print(f"✅ Attribution data: {self.csv_file}")
        
        # Create CSV with full attribution fields
        with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'file_id', 'filename', 'title', 'description',
                'author', 'artist', 'date', 'source', 'license',
                'url', 'thumbnail_url', 'page_url',
                'categories', 'width', 'height',
                'upload_date', 'uploader', 'institution',
                'download_date', 'local_filename'
            ])
    
    def search_plates(self, search_term, limit=500):
        """Search Wikimedia Commons for botanical illustrations"""
        print(f"\n🔍 Searching for '{search_term}' plates...")
        
        params = {
            'action': 'query',
            'format': 'json',
            'generator': 'search',
            'gsrsearch': f'{search_term} botanical illustration',
            'gsrnamespace': '6',  # File namespace
            'gsrlimit': limit,
            'prop': 'imageinfo',
            'iiprop': 'url|size|extmetadata|user|timestamp',
            'iiurlwidth': 1200
        }
        
        try:
            response = requests.get(self.api_url, params=params, timeout=30)
            data = response.json()
            
            pages = data.get('query', {}).get('pages', {})
            print(f"✅ Found {len(pages)} illustrations")
            return pages
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return {}
    
    def download_plate(self, page_data):
        """Download botanical plate with full attribution"""
        try:
            imageinfo = page_data.get('imageinfo', [{}])[0]
            
            # Get image URL
            image_url = imageinfo.get('url')
            if not image_url:
                return False
            
            # Get metadata
            metadata = imageinfo.get('extmetadata', {})
            
            # Download image
            response = requests.get(image_url, timeout=30)
            if response.status_code != 200:
                return False
            
            # Create filename
            original_name = page_data.get('title', 'Unknown').replace('File:', '')
            safe_name = original_name.replace(' ', '_').replace('/', '-')[:100]
            filename = f"wikimedia_{page_data.get('pageid', 'unknown')}_{safe_name}"
            
            # Ensure proper extension
            if not any(filename.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.tif', '.tiff']):
                filename += '.jpg'
            
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            # Extract attribution data
            artist = metadata.get('Artist', {}).get('value', 'Unknown')
            author = metadata.get('Author', {}).get('value', 'Unknown')
            date = metadata.get('DateTimeOriginal', {}).get('value', 
                   metadata.get('DateTime', {}).get('value', 'Unknown'))
            license_info = metadata.get('License', {}).get('value', 'Unknown')
            source = metadata.get('Credit', {}).get('value', 
                    metadata.get('Source', {}).get('value', 'Unknown'))
            description = metadata.get('ImageDescription', {}).get('value', '')
            institution = metadata.get('Institution', {}).get('value', '')
            
            # Save attribution data
            with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    page_data.get('pageid', ''),
                    original_name,
                    page_data.get('title', ''),
                    description[:500] if description else '',
                    author,
                    artist,
                    date,
                    source,
                    license_info,
                    image_url,
                    imageinfo.get('thumburl', ''),
                    f"https://commons.wikimedia.org/?curid={page_data.get('pageid', '')}",
                    ', '.join(metadata.get('Categories', {}).get('value', '').split('|')[:5]),
                    imageinfo.get('width', ''),
                    imageinfo.get('height', ''),
                    imageinfo.get('timestamp', ''),
                    imageinfo.get('user', ''),
                    institution,
                    datetime.now().isoformat(),
                    filename
                ])
            
            self.downloaded_count += 1
            return True
            
        except Exception as e:
            print(f"    ⚠️  Error: {e}")
            return False
    
    def run(self):
        """Main execution"""
        print("="*70)
        print("🎨 WIKIMEDIA COMMONS ORCHID PLATES DOWNLOADER")
        print("="*70)
        print("This downloads historical orchid botanical illustrations")
        print("from Wikimedia Commons with full attribution to:")
        print("  - Original botanical illustrators")
        print("  - Authors & botanists")
        print("  - Contributing institutions")
        print("  - Uploaders & digitizers")
        print("="*70)
        print()
        
        input("Press Enter to start downloading, or Ctrl+C to exit...")
        
        self.setup()
        
        # Search terms for different types of orchid illustrations
        search_terms = [
            "Orchidaceae Curtis",
            "Orchid lithograph",
            "Orchid Lindley",
            "Orchid Reichenbach",
            "Orchid Botanical Magazine",
            "Phragmipedium illustration",
            "Cypripedium illustration",
            "Cattleya illustration",
            "Dendrobium illustration",
            "Orchid Hooker",
            "Orchid botanical plate",
            "Orchidaceae illustration"
        ]
        
        for search_term in search_terms:
            pages = self.search_plates(search_term, limit=100)
            
            for page_id, page_data in pages.items():
                title = page_data.get('title', 'Unknown')
                print(f"  📥 Downloading: {title[:60]}...")
                
                if self.download_plate(page_data):
                    print(f"    ✅ Downloaded ({self.downloaded_count})")
                
                time.sleep(0.5)  # Respectful rate limiting
            
            time.sleep(2)
        
        print("\n" + "="*70)
        print("🎉 DOWNLOAD COMPLETE!")
        print("="*70)
        print(f"✅ Downloaded: {self.downloaded_count} botanical plates")
        print(f"📁 Images: {self.output_dir}")
        print(f"📊 Attribution data: {self.csv_file}")
        print("\n🙏 All original illustrators, botanists, institutions, and")
        print("   uploaders are credited in the CSV file!")
        print("="*70)

if __name__ == "__main__":
    downloader = WikimediaPlatesDownloader()
    downloader.run()
