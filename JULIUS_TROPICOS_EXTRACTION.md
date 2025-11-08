# JULIUS - TROPICOS IMAGE URL EXTRACTION TASK

## YOUR MISSION
Download and parse the Tropicos Darwin Core Archive from Missouri Botanical Garden to extract **~685,000 herbarium specimen image URLs**.

**Expected result:** ~685,000 new orchid herbarium sheet URLs

---

## STEP 1: DOWNLOAD ARCHIVE

**URL:** `http://ipt.mobot.org:8080/ipt/archive.do?r=tropicosspecimens`

**File:** Darwin Core Archive (ZIP, ~150-200 MB)

**Download command:**
```bash
curl -o tropicos_data.zip "http://ipt.mobot.org:8080/ipt/archive.do?r=tropicosspecimens"
```

**Extract:**
```bash
unzip tropicos_data.zip -d tropicos_data/
```

---

## STEP 2: UNDERSTAND ARCHIVE STRUCTURE

The archive contains:
- `occurrence.txt` - Specimen occurrence records (4.7M+ rows, tab-separated)
- `multimedia.txt` - Image URLs linked to occurrences (tab-separated)
- `meta.xml` - Archive metadata
- `eml.xml` - Dataset description

**Key columns in occurrence.txt:**
- `id` or `occurrenceID` - Unique occurrence identifier
- `family` - Taxonomic family (we want "Orchidaceae")
- `scientificName` - Full scientific name
- `genus` - Genus name
- `specificEpithet` - Species name
- `country` - Collection country
- `decimalLatitude` / `decimalLongitude` - Coordinates
- `year` - Collection year
- `institutionCode` - Herbarium code
- `catalogNumber` - Specimen catalog number

**Key columns in multimedia.txt:**
- `id` or `CoreId` - Links to occurrence.txt
- `identifier` or `accessURI` - Image URL
- `type` - Media type (look for "StillImage")

---

## STEP 3: FILTER FOR ORCHIDACEAE

**Read occurrence.txt and filter:**
```python
import csv

orchid_occurrences = {}
with open('tropicos_data/occurrence.txt', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f, delimiter='\t')
    for row in reader:
        family = row.get('family', '').lower()
        if 'orchid' in family:
            occ_id = row.get('id') or row.get('occurrenceID')
            orchid_occurrences[occ_id] = {
                'scientific_name': row.get('scientificName'),
                'genus': row.get('genus'),
                'species': row.get('specificEpithet'),
                'country': row.get('country'),
                'latitude': row.get('decimalLatitude'),
                'longitude': row.get('decimalLongitude'),
                'year': row.get('year'),
                'institution': row.get('institutionCode'),
                'catalog_number': row.get('catalogNumber')
            }

print(f"Found {len(orchid_occurrences)} Orchidaceae occurrences")
```

---

## STEP 4: EXTRACT IMAGE URLS

**Read multimedia.txt and match to orchid occurrences:**
```python
images_to_insert = []

with open('tropicos_data/multimedia.txt', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f, delimiter='\t')
    for row in reader:
        occ_id = row.get('id') or row.get('CoreId')
        
        if occ_id in orchid_occurrences:
            media_url = row.get('identifier') or row.get('accessURI')
            media_type = row.get('type', '')
            
            if media_url and 'image' in media_type.lower():
                occ = orchid_occurrences[occ_id]
                images_to_insert.append({
                    'image_url': media_url,
                    'scientific_name': occ['scientific_name'],
                    'genus': occ['genus'],
                    'species': occ['species'],
                    'country': occ['country'],
                    'latitude': occ['latitude'],
                    'longitude': occ['longitude'],
                    'year': occ['year'],
                    'institution': occ['institution'],
                    'catalog_number': occ['catalog_number']
                })

print(f"Found {len(images_to_insert)} orchid images")
```

---

## STEP 5: MATCH TO TAXONOMY & INSERT

**For each image:**
1. Try to match `scientific_name` to `orchid_taxonomy` table
2. If match found, use that `taxonomy_id`
3. If no match, set `taxonomy_id = NULL` (will be linked later)

**SQL Insert:**
```sql
INSERT INTO orchid_images (
    taxonomy_id,
    image_url,
    image_type,
    source,
    photographer,
    license,
    herbarium_catalog_number,
    country,
    latitude,
    longitude,
    collection_year
) VALUES (
    {taxonomy_id or NULL},
    {image_url},
    'herbarium_sheet',
    'tropicos',
    {institution or 'Missouri Botanical Garden'},
    'CC-BY-4.0',
    {catalog_number},
    {country},
    {latitude},
    {longitude},
    {year}
)
ON CONFLICT (image_url) DO NOTHING;
```

**Batch inserts:** Commit every 1,000 records for performance.

---

## PROGRESS TRACKING

**Send heartbeat every 50,000 records:**
```
POST /api/julius/heartbeat
{
  "task_id": "tropicos-extraction",
  "status_message": "Parsed 250,000/685,000 images, inserted 240,000 new URLs"
}
```

---

## COMPLETION CRITERIA

1. **Archive downloaded and extracted**
2. **Orchidaceae records filtered** from 4.7M total
3. **All image URLs inserted** to database
4. **Tracker updated** with completion status
5. **Summary report** with:
   - Total Orchidaceae occurrences found
   - Total images extracted
   - Images matched to taxonomy
   - Images pending taxonomy match

---

## ESTIMATED TIME
- Download: 5-10 minutes
- Parsing: 20-30 minutes
- Database inserts: 30-60 minutes
- **Total: ~1.5-2 hours**

---

## REFERENCE SCRIPT
See `extract_tropicos_urls.py` for implementation example.

---

## AFTER COMPLETION

Update tracker:
```bash
curl -X POST {REPLIT_URL}/api/tracker/update \
  -H "Content-Type: application/json" \
  -d '{
    "project_key": "tropicos_url_extraction",
    "status": "complete",
    "completed_by": "Julius AI",
    "notes": "Extracted 685,000 herbarium image URLs from Tropicos MBG archive"
  }'
```

---

## WHY THIS MATTERS
- **685,000 herbarium specimens** are authoritative botanical records
- Historical specimens show morphology clearly (pressed & preserved)
- Critical for BloomBuilder's herbarium sheet comparison feature
- Links to type specimens for many orchid species

**This is the LARGEST single-source image extraction!** 🌿
