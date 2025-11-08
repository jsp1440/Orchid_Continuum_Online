#!/usr/bin/env python3
"""
JSTOR Global Plants Orchid Herbarium Downloader
Downloads herbarium specimens from JSTOR Plants (Ithaka)
Preserves attribution to collectors, botanists, and herbaria
"""

import os
import requests
import csv
import time
from datetime import datetime

class JSTORPlantsDownloader:
    def __init__(self):
        self.base_url = "https://plants.jstor.org"
        
        self.base_dir = os.path.expanduser("~/orchid_downloads")
        self.output_dir = os.path.join(self.base_dir, "jstor_herbarium")
        self.csv_file = os.path.join(self.base_dir, "jstor_specimens_attribution.csv")
        
        self.downloaded_count = 0
        
    def setup(self):
        """Create directories and CSV file"""
        os.makedirs(self.output_dir, exist_ok=True)
        
        print(f"✅ Specimens will save to: {self.output_dir}")
        print(f"✅ Attribution data: {self.csv_file}")
        
        # Create CSV with full attribution fields
        with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'specimen_id', 'catalog_number', 'barcode',
                'scientific_name', 'family', 'genus', 'species',
                'collector', 'collection_number', 'collection_date',
                'country', 'locality', 'coordinates', 'elevation',
                'herbarium', 'institution', 'determined_by',
                'image_url', 'specimen_url', 'rights',
                'filename', 'download_date'
            ])
    
    def search_specimens(self, genus, limit=100):
        """Search JSTOR Plants for orchid herbarium specimens"""
        print(f"\n🔍 Searching JSTOR Plants for {genus} specimens...")
        
        # Note: JSTOR Plants requires institutional access or individual subscription
        # This is a template - you'll need valid credentials
        
        search_url = f"{self.base_url}/search"
        params = {
            'family': 'Orchidaceae',
            'genus': genus,
            'limit': limit
        }
        
        print("⚠️  JSTOR Plants requires institutional access")
        print("   Consider using open-access alternatives:")
        print("   - GBIF (already downloading)")
        print("   - iDigBio (already downloading)")
        print("   - Tropicos (Missouri Botanical Garden)")
        return []
    
    def run(self):
        """Main execution"""
        print("="*70)
        print("📚 JSTOR GLOBAL PLANTS HERBARIUM DOWNLOADER")
        print("="*70)
        print("⚠️  IMPORTANT: JSTOR Plants requires institutional subscription")
        print()
        print("Alternative FREE sources for herbarium specimens:")
        print("  ✅ iDigBio - US museum collections (RUNNING)")
        print("  ✅ GBIF - Global occurrence data (RUNNING)")
        print("  ✅ Tropicos - Missouri Botanical Garden (FREE)")
        print("  ✅ Harvard Herbaria - Public access")
        print()
        print("Your current downloaders are already getting herbarium sheets!")
        print("="*70)

if __name__ == "__main__":
    downloader = JSTORPlantsDownloader()
    downloader.run()
