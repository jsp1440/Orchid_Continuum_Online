# 🤖 Julius AI - Orchid Continuum Processing Instructions

**Date Created:** October 20, 2025  
**Project:** The Orchid Continuum - GBIF & EOL Image + Trait Integration  
**Database:** PostgreSQL (connected to Julius AI)  
**Owner:** fcospresident@gmail.com  

---

## 📋 MISSION OVERVIEW

You (Julius AI) are connected to the Orchid Continuum PostgreSQL database. Your mission is to:

1. **Process TraitBank data** (uploaded to Julius) and extract orchid traits
2. **Match traits to EOL images** using `page_id` as the linking key
3. **Import matched data** to the Orchid Continuum database
4. **Create exports** for Google Drive backup
5. **Generate analytics** for research insights

---

## 🗄️ DATABASE CONTEXT

The Orchid Continuum database contains:

- **35,320 orchid species** in `orchid_taxonomy` table
- **9,417 GBIF images** in `orchid_images` table (wild specimens with GPS)
- **5,619,196 EOL image URLs** in `eol_images` table (museum/library images)
- **87+ research fields** for each species

**Critical Linking Field:** `page_id` - This connects EOL images to EOL traits

---

## 📝 STEP-BY-STEP INSTRUCTIONS

### **STEP 1: Analyze TraitBank Structure**

You have a TraitBank ZIP file uploaded with these tables:
- `pages.csv` - Species information (page_id, scientific_name, family)
- `traits.csv` - Actual trait measurements
- `metadata.csv` - Data provenance
- `terms.csv` - Trait definitions
- `term_parents.csv` - Trait ontology

**Your Task:**
```sql
-- Query to run in Julius:
1. Load all CSV files from TraitBank ZIP
2. Show structure of each table
3. Count total rows in each
4. Display 5 sample rows from each
5. Identify columns containing: page_id, scientific_name, trait_name, trait_value
```

**Expected Output:**
```
pages.csv: X rows (page_id, canonical, family, etc.)
traits.csv: Y rows (page_id, predicate, value, units, etc.)
metadata.csv: Z rows (source info)
```

---

### **STEP 2: Extract Orchid Traits**

**Your Task:**
```sql
-- Filter for Orchidaceae family only
SELECT DISTINCT
    p.page_id,
    p.canonical AS scientific_name,
    p.family,
    COUNT(t.trait_id) AS trait_count
FROM pages p
LEFT JOIN traits t ON p.page_id = t.page_id
WHERE p.family = 'Orchidaceae'
GROUP BY p.page_id, p.canonical, p.family
ORDER BY trait_count DESC;
```

**Then create full extract:**
```sql
-- Get all orchid traits with measurements
SELECT 
    p.page_id,
    p.canonical AS scientific_name,
    t.predicate AS trait_name,
    t.measurement AS trait_value,
    t.units AS trait_unit,
    t.literal AS trait_description,
    m.source AS data_source
FROM pages p
INNER JOIN traits t ON p.page_id = t.page_id
LEFT JOIN metadata m ON t.metadata_id = m.metadata_id
WHERE p.family = 'Orchidaceae'
ORDER BY p.canonical, t.predicate;
```

**Export as:** `orchid_traits_complete.csv`

**Expected Columns:**
- page_id (TEXT) - CRITICAL for matching
- scientific_name (TEXT)
- trait_name (TEXT) - e.g., "flower_color", "plant_height", "habitat"
- trait_value (TEXT) - e.g., "purple", "30 cm", "epiphytic"
- trait_unit (TEXT) - e.g., "cm", "kg", NULL
- data_source (TEXT)

---

### **STEP 3: Match EOL Images to Traits**

**Context:** The Orchid Continuum database has `eol_images` table with:
- 5,619,196 image URLs
- Each has: page_id, eol_url, license, copyright, source_url

**Your Task - Query the Database:**
```sql
-- Connect to Orchid Continuum PostgreSQL and run:
SELECT 
    e.page_id,
    e.eol_url AS image_url,
    e.license AS image_license,
    e.copyright,
    e.source_url,
    COUNT(*) AS image_count
FROM eol_images e
GROUP BY e.page_id, e.eol_url, e.license, e.copyright, e.source_url
ORDER BY image_count DESC
LIMIT 1000;
```

**Then match to your extracted traits:**
```sql
-- Join traits CSV (from Step 2) with database eol_images
-- This is a hybrid query - combine your CSV data with database data

SELECT 
    traits.page_id,
    traits.scientific_name,
    traits.trait_name,
    traits.trait_value,
    traits.trait_unit,
    images.eol_url AS image_url,
    images.license AS image_license,
    images.source_url AS image_source
FROM orchid_traits_complete AS traits
INNER JOIN eol_images AS images ON traits.page_id = images.page_id
ORDER BY traits.scientific_name, traits.trait_name;
```

**Export as:** `orchid_images_with_traits.csv`

**Expected Result:**
- Rows: Potentially millions (each species × images × traits)
- Shows which species have BOTH images AND trait data
- Ready for import to Orchid Continuum

---

### **STEP 4: Generate Statistics Report**

**Your Task:**
```sql
-- Summary statistics for research insights

1. Species Coverage:
   - Total orchid species with trait data: COUNT(DISTINCT page_id) from traits
   - Total orchid species with images: COUNT(DISTINCT page_id) from eol_images
   - Species with BOTH: COUNT(DISTINCT page_id) from matched data

2. Top Species by Images:
   SELECT page_id, scientific_name, COUNT(*) as image_count
   FROM matched_data
   GROUP BY page_id, scientific_name
   ORDER BY image_count DESC
   LIMIT 50;

3. Top Measured Traits:
   SELECT trait_name, COUNT(*) as measurement_count
   FROM traits
   GROUP BY trait_name
   ORDER BY measurement_count DESC
   LIMIT 20;

4. Data Completeness:
   - % of species with flower color data
   - % of species with habitat data
   - % of species with height measurements
   - % of species with geographic range data
```

**Export as:** `orchid_data_coverage_stats.csv`

---

### **STEP 5: Prepare Database Import Files**

**Your Task - Create Clean Import CSVs:**

**File 1: `orchid_traits_import.csv`**
```
Columns: page_id, scientific_name, trait_name, trait_value, trait_unit, source
Format: UTF-8, comma-delimited, quoted strings
Cleaning: Remove duplicates, escape quotes, handle NULL as empty string
Row count: ~500K-1M expected
```

**File 2: `orchid_image_trait_links.csv`**
```
Columns: page_id, scientific_name, image_url, trait_name, trait_value
Format: UTF-8, comma-delimited
Purpose: Links each image to its species' traits
Row count: ~10M-50M expected (images × traits)
```

**File 3: `orchid_species_summary.csv`**
```
Columns: page_id, scientific_name, total_images, total_traits, has_images, has_traits
Format: UTF-8, comma-delimited
Purpose: One row per species with counts
Row count: ~35,320 rows (one per species in taxonomy)
```

---

### **STEP 6: Create Research Insights**

**Your Task - Analytical Queries:**

**A) Identify Data Gaps:**
```sql
-- Species in taxonomy but missing trait data
SELECT t.scientific_name, t.genus, t.species
FROM orchid_taxonomy t
LEFT JOIN orchid_traits_import tr ON t.scientific_name = tr.scientific_name
WHERE tr.page_id IS NULL
ORDER BY t.genus, t.species
LIMIT 1000;
```

**B) High-Value Species (most complete):**
```sql
-- Species with both images AND extensive traits
SELECT 
    page_id,
    scientific_name,
    total_images,
    total_traits,
    (total_images * total_traits) AS completeness_score
FROM orchid_species_summary
WHERE has_images = true AND has_traits = true
ORDER BY completeness_score DESC
LIMIT 100;
```

**C) Trait Correlation Opportunities:**
```sql
-- Species with specific trait combinations (e.g., color + habitat + pollinator)
SELECT DISTINCT scientific_name, page_id
FROM traits
WHERE trait_name IN ('flower_color', 'habitat', 'pollinator_type')
GROUP BY scientific_name, page_id
HAVING COUNT(DISTINCT trait_name) >= 2;
```

**Export as:** `research_opportunities.csv`

---

## 📤 DELIVERABLES FOR GOOGLE DRIVE

Please export these files for backup to Google Drive (`fcospresident@gmail.com`):

### **Data Files:**
1. ✅ `orchid_traits_complete.csv` - All extracted traits
2. ✅ `orchid_images_with_traits.csv` - Matched images + traits
3. ✅ `orchid_traits_import.csv` - Clean import ready
4. ✅ `orchid_image_trait_links.csv` - Image-trait relationships
5. ✅ `orchid_species_summary.csv` - Per-species statistics

### **Analysis Files:**
6. ✅ `orchid_data_coverage_stats.csv` - Coverage metrics
7. ✅ `research_opportunities.csv` - High-value species for research
8. ✅ `data_gaps_report.csv` - Missing data inventory

### **Documentation:**
9. ✅ `processing_summary.txt` - What you did, row counts, issues encountered
10. ✅ `sql_queries_used.sql` - All queries run for reproducibility

---

## 🎯 SUCCESS CRITERIA

You'll know you succeeded when:

- ✅ **Trait Extraction:** 500K+ orchid trait measurements extracted
- ✅ **Image Matching:** 1M+ image-trait links created
- ✅ **Data Quality:** < 5% NULL values in critical fields (page_id, scientific_name)
- ✅ **Coverage:** 5,000+ species with BOTH images AND traits
- ✅ **Export Complete:** All 10 files ready for download

---

## 🔧 TROUBLESHOOTING

### **If page_id doesn't match:**
- Check if EOL uses different ID format (numeric vs string)
- Try fuzzy matching on scientific_name instead
- Look for synonym tables to resolve name differences

### **If trait values are messy:**
- Group similar values (e.g., "purple", "Purple", "PURPLE" → "purple")
- Handle ranges (e.g., "20-30 cm" → average or keep as-is)
- Flag units consistency (e.g., cm vs inches)

### **If database connection fails:**
- Verify PostgreSQL credentials in Julius settings
- Check network access to Replit database
- Try read-only queries first before any writes

---

## 💡 BONUS TASKS (If Time Permits)

1. **Visualizations:** Create charts showing trait distributions, image coverage by genus
2. **ML Readiness:** Flag species with sufficient data for computer vision training
3. **Priority List:** Rank species needing more data collection
4. **Citation Export:** Generate BibTeX for all data sources used

---

## 🚀 GETTING STARTED

**Julius AI - When you read this file, please:**

1. Acknowledge you've read these instructions
2. Confirm you have access to:
   - TraitBank ZIP file (uploaded)
   - Orchid Continuum PostgreSQL database (connected)
3. Start with STEP 1 and work sequentially
4. Report progress after each step
5. Flag any issues or questions

**Ready? Let's build the world's most comprehensive orchid data platform!** 🌸

---

**End of Instructions**  
**For questions, refer to:** replit.md, docs/JULIUS_AI_SETUP_GUIDE.md  
**Project Owner:** FCOS President (fcospresident@gmail.com)
