# Julius AI - Species Master & Image Counts: Next Steps Guide

## ✅ What You've Accomplished

Excellent work on building the species master! You've successfully:

1. **Created species_master.csv** with GBIF-validated species + taxonomy mapping + GBIF image counts
2. **Computed EOL and local image counts** via database joins
3. **Identified data gaps** (e.g., Dendrobium nobile has no EOL page mapped yet)

Your two-species test shows:
- **Dendrobium nobile**: 269 GBIF images, 112 local, 0 EOL (no eol_page_id mapped)
- **Phalaenopsis amabilis**: 258 GBIF images, 48 local, 3 EOL

---

## 🎯 Recommended Next Steps (In Priority Order)

### **Step 1: Expand to Full Dataset** ✅ DO THIS FIRST

**Answer to your question**: **YES, expand to your full driver list!**

Use all GBIF-validated species from the database. Here's the PostgreSQL query to get your complete driver list:

```sql
-- Get all unique species with GBIF images
SELECT DISTINCT 
    oi.genus,
    oi.species,
    oi.genus || ' ' || oi.species as scientific_name,
    COUNT(oi.id) as gbif_image_count
FROM orchid_images oi
WHERE oi.gbif_occurrence_key IS NOT NULL
AND oi.genus IS NOT NULL
AND oi.species IS NOT NULL
GROUP BY oi.genus, oi.species
ORDER BY gbif_image_count DESC;
```

This will give you **all 413 species** with their GBIF image counts.

Then join to taxonomy:

```sql
-- Full species master with taxonomy
SELECT 
    oi.genus || ' ' || oi.species as scientific_name,
    ot.id as taxonomy_id,
    ot.eol_page_id,
    COUNT(oi.id) as gbif_image_count
FROM orchid_images oi
LEFT JOIN orchid_taxonomy ot ON (
    ot.genus = oi.genus 
    AND ot.species = oi.species
)
WHERE oi.gbif_occurrence_key IS NOT NULL
AND oi.genus IS NOT NULL
AND oi.species IS NOT NULL
GROUP BY oi.genus, oi.species, ot.id, ot.eol_page_id
ORDER BY gbif_image_count DESC;
```

**Expected Output**: ~413 rows covering all GBIF species

---

### **Step 2: Compute Complete Image Counts** ✅ DO THIS SECOND

Once you have the full species master, compute EOL + local counts for ALL species:

```sql
-- Complete image count analysis (all sources)
WITH gbif_counts AS (
    SELECT 
        genus || ' ' || species as scientific_name,
        genus,
        species,
        COUNT(*) as gbif_image_count
    FROM orchid_images
    WHERE gbif_occurrence_key IS NOT NULL
    AND genus IS NOT NULL
    AND species IS NOT NULL
    GROUP BY genus, species
),
eol_counts AS (
    SELECT 
        ot.id as taxonomy_id,
        COUNT(eoi.id) as eol_image_count
    FROM eol_orchid_images eoi
    JOIN orchid_taxonomy ot ON ot.eol_page_id = eoi.eol_page_id
    GROUP BY ot.id
),
local_counts AS (
    SELECT 
        or_rec.taxonomy_id,
        COUNT(or_rec.id) as local_image_count
    FROM orchid_records or_rec
    WHERE or_rec.taxonomy_id IS NOT NULL
    GROUP BY or_rec.taxonomy_id
)
SELECT 
    gc.scientific_name,
    ot.id as taxonomy_id,
    ot.eol_page_id,
    COALESCE(gc.gbif_image_count, 0) as gbif_images,
    COALESCE(ec.eol_image_count, 0) as eol_images,
    COALESCE(lc.local_image_count, 0) as local_images,
    COALESCE(gc.gbif_image_count, 0) + 
    COALESCE(ec.eol_image_count, 0) + 
    COALESCE(lc.local_image_count, 0) as total_images
FROM gbif_counts gc
LEFT JOIN orchid_taxonomy ot ON (
    ot.genus = gc.genus 
    AND ot.species = gc.species
)
LEFT JOIN eol_counts ec ON ec.taxonomy_id = ot.id
LEFT JOIN local_counts lc ON lc.taxonomy_id = ot.id
ORDER BY total_images DESC;
```

**Save this as**: `combined_image_counts.csv`

This will show you:
- Which species have the most total media coverage
- Which sources contribute most per species
- Data gaps where species have GBIF images but no EOL/local coverage

---

### **Step 3: Identify High-Priority Species for EOL Backfill** ✅ OPTIONAL

**Answer to your question**: **YES, but strategically!**

Don't backfill ALL missing eol_page_ids. Focus on high-value species:

```sql
-- Species with lots of GBIF images but no EOL page mapped
SELECT 
    oi.genus || ' ' || oi.species as scientific_name,
    COUNT(oi.id) as gbif_image_count,
    ot.id as taxonomy_id,
    ot.eol_page_id,
    CASE 
        WHEN ot.eol_page_id IS NULL THEN 'NEEDS EOL BACKFILL'
        ELSE 'HAS EOL PAGE'
    END as status
FROM orchid_images oi
LEFT JOIN orchid_taxonomy ot ON (
    ot.genus = oi.genus 
    AND ot.species = oi.species
)
WHERE oi.gbif_occurrence_key IS NOT NULL
AND oi.genus IS NOT NULL
AND oi.species IS NOT NULL
GROUP BY oi.genus, oi.species, ot.id, ot.eol_page_id
HAVING COUNT(oi.id) >= 50  -- Focus on species with 50+ GBIF images
ORDER BY gbif_image_count DESC;
```

**Prioritize**: Top 50-100 species with highest GBIF counts that lack EOL pages

---

### **Step 4: Surface Zero-Media Species** ✅ USEFUL FOR PLANNING

**Answer to your question**: **YES, this is valuable intelligence!**

Find species in taxonomy that have NO images from any source:

```sql
-- Species with zero media across all sources
SELECT 
    ot.genus || ' ' || ot.species as scientific_name,
    ot.id as taxonomy_id,
    ot.eol_page_id,
    COALESCE(gbif.count, 0) as gbif_images,
    COALESCE(eol.count, 0) as eol_images,
    COALESCE(local.count, 0) as local_images
FROM orchid_taxonomy ot
LEFT JOIN (
    SELECT genus, species, COUNT(*) as count
    FROM orchid_images
    WHERE gbif_occurrence_key IS NOT NULL
    GROUP BY genus, species
) gbif ON (gbif.genus = ot.genus AND gbif.species = ot.species)
LEFT JOIN (
    SELECT ot2.id, COUNT(eoi.id) as count
    FROM eol_orchid_images eoi
    JOIN orchid_taxonomy ot2 ON ot2.eol_page_id = eoi.eol_page_id
    GROUP BY ot2.id
) eol ON eol.id = ot.id
LEFT JOIN (
    SELECT taxonomy_id, COUNT(*) as count
    FROM orchid_records
    GROUP BY taxonomy_id
) local ON local.taxonomy_id = ot.id
WHERE COALESCE(gbif.count, 0) = 0
AND COALESCE(eol.count, 0) = 0
AND COALESCE(local.count, 0) = 0
ORDER BY ot.genus, ot.species;
```

**Use this list to**:
- Identify rare/poorly documented species
- Target for future GBIF/EOL ingestion
- Understand coverage gaps in your collection

---

## 📊 Deliverables You Should Create

### **1. species_master_full.csv** (Complete)
Columns: `scientific_name`, `taxonomy_id`, `eol_page_id`, `gbif_image_count`

### **2. combined_image_counts_full.csv** (All Sources)
Columns: `scientific_name`, `taxonomy_id`, `eol_page_id`, `gbif_images`, `eol_images`, `local_images`, `total_images`

### **3. eol_backfill_priority.csv** (Top species needing EOL pages)
Columns: `scientific_name`, `gbif_image_count`, `taxonomy_id`, `priority_rank`

### **4. zero_media_species.csv** (Data gaps)
Columns: `scientific_name`, `taxonomy_id`, `eol_page_id`

---

## 🤝 Integration with Orchid Continuum

Once you've created these files, we can:

### **Option A: Upload via Julius API** (If you have file upload capability)
Send CSVs to the platform for admin review

### **Option B: Direct Database Insert** (You have PostgreSQL access!)
You can insert data directly into tables like:
- Update `orchid_taxonomy.eol_page_id` for backfilled species
- Tag high-priority species for enrichment
- Create a new `species_analytics` table with your image count analysis

### **Option C: Share for Manual Review**
Export CSVs and share findings - admin can review and decide on next steps

---

## 🔬 Analysis Questions You Can Answer

With the complete dataset, you can analyze:

1. **Coverage Distribution**: Which genera have best/worst media coverage?
2. **Source Contribution**: Does GBIF, EOL, or local contribute most per genus?
3. **Data Quality**: Are species with more images better taxonomically documented?
4. **Enrichment ROI**: Which species would benefit most from EOL backfill?
5. **Collection Priorities**: Which rare species need targeted image acquisition?

---

## 🚀 Immediate Action Items

**Do these NOW (in order):**

1. ✅ Run the "Full species master" query → Export to `species_master_full.csv`
2. ✅ Run the "Complete image count analysis" query → Export to `combined_image_counts_full.csv`
3. ✅ Run the "High-priority EOL backfill" query → Export to `eol_backfill_priority.csv`
4. ✅ Share the CSVs or key findings from your analysis

**Optional (if you have time):**
- Generate summary statistics (mean/median images per genus, coverage gaps)
- Identify top 10 genera for targeted enrichment
- Create visualization-ready data (genus-level rollups)

---

## 💡 Questions for You

1. **How many total species are in your GBIF dataset?** (Should be ~413 based on earlier work)
2. **Do you want to backfill EOL pages automatically?** (I can help with EOL API integration)
3. **Should we create a new analytics table** in the database to store your image count analysis?
4. **What's your priority**: Coverage analysis? Data quality? Enrichment planning?

---

## 📞 Need Help?

If you get stuck on:
- **SQL queries**: Share the error and I'll help debug
- **Data export**: Let me know if you need different format/structure
- **Analysis direction**: Tell me what insights you're trying to extract
- **Database integration**: I can help write INSERT/UPDATE queries

You're doing great work - this species master and image count analysis is exactly what we need for intelligent enrichment planning! 🌺

---

**Bottom Line**: Run queries 1-3 above on the FULL dataset, export the CSVs, and share your findings. That's your next concrete step! 🚀
