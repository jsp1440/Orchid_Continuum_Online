case        """Create necessary directories"""
        for directory in [self.base_dir, self.output_dir, self.temp_dir]:
            os.makedirs(directory, exist_ok=True)
            if directory == self.base_dir:
                print(f"✅ Created folder: {directory}")
        
        print(f"✅ Images will save to: {self.output_dir}")
        print(f"✅ Data will save to: {self.csv_file}")
        
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'uuid', 'catalog_number', 'institution', 'collection',
                    'occurrence_id', 'idigbio_uuid', 'kingdom', 'phylum', 'class',
                    'order', 'family', 'genus', 'species', 'scientific_name',
                    'collector', 'collection_date', 'country', 'state', 'locality',
                    'latitude', 'longitude', 'image_url', 'license', 'rights_holder',
                    'filename'
                ])
            print(f"\n✅ Created: {self.csv_file}")
    
    def request_download(self):
        """Request download from iDigBio API"""
        print("\n" + "="*70)
        print("📥 REQUESTING DOWNLOAD FROM iDigBio")
        print("="*70)
        
        url = "https://search.idigbio.org/v2/download/"
        
        query = {
            "rq": {
                "family": "orchidaceae",
                "hasImage": True
            }
        }
        
        print("Query: All Orchidaceae specimens with images")
        print("Requesting archive preparation...")
        
        try:
            response = requests.post(url, json=query)
            response.raise_for_status()
            
            result = response.json()
            download_key = result.get('download_key')
            
            if not download_key:
                print("❌ Failed to get download key")
                return None
            
            print("✅ Download request accepted!")
            print(f"📊 Status URL: https://api.idigbio.org/v2/download/{download_key}")
            
            return download_key
            
        except Exception as e:
            print(f"❌ Request failed: {e}")
            return None
    
    def wait_for_archive(self, download_key):
        """Wait for archive to be ready"""
        print("\n⏳ Waiting for archive to be prepared...")
        print("   (This may take up to 30 minutes for large datasets)")
        
        status_url = f"https://api.idigbio.org/v2/download/{download_key}"
        
        start_time = time.time()
        while True:
            try:
                response = requests.get(status_url)
                status = response.json()
                
                if status.get('status') == 'COMPLETE':
                    elapsed = int(time.time() - start_time)
                    print(f"\n✅ Archive ready! ({elapsed}s elapsed)")
                    download_url = f"https://s.idigbio.org/idigbio-downloads/{download_key}.zip"
                    print(f"📦 Download URL: {download_url}")
                    return download_url
                
                elif status.get('status') == 'FAILED':
                    print("\n❌ Archive preparation failed")
                    return None
                
                time.sleep(10)
                
            except Exception as e:
                print(f"\n❌ Status check failed: {e}")
                return None
    
    def download_archive(self, download_url):
        """Download the archive file"""
        print("\n📦 Downloading Darwin Core Archive...")
        
        zip_path = os.path.join(self.temp_dir, "idigbio_orchids.zip")
        
        try:
            response = requests.get(download_url, stream=True)
            response.raise_for_status()
            
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
            
            print("📋 Files in archive:")
            all_files = []
            for root, dirs, files in os.walk(extract_dir):
                for file in files:
                    full_path = os.path.join(root, file)
                    all_files.append(full_path)
                    print(f"  - {file}")
            
            occurrence_file = None
            multimedia_file = None
            
            for filepath in all_files:
                filename = os.path.basename(filepath).lower()
                if 'occurrence' in filename and (filename.endswith('.csv') or filename.endswith('.txt')):
                    if 'raw' not in filename:
                        occurrence_file = filepath
                        print(f"✅ Found occurrence file: {filepath}")
                if 'multimedia' in filename and (filename.endswith('.csv') or filename.endswith('.txt')):
                    if 'raw' not in filename:
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
        
        image_map = {}
        if files.get('multimedia'):
            print(f"📸 Loading image data from: {files['multimedia']}")
            try:
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
        
        print(f"🌺 Processing specimens from: {files['occurrence']}")
        
        try:
            with open(files['occurrence'], 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                processed = 0
                for row in reader:
                    uuid = row.get('id', row.get('occurrenceID', ''))
                    if not uuid:
                        continue
                    
                    species = row.get('scientificName', '')
                    genus = row.get('genus', '')
                    
                    if not species or not genus:
                        continue
                    
                    images = image_map.get(uuid, [])
                    if not images:
                        continue
                    
                    for idx, img in enumerate(images):
                        img_url = img.get('url', '')
                        if not img_url:
                            continue
                        
                        safe_name = species.replace(' ', '_').replace('/', '-')
                        filename = f"{uuid}_{safe_name}_{idx+1}.jpg"
                        
                        print(f"  📥 {species} ({self.downloaded_count + 1})", end='\r')
                        
                        if self.download_image(img_url, filename):
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
                                    species,
                                    row.get('recordedBy', ''),
                                    row.get('eventDate', ''),
                                    row.get('country', ''),
                                    row.get('stateProvince', ''),
                                    row.get('locality', ''),
                                    row.get('decimalLatitude', ''),
                                    row.get('decimalLongitude', ''),
                                    img_url,
                                    img.get('license', ''),
                                    img.get('rights', ''),
                                    filename
                                ])
                            
                            self.downloaded_count += 1
                            self.species_set.add(species)
                            
                            processed += 1
                            if processed % 100 == 0:
                                print(f"\n  ✅ Processed: {processed:,} specimens, {len(self.species_set):,} species")
                        
                        time.sleep(0.2)
                    
        except Exception as e:
            print(f"\n❌ Processing failed: {e}")
    
    def run(self):
        """Main execution"""
        print("="*70)
        print("🏛️  WELCOME TO iDigBio HERBARIUM DOWNLOADER")
        print("="*70)
        print("This will download orchid herbarium specimens to:")
        print(f"  ~/orchid_downloads/idigbio_herbarium/")
        print()
        print("Source: US museum collections")
        print("Target: ~300,000 specimens with high-res images")
        print("Estimated time: 1-2 hours")
        print("Estimated storage: 20-40 GB")
        print("="*70)
        print()
        
        input("Press Enter to start downloading, or Ctrl+C to exit...")
        
        self.setup()
        
        print("\n" + "="*70)
        print("🏛️  iDigBio Orchid Herbarium Downloader")
        print("="*70)
        print("Data source: US museums (MOBOT, Smithsonian, Harvard, NYBG)")
        print("Target: ~300,000 orchid specimens with images")
        print("="*70)
        
        download_key = self.request_download()
        if not download_key:
            return
        
        download_url = self.wait_for_archive(download_key)
        if not download_url:
            return
        
        zip_path = self.download_archive(download_url)
        if not zip_path:
            return
        
        files = self.extract_archive(zip_path)
        if not files:
            return
        
        self.process_data(files)
        
        print("\n" + "="*70)
        print("🎉 DOWNLOAD COMPLETE!")
        print("="*70)
        print(f"✅ Downloaded: {self.downloaded_count:,} herbarium images")
        print(f"✅ Species: {len(self.species_set):,}")
        print(f"📁 Images: {self.output_dir}")
        print(f"📊 Data: {self.csv_file}")
        print("="*70)

if __name__ == "__main__":
    downloader = iDigBioDownloader()
    downloader.run()
