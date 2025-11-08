#!/usr/bin/env python3
"""
Wikimedia Commons Botanical Illustration Downloader
Downloads historical orchid botanical plates with full attribution
"""
import os, time, requests, csv, json
from pathlib import Path
from urllib.parse import quote

out_dir = Path(os.path.expanduser("~/orchid_downloads/botanical_illustrations"))
out_dir.mkdir(parents=True, exist_ok=True)

csv_file = Path(os.path.expanduser("~/orchid_downloads/botanical_illustrations_attribution.csv"))
if not csv_file.exists():
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        csv.writer(f).writerow([
            'filename', 'title', 'artist', 'date_created', 'source_book', 
            'institution', 'description', 'license', 'wikimedia_url', 
            'high_res_url', 'local_filename'
        ])

print("🎨 WIKIMEDIA COMMONS BOTANICAL ILLUSTRATION DOWNLOADER")
print("Downloading historical orchid botanical plates\n")

session = requests.Session()
session.headers.update({'User-Agent': 'OrchidContinuum/1.0'})

# Search categories for orchid illustrations
search_terms = [
    "Orchidaceae botanical illustration",
    "Orchid botanical plate",
    "Orchidaceae Curtis botanical",
    "Orchid Lindley illustration",
    "Orchidaceae herbarium illustration"
]

total_downloaded = 0
target = 5000

for search_term in search_terms:
    print(f"\n🔍 Searching: {search_term}")
    
    # Wikimedia Commons API search
    params = {
        'action': 'query',
        'format': 'json',
        'generator': 'search',
        'gsrsearch': f'filetype:bitmap {search_term}',
        'gsrlimit': 50,
        'prop': 'imageinfo',
        'iiprop': 'url|extmetadata|size',
        'iiurlwidth': 2000
    }
    
    try:
        resp = session.get('https://commons.wikimedia.org/w/api.php', params=params, timeout=30)
        data = resp.json()
        
        if 'query' not in data or 'pages' not in data['query']:
            print("  No results found")
            continue
        
        pages = data['query']['pages']
        count = 0
        
        for page_id, page in pages.items():
            if 'imageinfo' not in page:
                continue
            
            info = page['imageinfo'][0]
            
            # Get metadata
            meta = info.get('extmetadata', {})
            artist = meta.get('Artist', {}).get('value', 'Unknown')
            date_created = meta.get('DateTimeOriginal', {}).get('value', '')
            description = meta.get('ImageDescription', {}).get('value', '')
            license_name = meta.get('LicenseShortName', {}).get('value', 'Public Domain')
            credit = meta.get('Credit', {}).get('value', '')
            
            # Clean HTML tags from artist/description
            import re
            artist = re.sub('<[^<]+?>', '', artist)
            description = re.sub('<[^<]+?>', '', description)[:500]
            
            # Get high-res image URL
            image_url = info.get('url', '')
            if not image_url:
                continue
            
            # Create filename
            title = page.get('title', '').replace('File:', '').replace(' ', '_')[:100]
            fname = f"botanical_{total_downloaded}_{title}"
            if not fname.lower().endswith(('.jpg', '.png', '.jpeg')):
                fname += '.jpg'
            
            dest = out_dir / fname
            
            if dest.exists():
                continue
            
            try:
                print(f"  Downloading: {title[:60]}...")
                r = session.get(image_url, timeout=30)
                
                if r.status_code == 200:
                    with open(dest, "wb") as f:
                        f.write(r.content)
                    
                    # Save attribution data
                    with open(csv_file, 'a', newline='', encoding='utf-8') as f:
                        csv.writer(f).writerow([
                            fname,
                            page.get('title', ''),
                            artist,
                            date_created,
                            credit,
                            'Wikimedia Commons',
                            description,
                            license_name,
                            f"https://commons.wikimedia.org/wiki/{quote(page.get('title', ''))}",
                            image_url,
                            fname
                        ])
                    
                    count += 1
                    total_downloaded += 1
                    print(f"  ✅ {total_downloaded:,} total | Artist: {artist[:40]}")
                    time.sleep(0.3)
                    
                    if total_downloaded >= target:
                        break
                        
            except Exception as e:
                print(f"  Error: {e}")
        
        print(f"\n✅ Found {count} illustrations for '{search_term}'")
        time.sleep(2)
        
        if total_downloaded >= target:
            break
            
    except Exception as e:
        print(f"Search error: {e}")
        time.sleep(5)

print(f"\n🎉 COMPLETE! Downloaded {total_downloaded:,} botanical illustrations")
print(f"📁 Location: {out_dir}")
print(f"📊 Attribution data: {csv_file}")
