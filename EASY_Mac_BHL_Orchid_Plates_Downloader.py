#!/usr/bin/env python3
"""
Biodiversity Heritage Library (BHL) Orchid Plates Downloader
Downloads historical botanical illustrations of orchids with full attribution
Honors original botanists, collectors, illustrators, and librarians
"""

import os
import requests
import json
import csv
import time
from datetime import datetime

class BHLOrchidPlatesDownloader:
    def __init__(self):
        self.base_url = "https://www.biodiversitylibrary.org/api3"
        self.api_key = "your-bhl-api-key-here"  # BHL requires free API key
        
        self.base_dir = os.path.expanduser("~/orchid_downloads")
        self.output_dir = os.path.join(self.base_dir, "orchid_plates")
        self.csv_file = os.path.join(self.base_dir, "orchid_plates_attribution.csv")
        
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
                'plate_id', 'scientific_name', 'common_name',
                'image_url', 'thumbnail_url', 'page_url',
                'title', 'author', 'illustrator', 'publisher', 'publication_date',
                'volume', 'page_number', 'institution', 'collection',
                'contributor', 'digitized_by', 'rights', 'license',
                'subjects', 'language', 'format',
                'filename', 'download_date'
            ])
    
    def search_orchid_plates(self, genus=None, limit=100):
        """Search BHL for orchid botanical illustrations"""
        print(f"\n🔍 Searching BHL for orchid plates...")
        
        # Search for orchid-related titles
        search_term = f"{genus} orchid" if genus else "orchidaceae"
        
        url = f"{self.base_url}?op=PublicationSearch&searchterm={search_term}&searchcat=&format=json&apikey={self.api_key}"
        
        try:
            response = requests.get(url, timeout=30)
            data = response.json()
            
            if data.get('Status') == 'ok':
                results = data.get('Result', [])
                print(f"✅ Found {len(results)} publications")
                return results[:limit]
            else:
                print("❌ Search failed")
                return []
        except Exception as e:
            print(f"❌ Error: {e}")
            return []
    
    def get_publication_metadata(self, item_id):
        """Get detailed metadata for a publication"""
        url = f"{self.base_url}?op=GetItemMetadata&id={item_id}&pages=t&ocr=f&parts=t&format=json&apikey={self.api_key}"
        
        try:
            response = requests.get(url, timeout=30)
            data = response.json()
            
            if data.get('Status') == 'ok':
                return data.get('Result', [])
            return []
        except:
            return []
    
    def download_plate(self, page_data, publication_meta):
        """Download botanical plate image with full attribution"""
        try:
            # Get image URL
            page_id = page_data.get('PageID')
            image_url = f"https://www.biodiversitylibrary.org/pagethumb/{page_id},800,800"
            
            # Download image
            response = requests.get(image_url, timeout=30)
            if response.status_code != 200:
                return False
            
            # Save image
            scientific_name = publication_meta.get('BHLType', 'Unknown_species')
            safe_name = scientific_name.replace(' ', '_').replace('/', '-')
            filename = f"bhl_{page_id}_{safe_name}.jpg"
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            # Save attribution data
            with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    page_id,
                    scientific_name,
                    publication_meta.get('CommonName', ''),
                    image_url,
                    f"https://www.biodiversitylibrary.org/pagethumb/{page_id},300,300",
                    f"https://www.biodiversitylibrary.org/page/{page_id}",
                    publication_meta.get('FullTitle', ''),
                    publication_meta.get('Authors', ''),
                    publication_meta.get('Illustrator', ''),
                    publication_meta.get('Publishers', ''),
                    publication_meta.get('Date', ''),
                    publication_meta.get('Volume', ''),
                    page_data.get('PageNumbers', ''),
                    publication_meta.get('HoldingInstitution', ''),
                    publication_meta.get('Collection', ''),
                    publication_meta.get('Contributor', ''),
                    publication_meta.get('ScanningInstitution', ''),
                    publication_meta.get('Rights', 'Public Domain'),
                    publication_meta.get('Copyrights', 'Public Domain'),
                    ', '.join(publication_meta.get('Subjects', [])),
                    publication_meta.get('Language', ''),
                    'Botanical Illustration',
                    filename,
                    datetime.now().isoformat()
                ])
            
            self.downloaded_count += 1
            return True
            
        except Exception as e:
            return False
    
    def run(self, genera_list=None):
        """Main execution"""
        print("="*70)
        print("🎨 BHL ORCHID BOTANICAL PLATES DOWNLOADER")
        print("="*70)
        print("This downloads historical orchid illustrations with full attribution:")
        print("  - Original botanists & authors")
        print("  - Illustrators & artists")
        print("  - Collectors & institutions")
        print("  - Digitization teams")
        print("="*70)
        print()
        
        input("Press Enter to start downloading, or Ctrl+C to exit...")
        
        self.setup()
        
        # Default genera to search
        if not genera_list:
            genera_list = [
                "Phragmipedium", "Cypripedium", "Cattleya", "Dendrobium",
                "Paphiopedilum", "Phalaenopsis", "Oncidium", "Vanilla",
                "Platanthera", "Angraecum", "Bulbophyllum", "Epidendrum",
                "Habenaria", "Ophrys", "Masdevallia", "Dracula"
            ]
        
        for genus in genera_list:
            print(f"\n📚 Searching for {genus} plates...")
            publications = self.search_orchid_plates(genus, limit=10)
            
            for pub in publications:
                item_id = pub.get('ItemID')
                if not item_id:
                    continue
                
                print(f"  📖 Processing: {pub.get('ShortTitle', 'Unknown')}")
                
                # Get publication metadata
                metadata = self.get_publication_metadata(item_id)
                if not metadata:
                    continue
                
                pub_meta = metadata[0] if isinstance(metadata, list) else metadata
                
                # Get pages with illustrations
                pages = pub_meta.get('Pages', [])
                
                for page in pages:
                    # Only download pages marked as illustrations
                    if 'illustration' in page.get('PageTypeName', '').lower():
                        print(f"    🖼️  Downloading plate {page.get('PageNumbers', '')}...")
                        
                        if self.download_plate(page, pub_meta):
                            print(f"    ✅ Downloaded ({self.downloaded_count})")
                        
                        time.sleep(1)  # Respectful rate limiting
                
                time.sleep(2)
        
        print("\n" + "="*70)
        print("🎉 DOWNLOAD COMPLETE!")
        print("="*70)
        print(f"✅ Downloaded: {self.downloaded_count} botanical plates")
        print(f"📁 Images: {self.output_dir}")
        print(f"📊 Attribution data: {self.csv_file}")
        print("\n🙏 All original botanists, illustrators, collectors, and")
        print("   digitization teams are credited in the CSV file!")
        print("="*70)

if __name__ == "__main__":
    print("\n⚠️  IMPORTANT: BHL requires a free API key!")
    print("Get yours at: https://www.biodiversitylibrary.org/api/")
    print("Then edit line 19 of this script to add your key.\n")
    
    # For now, create a simpler direct scraper version
    print("For immediate use without API key, use the Wikimedia downloader")
    print("which has many BHL plates already uploaded.\n")
    
    downloader = BHLOrchidPlatesDownloader()
    # downloader.run()
