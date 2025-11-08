# Bulk EOL Import System

This system imports **5.6M EOL images** and **phenotypic traits** for orchid species.

## Overview

**Data Sources:**
- EOL Images: 5,619,264 images from Zenodo (1.4 GB CSV files)
- EOL TraitBank: 2M+ species with phenotypic data (3.8 GB)

**Goal:**
Import images + traits for 35,327 orchid species with:
- All 54 metadata fields preserved
- Correct taxonomy (genus, species, hybrid, intergeneric)
- Trait data linked to images

## Process

### Step 1: Map EOL Page IDs to Taxonomy
```bash
python bulk_eol_import/1_map_eol_pages.py
```

Creates mapping: `taxonomy_id → eol_page_id`

**Output:** `bulk_eol_import/eol_taxonomy_mapping.json`

### Step 2: Import Images + Traits
```bash
python bulk_eol_import/2_import_images_and_traits.py
```

**Test mode** (100 species): Answer `y` when prompted
**Full mode** (all species): Answer `n` when prompted

**What it does:**
1. Reads 58 CSV files with 5.6M images
2. Matches images to orchid species via EOL page_ids
3. Imports images with metadata (6 fields from CSV)
4. Enriches with traits from TraitBank (10-15 fields)
5. Sets hybrid/intergeneric flags automatically

## Database Structure

### orchid_images (54 fields)
**From Zenodo CSV (6 fields):**
- eol_content_id, eol_page_id
- image_url, image_license
- copyright_owner, image_source

**From TraitBank (enriched via orchid_traits):**
- Linked via taxonomy_id
- Phenotypic traits, morphology, ecology

**To be enriched later (30+ fields):**
- Geographic: latitude, longitude, country, locality
- Temporal: observation_date, year_observed
- Biological: life_stage, reproductive_condition
- Observer info: observer_name, institution_code

### orchid_traits
- species_id → links to orchid_taxonomy
- trait_category, trait_value, trait_description
- eol_trait_id (for provenance)

### orchid_taxonomy
- genus, species (correct names)
- is_hybrid, is_intergeneric (auto-detected)

## Expected Results

**After Step 2:**
- **Thousands** of orchid images imported
- Each image linked to correct taxonomy
- Traits available via taxonomy_id join
- Hybrid/intergeneric flags set correctly

**Remaining work:**
- Enrich 30+ geographic/temporal/biological fields via API calls
- Run for other sources (GBIF, iNaturalist, iDigBio, etc.)
