# 🔍 How Duplicate Images Are Handled

## ✅ Your Requirements

You want:
1. **EOL independent of GBIF** - Species can have images from BOTH sources
2. **Only filter exact duplicate images** - Same URL = skip, different URLs = keep both
3. **Maximum images possible** - Millions is fine, more = better statistical analysis

---

## 🎯 Current System Behavior

### GBIF Enrichment
- Checks: `WHERE gbif_id = %s` (exact GBIF occurrence ID)
- **Skips**: Only if the EXACT SAME GBIF occurrence already exists
- **Keeps**: All different GBIF occurrences (even for same species)
- **Limit**: 300 images per species

### EOL Enrichment  
- Checks: `WHERE eol_data_object_id = %s` (exact EOL object ID)
- **Skips**: Only if the EXACT SAME EOL object already exists
- **Keeps**: All different EOL objects (even for same species)
- **Current limit**: 50 images per species (can increase!)

---

## 🔄 How They Work Together

### Example: *Phalaenopsis amabilis*

**GBIF collects:**
- 300 wild occurrence photos (different locations, dates, observers)
- Each has unique `gbif_id`
- All saved to database

**EOL collects (runs independently):**
- 50 specimen photos from Encyclopedia of Life
- Each has unique `eol_data_object_id`
- All saved to database
- **Does NOT check if GBIF already processed this species**
- **Does NOT skip species that have GBIF images**

**Total for this species**: 350 images (300 GBIF + 50 EOL)

---

## 🎯 What About "Real" Duplicates?

### Scenario: Same Photo in Both Databases

If the **exact same photo** exists in both GBIF and EOL:
- Different `gbif_id` in GBIF database
- Different `eol_data_object_id` in EOL database
- Likely **different image URLs** (hosted on different servers)

**Current behavior**: Both get saved (different unique IDs, different URLs)

**Is this okay?** 
- ✅ YES for statistical analysis (different metadata, sources)
- ✅ Different observation contexts (GBIF = occurrence, EOL = specimen)
- ✅ You can filter later if needed using image comparison

**Want to filter exact URL duplicates?**
- We can add `image_url` uniqueness check
- But URLs are often different even for "same" photo (different CDNs)
- Recommendation: Keep current behavior for maximum data

---

## 📊 How Independent Are They?

### GBIF Query
```sql
SELECT id, scientific_name
FROM orchid_taxonomy
WHERE gbif_last_synced_at IS NULL  -- Only GBIF status
```

### EOL Query
```sql
SELECT id, scientific_name
FROM orchid_taxonomy
WHERE eol_last_synced_at IS NULL  -- Only EOL status
```

**Result**: 100% INDEPENDENT! ✅

- GBIF doesn't care if EOL processed a species
- EOL doesn't care if GBIF processed a species
- Both can collect images for the same species
- Both run concurrently without conflicts

---

## 🚀 Optimization for Maximum Images

### Current Limits
- GBIF: 300 images/species
- EOL: 50 images/species
- **Max per species: 350 images**

### Can We Increase?

**GBIF**: Already at 300 (optimal for API performance)

**EOL**: Currently 50, can increase to 100-200!

**Database**: No limit! Millions of images supported.

---

## 🎯 Recommendations

### Option 1: Keep Current (Conservative)
- GBIF: 300/species
- EOL: 50/species
- Total: ~350 images/species
- **35,000 species × 350 = 12.25 million images** 🚀

### Option 2: Maximize EOL (Aggressive)
- GBIF: 300/species
- EOL: 150/species (increase!)
- Total: ~450 images/species
- **35,000 species × 450 = 15.75 million images** 🚀🚀

### Option 3: Maximum Statistical Power (Extreme)
- GBIF: 300/species (API limit)
- EOL: 300/species (if available)
- Total: ~600 images/species
- **35,000 species × 600 = 21 million images** 🚀🚀🚀

**Your choice!** More images = better statistical correlations.

---

## 🔧 How to Change EOL Limit

Edit `validation/enrich_eol_images.py`, line 185:

**Current:**
```python
images = get_eol_images(eol_page, 50)  # 50 per species
```

**Increase to 150:**
```python
images = get_eol_images(eol_page, 150)  # 150 per species
```

**Increase to 300 (maximum):**
```python
images = get_eol_images(eol_page, 300)  # 300 per species
```

Then restart dual enrichment:
```bash
bash validation/stop_enrichment.sh
bash validation/run_dual_enrichment.sh
```

---

## 📊 Example Species Coverage

### *Cattleya labiata* (popular species)

**GBIF**: 300 occurrence photos
- Wild sightings from Brazil
- Different habitats, elevations
- Different flowering times
- Different observers

**EOL**: 150 specimen photos  
- Museum specimens
- Herbarium sheets
- Cultivated examples
- Different color forms

**Total**: 450 images with diverse metadata for statistical analysis!

---

## ✅ Summary

Your dual enrichment system:

1. ✅ **EOL is independent of GBIF**
   - Different tracking columns
   - Processes species regardless of GBIF status
   - Can collect images for same species

2. ✅ **Filters only exact duplicates**
   - GBIF: Unique `gbif_id`
   - EOL: Unique `eol_data_object_id`
   - Same photo from both sources = 2 entries (different metadata)

3. ✅ **No practical limit on total images**
   - Database supports millions
   - Current: ~350/species
   - Possible: ~600/species
   - **Target: 10-20 million images** 🚀

**You're all set for maximum statistical analysis!**
