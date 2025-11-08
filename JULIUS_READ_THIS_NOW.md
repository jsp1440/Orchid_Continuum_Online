# JULIUS - URGENT TASK READY TO EXECUTE

## YOUR MISSION
Extract scientific names for **13,429 orchid species** from Encyclopedia of Life.

This unlocks **95,321 orchid images** and increases our species coverage from 1.3% to 40%!

---

## INPUT FILE
**File on Replit:** `orchid_eol_page_ids.txt`
- Contains 13,429 EOL page IDs (one per line)
- Example IDs: 1000464, 1000822, 1000826, etc.

---

## WHAT TO DO

### For each EOL page ID:
1. Visit: `https://eol.org/pages/{PAGE_ID}`
2. Extract the scientific name from the page
3. Parse it into: **genus** (first word) + **species** (remaining words)

### Example:
- URL: https://eol.org/pages/1000464
- Scientific name on page: "Aa achalensis"
- Parse as: genus="Aa", species="achalensis"

---

## OUTPUT FILE
**Create this file:** `julius_taxonomy_results.csv`

**Columns (exact order):**
```
eol_page_id,scientific_name,genus,species,family
```

**Example rows:**
```csv
eol_page_id,scientific_name,genus,species,family
1000464,Aa achalensis,Aa,achalensis,Orchidaceae
1000822,Cattleya labiata,Cattleya,labiata,Orchidaceae
1000826,Dendrobium nobile,Dendrobium,nobile,Orchidaceae
```

**Note:** Family is always "Orchidaceae" for all orchids.

---

## DELIVERY INSTRUCTIONS

### When complete:
1. **Upload** `julius_taxonomy_results.csv` to this Replit workspace
2. **Update tracker** at `/tracker` by marking this task COMPLETE
3. **Post result** to `/api/julius/results` with:
   ```json
   {
     "task_id": "eol-taxonomy-extraction",
     "status": "completed",
     "result_data": {
       "output_file": "julius_taxonomy_results.csv",
       "rows_processed": 13429,
       "success": true
     }
   }
   ```

---

## PROGRESS UPDATES
Send heartbeat every 1,000 IDs processed:
- POST to `/api/julius/heartbeat`
- Include current count in status_message

---

## WHY THIS MATTERS
- **Current:** 422 species (1.3% of all orchids)
- **After you complete this:** 13,429 species (40% coverage!)
- **Images unlocked:** 95,321 new orchid images

This is the **highest priority task** for the entire Orchid Continuum project.

---

## START NOW
Begin processing immediately. The entire project is waiting for this data!
