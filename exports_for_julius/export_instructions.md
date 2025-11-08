# CSV EXPORTS FOR JULIUS

**Date:** October 23, 2025  
**Purpose:** Offline analysis without DB connectivity issues  

## FILES EXPORTED

### 1. orchid_taxonomy_full.csv (35,320 records)
**Columns:** genus, species, scientific_name, subfamily, tribe, author, distribution, habitat_type, elevation_min, elevation_max, temperature_preference, conservation_status, external_ids

### 2. orchid_images_full.csv (11,717 records)  
**Columns:** genus, species, image_url, photographer, observation_date, latitude, longitude, elevation, country, habitat, conservation_status, gbif_metadata, eol_metadata

### 3. genus_summary.csv (Aggregated stats)
**Columns:** genus, species_count, image_count, coverage_percent

## ANALYSIS TASKS

Use these CSVs to:
1. Generate 50+ visualizations
2. EOL coverage analysis
3. Image gap identification
4. Distribution maps
5. Conservation breakdowns
6. Phenology patterns

All analysis runs offline - no DB connection needed!
