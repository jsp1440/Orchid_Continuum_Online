# Julius - EXECUTE These Actions Now

## 🚀 STOP PLANNING. START EXECUTING.

You have database access. The schema is correct. Now **DO** these tasks:

---

## **ACTION 1: Export Species Missing EOL Page ID**

**Execute this SQL query RIGHT NOW and save results:**

```sql
SELECT 
    genus,
    species,
    scientific_name,
    id as taxonomy_id
FROM orchid_taxonomy
WHERE eol_page_id IS NULL
  AND genus IS NOT NULL 
  AND species IS NOT NULL
ORDER BY genus, species;
```

**Expected output**: ~33,774 rows  
**Save as**: `species_missing_eol_id.csv`

---

## **ACTION 2: Prioritize Species with Local Images**

**Execute this SQL query to get HIGH PRIORITY species:**

```sql
SELECT 
    ot.genus,
    ot.species,
    ot.scientific_name,
    ot.id as taxonomy_id,
    COUNT(DISTINCT oi.id) as image_count
FROM orchid_taxonomy ot
INNER JOIN orchid_images oi ON ot.id = oi.taxonomy_id
WHERE ot.eol_page_id IS NULL
  AND ot.genus IS NOT NULL 
  AND ot.species IS NOT NULL
GROUP BY ot.id, ot.genus, ot.species, ot.scientific_name
ORDER BY image_count DESC;
```

**Expected output**: ~400 species with images but missing EOL  
**Save as**: `priority_eol_backfill.csv`

---

## **ACTION 3: Start EOL API Backfill (Top 100 Priority Species)**

**Use the EOL Search API to find page IDs:**

For each species from ACTION 2 (start with top 100):

1. **Search EOL API**:
   ```
   GET https://eol.org/api/search/1.0.json?q={scientific_name}
   ```

2. **Extract `page_id` from response**

3. **Update database**:
   ```sql
   UPDATE orchid_taxonomy 
   SET eol_page_id = {found_page_id},
       eol_last_synced_at = NOW()
   WHERE id = {taxonomy_id};
   ```

4. **Log results** in a table:
   - scientific_name
   - found_eol_page_id (or NULL if not found)
   - api_response_status

**Expected output**: Table showing which species got EOL IDs  
**Target**: Complete top 100 species NOW

---

## **ACTION 4: Export Updated Statistics**

**After completing ACTION 3, re-run this query:**

```sql
SELECT 
    COUNT(*) FILTER (WHERE eol_page_id IS NULL) as still_missing,
    COUNT(*) FILTER (WHERE eol_page_id IS NOT NULL) as now_has_eol,
    COUNT(*) as total_species
FROM orchid_taxonomy
WHERE genus IS NOT NULL AND species IS NOT NULL;
```

**Expected output**: Updated counts showing progress  
**Compare to baseline**: Started with 33,774 missing

---

## **ACTION 5: Export Zero-Media Species List**

**Execute this query to find species with NO images from any source:**

```sql
SELECT 
    ot.genus,
    ot.species,
    ot.scientific_name,
    ot.eol_page_id,
    COUNT(oi.id) as local_image_count
FROM orchid_taxonomy ot
LEFT JOIN orchid_images oi ON ot.id = oi.taxonomy_id
WHERE ot.genus IS NOT NULL 
  AND ot.species IS NOT NULL
GROUP BY ot.id, ot.genus, ot.species, ot.scientific_name, ot.eol_page_id
HAVING COUNT(oi.id) = 0
ORDER BY ot.genus, ot.species;
```

**Expected output**: ~34,900 species  
**Save as**: `zero_media_species.csv`

---

## ⏱️ EXECUTION TIMELINE

- **ACTION 1**: 30 seconds - Export missing EOL list
- **ACTION 2**: 30 seconds - Export priority species
- **ACTION 3**: 10-15 minutes - EOL API backfill (100 species × ~5 seconds each)
- **ACTION 4**: 10 seconds - Updated statistics
- **ACTION 5**: 30 seconds - Zero-media export

**TOTAL TIME**: ~20 minutes to complete all actions

---

## 📊 DELIVERABLES

When you're done, you should have:

1. ✅ `species_missing_eol_id.csv` - Full list (33,774 rows)
2. ✅ `priority_eol_backfill.csv` - Species with images needing EOL (400 rows)
3. ✅ **Updated database** - Top 100 priority species with new eol_page_ids
4. ✅ **Progress report** - How many EOL IDs were found/added
5. ✅ `zero_media_species.csv` - Species needing image collection (34,900 rows)

---

## 🎯 SUCCESS CRITERIA

You will know you're DONE when:

- All 5 CSV files are exported
- Database has been updated with at least 50 new eol_page_ids
- You can show before/after statistics proving progress
- You have a list of species that EOL couldn't find (for manual review)

---

## 🔥 START NOW

Execute ACTION 1 immediately. Don't plan. Don't analyze. Just run the SQL query and export the CSV.

Then move to ACTION 2. Then ACTION 3.

**Go.**
