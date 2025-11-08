# Julius AI: Find Missing Images & Data for Orchids

## 🎯 Mission: Get Images and Data for Orchids We Don't Have

**Current Status:**
- 5,915 total orchids
- 3,101 have images (52%) → **2,814 need images!**
- Only 21 validated with GBIF
- Most are hybrids/cultivars (not wild species)

---

## 📊 Step 1: Analyze What's Missing

### Query 1: Top Orchids Missing Images
```sql
SELECT 
  id, genus, species, scientific_name,
  source, photographer,
  created_at
FROM orchid_record
WHERE image_url IS NULL
ORDER BY created_at DESC
LIMIT 100;
```

**Julius, can you:**
1. Identify the 100 most important orchids missing images
2. Group them by genus to find patterns
3. Check if they're wild species or hybrids

---

### Query 2: Missing Critical Data
```sql
SELECT 
  id, genus, species,
  CASE WHEN image_url IS NULL THEN 1 ELSE 0 END as missing_image,
  CASE WHEN native_habitat IS NULL THEN 1 ELSE 0 END as missing_habitat,
  CASE WHEN bloom_time IS NULL THEN 1 ELSE 0 END as missing_bloom,
  CASE WHEN water_requirements IS NULL THEN 1 ELSE 0 END as missing_water,
  CASE WHEN light_requirements IS NULL THEN 1 ELSE 0 END as missing_light,
  CASE WHEN cultural_notes IS NULL THEN 1 ELSE 0 END as missing_culture
FROM orchid_record
WHERE 
  image_url IS NULL 
  OR native_habitat IS NULL 
  OR bloom_time IS NULL
ORDER BY 
  (CASE WHEN image_url IS NULL THEN 1 ELSE 0 END +
   CASE WHEN native_habitat IS NULL THEN 1 ELSE 0 END +
   CASE WHEN bloom_time IS NULL THEN 1 ELSE 0 END) DESC
LIMIT 500;
```

**Julius, prioritize orchids missing multiple fields!**

---

## 🔍 Step 2: Identify Data Sources for Different Orchid Types

### Query 3: Wild Species (GBIF Candidates)
```sql
SELECT genus, species, scientific_name, COUNT(*) as count
FROM orchid_record
WHERE 
  scientific_name IS NOT NULL
  AND scientific_name NOT LIKE '%×%'  -- Not a hybrid
  AND scientific_name ~ '^[A-Z][a-z]+ [a-z]+'  -- Proper binomial format
  AND gbif_species_key IS NULL  -- Not yet validated
  AND image_url IS NULL  -- Missing image
GROUP BY genus, species, scientific_name
ORDER BY count DESC
LIMIT 100;
```

**These can use GBIF for images and occurrence data!**

---

### Query 4: Hybrids Needing Alternative Sources
```sql
SELECT 
  genus, species, scientific_name,
  CASE 
    WHEN scientific_name LIKE '%×%' THEN 'Hybrid (× symbol)'
    WHEN genus IN ('Laeliacattleya', 'Potinara', 'Brassocattleya', 'Sophrolaeliocattleya') 
      THEN 'Intergeneric Hybrid'
    WHEN species IS NULL OR species = '' THEN 'Cultivar'
    ELSE 'Unknown'
  END as hybrid_type,
  COUNT(*) as count
FROM orchid_record
WHERE image_url IS NULL
GROUP BY genus, species, scientific_name, hybrid_type
ORDER BY count DESC
LIMIT 200;
```

**Julius, for these hybrids, recommend:**
- ✅ OrchidWiz database (192,000+ hybrids with photos)
- ✅ RHS International Orchid Register (hybrid parentage)
- ✅ Vendor catalogs: Andy's Orchids, Ecuagenera, rePotme
- ✅ Orchid society photo databases (AOS, local societies)
- ✅ AI-generated composite images from parent species

---

## 🌐 Step 3: Web Scraping Opportunities

### Query 5: Orchids from Specific Sources
```sql
SELECT source, COUNT(*) as count, 
  COUNT(CASE WHEN image_url IS NULL THEN 1 END) as missing_images
FROM orchid_record
WHERE source IS NOT NULL
GROUP BY source
ORDER BY missing_images DESC;
```

**Julius, identify sources we can scrape again for missing data**

---

## 🤖 Step 4: AI-Powered Enrichment Strategy

### Option A: Genus-Level Inference for Hybrids
**For hybrids without data, use genus characteristics:**

```sql
-- Find well-documented orchids in same genus
SELECT o1.genus, o1.species,
  o2.native_habitat, o2.bloom_time, 
  o2.water_requirements, o2.light_requirements
FROM orchid_record o1
LEFT JOIN orchid_record o2 
  ON o1.genus = o2.genus 
  AND o2.native_habitat IS NOT NULL
WHERE o1.native_habitat IS NULL
LIMIT 100;
```

**Can we infer Cattleya hybrid requirements from Cattleya species data?**

---

### Option B: Parent Species Data for Hybrids
**Use orchid_parentage table:**

```sql
SELECT 
  op.hybrid_name,
  op.pod_parent,
  op.pollen_parent,
  or1.native_habitat as pod_habitat,
  or2.native_habitat as pollen_habitat,
  or1.bloom_time as pod_bloom,
  or2.bloom_time as pollen_bloom
FROM orchid_parentage op
LEFT JOIN orchid_record or1 ON op.pod_parent LIKE '%' || or1.species || '%'
LEFT JOIN orchid_record or2 ON op.pollen_parent LIKE '%' || or2.species || '%'
WHERE op.hybrid_name IN (
  SELECT scientific_name FROM orchid_record WHERE native_habitat IS NULL
)
LIMIT 100;
```

**Hybrid care = average of parent species requirements!**

---

## 📸 Step 5: Image Source Recommendations

### For Wild Species (300-500 estimated):
1. **GBIF API** - Real specimen photos with location data
2. **iNaturalist** - Community observations with CC licenses
3. **EOL (Encyclopedia of Life)** - Curated species images
4. **Wikimedia Commons** - Free orchid photos

### For Hybrids/Cultivars (5,500+):
1. **OrchidWiz** - Subscription database, 265,000+ photos
2. **AOS Photo Gallery** - American Orchid Society awards
3. **Vendor Websites**:
   - Andy's Orchids (orchidphile.com)
   - Ecuagenera (ecuagenera.com)
   - rePotme (repotme.com)
   - Hausermann's Orchids
4. **Stock Photos**:
   - Unsplash (free, high quality)
   - Pexels (free, commercial use)
   - Search by genus name
5. **AI Generation**:
   - Use OpenAI DALL-E or Stable Diffusion
   - Generate from text descriptions
   - Based on genus characteristics

---

## 🎯 Step 6: Actionable Deliverables for Julius

**Please provide:**

### 1. Priority List (CSV/JSON format)
```json
{
  "orchid_id": 123,
  "genus": "Phalaenopsis",
  "species": "amabilis",
  "missing": ["image", "habitat", "bloom_time"],
  "enrichment_strategy": "GBIF + iNaturalist",
  "priority_score": 85,
  "estimated_success_rate": "High - wild species"
}
```

### 2. Genus-Level Statistics
- Which genera have the best enrichment potential?
- Which need alternative approaches (hybrids)?
- Success rate estimates by genus

### 3. Data Source Mapping
```
Phalaenopsis (wild species): GBIF (90% success expected)
Cattleya (mostly hybrids): Vendor catalogs + stock photos (60% success)
Dendrobium (mixed): GBIF for species, vendors for hybrids (70% success)
```

### 4. Batch Processing Plan
- **Batch 1 (500 orchids)**: Wild species → GBIF enrichment
- **Batch 2 (1000 orchids)**: Popular hybrids → Vendor scraping
- **Batch 3 (500 orchids)**: Rare hybrids → AI generation
- **Batch 4 (814 orchids)**: Remaining → Best effort

### 5. SQL Scripts for Auto-Enrichment
- Scripts to populate data from similar orchids
- Genus-level inference queries
- Parent species averaging for hybrids

---

## 🚀 Expected Outcomes

**Realistic Targets:**
- **Images**: 52% → 85% (add 1,950+ images)
  - Wild species: GBIF/iNaturalist (300 images)
  - Popular hybrids: Vendors/AOS (1,000 images)
  - Stock photos by genus: (650 images)
  
- **Habitat Data**: 8% → 60% (add 3,075 records)
  - Wild species: GBIF occurrence (300)
  - Genus inference: (2,000)
  - Parent averaging: (775)

- **Bloom/Care Data**: 15% → 70% (add 3,253 records)
  - Vendor catalog scraping
  - Genus-level defaults
  - AI-generated recommendations

---

## 🔑 Connection Info

**PostgreSQL:**
```
postgresql://neondb_owner:npg_feOt1Ek0KLrF@ep-snowy-firefly-afvebui7.c-2.us-west-2.aws.neon.tech/neondb?sslmode=require
```

**API Access:**
```
curl -H "X-API-Key: julius_fvLLggj7H8MsvQShwbSSzeZGrUPrLNnMMuhnoWW9FVI" \
  https://[app-url]/api/julius/stats/overview
```

---

## 📋 Julius, Your Task:

1. **Run all the queries above** to analyze the database
2. **Identify the 500 highest-priority orchids** for enrichment
3. **Map each orchid to the best data source** (GBIF, vendors, AI, etc.)
4. **Provide a realistic enrichment plan** with success rate estimates
5. **Generate CSV/JSON output** with orchid IDs and recommended actions
6. **Suggest automation opportunities** (genus inference, parent averaging)

**BONUS: If you can directly find image URLs from sources like Unsplash, Wikimedia Commons, or identify vendor pages to scrape - that would be AMAZING!**

---

**Ready to start? Connect to the database and let's get these 2,814 orchids their images! 🌸📸**
