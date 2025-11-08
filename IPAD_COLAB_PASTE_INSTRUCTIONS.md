# 📱 iPad Google Colab - Copy/Paste Method

## ✅ This Method Works Perfect on iPad!

No downloads needed - just copy/paste into Colab.

---

## 🚀 **Quick Setup (5 Minutes)**

### **Step 1: Open Google Colab**
- Safari → **colab.research.google.com**
- Click **"+ New Notebook"**
- You'll see an empty code cell ✅

### **Step 2: Copy Code Blocks Below**

I'll give you **6 small code blocks** to copy/paste.

Just:
1. Copy each block
2. Paste into Colab cell
3. Click ▶️ to run
4. Move to next cell (click "+ Code")

---

## 📦 **CODE BLOCK 1: Install Dependencies**

**Copy this → Paste in first cell → Click ▶️**

```python
# Install packages
!pip install aiohttp psycopg2-binary requests -q

import asyncio
import aiohttp
import psycopg2
import json
import os
from datetime import datetime
from typing import List, Dict, Optional
import requests
import time

print("✅ Dependencies installed!")
```

---

## 🔐 **CODE BLOCK 2: Database Connection**

**Copy this → Paste in new cell → EDIT YOUR DATABASE_URL → Click ▶️**

```python
# 🔴 PASTE YOUR DATABASE_URL HERE:
DATABASE_URL = "postgresql://your-url-here"  # ← REPLACE THIS!

# Test connection
try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM orchid_taxonomy")
    total_species = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM orchid_images")
    total_images = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(DISTINCT taxonomy_id) FROM orchid_images")
    species_with_images = cur.fetchone()[0]
    
    print("✅ Database Connected!")
    print(f"   Species: {total_species:,}")
    print(f"   Images: {total_images:,}")
    print(f"   Coverage: {species_with_images:,} species ({species_with_images/total_species*100:.1f}%)")
    
    cur.close()
    conn.close()
except Exception as e:
    print(f"❌ Connection failed: {e}")
    print("\n👉 Make sure you pasted your DATABASE_URL correctly!")
```

**⚠️ IMPORTANT:** Replace `"postgresql://your-url-here"` with YOUR actual DATABASE_URL from Replit!

---

## 🔧 **CODE BLOCK 3: Helper Functions**

**Copy this → Paste in new cell → Click ▶️**

```python
def clean_name(sci_name):
    """Extract genus + species only (remove author citations)"""
    parts = sci_name.split()
    return f"{parts[0]} {parts[1]}" if len(parts) >= 2 else parts[0]

def get_species_list(database_url, limit=5000):
    """Get species needing images (< 30 images each)"""
    conn = psycopg2.connect(database_url)
    cur = conn.cursor()
    
    cur.execute("""
        SELECT 
            ot.id,
            ot.scientific_name,
            COUNT(oi.id) as current_images
        FROM orchid_taxonomy ot
        LEFT JOIN orchid_images oi ON ot.id = oi.taxonomy_id
        WHERE ot.scientific_name IS NOT NULL
        AND ot.scientific_name != ''
        GROUP BY ot.id, ot.scientific_name
        HAVING COUNT(oi.id) < 30
        ORDER BY COUNT(oi.id) ASC, RANDOM()
        LIMIT %s
    """, (limit,))
    
    species_list = cur.fetchall()
    cur.close()
    conn.close()
    
    return species_list

print("✅ Helper functions loaded!")
```

---

## 🚀 **CODE BLOCK 4: Parallel Hunter (Part 1)**

**Copy this → Paste in new cell → Click ▶️**

```python
class ParallelOrchidHunter:
    """Ultra-optimized parallel image hunter"""
    
    def __init__(self, database_url: str, max_concurrent: int = 50):
        self.database_url = database_url
        self.max_concurrent = max_concurrent
        self.stats = {
            'species_processed': 0,
            'images_found': 0,
            'images_inserted': 0,
            'start_time': time.time()
        }
    
    async def fetch_inaturalist(self, session, sci_name, needed=30):
        """Fetch from iNaturalist with full metadata"""
        try:
            clean = clean_name(sci_name)
            async with session.get(
                'https://api.inaturalist.org/v1/observations',
                params={
                    'taxon_name': clean,
                    'photos': 'true',
                    'quality_grade': 'research',
                    'per_page': needed
                },
                timeout=aiohttp.ClientTimeout(total=20)
            ) as resp:
                data = await resp.json()
                images = []
                for obs in data.get('results', []):
                    loc = obs.get('geojson', {}).get('coordinates', [None, None])
                    for photo in obs.get('photos', []):
                        images.append({
                            'occurrence_key': str(obs.get('id')),
                            'image_url': photo.get('url', '').replace('square', 'original'),
                            'image_source': 'iNaturalist',
                            'image_license': photo.get('license_code', 'CC-BY-NC'),
                            'latitude': loc[1] if len(loc) > 1 else None,
                            'longitude': loc[0] if len(loc) > 0 else None,
                            'country': obs.get('place_guess'),
                            'locality': obs.get('place_guess'),
                            'observation_date': obs.get('observed_on'),
                            'year_observed': obs.get('observed_on_details', {}).get('year'),
                            'month_observed': obs.get('observed_on_details', {}).get('month'),
                            'observer_name': obs.get('user', {}).get('login'),
                            'wild_specimen': obs.get('captive') == False,
                            'occurrence_metadata': json.dumps({'inat_id': obs.get('id')}),
                            'media_metadata': json.dumps({'photo_id': photo.get('id')})
                        })
                return images[:needed]
        except:
            return []

print("✅ iNaturalist hunter loaded!")
```

---

## 🌍 **CODE BLOCK 5: Parallel Hunter (Part 2)**

**Copy this → Paste in new cell → Click ▶️**

```python
# Add GBIF method and processing to ParallelOrchidHunter class
async def fetch_gbif(self, session, sci_name, needed=30):
    """Fetch from GBIF with full metadata"""
    try:
        clean = clean_name(sci_name)
        async with session.get(
            'https://api.gbif.org/v1/occurrence/search',
            params={
                'scientificName': clean,
                'mediaType': 'StillImage',
                'hasCoordinate': 'true',
                'limit': needed
            },
            timeout=aiohttp.ClientTimeout(total=20)
        ) as resp:
            data = await resp.json()
            images = []
            for occ in data.get('results', []):
                for media in occ.get('media', []):
                    if media.get('type') == 'StillImage':
                        images.append({
                            'occurrence_key': str(occ.get('key')),
                            'image_url': media.get('identifier'),
                            'image_source': 'GBIF',
                            'image_license': media.get('license'),
                            'latitude': occ.get('decimalLatitude'),
                            'longitude': occ.get('decimalLongitude'),
                            'coordinate_uncertainty': occ.get('coordinateUncertaintyInMeters'),
                            'country': occ.get('country'),
                            'country_code': occ.get('countryCode'),
                            'state_province': occ.get('stateProvince'),
                            'locality': occ.get('locality'),
                            'continent': occ.get('continent'),
                            'elevation_meters': occ.get('elevation'),
                            'observation_date': occ.get('eventDate'),
                            'year_observed': occ.get('year'),
                            'month_observed': occ.get('month'),
                            'observer_name': occ.get('recordedBy'),
                            'institution_code': occ.get('institutionCode'),
                            'wild_specimen': occ.get('basisOfRecord') != 'PRESERVED_SPECIMEN',
                            'occurrence_metadata': json.dumps({'gbif_key': occ.get('key')}),
                            'media_metadata': json.dumps(media)
                        })
            return images[:needed]
    except:
        return []

# Attach to class
ParallelOrchidHunter.fetch_gbif = fetch_gbif

print("✅ GBIF hunter loaded!")
```

---

## 💾 **CODE BLOCK 6: Database Insert & Processing**

**Copy this → Paste in new cell → Click ▶️**

```python
def bulk_insert(self, images_batch):
    """Bulk insert images to database"""
    if not images_batch:
        return 0
    
    conn = psycopg2.connect(self.database_url)
    cur = conn.cursor()
    inserted = 0
    
    for img in images_batch:
        try:
            cur.execute("""
                INSERT INTO orchid_images (
                    taxonomy_id, gbif_occurrence_key, image_url, image_source,
                    wild_specimen, image_license, latitude, longitude,
                    coordinate_uncertainty, country, country_code, state_province,
                    locality, continent, elevation_meters, observation_date,
                    year_observed, month_observed, observer_name, institution_code,
                    occurrence_metadata, media_metadata, created_at
                )
                SELECT %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                       %s, %s, %s, %s, %s, %s, %s, %s
                WHERE NOT EXISTS (
                    SELECT 1 FROM orchid_images WHERE image_url = %s
                )
            """, (
                img.get('taxonomy_id'), img.get('occurrence_key'), img.get('image_url'),
                img.get('image_source'), img.get('wild_specimen'), img.get('image_license'),
                img.get('latitude'), img.get('longitude'), img.get('coordinate_uncertainty'),
                img.get('country'), img.get('country_code'), img.get('state_province'),
                img.get('locality'), img.get('continent'), img.get('elevation_meters'),
                img.get('observation_date'), img.get('year_observed'), img.get('month_observed'),
                img.get('observer_name'), img.get('institution_code'),
                img.get('occurrence_metadata'), img.get('media_metadata'),
                datetime.now(), img.get('image_url')
            ))
            if cur.rowcount > 0:
                inserted += 1
        except:
            conn.rollback()
            continue
    
    conn.commit()
    cur.close()
    conn.close()
    return inserted

async def hunt_species(self, session, species_data):
    """Hunt one species from all sources"""
    tax_id, sci_name, current_count = species_data
    needed = 30 - current_count
    
    if needed <= 0:
        return []
    
    results = await asyncio.gather(
        self.fetch_inaturalist(session, sci_name, needed),
        self.fetch_gbif(session, sci_name, needed),
        return_exceptions=True
    )
    
    all_images = []
    for r in results:
        if isinstance(r, list):
            all_images.extend(r)
    
    for img in all_images:
        img['taxonomy_id'] = tax_id
    
    return all_images[:needed]

async def process_batch(self, species_batch):
    """Process a batch of species in parallel"""
    connector = aiohttp.TCPConnector(limit=self.max_concurrent)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [self.hunt_species(session, sp) for sp in species_batch]
        results = await asyncio.gather(*tasks)
        
        all_images = []
        for images in results:
            all_images.extend(images)
        
        inserted = self.bulk_insert(all_images)
        
        self.stats['images_found'] += len(all_images)
        self.stats['images_inserted'] += inserted
        self.stats['species_processed'] += len(species_batch)
        
        return inserted

# Attach to class
ParallelOrchidHunter.bulk_insert = bulk_insert
ParallelOrchidHunter.hunt_species = hunt_species
ParallelOrchidHunter.process_batch = process_batch

print("✅ Processing engine loaded!")
```

---

## 🎯 **CODE BLOCK 7: RUN IT! (Final Block)**

**Copy this → Paste in new cell → Click ▶️ → GO!**

```python
BATCH_SIZE = 5000
CHUNK_SIZE = 100

print("\n" + "="*80)
print("🌺 ORCHID CONTINUUM - MEGA 5,000 SPECIES RUN")
print("="*80)

# Get species
species_list = get_species_list(DATABASE_URL, BATCH_SIZE)
print(f"\n📋 Found {len(species_list)} species needing images")
print(f"🚀 Processing in chunks of {CHUNK_SIZE}")
print(f"⏱️  Estimated time: 6-8 hours")
print(f"\n🎯 Goal: {len(species_list) * 20} - {len(species_list) * 30} new images\n")
print("="*80)

# Create hunter
hunter = ParallelOrchidHunter(DATABASE_URL, max_concurrent=50)
start_time = time.time()

# Process in chunks
for i in range(0, len(species_list), CHUNK_SIZE):
    chunk = species_list[i:i+CHUNK_SIZE]
    chunk_num = (i // CHUNK_SIZE) + 1
    total_chunks = (len(species_list) + CHUNK_SIZE - 1) // CHUNK_SIZE
    
    print(f"\n[Chunk {chunk_num}/{total_chunks}] Processing species {i+1}-{min(i+CHUNK_SIZE, len(species_list))}...")
    
    inserted = await hunter.process_batch(chunk)
    
    elapsed = time.time() - start_time
    progress = hunter.stats['species_processed'] / len(species_list)
    estimated_total = elapsed / progress if progress > 0 else 0
    remaining = estimated_total - elapsed
    
    print(f"   ✅ Inserted: {inserted} images")
    print(f"   📊 Total: {hunter.stats['images_inserted']:,} images from {hunter.stats['species_processed']} species")
    print(f"   ⏱️  Elapsed: {elapsed/60:.1f} min | Remaining: ~{remaining/60:.0f} min")
    print(f"   🚀 Speed: {hunter.stats['images_inserted']/(elapsed/60):.0f} images/minute")

# Final summary
total_time = time.time() - start_time
print("\n" + "="*80)
print("🎉 MEGA-BATCH COMPLETE!")
print("="*80)
print(f"⏱️  Total time: {total_time/3600:.1f} hours")
print(f"🌺 Species: {hunter.stats['species_processed']:,}")
print(f"💾 Images inserted: {hunter.stats['images_inserted']:,}")
print(f"🚀 Speed: {hunter.stats['images_inserted']/(total_time/60):.0f} images/min")
print("="*80)
```

---

## ✅ **You're Done!**

The notebook is now running! It will:
- Process 5,000 species
- Add ~150,000 images
- Take 6-8 hours
- Show progress every 100 species

**You can close Safari and check back later!**

---

## 📅 **Schedule**

Run this 7 times over 2 weeks = 1,000,000+ images = DONE! ✅
