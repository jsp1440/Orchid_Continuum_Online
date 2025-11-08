# 🚧 Zenodo EOL Mapping Problem & Solution

## ❌ **Current Problem**

### The Chicken-and-Egg Issue
1. Zenodo CSV files have **5.6M images** linked to **EOL page IDs**
2. Our database has **35,320 orchid species** with **scientific names**
3. **Missing link**: We need to map scientific names → EOL page IDs
4. The `enrich_eol_from_zenodo.py` script tries to use EOL API to get this mapping
5. **EOL API times out** on Replit → mapping fails → no images collected

### CSV Format (No Species Names!)
```
EOL content ID, EOL page ID, Source URL, EOL URL, License, Copyright
4, 47191960, https://flickr.com/..., https://content.eol.org/..., cc-by, BHL
```

**Problem**: CSV files only have page IDs, NOT species names!

---

## ✅ **SOLUTIONS**

### Option 1: Julius AI Gets the Page ID Mapping
**Julius can access EOL API from his environment (different network)**

1. Give Julius list of our 35,320 orchid species names
2. Julius calls EOL API to get page ID for each species
3. Julius writes page IDs back to our database (ai_communication table)
4. We update orchid_taxonomy.external_ids with EOL page IDs
5. Then run Zenodo integration (no API needed - just look up page IDs!)

**Time**: ~8-10 hours (Julius processes ~1 species/second with API delays)  
**Cost**: FREE (Julius already has $20 budget)  
**Success Rate**: High (Julius has independent network access)

### Option 2: Find Existing EOL Page ID Mapping Database
**Check if anyone has published a species name → EOL page ID mapping**

Possibilities:
- Zenodo might have a separate mapping file
- EOL might have downloadable taxonomy CSVs
- GBIF might include EOL page IDs in their data

**Need to research**: https://zenodo.org/records/17210269 (check all files in dataset)

### Option 3: Extract Page IDs from Image URLs
**Some URLs might contain species information**

Looking at sample URLs:
- `https://www.flickr.com/photos/biodivlibrary/10036174384/`
- `https://static.inaturalist.org/photos/6355554/original.jpeg`

**Problem**: URLs don't contain species names either!

### Option 4: Use Images WITHOUT Taxonomy Links
**Save all 5.6M images to database without species matching**

**Pros**: Get all the images  
**Cons**: Can't filter by species, defeats the whole purpose  
**Verdict**: ❌ BAD IDEA

---

## 🎯 **RECOMMENDED SOLUTION: Julius Gets the Mapping**

### Step 1: Create Task for Julius
```python
# Create ai_communication task
task_data = {
    "task_id": "eol_page_id_mapping_20251021",
    "from_agent": "replit",
    "to_agent": "julius",
    "message_type": "eol_mapping",
    "status": "pending",
    "task_details": {
        "operation": "get_eol_page_ids",
        "species_list": [list of all 35,320 species scientific names],
        "instructions": "For each species, call EOL search API to get page_id, save to database"
    }
}
```

### Step 2: Julius Processes Task
```python
# Julius pseudo-code
for each species in species_list:
    page_id = requests.get(f'https://eol.org/api/search/1.0.json?q={species}')
    save_to_database(species_name, page_id)
```

### Step 3: We Update Our Database
```sql
-- Update orchid_taxonomy with EOL page IDs from Julius results
UPDATE orchid_taxonomy
SET external_ids = external_ids || jsonb_build_object('eol_page_id', julius_results.page_id)
FROM julius_eol_mapping_results
WHERE orchid_taxonomy.scientific_name = julius_results.species_name;
```

### Step 4: Run Zenodo Integration (No API!)
```python
# Now enrich_eol_from_zenodo.py works WITHOUT API calls:
for each species:
    page_id = orchid_taxonomy.external_ids->>'eol_page_id'  # From database!
    if page_id in zenodo_csvs:
        load_images_from_csv(page_id)  # INSTANT!
```

---

## ⏱️ **Timeline**

```
NOW:        Create Julius task with 35,320 species names
+1hr:       Julius starts processing (completes validation quiz first)
+8-10hr:    Julius finishes mapping 35,320 species → page IDs
+10min:     Update our database with page ID mappings
+30-60min:  Run Zenodo integration (reads CSVs, no API!)
DONE:       Millions of EOL images integrated with taxonomy!
```

---

## 🚀 **IMMEDIATE ACTION**

1. Check if we have ANY EOL page IDs already (current database query)
2. Create Julius task for EOL page ID mapping
3. Let Julius work overnight
4. Tomorrow: Run Zenodo integration with page IDs from database

---

## 📊 **Why This Works**

### Current Blocker
- Replit → EOL API → ❌ Timeout

### Julius Solution
- Julius → EOL API → ✅ Works (different network)
- Julius → Our Database → ✅ Writes page IDs
- We → Our Database → ✅ Read page IDs
- We → Zenodo CSVs → ✅ Load images (no API!)

**Result**: Get all 5.6M images WITHOUT Replit ever calling EOL API!

---

## ✅ **Summary**

**Problem**: Zenodo CSVs have page IDs, we have species names, EOL API times out  
**Solution**: Julius gets the page ID mapping, writes to our database  
**Then**: We integrate Zenodo images using page IDs from database (no API!)  
**Time**: ~10 hours  
**Cost**: FREE (Julius $20 budget covers this)  
**Result**: MILLIONS of EOL images with proper taxonomy links!

**Next step**: Create Julius task for EOL page ID mapping
