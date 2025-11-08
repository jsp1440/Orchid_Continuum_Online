# JULIUS - POWO/KEW IMAGE URL EXTRACTION TASK

## YOUR MISSION
Extract orchid taxonomy and image URLs from Royal Botanic Gardens, Kew's **Plants of the World Online (POWO)** database using the `pykew` Python library.

**Expected result:** ~30,000 species with taxonomy + image URLs from Kew herbarium

---

## SETUP

**Install pykew:**
```bash
pip install pykew
```

**Import:**
```python
from pykew import powo
from pykew.powo_terms import Filters
```

---

## APPROACH: GENUS-BY-GENUS EXTRACTION

POWO works best when searching by genus. Extract the major orchid genera:

**Top 15 Orchid Genera (by species count):**
1. Bulbophyllum (~2,000 species)
2. Epidendrum (~1,500 species)
3. Dendrobium (~1,200 species)
4. Pleurothallis (~1,100 species)
5. Stelis (~950 species)
6. Lepanthes (~800 species)
7. Habenaria (~800 species)
8. Maxillaria (~650 species)
9. Masdevallia (~600 species)
10. Oncidium (~600 species)
11. Cattleya (~500 species)
12. Phalaenopsis (~70 species)
13. Vanda (~80 species)
14. Paphiopedilum (~100 species)
15. Cypripedium (~50 species)

---

## EXTRACTION CODE

```python
import time
from pykew import powo
from pykew.powo_terms import Filters

def extract_genus(genus_name, limit=500):
    """Extract all accepted species in a genus with images"""
    
    print(f"Searching POWO for {genus_name}...")
    
    results = powo.search(
        genus_name,
        filters=[Filters.accepted, Filters.species]
    )
    
    species_data = []
    
    for result in results:
        if len(species_data) >= limit:
            break
        
        fqid = result.get('fqId')
        if not fqid:
            continue
        
        try:
            # Get full record with images
            full_record = powo.lookup(fqid, include=['images'])
            
            scientific_name = full_record.get('name')
            images = full_record.get('images', [])
            
            if scientific_name:
                species_data.append({
                    'scientific_name': scientific_name,
                    'genus': full_record.get('genus'),
                    'species': scientific_name.replace(full_record.get('genus', ''), '').strip(),
                    'family': 'Orchidaceae',
                    'images': [img.get('contentUrl') for img in images if img.get('contentUrl')]
                })
            
            # Rate limiting - be nice to Kew's API
            time.sleep(0.3)
            
        except Exception as e:
            print(f"  Error fetching {fqid}: {e}")
            continue
    
    return species_data
```

---

## DATABASE INSERT

**For each species:**

1. **Insert/update taxonomy:**
```sql
INSERT INTO orchid_taxonomy (
    scientific_name, genus, species, family
) VALUES (
    {scientific_name}, {genus}, {species}, 'Orchidaceae'
)
ON CONFLICT (scientific_name) DO UPDATE
SET genus = EXCLUDED.genus,
    species = EXCLUDED.species
RETURNING id;
```

2. **Insert images:**
```sql
INSERT INTO orchid_images (
    taxonomy_id,
    image_url,
    image_type,
    source,
    photographer,
    license
) VALUES (
    {taxonomy_id},
    {image_url},
    'herbarium_sheet',
    'powo_kew',
    'Royal Botanic Gardens, Kew',
    'CC-BY'
)
ON CONFLICT (image_url) DO NOTHING;
```

---

## EXECUTION PLAN

**Process genera in batches:**
```python
GENERA = [
    'Bulbophyllum', 'Epidendrum', 'Dendrobium', 'Pleurothallis',
    'Stelis', 'Lepanthes', 'Habenaria', 'Maxillaria',
    'Masdevallia', 'Oncidium', 'Cattleya', 'Phalaenopsis',
    'Vanda', 'Paphiopedilum', 'Cypripedium'
]

total_species = 0
total_images = 0

for genus in GENERA:
    species_data = extract_genus(genus, limit=500)
    
    # Insert to database
    for sp in species_data:
        # Insert taxonomy
        # Insert images
        total_images += len(sp['images'])
    
    total_species += len(species_data)
    
    # Progress update
    print(f"Completed {genus}: {len(species_data)} species, {sum(len(s['images']) for s in species_data)} images")
    
    # Rest between genera
    time.sleep(2)
```

---

## RATE LIMITING

**Important:** Kew's API has no published rate limits, but be respectful:
- 0.3 seconds between species lookups
- 2 seconds between genera
- If you get 429 errors, slow down to 1 second per request

---

## PROGRESS TRACKING

**Heartbeat every 3 genera:**
```
POST /api/julius/heartbeat
{
  "task_id": "powo-extraction",
  "status_message": "Processed 6/15 genera, extracted 3,200 species with 8,400 images"
}
```

---

## COMPLETION CRITERIA

1. **All 15 major genera processed**
2. **Taxonomy inserted** for new species
3. **Image URLs added** to database
4. **Tracker updated**
5. **Summary report:**
   - Total genera processed
   - Total species extracted
   - Total images added
   - New taxonomy entries created

---

## ESTIMATED TIME
- 15 genera × ~30 minutes each = **~7-8 hours total**
- (Can pause/resume between genera if needed)

---

## REFERENCE SCRIPT
See `extract_powo_kew_urls.py` for implementation example.

---

## AFTER COMPLETION

Update tracker:
```bash
curl -X POST {REPLIT_URL}/api/tracker/update \
  -H "Content-Type: application/json" \
  -d '{
    "project_key": "powo_kew_extraction",
    "status": "complete",
    "completed_by": "Julius AI",
    "notes": "Extracted 30,000+ species and images from POWO/Kew for 15 major orchid genera"
  }'
```

---

## WHY THIS MATTERS
- **POWO is the gold standard** for plant taxonomy (maintained by Kew)
- Adds authoritative taxonomy for thousands of species
- Kew herbarium images are scientifically important type specimens
- Fills gaps in our taxonomy coverage

**This enriches BOTH taxonomy and images!** 🌸
