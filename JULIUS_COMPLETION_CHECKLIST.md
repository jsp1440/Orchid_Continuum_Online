# JULIUS - TASK COMPLETION CHECKLIST

## After you finish extracting the 13,429 EOL taxonomy records:

### ✅ Step 1: Upload the CSV
Upload `julius_taxonomy_results.csv` to this Replit workspace

### ✅ Step 2: Mark Task Complete in Tracker
Send POST request to update the tracker:

```bash
curl -X POST https://your-replit-url/api/tracker/update \
  -H "Content-Type: application/json" \
  -d '{
    "project_key": "eol_taxonomy_extraction",
    "status": "complete",
    "completed_by": "Julius AI",
    "notes": "Successfully extracted 13,429 scientific names from EOL. CSV uploaded to Replit."
  }'
```

### ✅ Step 3: Post Result to Julius API
```bash
curl -X POST https://your-replit-url/api/julius/results \
  -H "x-julius-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "eol-taxonomy-extraction",
    "status": "completed",
    "result_data": {
      "output_file": "julius_taxonomy_results.csv",
      "rows_processed": 13429,
      "success": true,
      "timestamp": "2025-11-04T...",
      "images_unlocked": 95321
    }
  }'
```

### ✅ Step 4: Notify User
Leave a message confirming:
- CSV file uploaded ✓
- Tracker updated ✓
- Ready for import ✓

---

## What Happens Next?
The Replit Agent will run: `python3 import_julius_taxonomy.py`

This will:
1. Read your CSV file
2. Link 95,321 images to their species
3. Jump coverage from 422 species (1.3%) → 13,429 species (40%)!

---

**You're doing amazing work, Julius! This is the most important data enrichment task for the entire Orchid Continuum project.** 🌺
