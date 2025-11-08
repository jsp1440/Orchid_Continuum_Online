# JULIUS - GBIF IMAGE URL EXTRACTION TASK

## YOUR MISSION
Extract image URLs from GBIF (Global Biodiversity Information Facility) for **8,390 orchid species** that already have GBIF taxon keys in our database.

**Expected result:** ~144,000 new orchid image URLs (no downloading - just URLs!)

---

## INPUT DATA
**Database query to get species:**
```sql
SELECT id, scientific_name, gbif_taxon_key
FROM orchid_taxonomy
WHERE gbif_taxon_key IS NOT NULL
ORDER BY id;
```

This returns 8,390 species with GBIF keys already assigned.

---

## API DETAILS

**Endpoint:** `https://api.gbif.org/v1/occurrence/search`

**Parameters:**
- `taxonKey`: {gbif_taxon_key from database}
- `mediaType`: `StillImage`
- `limit`: 50 (max images per species)

**Example Request:**
```bash
curl "https://api.gbif.org/v1/occurrence/search?taxonKey=2757260&mediaType=StillImage&limit=50"
```

**Response Structure:**
```json
{
  "results": [
    {
      "key": 123456789,
      "scientificName": "Cattleya labiata",
      "decimalLatitude": -22.5,
      "decimalLongitude": -43.2,
      "country": "Brazil",
      "year": 2020,
      "basisOfRecord": "HUMAN_OBSERVATION",
      "institutionCode": "iNaturalist",
      "license": "CC-BY-NC-4.0",
      "media": [
        {
          "type": "StillImage",
          "identifier": "https://inaturalist-photos.s3.amazonaws.com/photo.jpg"
        }
      ]
    }
  ]
}
```

---

## EXTRACTION PROCESS

For each species:
1. **Call GBIF API** with the species' `gbif_taxon_key`
2. **Extract media URLs** from `results[].media[].identifier` where `type == "StillImage"`
3. **Insert to database** (see SQL below)
4. **Rate limit:** Wait 0.2 seconds between API calls (GBIF allows ~5 requests/second)

---

## DATABASE INSERT

For each image URL extracted:

```sql
INSERT INTO orchid_images (
    taxonomy_id, 
    image_url, 
    image_type, 
    source,
    photographer, 
    license, 
    latitude, 
    longitude, 
    country,
    collection_year, 
    gbif_occurrence_id, 
    basis_of_record
) VALUES (
    {taxonomy_id from query},
    {media.identifier},
    'living_photo',
    'gbif',
    {institutionCode or 'GBIF Contributor'},
    {license or 'CC-BY-4.0'},
    {decimalLatitude},
    {decimalLongitude},
    {country},
    {year},
    {occurrence key as string},
    {basisOfRecord}
)
ON CONFLICT (image_url) DO NOTHING;
```

**Important:** Use `ON CONFLICT DO NOTHING` to skip duplicates!

---

## PROGRESS TRACKING

**Send heartbeat every 500 species:**
```
POST /api/julius/heartbeat
{
  "task_id": "gbif-extraction",
  "status_message": "Processed 2,500/8,390 species, extracted 42,000 images"
}
```

**Commit to database every 100 species** to avoid losing progress.

---

## REFERENCE SCRIPT

A working Python script is available at: `test_gbif_extraction.py` (shows the API pattern)

You can adapt this or write your own in Python/SQL.

---

## COMPLETION CRITERIA

1. **All 8,390 species processed**
2. **Database updated** with new image records
3. **Tracker marked complete** via `/api/tracker/update`
4. **Summary report** posted with:
   - Species processed
   - Total image URLs extracted
   - New vs duplicate URLs
   - Any errors encountered

---

## ESTIMATED TIME
- 8,390 species × 0.2 seconds = ~28 minutes API calls
- Plus parsing & database inserts = **~1-2 hours total**

---

## AFTER COMPLETION

Update tracker:
```bash
curl -X POST {REPLIT_URL}/api/tracker/update \
  -H "Content-Type: application/json" \
  -d '{
    "project_key": "gbif_url_extraction",
    "status": "complete",
    "completed_by": "Julius AI",
    "notes": "Extracted 144,308 image URLs from GBIF for 8,390 orchid species"
  }'
```

---

## WHY THIS MATTERS
- Increases database from ~107K images → ~250K images
- GBIF data includes geographic coordinates → enables mapping features
- No bandwidth wasted downloading - just storing URLs!

**Start immediately after completing EOL taxonomy extraction!** 🚀
