# Julius AI - Orchid Continuum Database Connection Guide

## ✅ Database Status: ACCESSIBLE

**Connection String**: Available via PostgreSQL direct connection
**Database**: PostgreSQL on Neon (ep-snowy-firefly-afvebui7.c-2.us-west-2.aws.neon.tech/neondb)

---

## 🔑 Critical Schema Information

### **CORRECT Join Column Names**

❌ **WRONG**: `orchid_images.orchid_taxonomy_id`  
✅ **CORRECT**: `orchid_images.taxonomy_id`

### **Table Schemas**

**orchid_taxonomy** (35,320 total taxa):
- `id` INTEGER - Primary key
- `genus` VARCHAR
- `species` VARCHAR  
- `scientific_name` VARCHAR
- `eol_page_id` INTEGER - **IMPORTANT: 95% NULL (33,774 missing)**
- `external_ids` JSONB - Contains eol_page_id as JSON
- `eol_last_synced_at` TIMESTAMP

**orchid_images** (10,534 GBIF images):
- `id` INTEGER - Primary key
- `taxonomy_id` INTEGER - **This is the foreign key to orchid_taxonomy.id**
- `gbif_occurrence_key` VARCHAR
- `image_url` TEXT
- `wild_specimen` BOOLEAN
- `latitude`, `longitude` NUMERIC
- `country`, `state_province`, `locality` - Geographic data

---

## 📊 Current Data Status

### **Image Counts Summary**
- **Total species**: 35,320
- **Species with local images**: ~400
- **Species with eol_page_id**: 1,546 (4.4%)
- **Species missing eol_page_id**: 33,774 (95.6%)

### **Top Species by Local Image Count**
1. Epidendrum paniculatum - 313 images (missing eol_page_id)
2. Cymbidium goeringii - 310 images (has eol_page_id: 1092726)
3. Oncidium sphacelatum - 310 images (missing eol_page_id)
4. Bulbophyllum species - 300 images (missing eol_page_id)
5. Pleurothallis liripipia - 300 images (missing eol_page_id)

---

## 🔧 Correct Query Examples

### **Combined Image Counts** (Local + EOL)

```sql
SELECT 
    ot.genus,
    ot.species,
    ot.scientific_name,
    ot.eol_page_id,
    COUNT(DISTINCT oi.id) as local_image_count,
    CASE 
        WHEN ot.eol_page_id IS NULL THEN 0 
        ELSE 0  -- EOL images not yet ingested
    END as eol_image_count,
    COUNT(DISTINCT oi.id) as total_combined_count,
    CASE 
        WHEN ot.eol_page_id IS NULL THEN 'missing_eol_id'
        WHEN COUNT(DISTINCT oi.id) = 0 THEN 'zero_local_images'
        ELSE 'has_data'
    END as data_status
FROM orchid_taxonomy ot
LEFT JOIN orchid_images oi ON ot.id = oi.taxonomy_id
WHERE ot.genus IS NOT NULL AND ot.species IS NOT NULL
GROUP BY ot.id, ot.genus, ot.species, ot.scientific_name, ot.eol_page_id
ORDER BY total_combined_count DESC;
```

### **Species Missing EOL Page ID**

```sql
SELECT 
    genus,
    species,
    scientific_name,
    COUNT(*) OVER() as total_missing
FROM orchid_taxonomy
WHERE eol_page_id IS NULL
  AND genus IS NOT NULL 
  AND species IS NOT NULL
ORDER BY genus, species
LIMIT 1000;
```

### **Species with Zero Images from Both Sources**

```sql
SELECT 
    ot.genus,
    ot.species,
    ot.scientific_name,
    ot.eol_page_id,
    COUNT(oi.id) as local_count
FROM orchid_taxonomy ot
LEFT JOIN orchid_images oi ON ot.id = oi.taxonomy_id
WHERE ot.genus IS NOT NULL 
  AND ot.species IS NOT NULL
GROUP BY ot.id, ot.genus, ot.species, ot.scientific_name, ot.eol_page_id
HAVING COUNT(oi.id) = 0
ORDER BY ot.genus, ot.species
LIMIT 1000;
```

---

## 📦 Data Export Files

**combined_image_counts.csv** - Full dataset exported (see attached file)
- Contains all species with local image counts
- Flags missing eol_page_id
- Identifies species needing EOL backfill

---

## 🎯 Julius Tasks - Actionable Steps

### **Task 1: Export Combined Image Counts** ✅ READY
Use the query above or download the exported CSV file.

### **Task 2: Backfill Missing eol_page_id**
- **33,774 species** need EOL search
- Priority: Species with local images first (400 species)
- Use EOL API: `https://eol.org/api/search/1.0.json?q={scientific_name}`

### **Task 3: Identify Species with Zero Media**
- Run the "zero images" query above
- These species need future image ingestion from:
  - EOL API (if eol_page_id exists or can be found)
  - iNaturalist
  - GBIF (additional specimens)
  - Tropicos

---

## 🔒 Connection Notes

- SSL mode required for Neon database
- If using Python: `ssl=require` parameter
- Direct SQL queries work best (avoid ORM complexity for bulk operations)
- Recommended: Use `functions.postgres_query` tool with correct column names above

---

**Last Updated**: October 29, 2025  
**Status**: Database accessible, schema verified, queries corrected ✅
