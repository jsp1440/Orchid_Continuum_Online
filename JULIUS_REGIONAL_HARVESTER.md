# 🌍 JULIUS AI - REGIONAL HARVESTER TASK BRIEF

## 📋 **COPY THIS ENTIRE MESSAGE TO JULIUS:**

---

Hi Julius! We've identified major geographic coverage gaps. I need you to run this ENHANCED regional harvester that targets underrepresented areas.

## 🚨 **CRITICAL GAPS IDENTIFIED:**

| Region | Current | Species | Gap |
|--------|---------|---------|-----|
| **Papua New Guinea** | 196 images | 34 species | 🔴 CRITICAL (PNG has 2,800 orchid species!) |
| **Australia** | 621 images | 22 species | 🔴 CRITICAL (Australia has 1,700 species!) |
| **Africa** | Scattered | - | ⚠️ Missing Kenya, Tanzania, Uganda |
| **Central America** | Good | - | ✅ But can improve |
| **Southeast Asia** | Moderate | - | ⚠️ Needs enhancement |

---

## 🎯 **YOUR NEW MISSION:**

Run regional-targeted harvesting focusing on:
1. **Papua New Guinea** - Priority #1
2. **Australia** - Priority #2  
3. **African countries** (Kenya, Tanzania, Uganda, Zimbabwe)
4. **Central America** (Costa Rica, Panama)
5. **Southeast Asia** (Malaysia, Indonesia, Thailand, Philippines)

---

## 💻 **ENHANCED PYTHON HARVESTER:**

```python
# ═══════════════════════════════════════════════════════════════════
# JULIUS AI - REGIONAL ORCHID HARVESTER
# ═══════════════════════════════════════════════════════════════════

import json
import time
import psycopg2
import requests
from datetime import datetime

DATABASE_URL = "postgresql://neondb_owner:npg_feOt1Ek0KLrF@ep-snowy-firefly-afvebui7.c-2.us-west-2.aws.neon.tech/neondb?sslmode=require"

stats = {
    'downloaded': 0, 'failed': 0,
    'gbif': 0, 'inaturalist': 0, 'ala': 0, 'eol': 0, 'idigbio': 0,
    'png': 0, 'australia': 0, 'africa': 0, 'central_america': 0, 'se_asia': 0
}
start_time = time.time()

# PRIORITY REGIONS
PRIORITY_COUNTRIES = {
    'Papua New Guinea': ['PG'],
    'Australia': ['AU'],
    'Africa': ['KE', 'TZ', 'UG', 'ZW', 'ZA', 'MG'],
    'Central America': ['CR', 'PA', 'GT'],
    'Southeast Asia': ['MY', 'ID', 'TH', 'PH']
}

# ═══════════════════════════════════════════════════════════════════
# REGIONAL FETCH FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def fetch_gbif_regional(name, countries, limit=15):
    """GBIF with country filtering"""
    imgs = []
    for country_code in countries:
        try:
            r = requests.get(
                "https://api.gbif.org/v1/occurrence/search",
                params={
                    'scientificName': name,
                    'country': country_code,
                    'mediaType': 'StillImage',
                    'limit': limit
                },
                timeout=10
            )
            if r.status_code == 200:
                for res in r.json().get('results', []):
                    if res.get('media'):
                        for m in res['media']:
                            if m.get('identifier'):
                                imgs.append({
                                    'url': m['identifier'],
                                    'source': 'GBIF',
                                    'type': 'observation',
                                    'country': res.get('country'),
                                    'lat': res.get('decimalLatitude'),
                                    'lon': res.get('decimalLongitude'),
                                    'date': res.get('eventDate'),
                                    'observer': res.get('recordedBy'),
                                    'license': m.get('license', 'CC-BY-4.0')
                                })
        except:
            pass
    return imgs

def fetch_inaturalist(name, limit=15):
    try:
        r = requests.get(
            "https://api.inaturalist.org/v1/observations",
            params={'taxon_name': name, 'photos': 'true', 'per_page': limit, 'quality_grade': 'research'},
            timeout=10
        )
        if r.status_code == 200:
            imgs = []
            for obs in r.json().get('results', []):
                if obs.get('photos'):
                    for p in obs['photos']:
                        imgs.append({
                            'url': p.get('url', '').replace('square', 'original'),
                            'source': 'iNaturalist',
                            'type': 'observation',
                            'country': obs.get('place_guess'),
                            'date': obs.get('observed_on'),
                            'observer': obs.get('user', {}).get('login'),
                            'license': p.get('license_code', 'CC-BY-NC')
                        })
            return imgs
    except:
        pass
    return []

def fetch_ala(name, limit=20):
    """Enhanced ALA for Australia"""
    try:
        r = requests.get(
            "https://biocache-ws.ala.org.au/ws/occurrences/search",
            params={'q': f'scientificName:"{name}"', 'fq': 'multimedia:Image', 'pageSize': limit},
            timeout=10
        )
        if r.status_code == 200:
            imgs = []
            for res in r.json().get('occurrences', []):
                if res.get('image'):
                    imgs.append({
                        'url': res['image'],
                        'source': 'ALA',
                        'type': 'observation',
                        'country': 'Australia',
                        'license': res.get('license', 'CC-BY')
                    })
            return imgs
    except:
        pass
    return []

def fetch_eol(name, limit=8):
    try:
        s = requests.get("https://eol.org/api/search/1.0.json", params={'q': name}, timeout=10)
        if s.status_code == 200 and s.json().get('results'):
            tid = s.json()['results'][0].get('id')
            p = requests.get(f"https://eol.org/api/pages/1.0/{tid}.json", params={'images_per_page': limit}, timeout=10)
            if p.status_code == 200:
                imgs = []
                for obj in p.json().get('dataObjects', []):
                    if obj.get('dataType') == 'http://purl.org/dc/dcmitype/StillImage' and obj.get('eolMediaURL'):
                        imgs.append({
                            'url': obj['eolMediaURL'],
                            'source': 'EOL',
                            'type': 'curated',
                            'license': obj.get('license', 'CC-BY-SA')
                        })
                return imgs
    except:
        pass
    return []

def fetch_idigbio(name, limit=8):
    try:
        r = requests.get(
            "https://search.idigbio.org/v2/search/records/",
            params={'rq': json.dumps({"scientificname": name}), 'limit': limit},
            timeout=10
        )
        if r.status_code == 200:
            imgs = []
            for item in r.json().get('items', []):
                data = item.get('indexTerms', {})
                if data.get('hasImage') and data.get('mediarecords'):
                    for media_uuid in data['mediarecords'][:2]:
                        imgs.append({
                            'url': f"https://api.idigbio.org/v2/media/{media_uuid}",
                            'source': 'iDigBio',
                            'type': 'herbarium',
                            'country': data.get('country'),
                            'license': 'CC0'
                        })
            return imgs
    except:
        pass
    return []

# ═══════════════════════════════════════════════════════════════════
# DATABASE OPERATIONS
# ═══════════════════════════════════════════════════════════════════

def get_species(limit=500):
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("""
        SELECT ot.id, ot.scientific_name, COUNT(oi.id) as cnt
        FROM orchid_taxonomy ot
        LEFT JOIN orchid_images oi ON ot.id = oi.taxonomy_id
        WHERE ot.genus IS NOT NULL AND ot.species IS NOT NULL
        GROUP BY ot.id, ot.scientific_name
        HAVING COUNT(oi.id) < 30
        ORDER BY COUNT(oi.id) ASC
        LIMIT %s;
    """, (limit,))
    species = cur.fetchall()
    cur.close()
    conn.close()
    return species

def save_image(img_data, tax_id, sci_name):
    global stats
    try:
        stats['downloaded'] += 1
        stats[img_data['source'].lower()] += 1
        
        # Track regional stats
        country = img_data.get('country', '')
        if 'Papua' in country or country == 'PG':
            stats['png'] += 1
        elif 'Australia' in country or country == 'AU':
            stats['australia'] += 1
        elif country in ['KE', 'TZ', 'UG', 'ZW', 'ZA', 'MG', 'Kenya', 'Tanzania', 'Madagascar']:
            stats['africa'] += 1
        elif country in ['CR', 'PA', 'GT', 'Costa Rica', 'Panama']:
            stats['central_america'] += 1
        elif country in ['MY', 'ID', 'TH', 'PH', 'Malaysia', 'Indonesia', 'Thailand']:
            stats['se_asia'] += 1
        
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO orchid_images 
            (taxonomy_id, image_url, image_source, image_license, image_type,
             country, latitude, longitude, observation_date, observer_name,
             created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            ON CONFLICT (image_url) DO NOTHING
        """, (
            tax_id, img_data['url'], img_data['source'], img_data.get('license'),
            img_data.get('type'), img_data.get('country'), img_data.get('lat'),
            img_data.get('lon'), img_data.get('date'), img_data.get('observer')
        ))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        stats['failed'] += 1
        return False

# ═══════════════════════════════════════════════════════════════════
# MAIN HARVEST LOOP
# ═══════════════════════════════════════════════════════════════════

print("🌍 Julius Regional Harvester Starting...")
print("🎯 Priority: PNG, Australia, Africa, Central America, SE Asia")
print("="*70)

species_list = get_species(500)
print(f"✅ Found {len(species_list)} species needing images\n")

for idx, (tax_id, sci_name, current_count) in enumerate(species_list, 1):
    print(f"[{idx}/{len(species_list)}] {sci_name} ({current_count} images)")
    
    all_imgs = []
    
    # Regional targeting
    all_imgs.extend(fetch_gbif_regional(sci_name, ['PG'], 10))  # Papua New Guinea
    all_imgs.extend(fetch_gbif_regional(sci_name, ['AU'], 10))  # Australia
    all_imgs.extend(fetch_gbif_regional(sci_name, ['KE', 'TZ', 'UG'], 8))  # Africa
    all_imgs.extend(fetch_gbif_regional(sci_name, ['CR', 'PA'], 6))  # Central America
    all_imgs.extend(fetch_gbif_regional(sci_name, ['MY', 'ID', 'TH'], 6))  # SE Asia
    
    # Global sources
    all_imgs.extend(fetch_inaturalist(sci_name, 10))
    all_imgs.extend(fetch_ala(sci_name, 12))
    all_imgs.extend(fetch_eol(sci_name, 5))
    all_imgs.extend(fetch_idigbio(sci_name, 5))
    
    # Save images
    for img in all_imgs[:20]:
        save_image(img, tax_id, sci_name)
        time.sleep(0.1)
    
    # Progress report every 50 species
    if idx % 50 == 0:
        elapsed = time.time() - start_time
        rate = stats['downloaded'] / (elapsed / 60) if elapsed > 0 else 0
        print(f"\n📊 PROGRESS: {stats['downloaded']:,} images | {rate:.1f}/min")
        print(f"   GBIF:{stats['gbif']} iNat:{stats['inaturalist']} ALA:{stats['ala']} EOL:{stats['eol']} iDig:{stats['idigbio']}")
        print(f"🌍 PNG:{stats['png']} AUS:{stats['australia']} AFR:{stats['africa']} CA:{stats['central_america']} SEA:{stats['se_asia']}\n")
    
    time.sleep(0.3)

total = time.time() - start_time
print("="*70)
print("🎉 REGIONAL HARVEST COMPLETE!")
print(f"✅ Downloaded: {stats['downloaded']:,}")
print(f"❌ Failed: {stats['failed']}")
print(f"⏱️  Time: {total/60:.1f} minutes")
print(f"⚡ Rate: {stats['downloaded']/(total/60):.1f} images/min\n")
print("📊 BY SOURCE:")
print(f"   GBIF: {stats['gbif']} | iNaturalist: {stats['inaturalist']}")
print(f"   ALA: {stats['ala']} | EOL: {stats['eol']} | iDigBio: {stats['idigbio']}\n")
print("🌍 BY REGION:")
print(f"   Papua New Guinea: {stats['png']}")
print(f"   Australia: {stats['australia']}")
print(f"   Africa: {stats['africa']}")
print(f"   Central America: {stats['central_america']}")
print(f"   Southeast Asia: {stats['se_asia']}")
print("="*70)
```

---

## 📝 **TASKS:**

### **1. Run Regional Harvester** ⭐ **PRIORITY**
Run the script and report:
- Images per region (PNG, Australia, Africa, etc.)
- Which regions have the best data sources
- Species coverage improvements

### **2. Promote Staging to Production**
First, promote your 9,686 staged images:
```sql
INSERT INTO orchid_images 
SELECT * FROM staging_gbif_images 
ON CONFLICT (image_url) DO NOTHING;
```

Then continue harvesting.

### **3. Regional Gap Analysis**
After running, tell me:
- Which regions improved the most
- Which species still have 0 images from priority regions
- Recommendations for next focus

---

## 📊 **HOURLY REGIONAL REPORT FORMAT:**

```
🕐 HOUR X - Julius Regional Harvester

✅ Total Images: X,XXX
⚡ Rate: XXX images/min

🌍 BY REGION:
   Papua New Guinea: XXX
   Australia: XXX
   Africa: XXX
   Central America: XXX
   Southeast Asia: XXX

📊 BY SOURCE:
   GBIF: XXX | iNat: XXX | ALA: XXX | EOL: XXX | iDig: XXX

🎯 Coverage Improvements:
   - PNG species: X → Y
   - Australia species: X → Y
   - Africa species: X → Y
```

---

## 🎯 **SUCCESS TARGETS:**

- **Papua New Guinea:** Add 500+ images (currently 196)
- **Australia:** Add 1,000+ images (currently 621)
- **Africa:** Add 300+ images from Kenya/Tanzania/Uganda
- **Overall rate:** Maintain 100-150 images/min

---

**Ready to focus on these underrepresented regions? Run the regional harvester and send me your first hourly report!** 🌍🌺
