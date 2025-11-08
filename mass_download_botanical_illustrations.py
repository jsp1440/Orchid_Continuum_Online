#!/usr/bin/env python3
"""
Mass Download Botanical Illustrations from Internet Archive
Downloads multiple orchid book ZIP archives and converts to JPG
"""
import os
import time
import requests
from PIL import Image
from pathlib import Path
import zipfile

OUT_DIR = Path("attached_assets/botanical_illustrations")
OUT_DIR.mkdir(parents=True, exist_ok=True)

session = requests.Session()
session.headers.update({'User-Agent': 'OrchidContinuum/1.0 (Educational Research)'})

# List of orchid books with ZIP archives on Internet Archive
ORCHID_BOOKS = [
    {
        'id': 'reichenbachia00sand',
        'title': 'Reichenbachia: Orchids Illustrated - Series 1',
        'zip_url': 'https://archive.org/download/reichenbachia00sand/reichenbachia00sand_jp2.zip'
    },
    {
        'id': 'mobot31753003528727',
        'title': 'Lindenia: Iconographie des Orchidées Vol 1',
        'zip_url': 'https://archive.org/download/mobot31753003528727/mobot31753003528727_jp2.zip'
    },
    {
        'id': 'mobot31753003528735',
        'title': 'Lindenia: Iconographie des Orchidées Vol 2',
        'zip_url': 'https://archive.org/download/mobot31753003528735/mobot31753003528735_jp2.zip'
    },
    {
        'id': 'orchidalbumcomp01warn',
        'title': 'The Orchid Album Vol 1',
        'zip_url': 'https://archive.org/download/orchidalbumcomp01warn/orchidalbumcomp01warn_jp2.zip'
    },
    {
        'id': 'orchidalbumcomp02warn',
        'title': 'The Orchid Album Vol 2',
        'zip_url': 'https://archive.org/download/orchidalbumcomp02warn/orchidalbumcomp02warn_jp2.zip'
    }
]

total_downloaded = 0
total_converted = 0

print("=" * 80)
print("🎨 MASS BOTANICAL ILLUSTRATION DOWNLOADER")
print("=" * 80)
print(f"Target: {len(ORCHID_BOOKS)} orchid books")
print(f"Output directory: {OUT_DIR.absolute()}\n")

for idx, book in enumerate(ORCHID_BOOKS, 1):
    print(f"\n📚 [{idx}/{len(ORCHID_BOOKS)}] {book['title']}")
    print("-" * 80)
    
    zip_file = OUT_DIR / f"{book['id']}.zip"
    extract_dir = OUT_DIR / f"{book['id']}_jp2"
    
    # Download ZIP if not already downloaded
    if not zip_file.exists():
        print(f"  ⬇️  Downloading ZIP archive...", end=' ', flush=True)
        try:
            resp = session.get(book['zip_url'], timeout=180, stream=True)
            
            if resp.status_code == 200:
                with open(zip_file, 'wb') as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                size_mb = zip_file.stat().st_size / (1024 * 1024)
                print(f"✅ ({size_mb:.1f} MB)")
                total_downloaded += 1
            else:
                print(f"❌ HTTP {resp.status_code}")
                continue
        except Exception as e:
            print(f"❌ Error: {e}")
            continue
    else:
        print(f"  ⏭️  ZIP already downloaded")
    
    # Extract ZIP
    print(f"  📦 Extracting images...", end=' ', flush=True)
    try:
        with zipfile.ZipFile(zip_file, 'r') as zf:
            zf.extractall(OUT_DIR)
            jp2_files = [f for f in zf.namelist() if f.lower().endswith('.jp2')]
            print(f"✅ ({len(jp2_files)} JP2 files)")
    except Exception as e:
        print(f"❌ Error: {e}")
        continue
    
    # Convert JP2 to JPG
    print(f"  🔄 Converting to JPG...", flush=True)
    if extract_dir.exists():
        converted = 0
        for jp2_file in extract_dir.glob('*.jp2'):
            jpg_file = OUT_DIR / f"{book['id']}_{jp2_file.stem}.jpg"
            
            if jpg_file.exists():
                converted += 1
                continue
            
            try:
                img = Image.open(jp2_file)
                img.convert('RGB').save(jpg_file, 'JPEG', quality=90)
                converted += 1
                
                if converted % 10 == 0:
                    print(f"     Progress: {converted} images converted", flush=True)
                
            except Exception as e:
                print(f"     ❌ Error converting {jp2_file.name}: {e}")
        
        total_converted += converted
        print(f"  ✅ Converted {converted} botanical plates to JPG")
    
    # Cleanup: Delete ZIP to save space
    if zip_file.exists():
        zip_file.unlink()
        print(f"  🗑️  Deleted ZIP to save space")
    
    time.sleep(2)

print("\n" + "=" * 80)
print("📊 FINAL SUMMARY")
print("=" * 80)
print(f"Books processed: {len(ORCHID_BOOKS)}")
print(f"ZIPs downloaded: {total_downloaded}")
print(f"Total botanical illustrations: {total_converted}")
print(f"Location: {OUT_DIR.absolute()}")

# Count final JPG files
jpg_files = list(OUT_DIR.glob('*.jpg'))
print(f"\n✅ Final count: {len(jpg_files)} JPG botanical illustrations ready for BloomBuilder!")
