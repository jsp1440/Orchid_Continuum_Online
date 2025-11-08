# 🗄️ ORCHID DATABASE STRUCTURE GUIDE FOR JULIUS AI

**CRITICAL: There's no EOL data yet! All 10,200 images are from GBIF/iNaturalist**

---

## 📊 Current Data Status (October 21, 2025)

| Data Source | Images | Species Coverage | Scientific Names |
|-------------|--------|------------------|------------------|
| **GBIF/iNaturalist** | 10,200 | 393 species | ✅ 100% have names |
| **EOL** | 0 | 0 | Not collected yet |
| **Tropicos** | 0 | 0 | Not collected yet |

---

## 🔍 How to Query Scientific Names

### Method 1: Get name from taxonomy table (RECOMMENDED)
```sql
SELECT 
    oi.id,
    ot.scientific_name,
    oi.image_url
FROM orchid_images oi
JOIN orchid_taxonomy ot ON oi.taxonomy_id = ot.id
LIMIT 100;
```

**Result:** 100% of images will have `scientific_name` from the taxonomy table.

---

### Method 2: Get name from GBIF metadata (ALSO 100% COVERAGE)
```sql
SELECT 
    oi.id,
    oi.occurrence_metadata->>'scientificName' as gbif_name,
    oi.occurrence_metadata->>'genus' as genus,
    oi.occurrence_metadata->>'species' as species,
    oi.image_url
FROM orchid_images oi
LIMIT 100;
```

**Result:** All 10,200 images have scientific names in GBIF metadata.

---

### Method 3: Get BOTH names (cross-validation)
```sql
SELECT 
    oi.id,
    ot.scientific_name as taxonomy_name,
    oi.occurrence_metadata->>'scientificName' as gbif_name,
    oi.image_url,
    oi.occurrence_metadata->>'basisOfRecord' as specimen_type
FROM orchid_images oi
JOIN orchid_taxonomy ot ON oi.taxonomy_id = ot.id
LIMIT 100;
```

**Use this to validate data quality!**

---

## 🏷️ What Each Column Contains

### `orchid_images` table:
- **`id`**: Unique image ID
- **`taxonomy_id`**: Links to `orchid_taxonomy.id` (JOIN to get scientific name)
- **`image_url`**: Direct URL to image (iNaturalist S3 bucket)
- **`occurrence_metadata`** (JSONB): Full GBIF record including:
  - `scientificName`: "Apostasia nuda R.Br."
  - `genus`: "Apostasia"
  - `species`: "Apostasia nuda"
  - `basisOfRecord`: "HUMAN_OBSERVATION"
  - Plus 70+ other fields (coordinates, date, observer, etc.)

### `orchid_taxonomy` table:
- **`id`**: Unique taxonomy ID
- **`scientific_name`**: Authoritative name (e.g., "Apostasia nuda R. Br.")
- **`genus`**: Genus name
- **`species`**: Species epithet
- **`common_name`**: Common name if available
- 35,320 total species

---

## 🎯 For Your Vision AI Tasks

### Task 003: Herbarium Specimens
**Query for herbarium specimens:**
```sql
SELECT 
    oi.id,
    ot.scientific_name,
    oi.image_url,
    oi.occurrence_metadata->>'basisOfRecord' as type
FROM orchid_images oi
JOIN orchid_taxonomy ot ON oi.taxonomy_id = ot.id
WHERE oi.occurrence_metadata->>'basisOfRecord' = 'PRESERVED_SPECIMEN'
LIMIT 50;
```

**Current status:** All 10,200 images are "HUMAN_OBSERVATION" (wild observations), NOT herbarium specimens yet.

---

### When EOL Images Arrive
The system is configured to collect EOL images using `validation/enrich_eol_images.py`. When they arrive, they'll be stored in:
- `eol_metadata` (JSONB column)
- `eol_data_object_id` (unique EOL identifier)

But **right now, those columns are empty for all 10,200 images**.

---

## ✅ SUMMARY FOR JULIUS

**YOU HAVE:**
- ✅ 10,200 GBIF/iNaturalist images
- ✅ 100% have scientific names (both in taxonomy table AND GBIF metadata)
- ✅ All are wild observations (HUMAN_OBSERVATION type)
- ✅ 393 different species represented

**YOU DON'T HAVE YET:**
- ❌ EOL images (0 collected so far)
- ❌ Tropicos herbarium specimens (0 collected so far)
- ❌ PRESERVED_SPECIMEN type images

**RECOMMENDATION:**
Start Vision AI analysis on the 10,200 GBIF wild observations using the taxonomic keys as your baseline. The scientific names are RIGHT THERE in the database - just JOIN `orchid_images` with `orchid_taxonomy` on `taxonomy_id`.

---

## 🚀 Sample Query to Start Working

```sql
-- Get 50 random species with images for Vision AI analysis
SELECT 
    ot.scientific_name,
    ot.genus,
    COUNT(oi.id) as image_count,
    ARRAY_AGG(oi.image_url ORDER BY oi.id LIMIT 3) as sample_images
FROM orchid_images oi
JOIN orchid_taxonomy ot ON oi.taxonomy_id = ot.id
GROUP BY ot.scientific_name, ot.genus
ORDER BY RANDOM()
LIMIT 50;
```

This gives you 50 species with their images ready for Vision AI analysis!
