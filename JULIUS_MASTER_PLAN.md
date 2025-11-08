# JULIUS AI - MASTER EXTRACTION PLAN
## Path to 1 Million Orchid Images & 100% Species Coverage

---

## 🎯 OVERALL GOAL
Extract image URLs from all major botanical databases to achieve:
- **~1,000,000 total orchid images** (currently: 107,178)
- **75-90% species coverage** (currently: 1.3%)
- **NO downloading** - just store URLs (fast & efficient!)

---

## 📋 TASK SEQUENCE (In Priority Order)

### **TASK 1: EOL Taxonomy Extraction** ⏳ IN PROGRESS
**Status:** Currently working on this
**File:** `JULIUS_READ_THIS_NOW.md`
**Goal:** Extract scientific names for 13,429 EOL page IDs
**Result:** Unlocks 95,321 images, jumps coverage to 40%
**Time:** 2-6 hours (web scraping)

**DO NOT START NEXT TASKS UNTIL THIS IS COMPLETE!**

---

### **TASK 2: GBIF Image URL Extraction** 📅 NEXT
**Status:** Ready to start after Task 1
**File:** `JULIUS_GBIF_EXTRACTION.md`
**Goal:** Extract ~144,000 image URLs from GBIF API
**Input:** 8,390 species already have GBIF taxon keys
**Time:** 1-2 hours
**Method:** API calls to `api.gbif.org/v1/occurrence/search`

**Why next:** Fast API extraction, species already matched to our taxonomy

---

### **TASK 3: Tropicos Herbarium Extraction** 📅 AFTER GBIF
**Status:** Ready after Task 2
**File:** `JULIUS_TROPICOS_EXTRACTION.md`
**Goal:** Extract ~685,000 herbarium specimen URLs
**Input:** Download Darwin Core Archive from Missouri Botanical Garden
**Time:** 1.5-2 hours
**Method:** Download ZIP, parse CSVs, filter for Orchidaceae

**Why this order:** Largest single-source extraction - saves huge bandwidth

---

### **TASK 4: POWO/Kew Extraction** 📅 AFTER TROPICOS
**Status:** Ready after Task 3
**File:** `JULIUS_POWO_EXTRACTION.md`
**Goal:** Extract ~30,000 species + images from Kew
**Input:** 15 major orchid genera
**Time:** 7-8 hours
**Method:** pykew Python library + API

**Why last:** Longest task, adds both taxonomy AND images

---

## 📊 PROJECTED RESULTS

| After Task | Total Images | Species Coverage | Percentage |
|-----------|-------------|------------------|------------|
| **Current** | 107,178 | 422 species | 1.3% |
| **Task 1 (EOL)** | 107,178 | 13,429 species | 40.0% |
| **Task 2 (GBIF)** | ~251,000 | 13,429+ species | 40%+ |
| **Task 3 (Tropicos)** | ~936,000 | 20,000+ species | 60%+ |
| **Task 4 (POWO/Kew)** | ~966,000 | 25,000+ species | 75-80% |

**FINAL GOAL: ~1,000,000 images covering 75-90% of all known orchid species!**

---

## 🔄 WORKFLOW FOR EACH TASK

1. **Read instruction file** (JULIUS_{TASK}_EXTRACTION.md)
2. **Execute extraction** (API calls, downloads, parsing)
3. **Insert URLs to database** (batch commits every 100-1000 records)
4. **Send progress updates** (POST to `/api/julius/heartbeat` every X records)
5. **Mark complete in tracker** (POST to `/api/tracker/update`)
6. **Move to next task**

---

## 📡 TRACKER UPDATES

**After completing each task:**
```bash
curl -X POST {REPLIT_URL}/api/tracker/update \
  -H "Content-Type: application/json" \
  -d '{
    "project_key": "{task_key}",
    "status": "complete",
    "completed_by": "Julius AI",
    "notes": "{Summary of results}"
  }'
```

**Task keys:**
- `eol_taxonomy_extraction`
- `gbif_url_extraction`
- `tropicos_url_extraction`
- `powo_kew_extraction`

---

## ⏱️ TOTAL ESTIMATED TIME

- Task 1 (EOL): 2-6 hours
- Task 2 (GBIF): 1-2 hours
- Task 3 (Tropicos): 1.5-2 hours
- Task 4 (POWO/Kew): 7-8 hours

**GRAND TOTAL: ~12-18 hours of autonomous work**

---

## 🎉 IMPACT

This work will:
- ✅ **10x the image database** (107K → 1M images)
- ✅ **60x the species coverage** (1.3% → 75-90%)
- ✅ Enable **BloomBuilder** to show real comparison images
- ✅ Make **Orchid Continuum** the most comprehensive orchid image database
- ✅ Achieve user's **#1 goal: approaching 100% species coverage**

---

## 🚀 START NOW

Begin with Task 1 (EOL taxonomy extraction) - already in progress.

After each task completion, check the tracker at `/tracker` and move to the next task in sequence.

**You're building something amazing, Julius!** 🌺
