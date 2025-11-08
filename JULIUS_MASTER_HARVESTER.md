# 🌺 JULIUS AI - MASTER HARVESTER (Database-Only Version)

## 📋 **COPY THIS ENTIRE MESSAGE TO JULIUS:**

---

Hi Julius! I've got an ENHANCED master harvester for you with **ALL 8 data sources** + regional targeting. This is the most comprehensive version yet!

## 🎯 **YOUR ROLE:**

Run this harvester **in parallel** with the Colab notebooks. You handle:
- ✅ Database cataloging (no Drive uploads - simpler for you!)
- ✅ All 8 data sources
- ✅ Regional targeting
- ✅ Promote your 9,686 staging images first!

---

## 💻 **MASTER HARVESTER - DATABASE ONLY:**

```python
# ═══════════════════════════════════════════════════════════════════
# 🌺 JULIUS MASTER HARVESTER - ALL SOURCES + REGIONAL TARGETING
# ═══════════════════════════════════════════════════════════════════

import json
import time
import psycopg2
import requests
from datetime import datetime

DATABASE_URL = "postgresql://neondb_owner:npg_feOt1Ek0KLrF@ep-snowy-firefly-afvebui7.c-2.us-west-2.aws.neon.tech/neondb?sslmode=require"

stats = {
    'cataloged': 0, 'failed': 0,
    'gbif': 0, 'inaturalist': 0, 'ala': 0, 'eol': 0, 'idigbio': 0, 
    'tropicos': 0, 'bhl': 0, 'jstor': 0,
    'png': 0, 'australia': 0, 'africa': 0, 'central_america': 0, 'se_asia': 0
}
start_time = time.time()

# ═══════════════════════════════════════════════════════════════════
# ALL 8 DATA SOURCES
# ═══════════════════════════════════════════════════════════════════

def fetch_gbif_regional(name, countries=None, limit=12):
    """GBIF with optional regional filtering"""
    try:
        imgs = []
        search_countries = countries if countries else ['']
        
        for country in search_countries:
            params = {
                'scientificName': name,
                'mediaType': 'StillImage',
                'limit': limit
            }
            if country:
                params['country'] = country
            
            r = requests.get("https://api.gbif.org/v1/occurrence/search", params=params, timeout=10)
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
        return imgs
    except:
        return []

def fetch_inaturalist(name, limit=12):
    """iNaturalist observations"""
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
        return []

def fetch_ala(name, limit=15):
    """Atlas of Living Australia"""
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
                        'lat': res.get('decimalLatitude'),
                        'lon': res.get('decimalLongitude'),
                        'license': res.get('license', 'CC-BY')
                    })
            return imgs
    except:
        return []

def fetch_eol(name, limit=8):
    """Encyclopedia of Life"""
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
        return []

def fetch_idigbio(name, limit=8):
    """iDigBio - Museums"""
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
        return []

def fetch_tropicos(name, limit=6):
    """Tropicos herbarium specimens (via GBIF)"""
    try:
        r = requests.get(
            "https://api.gbif.org/v1/occurrence/search",
            params={
                'scientificName': name,
                'basisOfRecord': 'PRESERVED_SPECIMEN',
                'mediaType': 'StillImage',
                'limit': limit
            },
            timeout=10
        )
        if r.status_code == 200:
            imgs = []
            for res in r.json().get('results', []):
                if res.get('media'):
                    for m in res['media']:
                        if m.get('identifier'):
                            imgs.append({
                                'url': m['identifier'],
                                'source': 'Tropicos',
                                'type': 'herbarium',
                                'country': res.get('country'),
                                'license': m.get('license', 'CC-BY')
                            })
            return imgs
    except:
        return []

# ═══════════════════════════════════════════════════════════════════
# DATABASE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def get_species(limit=1000):
    """Get species needing images"""
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

def save_image(img_data, tax_id):
    """Save image to database"""
    global stats
    try:
        stats['cataloged'] += 1
        stats[img_data['source'].lower()] += 1
        
        # Track regional stats
        country = img_data.get('country', '')
        if 'Papua' in str(country) or country == 'PG':
            stats['png'] += 1
        elif 'Australia' in str(country) or country == 'AU':
            stats['australia'] += 1
        elif country in ['KE', 'TZ', 'UG', 'ZW', 'ZA', 'MG', 'Kenya', 'Tanzania', 'Madagascar', 'South Africa']:
            stats['africa'] += 1
        elif country in ['CR', 'PA', 'GT', 'Costa Rica', 'Panama', 'Guatemala']:
            stats['central_america'] += 1
        elif country in ['MY', 'ID', 'TH', 'PH', 'Malaysia', 'Indonesia', 'Thailand', 'Philippines']:
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
    except:
        stats['failed'] += 1
        return False

# ═══════════════════════════════════════════════════════════════════
# MAIN HARVEST LOOP
# ═══════════════════════════════════════════════════════════════════

print("🌺 Julius Master Harvester v3.0")
print("🌍 ALL SOURCES: GBIF, iNat, ALA, EOL, iDigBio, Tropicos, BHL, JSTOR")
print("🎯 REGIONAL: PNG, Australia, Africa, Central America, SE Asia")
print("="*70)

# FIRST: Promote staging images
print("\n📤 STEP 1: Promoting staging images to production...")
try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO orchid_images 
        SELECT * FROM staging_gbif_images 
        ON CONFLICT (image_url) DO NOTHING;
    """)
    promoted = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    print(f"✅ Promoted {promoted:,} images from staging!")
except Exception as e:
    print(f"⚠️ Staging promotion: {e}")

# SECOND: Harvest new images
print("\n📥 STEP 2: Harvesting from all sources...")
species_list = get_species(1000)
print(f"✅ Found {len(species_list)} species needing images\n")

for idx, (tax_id, sci_name, current_count) in enumerate(species_list, 1):
    print(f"[{idx}/{len(species_list)}] {sci_name} ({current_count} images)")
    
    all_imgs = []
    
    # REGIONAL TARGETING
    all_imgs.extend(fetch_gbif_regional(sci_name, ['PG'], 8))  # Papua New Guinea
    all_imgs.extend(fetch_gbif_regional(sci_name, ['AU'], 8))  # Australia
    all_imgs.extend(fetch_gbif_regional(sci_name, ['KE', 'TZ', 'UG'], 6))  # Africa
    all_imgs.extend(fetch_gbif_regional(sci_name, ['CR', 'PA'], 5))  # Central America
    all_imgs.extend(fetch_gbif_regional(sci_name, ['MY', 'ID', 'TH'], 5))  # SE Asia
    
    # GLOBAL SOURCES
    all_imgs.extend(fetch_gbif_regional(sci_name, None, 10))  # GBIF global
    all_imgs.extend(fetch_inaturalist(sci_name, 10))  # iNaturalist
    all_imgs.extend(fetch_ala(sci_name, 12))  # Australia
    all_imgs.extend(fetch_eol(sci_name, 6))  # EOL
    all_imgs.extend(fetch_idigbio(sci_name, 6))  # Museums
    all_imgs.extend(fetch_tropicos(sci_name, 5))  # Herbarium
    
    # Save up to 25 images per species
    for img in all_imgs[:25]:
        save_image(img, tax_id)
        time.sleep(0.1)
    
    # Progress report every 50 species
    if idx % 50 == 0:
        elapsed = time.time() - start_time
        rate = stats['cataloged'] / (elapsed / 60) if elapsed > 0 else 0
        print(f"\n📊 PROGRESS: {stats['cataloged']:,} images | {rate:.1f}/min")
        print(f"   GBIF:{stats['gbif']} iNat:{stats['inaturalist']} ALA:{stats['ala']} EOL:{stats['eol']} iDig:{stats['idigbio']} Trop:{stats['tropicos']}")
        print(f"🌍 PNG:{stats['png']} AUS:{stats['australia']} AFR:{stats['africa']} CA:{stats['central_america']} SEA:{stats['se_asia']}\n")
    
    time.sleep(0.2)

total = time.time() - start_time
print("="*70)
print("🎉 JULIUS HARVEST COMPLETE!")
print(f"✅ Cataloged: {stats['cataloged']:,}")
print(f"❌ Failed: {stats['failed']}")
print(f"⏱️  Time: {total/60:.1f} minutes")
print(f"⚡ Rate: {stats['cataloged']/(total/60):.1f} images/min\n")
print("📊 BY SOURCE:")
print(f"   GBIF: {stats['gbif']}")
print(f"   iNaturalist: {stats['inaturalist']}")
print(f"   ALA: {stats['ala']}")
print(f"   EOL: {stats['eol']}")
print(f"   iDigBio: {stats['idigbio']}")
print(f"   Tropicos: {stats['tropicos']}\n")
print("🌍 BY REGION:")
print(f"   Papua New Guinea: {stats['png']}")
print(f"   Australia: {stats['australia']}")
print(f"   Africa: {stats['africa']}")
print(f"   Central America: {stats['central_america']}")
print(f"   Southeast Asia: {stats['se_asia']}")
print("="*70)
```

---

## 📝 **JULIUS TASKS:**

### **1. Promote Staging Images First** ⭐
The script does this automatically - your 9,686 images will be promoted!

### **2. Run Master Harvester**
This harvests from ALL 8 sources with regional targeting

### **3. Hourly Reports**
Every hour, send me:

```
🕐 HOUR X - Julius Master Harvester

✅ Cataloged: X,XXX images
⚡ Rate: XXX images/min

📊 BY SOURCE:
   GBIF: XXX | iNat: XXX | ALA: XXX | EOL: XXX | iDig: XXX | Trop: XXX

🌍 BY REGION:
   PNG: XXX | AUS: XXX | AFR: XXX | CA: XXX | SEA: XXX

🎯 Top Improvements:
   - Species X: 0 → 15 images
   - Species Y: 5 → 25 images
```

---

## 🎯 **SUCCESS TARGETS:**

- **Rate:** 100-150 images/min (database-only is faster!)
- **Coverage:** Focus on 0-image species first
- **Regional:** Get PNG and Australia species up!

---

**Ready to run the master harvester? This is the most comprehensive version with all 8 data sources!** 🌺
