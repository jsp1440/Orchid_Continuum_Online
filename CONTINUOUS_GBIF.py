#!/usr/bin/env python3
import os, time, requests, csv
from pathlib import Path

out_dir = Path(os.path.expanduser("~/orchid_downloads/gbif_continuous"))
out_dir.mkdir(parents=True, exist_ok=True)

csv_file = Path(os.path.expanduser("~/orchid_downloads/gbif_continuous_full_data.csv"))
if not csv_file.exists():
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        csv.writer(f).writerow([
            'gbif_id', 'scientific_name', 'genus', 'family', 'order', 'class', 'kingdom',
            'country', 'locality', 'latitude', 'longitude', 'elevation',
            'collector', 'collection_date', 'institution_code', 'catalog_number',
            'basis_of_record', 'photographer', 'license', 'image_url', 'local_filename'
        ])

print("🌍 CONTINUOUS GBIF DOWNLOADER")
print("Target: 2 million images with full taxonomy data")
print("Press Ctrl+C to stop\n")

session = requests.Session()
offset = 0
batch_size = 1000
total_downloaded = 0
target = 2000000

while total_downloaded < target:
    print(f"\n{'='*80}")
    print(f"Batch {offset} | Downloaded: {total_downloaded:,} / {target:,}")
    print(f"{'='*80}")
    
    try:
        params = {"familyKey": 7689, "mediaType": "StillImage", "limit": batch_size, "offset": offset}
        resp = session.get("https://api.gbif.org/v1/occurrence/search", params=params, timeout=40)
        
        if resp.status_code != 200:
            print(f"API Error: {resp.status_code}, retrying...")
            time.sleep(10)
            continue
        
        records = resp.json().get("results", [])
        if not records:
            print("No more records!")
            break
        
        batch_count = 0
        for idx, rec in enumerate(records, 1):
            media = rec.get("media", [])
            if not media or not media[0].get("identifier"):
                continue
            
            url = media[0]["identifier"]
            fname = f"gbif_{offset}_{idx}.jpg"
            dest = out_dir / fname
            
            if dest.exists():
                continue
            
            try:
                r = session.get(url, timeout=25)
                if r.status_code == 200:
                    with open(dest, "wb") as f:
                        f.write(r.content)
                    
                    with open(csv_file, 'a', newline='', encoding='utf-8') as f:
                        csv.writer(f).writerow([
                            rec.get('key', ''), rec.get('species', ''), rec.get('genus', ''),
                            rec.get('family', ''), rec.get('order', ''), rec.get('class', ''),
                            rec.get('kingdom', ''), rec.get('country', ''), rec.get('locality', ''),
                            rec.get('decimalLatitude', ''), rec.get('decimalLongitude', ''),
                            rec.get('elevation', ''), rec.get('recordedBy', ''),
                            rec.get('eventDate', ''), rec.get('institutionCode', ''),
                            rec.get('catalogNumber', ''), rec.get('basisOfRecord', ''),
                            media[0].get('creator', ''), media[0].get('license', ''), url, fname
                        ])
                    
                    batch_count += 1
                    total_downloaded += 1
                    
                    if batch_count % 100 == 0:
                        percent = (total_downloaded / target) * 100
                        print(f"  {batch_count} this batch | {total_downloaded:,} total ({percent:.2f}%)")
                    
                    time.sleep(0.15)
            except:
                pass
        
        print(f"✅ Batch done: {batch_count} images")
        offset += batch_size
        time.sleep(2)
        
    except KeyboardInterrupt:
        print(f"\n🛑 Stopped. Downloaded: {total_downloaded:,}")
        break
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(10)

print(f"\n🎉 Complete! {total_downloaded:,} images")
