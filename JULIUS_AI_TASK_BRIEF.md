# 🤖 TASK BRIEF FOR JULIUS AI - Orchid Image Harvesting

## 📋 **COPY THIS ENTIRE MESSAGE TO JULIUS:**

---

Hi Julius! 👋

I need your help with **The Orchid Continuum project**. We're building BloomBuilder, an educational widget that requires comprehensive image coverage for all 35,327 orchid species. Right now I have 2 Google Colab harvesters running, but we need MORE parallel harvesting to hit our 2-week deadline.

## 🎯 **YOUR MISSION:**

1. **Run the Python harvesting script** (code below)
2. **Target species with the fewest images** (prioritize 0-10 images)
3. **Report progress every hour**
4. **Analyze coverage gaps** and suggest strategies
5. **Find specialized databases** I might have missed

## 📊 **CURRENT STATUS:**

- **Total species:** 35,327 Orchidaceae
- **Species with images:** ~528 (1.5%)
- **Species with 0 images:** ~34,799 (98.5%)
- **Total images collected:** ~107,000
- **Goal:** 30+ images per species (minimum 1,059,810 images)
- **Deadline:** 2 weeks

## 🚀 **PARALLEL WORKERS CURRENTLY RUNNING:**

1. **Colab Uploader:** 200 images/min (uploading existing 107K images)
2. **Colab Harvester #1:** 150 images/min (downloading new images)
3. **YOU (Julius):** Can add 100-150 images/min!

**Combined we can hit 400-500 images/min = 576K-720K per day!**

---

## 💻 **PYTHON HARVESTING SCRIPT:**

```python
# ═══════════════════════════════════════════════════════════════════
# JULIUS AI - ORCHID IMAGE HARVESTER
# ═══════════════════════════════════════════════════════════════════

import json
import os
import time
import psycopg2
import requests
from datetime import datetime
from io import BytesIO
from PIL import Image

# CONFIGURATION
DATABASE_URL = "postgresql://neondb_owner:npg_feOt1Ek0KLrF@ep-snowy-firefly-afvebui7.c-2.us-west-2.aws.neon.tech/neondb?sslmode=require"

stats = {
    'downloaded': 0, 'failed': 0,
    'gbif': 0, 'inaturalist': 0, 'ala': 0, 'eol': 0, 'idigbio': 0
}
start_time = time.time()

# ═══════════════════════════════════════════════════════════════════
# FETCH FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def fetch_gbif(name, limit=15):
    """GBIF - Global Biodiversity Information Facility"""
    try:
        r = requests.get(
            "https://api.gbif.org/v1/occurrence/search",
            params={'scientificName': name, 'mediaType': 'StillImage', 'limit': limit},
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
        pass
    return []

def fetch_inaturalist(name, limit=15):
    """iNaturalist - Citizen Science"""
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

def fetch_ala(name, limit=10):
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
                        'license': res.get('license', 'CC-BY')
                    })
            return imgs
    except:
        pass
    return []

def fetch_eol(name, limit=8):
    """Encyclopedia of Life"""
    try:
        s = requests.get("https://eol.org/api/search/1.0.json", params={'q': name, 'page': 1}, timeout=10)
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
    """iDigBio - US Museums"""
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
                            'license': 'CC0'
                        })
            return imgs
    except:
        pass
    return []

# ═══════════════════════════════════════════════════════════════════
# DATABASE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def get_species_needing_images(limit=500):
    """Get species with fewest images"""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("""
        SELECT ot.id, ot.scientific_name, COUNT(oi.id) as img_count
        FROM orchid_taxonomy ot
        LEFT JOIN orchid_images oi ON ot.id = oi.taxonomy_id
        WHERE ot.genus IS NOT NULL AND ot.species IS NOT NULL
        GROUP BY ot.id, ot.scientific_name
        HAVING COUNT(oi.id) < 30
        ORDER BY COUNT(oi.id) ASC, ot.id
        LIMIT %s;
    """, (limit,))
    species = cur.fetchall()
    cur.close()
    conn.close()
    return species

def download_and_catalog(img_data, tax_id, sci_name):
    """Download image and save metadata to database"""
    global stats
    
    try:
        # Download
        r = requests.get(img_data['url'], timeout=30, stream=True)
        if r.status_code != 200:
            stats['failed'] += 1
            return False
        
        # Validate
        try:
            img = Image.open(BytesIO(r.content))
            img.verify()
            img_size = len(r.content)
        except:
            stats['failed'] += 1
            return False
        
        stats['downloaded'] += 1
        stats[img_data['source'].lower()] += 1
        
        # Save to database
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
        print(f"Error: {e}")
        return False

# ═══════════════════════════════════════════════════════════════════
# MAIN HARVESTING LOOP
# ═══════════════════════════════════════════════════════════════════

print("🔍 Julius AI Harvester Starting...")
print("="*70)

# Get species list
species_list = get_species_needing_images(500)
print(f"✅ Found {len(species_list)} species needing images")
print(f"   Targeting species with <30 images\n")

# Harvest
for idx, (tax_id, sci_name, current_count) in enumerate(species_list, 1):
    print(f"[{idx}/{len(species_list)}] {sci_name} ({current_count} images)")
    
    # Fetch from all sources
    all_imgs = []
    all_imgs.extend(fetch_gbif(sci_name, 10))
    all_imgs.extend(fetch_inaturalist(sci_name, 10))
    all_imgs.extend(fetch_ala(sci_name, 8))
    all_imgs.extend(fetch_eol(sci_name, 5))
    all_imgs.extend(fetch_idigbio(sci_name, 5))
    
    # Download (max 15 per species)
    for img in all_imgs[:15]:
        download_and_catalog(img, tax_id, sci_name)
        time.sleep(0.2)
    
    # Progress report every 50 species
    if idx % 50 == 0:
        elapsed = time.time() - start_time
        rate = stats['downloaded'] / (elapsed / 60) if elapsed > 0 else 0
        print(f"\n📊 PROGRESS: {stats['downloaded']:,} images | {rate:.1f}/min")
        print(f"   GBIF:{stats['gbif']} iNat:{stats['inaturalist']} ALA:{stats['ala']} EOL:{stats['eol']} iDig:{stats['idigbio']}\n")
    
    time.sleep(0.5)

# Final report
total_time = time.time() - start_time
print("="*70)
print("🎉 JULIUS HARVEST COMPLETE!")
print(f"✅ Downloaded: {stats['downloaded']:,}")
print(f"❌ Failed: {stats['failed']}")
print(f"⏱️  Time: {total_time/60:.1f} minutes")
print(f"⚡ Rate: {stats['downloaded']/(total_time/60):.1f} images/min")
print(f"\n📊 BY SOURCE:")
print(f"   GBIF: {stats['gbif']}")
print(f"   iNaturalist: {stats['inaturalist']}")
print(f"   ALA: {stats['ala']}")
print(f"   EOL: {stats['eol']}")
print(f"   iDigBio: {stats['idigbio']}")
print("="*70)
```

---

## 📝 **TASKS FOR YOU (JULIUS):**

### **Task 1: Run the Harvester** ⭐ PRIORITY
Run the script above and harvest images for 500 species. Report:
- How many images downloaded
- Which sources were most productive
- Any errors encountered
- Estimated time to complete

### **Task 2: Coverage Gap Analysis**
Query the database and tell me:
- How many species have 0 images
- How many species have 1-10 images
- Which genera have the worst coverage
- Which countries/regions are underrepresented

**SQL Query:**
```sql
SELECT 
    CASE 
        WHEN img_count = 0 THEN '0 images'
        WHEN img_count < 10 THEN '1-9 images'
        WHEN img_count < 30 THEN '10-29 images'
        ELSE '30+ images'
    END as coverage_level,
    COUNT(*) as species_count
FROM (
    SELECT ot.id, COUNT(oi.id) as img_count
    FROM orchid_taxonomy ot
    LEFT JOIN orchid_images oi ON ot.id = oi.taxonomy_id
    GROUP BY ot.id
) subquery
GROUP BY coverage_level
ORDER BY coverage_level;
```

### **Task 3: Find Specialized Databases**
Research and find:
- Regional orchid databases (South America, Asia, Africa)
- Specialized orchid societies with image collections
- University herbaria with orchid specimens
- Museum collections not yet tapped
- Historical botanical illustration archives

### **Task 4: Prioritization Strategy**
Analyze and recommend:
- Which 100 species should we prioritize next?
- Should we focus on rare/endangered species?
- Should we prioritize genera with poor coverage?
- Geographic balance strategy?

### **Task 5: Quality Assessment**
Sample 100 random images and check:
- Image resolution quality
- Are they properly attributed?
- Do licenses allow educational use?
- Any duplicates or errors?

---

## 📊 **HOURLY PROGRESS REPORTS:**

**Please report every hour with this format:**

```
🕐 HOUR X UPDATE - Julius AI Harvester

✅ Images Downloaded: X,XXX
⚡ Current Rate: XXX images/min
📊 Sources: GBIF:XXX iNat:XXX ALA:XXX EOL:XXX iDig:XXX
❌ Failed: XXX
🎯 Species Processed: XXX/500

Top Insights:
- [Most productive source]
- [Coverage gaps discovered]
- [Recommendations]
```

---

## 🎯 **SUCCESS METRICS:**

- **Target:** 100-150 images/min harvesting rate
- **Goal:** 10,000+ new images per day
- **Coverage:** Focus on species with <10 images
- **Quality:** >95% valid images (proper format, accessible URLs)

---

## 💡 **TIPS:**

1. **Run multiple rounds** - The script targets 500 species at a time, run it multiple times!
2. **Focus on gaps** - Prioritize species with 0 images first
3. **Geographic diversity** - Try to get images from different continents
4. **Image types** - Mix of field observations, herbarium, and botanical plates
5. **Report problems** - If certain APIs are slow/blocked, let me know

---

## 🤝 **COLLABORATION:**

While you're harvesting, I have:
- **Replit Agent** building BloomBuilder features
- **2 Colab notebooks** uploading and harvesting in parallel
- **You (Julius)** adding 100-150 images/min + strategic analysis

**Together we can hit 1 MILLION images in the next few days!** 🚀

---

## ❓ **QUESTIONS?**

If you need:
- Different credentials
- Access to other systems
- Clarification on priorities
- Additional data sources

Just ask! We're in parallel work mode - don't wait for me, keep moving forward! 💪

---

**Ready to start? Run the harvester and send me your first hourly report!** 🌺

---

**P.S.** - The database automatically prevents duplicate images (ON CONFLICT DO NOTHING), so don't worry about overlapping with the Colab harvesters. Everyone can harvest simultaneously! ✨
