#!/usr/bin/env python3
"""
iDigBio Orchid Herbarium Specimen Downloader - Mac Version
Downloads ~300,000 orchid specimens from US museums with images

FEATURES:
- Missouri Botanical Garden, Smithsonian, Harvard, New York Botanical Garden
- High-resolution herbarium specimen scans
- Complete specimen metadata (collector, date, location, institution)
- All CC-licensed images

SETUP (one time):
    pip3 install requests

USAGE:
    python3 EASY_Mac_iDigBio_Downloader.py

The script will:
- Create folder: ~/orchid_downloads/idigbio_herbarium/
- Download Darwin Core Archive from iDigBio
- Extract specimen images with full metadata
- Save data to: idigbio_specimens.csv
"""

import requests
import json
import time
import os
import zipfile
import csv
from pathlib import Path

class iDigBioDownloader:
    def __init__(self):
        # Create folder in user's home directory
        home = str(Path.home())
        self.base_dir = os.path.join(home, "orchid_downloads")
        self.output_dir = os.path.join(self.base_dir, "idigbio_herbarium")
        self.temp_dir = os.path.join(self.base_dir, "temp")
        self.csv_file = os.path.join(self.base_dir, "idigbio_specimens.csv")
        
        # Auto-create directories
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)
        
        self.downloaded_count = 0
        self.species_set = set()
        
        print(f"\n✅ Created folder: {self.base_dir}")
        print(f"✅ Images will save to: {self.output_dir}")
        print(f"✅ Data will save to: {self.csv_file}\n")
        
        self.init_csv()
    
    def init_csv(self):
        """Initialize CSV with comprehensive specimen fields"""
        with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                # SPECIMEN IDs
                'uuid', 'catalog_number', 'institution_code', 'collection_code',
                'occurrence_id', 'record_id',
                # TAXONOMY
                'kingdom', 'phylum', 'class', 'order', 'family', 
                'genus', 'species', 'subspecies', 'variety',
                'scientific_name', 'scientific_name_author', 'taxon_rank',
                'common_name', 'taxon_id',
                # SPECIMEN INFO
                'basis_of_record', 'type_status', 'preparations',
                # COLLECTION
                'recorded_by', 'collector_number', 'identified_by',
                'date_identified', 'collection_date', 'year', 'month', 'day',
                # LOCATION
                'country', 'state_province', 'county', 'locality',
                'latitude', 'longitude', 'coordinate_uncertainty', 'geodetic_datum',
                'elevation_m', 'depth_m', 'habitat',
                # IMAGES
                'has_image', 'image_url', 'image_filename', 'license', 'rights_holder',
                # METADATA
                'data_source', 'modified_date', 'references'
            ])
        print(f"✅ Created: {self.csv_file}")
    
    def request_download(self):
        """Request iDigBio to prepare download"""
        print("\n" + "="*70)
        print("📥 REQUESTING DOWNLOAD FROM iDigBio")
        print("="*70)
        print("Query: All Orchidaceae specimens with images")
        print("Requesting archive preparation...")
        
        # Build query for orchids with images
        query = {
            "family": "orchidaceae",
            "hasImage": True
        }
        
        params = {
            "rq": json.dumps(query)
        }
        
        try:
            response = requests.get(
                "https://api.idigbio.org/v2/download/",
                params=params,
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                status_url = data.get('status_url')
                print(f"✅ Download request accepted!")
                print(f"📊 Status URL: {status_url}")
                return status_url
            else:
                print(f"❌ Error {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
            return None
    
    def poll_status(self, status_url, max_wait_minutes=30):
        """Poll status endpoint until download is ready"""
        print("\n⏳ Waiting for archive to be prepared...")
        print(f"   (This may take up to {max_wait_minutes} minutes for large datasets)")
        
        start_time = time.time()
        max_wait_seconds = max_wait_minutes * 60
        check_count = 0
        
        while True:
            check_count += 1
            elapsed = int(time.time() - start_time)
            
            try:
                response = requests.get(status_url, timeout=30)
                data = response.json()
                
                if data.get('complete'):
                    download_url = data.get('download_url')
                    print(f"\n✅ Archive ready! ({elapsed}s elapsed)")
                    print(f"📦 Download URL: {download_url}")
                    return download_url
                
                task_status = data.get('task_status', 'UNKNOWN')
                print(f"   [{elapsed}s] Check #{check_count}: {task_status}...", end='\r')
                
                if elapsed > max_wait_seconds:
                    print(f"\n❌ Timeout after {max_wait_minutes} minutes")
                    return None
                
                time.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                print(f"\n❌ Status check failed: {e}")
                return None
    
    def download_archive(self, download_url):
        """Download the Darwin Core Archive ZIP file"""
        print("\n📦 Downloading Darwin Core Archive...")
        
        zip_path = os.path.join(self.temp_dir, "idigbio_orchids.zip")
        
        try:
            response = requests.get(download_url, stream=True, timeout=300)
            total_size = int(response.headers.get('content-length', 0))
            
            with open(zip_path, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            mb = downloaded / 1024 / 1024
                            print(f"   Downloaded: {mb:.1f} MB ({percent:.1f}%)", end='\r')
            
            print(f"\n✅ Archive downloaded: {zip_path}")
            return zip_path
            
        except Exception as e:
            print(f"\n❌ Download failed: {e}")
            return None
    
    def extract_archive(self, zip_path):
        """Extract Darwin Core Archive"""
        print("\n📂 Extracting archive...")
        
        extract_dir = os.path.join(self.temp_dir, "extracted")
        os.makedirs(extract_dir, exist_ok=True)
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            print(f"✅ Extracted to: {extract_dir}")
            
            # List all extracted files
            print("📋 Files in archive:")
            all_files = []
            for root, dirs, files in os.walk(extract_dir):
                for file in files:
                    full_path = os.path.join(root, file)
                    all_files.append(full_path)
                    print(f"  - {file}")
            
            # Look for occurrence and multimedia files (try different names/locations)
            occurrence_file = None
            multimedia_file = None
            
            for filepath in all_files:
                filename = os.path.basename(filepath).lower()
                # iDigBio uses .csv files (not .txt)
                if 'occurrence' in filename and (filename.endswith('.csv') or filename.endswith('.txt')):
                    if 'raw' not in filename:  # Prefer processed version
                        occurrence_file = filepath
                        print(f"✅ Found occurrence file: {filepath}")
                if 'multimedia' in filename and (filename.endswith('.csv') or filename.endswith('.txt')):
                    if 'raw' not in filename:  # Prefer processed version
                        multimedia_file = filepath
                        print(f"✅ Found multimedia file: {filepath}")
            
            return {
                'occurrence': occurrence_file,
                'multimedia': multimedia_file
            }
            
        except Exception as e:
            print(f"❌ Extraction failed: {e}")
            return None
    
    def download_image(self, url, filename):
        """Download specimen image"""
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                filepath = os.path.join(self.output_dir, filename)
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                return True
            return False
        except:
            return False
    
    def process_data(self, files):
        """Process occurrence and multimedia files"""
        print("\n" + "="*70)
        print("📊 PROCESSING SPECIMEN DATA")
        print("="*70)
        
        if not files or not files.get('occurrence'):
            print("❌ No occurrence data found")
            return
        
        # Load multimedia data (images)
        image_map = {}
        if files.get('multimedia'):
            print(f"📸 Loading image data from: {files['multimedia']}")
            try:
                # iDigBio uses comma-separated CSV (not tab-delimited)
                with open(files['multimedia'], 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        core_id = row.get('coreid', '')
                        if core_id:
                            if core_id not in image_map:
                                image_map[core_id] = []
                            image_map[core_id].append({
                                'url': row.get('accessURI', ''),
                                'license': row.get('license', ''),
                                'rights': row.get('rightsHolder', '')
                            })
                print(f"✅ Loaded {len(image_map):,} image records")
            except Exception as e:
                print(f"⚠️ Could not load image data: {e}")
        
        # Process occurrence data
        print(f"🌺 Processing specimens from: {files['occurrence']}")
        
        try:
            # iDigBio uses comma-separated CSV (not tab-delimited)
            with open(files['occurrence'], 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                processed = 0
                for row in reader:
                    # Get specimen UUID
                    uuid = row.get('id', row.get('occurrenceID', ''))
                    if not uuid:
                        continue
                    
                    # Get species name
                    species = row.get('scientificName', '')
                    genus = row.get('genus', '')
                    
                    if not species or not genus:
                        continue
                    
                    # Get images for this specimen
                    images = image_map.get(uuid, [])
                    if not images:
                        continue  # Skip specimens without images
                    
                    # Download images
                    for idx, img in enumerate(images):
                        img_url = img.get('url', '')
                        if not img_url:
                            continue
                        
                        safe_name = species.replace(' ', '_').replace('/', '-')
                        filename = f"{uuid}_{safe_name}_{idx+1}.jpg"
                        
                        print(f"  📥 {species} ({self.downloaded_count + 1})", end='\r')
                        
                        if self.download_image(img_url, filename):
                            # Write to CSV
                            with open(self.csv_file, 'a', newline='', encoding='utf-8') as csv_f:
                                writer = csv.writer(csv_f)
                                writer.writerow([
                                    uuid,
                                    row.get('catalogNumber', ''),
                                    row.get('institutionCode', ''),
                                    row.get('collectionCode', ''),
                                    row.get('occurrenceID', ''),
                                    row.get('id', ''),
                                    row.get('kingdom', ''),
                                    row.get('phylum', ''),
                                    row.get('class', ''),
                                    row.get('order', ''),
                                    row.get('family', ''),
                                    row.get('genus', ''),
                                    row.get('specificEpithet', ''),
                                    row.get('infraspecificEpithet', ''),
                                    row.get('variety', ''),
                                    row.get('scientificName', ''),
                                    row.get('scientificNameAuthorship', ''),
                                    row.get('taxonRank', ''),
                                    row.get('vernacularName', ''),
                                    row.get('taxonID', ''),
                                    row.get('basisOfRecord', ''),
                                    row.get('typeStatus', ''),
                                    row.get('preparations', ''),
                                    row.get('recordedBy', ''),
                                    row.get('recordNumber', ''),
                                    row.get('identifiedBy', ''),
                                    row.get('dateIdentified', ''),
                                    row.get('eventDate', ''),
                                    row.get('year', ''),
                                    row.get('month', ''),
                                    row.get('day', ''),
                                    row.get('country', ''),
                                    row.get('stateProvince', ''),
                                    row.get('county', ''),
                                    row.get('locality', ''),
                                    row.get('decimalLatitude', ''),
                                    row.get('decimalLongitude', ''),
                                    row.get('coordinateUncertaintyInMeters', ''),
                                    row.get('geodeticDatum', ''),
                                    row.get('minimumElevationInMeters', ''),
                                    row.get('minimumDepthInMeters', ''),
                                    row.get('habitat', ''),
                                    'true',
                                    img_url,
                                    filename,
                                    img.get('license', ''),
                                    img.get('rights', ''),
                                    row.get('datasetName', ''),
                                    row.get('modified', ''),
                                    row.get('references', '')
                                ])
                            
                            self.downloaded_count += 1
                            self.species_set.add(species)
                            time.sleep(0.1)
                    
                    processed += 1
                    if processed % 100 == 0:
                        print(f"\n  ✅ Processed: {processed:,} specimens, {self.downloaded_count:,} images")
                
                print(f"\n✅ Processing complete!")
                
        except Exception as e:
            print(f"❌ Processing failed: {e}")
    
    def run(self):
        """Main download process"""
        print("\n" + "="*70)
        print("🏛️  iDigBio Orchid Herbarium Downloader")
        print("="*70)
        print("Data source: US museums (MOBOT, Smithsonian, Harvard, NYBG)")
        print("Target: ~300,000 orchid specimens with images")
        print("="*70)
        
        # Step 1: Request download
        status_url = self.request_download()
        if not status_url:
            print("❌ Failed to request download")
            return
        
        # Step 2: Wait for archive to be ready
        download_url = self.poll_status(status_url)
        if not download_url:
            print("❌ Failed to get download URL")
            return
        
        # Step 3: Download archive
        zip_path = self.download_archive(download_url)
        if not zip_path:
            print("❌ Failed to download archive")
            return
        
        # Step 4: Extract archive
        files = self.extract_archive(zip_path)
        if not files:
            print("❌ Failed to extract archive")
            return
        
        # Step 5: Process data and download images
        self.process_data(files)
        
        # Final summary
        print("\n" + "="*70)
        print("🎉 DOWNLOAD COMPLETE!")
        print("="*70)
        print(f"✅ Downloaded: {self.downloaded_count:,} herbarium images")
        print(f"✅ Species: {len(self.species_set):,}")
        print(f"📁 Images: {self.output_dir}")
        print(f"📊 Data: {self.csv_file}")
        print("="*70 + "\n")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("🏛️  WELCOME TO iDigBio HERBARIUM DOWNLOADER")
    print("="*70)
    print("This will download orchid herbarium specimens to:")
    print("  ~/orchid_downloads/idigbio_herbarium/")
    print("\nSource: US museum collections")
    print("Target: ~300,000 specimens with high-res images")
    print("Estimated time: 1-2 hours")
    print("Estimated storage: 20-40 GB")
    print("="*70)
    
    input("\nPress Enter to start downloading, or Ctrl+C to exit...")
    
    downloader = iDigBioDownloader()
    downloader.run()
