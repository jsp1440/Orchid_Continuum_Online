#!/usr/bin/env python3
"""
Biodiversity Heritage Library (BHL) Orchid Illustration Downloader
Downloads historical botanical plates from digitized books
"""
import os, time, requests, csv
from pathlib import Path

out_dir = Path(os.path.expanduser("~/orchid_downloads/bhl_botanical_plates"))
out_dir.mkdir(parents=True, exist_ok=True)

csv_file = Path(os.path.expanduser("~/orchid_downloads/bhl_botanical_plates_attribution.csv"))
if not csv_file.exists():
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        csv.writer(f).writerow([
            'page_id', 'book_title', 'author', 'publication_year', 'publisher',
            'volume', 'page_number', 'illustration_type', 'institution',
            'bhl_url', 'image_url', 'local_filename'
        ])

print("📚 BIODIVERSITY HERITAGE LIBRARY DOWNLOADER")
print("Downloading historical orchid botanical plates from digitized books\n")

session = requests.Session()
session.headers.update({'User-Agent': 'OrchidContinuum/1.0'})

# BHL API key (public, no registration needed)
api_key = 'bbe34ec1-80bc-4f36-b45d-04c8ff4e9f85'

# Search for orchid-related titles
search_terms = ['orchidaceae', 'orchid', 'orchideae']
total_downloaded = 0
target = 10000

for search in search_terms:
    print(f"\n🔍 Searching BHL for: {search}")
    
    # Search for titles
    params = {
        'op': 'TitleSearchSimple',
        'searchterm': search,
        'format': 'json',
        'apikey': api_key
    }
    
    try:
        resp = session.get('https://www.biodiversitylibrary.org/api3', params=params, timeout=30)
        data = resp.json()
        
        if 'Result' not in data:
            continue
        
        titles = data['Result'][:20]  # Limit to 20 books per search term
        
        for title in titles:
            title_id = title.get('TitleID')
            title_name = title.get('FullTitle', 'Unknown')
            
            print(f"\n📖 Book: {title_name[:60]}")
            
            # Get items (volumes) for this title
            item_params = {
                'op': 'GetTitleMetadata',
                'id': title_id,
                'items': 't',
                'format': 'json',
                'apikey': api_key
            }
            
            item_resp = session.get('https://www.biodiversitylibrary.org/api3', params=item_params, timeout=30)
            item_data = item_resp.json()
            
            if 'Result' not in item_data or not item_data['Result']:
                continue
            
            items = item_data['Result'][0].get('Items', [])[:5]  # Limit to 5 volumes
            
            for item in items:
                item_id = item.get('ItemID')
                volume = item.get('Volume', '')
                
                # Get pages with illustrations
                page_params = {
                    'op': 'GetItemMetadata',
                    'id': item_id,
                    'pages': 't',
                    'format': 'json',
                    'apikey': api_key
                }
                
                page_resp = session.get('https://www.biodiversitylibrary.org/api3', params=page_params, timeout=30)
                page_data = page_resp.json()
                
                if 'Result' not in page_data or not page_data['Result']:
                    continue
                
                pages = page_data['Result'][0].get('Pages', [])
                
                # Filter for illustration pages only
                for page in pages:
                    page_types = page.get('PageTypes', [])
                    
                    # Look for illustrations/plates
                    is_illustration = any(
                        pt.get('PageTypeName', '').lower() in ['illustration', 'plate', 'figure']
                        for pt in page_types
                    )
                    
                    if not is_illustration:
                        continue
                    
                    page_id = page.get('PageID')
                    page_num = page.get('PageNumber', '')
                    
                    # Get high-res image URL
                    image_url = f"https://www.biodiversitylibrary.org/pagethumb/{page_id},2048"
                    
                    fname = f"bhl_{page_id}.jpg"
                    dest = out_dir / fname
                    
                    if dest.exists():
                        continue
                    
                    try:
                        print(f"  📄 Page {page_num}...", end='')
                        r = session.get(image_url, timeout=30)
                        
                        if r.status_code == 200 and len(r.content) > 5000:
                            with open(dest, "wb") as f:
                                f.write(r.content)
                            
                            # Save attribution
                            with open(csv_file, 'a', newline='', encoding='utf-8') as f:
                                csv.writer(f).writerow([
                                    page_id,
                                    title_name,
                                    title.get('Authors', [{}])[0].get('Name', 'Unknown') if title.get('Authors') else 'Unknown',
                                    title.get('StartYear', ''),
                                    item.get('Publisher', ''),
                                    volume,
                                    page_num,
                                    ', '.join([pt.get('PageTypeName', '') for pt in page_types]),
                                    item.get('HoldingInstitution', 'BHL'),
                                    f"https://www.biodiversitylibrary.org/page/{page_id}",
                                    image_url,
                                    fname
                                ])
                            
                            total_downloaded += 1
                            print(f" ✅ ({total_downloaded:,} total)")
                            time.sleep(0.5)
                            
                            if total_downloaded >= target:
                                break
                    except Exception as e:
                        print(f" Error: {e}")
                
                if total_downloaded >= target:
                    break
            
            if total_downloaded >= target:
                break
            
            time.sleep(1)
        
        if total_downloaded >= target:
            break
            
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(3)

print(f"\n🎉 COMPLETE! Downloaded {total_downloaded:,} botanical plates from BHL")
print(f"📁 Location: {out_dir}")
print(f"📊 Attribution: {csv_file}")
