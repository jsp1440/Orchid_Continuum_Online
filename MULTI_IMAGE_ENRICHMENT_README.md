# Multi-Image Enrichment System

## Overview

The Orchid Continuum now collects **UNLIMITED images per species** from GBIF, storing up to 100 images per species with complete metadata (75+ fields) for AI vision training.

## Current Status

✅ **System is RUNNING and collecting images continuously**

### Latest Stats
- **409 images** collected from **15 species**
- Average: **27.3 images per species**
- Top species: **100 images each** (Pogonia Juss., Cleistesiopsis)

## Database Schema

### orchid_images Table
Stores unlimited images per species with complete metadata:

**Core Fields:**
- `id`: Primary key
- `taxonomy_id`: Links to orchid_taxonomy
- `gbif_occurrence_key`: Unique GBIF occurrence ID
- `image_url`: Direct link to image
- `image_license`: License information

**Geographic Metadata (13 fields):**
- latitude, longitude, coordinate_uncertainty
- country, country_code, state_province
- locality, continent

**Temporal Metadata (7 fields):**
- observation_date, year_observed, month_observed
- Full timestamps

**Observer/Collection (7 fields):**
- observer_name, institution_code
- Complete attribution

**Specimen Details (9 fields):**
- individual_count, sex, life_stage
- reproductive_condition

**Conservation:**
- iucn_red_list_category

**Complete Data:**
- `occurrence_metadata`: Full GBIF occurrence JSON (75+ fields)
- `media_metadata`: Complete media information JSON

## How It Works

1. **Query**: Selects species that haven't been enriched yet
2. **GBIF API**: Gets taxon key for species name
3. **Image Collection**: Fetches up to 100 wild specimen images
4. **Metadata Extraction**: Captures ALL 75+ metadata fields
5. **Database Storage**: Saves each image with complete metadata
6. **Continue**: Moves to next species

### Rate Limiting
- 10 requests/second to respect GBIF API guidelines
- Processes ~2-5 species per second
- Expected time: Several hours for all 35,320 species

## Monitoring

### Check Progress
```bash
./validation/monitor_progress.sh
```

### Watch Live
```bash
tail -f /tmp/image_enrichment.log
```

### Database Query
```sql
SELECT 
    COUNT(DISTINCT taxonomy_id) as species,
    COUNT(*) as total_images,
    ROUND(COUNT(*)::numeric / COUNT(DISTINCT taxonomy_id), 1) as avg
FROM orchid_images;
```

## Starting/Stopping

### Start Enrichment
```bash
cd /home/runner/workspace
nohup python -u validation/enrich_images_simple.py --batch-size 100 > /tmp/image_enrichment.log 2>&1 &
```

### Stop Enrichment
```bash
pkill -f enrich_images_simple
```

### Check if Running
```bash
ps aux | grep enrich_images_simple | grep -v grep
```

## Files

- `validation/enrich_images_simple.py`: Main enrichment script (simple & reliable)
- `validation/monitor_progress.sh`: Progress monitoring script
- `/tmp/image_enrichment.log`: Live enrichment log
- Database table: `orchid_images`

## Expected Results

**Target**: 50K-100K+ total images across 35,320 species

**Success Metrics**:
- ✅ Multiple images per species (not just one)
- ✅ Complete metadata for each image (75+ fields)
- ✅ Wild specimen images (not cultivated)
- ✅ Diverse geographic locations
- ✅ Complete JSON for advanced analysis

## Metadata Captured

Every image includes:

1. **Geographic**: Exact coordinates, location hierarchy
2. **Temporal**: Observation date/time with timezone
3. **Taxonomic**: Complete classification
4. **Observer**: Who recorded the observation
5. **Specimen**: Life stage, sex, reproductive condition
6. **Quality**: Coordinate uncertainty, data issues
7. **Conservation**: IUCN Red List status
8. **Media**: License, format, references
9. **Complete JSON**: Everything GBIF provides!

## AI Vision Training

This dataset enables:
- Species identification training
- Geographic distribution analysis
- Habitat preference learning
- Phenotypic variation analysis
- Conservation status correlation
- Temporal pattern detection

---

**Note**: The enrichment runs continuously until all 35,320 species have been processed. You can check progress anytime using the monitoring script!
