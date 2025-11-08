#!/usr/bin/env python3
"""
Botanical Illustration Downloader for Orchid Continuum
Downloads historical orchid botanical plates from multiple sources
Runs on Replit server to avoid Mac environment issues
"""
import os
import time
import requests
import zipfile
import csv
from pathlib import Path
from datetime import datetime

# Setup directories
DOWNLOAD_DIR = Path("attached_assets/botanical_illustrations")
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Attribution CSV
CSV_FILE = DOWNLOAD_DIR / "botanical_illustrations_attribution.csv"
if not CSV_FILE.exists():
    with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
        csv.writer(f).writerow([
            'filename', 'book_title', 'author', 'year', 'page_number',
            'source', 'license', 'source_url', 'download_date'
        ])

session = requests.Session()
session.headers.update({'User-Agent': 'OrchidContinuum/1.0 (Educational Research)'})

print("=" * 80)
print("🎨 BOTANICAL ILLUSTRATION DOWNLOADER - Replit Server")
print("=" * 80)
print(f"Download directory: {DOWNLOAD_DIR.absolute()}")
print(f"Attribution file: {CSV_FILE.absolute()}\n")

# Strategy 1: Try direct download of known orchid botanical plates from Wikimedia
print("\n📥 STRATEGY 1: Direct Wikimedia URLs")
print("-" * 80)

wikimedia_plates = [
    {
        'url': 'https://upload.wikimedia.org/wikipedia/commons/8/8f/Cattleya_labiata_-_Edwards_vol_33_pl_3998_%281847%29.jpg',
        'title': "Cattleya labiata - Curtis's Botanical Magazine",
        'author': 'Walter Hood Fitch',
        'year': '1847'
    },
    {
        'url': 'https://upload.wikimedia.org/wikipedia/commons/0/0c/Paphiopedilum_insigne_-_Curtis%27_101_%28Ser._3_no._31%29_pl._6152_%281875%29.jpg',
        'title': "Paphiopedilum insigne - Curtis's Botanical Magazine",
        'author': 'Walter Hood Fitch',
        'year': '1875'
    },
    {
        'url': 'https://upload.wikimedia.org/wikipedia/commons/f/fc/Dendrobium_nobile_-_Edwards_vol_19_pl_1580_%281833%29.jpg',
        'title': "Dendrobium nobile - Curtis's Botanical Magazine",
        'author': 'Sydenham Edwards',
        'year': '1833'
    },
    {
        'url': 'https://upload.wikimedia.org/wikipedia/commons/b/b3/Vanda_coerulea_-_Bot._Reg._33_pl._67_%281847%29.jpg',
        'title': 'Vanda coerulea - Botanical Register',
        'author': 'Unknown',
        'year': '1847'
    }
]

wikimedia_count = 0
for idx, plate in enumerate(wikimedia_plates, 1):
    fname = f"wikimedia_orchid_{idx:03d}.jpg"
    dest = DOWNLOAD_DIR / fname
    
    if dest.exists():
        print(f"  {idx}. {plate['title'][:50]}... ⏭️  (already exists)")
        wikimedia_count += 1
        continue
    
    try:
        print(f"  {idx}. {plate['title'][:50]}...", end=' ', flush=True)
        r = session.get(plate['url'], timeout=30)
        
        if r.status_code == 200 and len(r.content) > 5000:
            with open(dest, 'wb') as f:
                f.write(r.content)
            
            with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
                csv.writer(f).writerow([
                    fname, plate['title'], plate['author'], plate['year'], idx,
                    'Wikimedia Commons', 'Public Domain', plate['url'],
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ])
            
            wikimedia_count += 1
            print(f"✅ ({len(r.content) // 1024} KB)")
            time.sleep(0.5)
        else:
            print(f"❌ Failed (HTTP {r.status_code})")
    except Exception as e:
        print(f"❌ Error: {e}")

print(f"\n✅ Wikimedia: {wikimedia_count} illustrations downloaded")

# Strategy 2: Download from Internet Archive using direct item page scraping
print("\n📥 STRATEGY 2: Internet Archive Direct Page Downloads")
print("-" * 80)

# Known working Internet Archive item with viewable images
ia_items = [
    {
        'id': 'mobot31753003528727',  # Lindenia alternative ID
        'title': 'Lindenia: Iconographie des Orchidées',
        'author': 'Linden',
        'year': '1885'
    }
]

ia_count = 0
for item in ia_items:
    print(f"\n  📖 {item['title']}")
    
    # Try to get list of files
    try:
        meta_url = f"https://archive.org/metadata/{item['id']}/files"
        resp = session.get(meta_url, timeout=30)
        
        if resp.status_code == 200:
            data = resp.json()
            
            # Look for image files
            image_files = []
            for file_info in data.get('result', []):
                name = file_info.get('name', '')
                if any(ext in name.lower() for ext in ['.jpg', '.jpeg', '.jp2', '.png']):
                    if '_jp2' not in name and 'thumb' not in name.lower():
                        image_files.append(name)
            
            print(f"     Found {len(image_files)} image files")
            
            # Download first 10 as test
            for idx, img_name in enumerate(image_files[:10], 1):
                img_url = f"https://archive.org/download/{item['id']}/{img_name}"
                fname = f"ia_{item['id'][:15]}_p{idx:03d}.jpg"
                dest = DOWNLOAD_DIR / fname
                
                if dest.exists():
                    ia_count += 1
                    continue
                
                try:
                    print(f"     {idx}. Page {idx}...", end=' ', flush=True)
                    r = session.get(img_url, timeout=30)
                    
                    if r.status_code == 200 and len(r.content) > 10000:
                        with open(dest, 'wb') as f:
                            f.write(r.content)
                        
                        with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
                            csv.writer(f).writerow([
                                fname, item['title'], item['author'], item['year'], idx,
                                'Internet Archive', 'Public Domain',
                                f"https://archive.org/details/{item['id']}/page/n{idx}",
                                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            ])
                        
                        ia_count += 1
                        print(f"✅ ({len(r.content) // 1024} KB)")
                        time.sleep(0.5)
                    else:
                        print(f"❌ Failed")
                except Exception as e:
                    print(f"❌ Error: {e}")
        else:
            print(f"     ❌ Could not access metadata (HTTP {resp.status_code})")
    except Exception as e:
        print(f"     ❌ Error: {e}")

print(f"\n✅ Internet Archive: {ia_count} illustrations downloaded")

# Summary
print("\n" + "=" * 80)
print("📊 DOWNLOAD SUMMARY")
print("=" * 80)
total = wikimedia_count + ia_count
print(f"Total illustrations downloaded: {total}")
print(f"Location: {DOWNLOAD_DIR.absolute()}")
print(f"Attribution data: {CSV_FILE.absolute()}")

if total > 0:
    print("\n✅ SUCCESS! Botanical illustrations are ready for BloomBuilder!")
else:
    print("\n⚠️  No illustrations downloaded - investigating alternative sources...")
