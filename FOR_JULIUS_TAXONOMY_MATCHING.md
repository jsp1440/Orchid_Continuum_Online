# Julius: Orchid Taxonomy Matching Project

## Mission
Match 95,162 orchid image URLs to their scientific names using EOL page IDs. This will expand coverage from 422 species to ~13,429 species (40% of all orchids).

## What Replit Agent Has Done
✅ Extracted 95,162 orchid image URLs from 5.6M EOL manifest rows  
✅ Imported URLs into database  
✅ Created mapping files ready for your analysis  

## Your Task
Fetch scientific names (genus + species) for 13,429 EOL page IDs and match them to the image URLs.

## Files Ready For You

### 1. `orchid_eol_page_ids.txt`
- 13,429 EOL page IDs (one per line)
- These are all confirmed orchid species
- Format: `1000464` (just the ID number)

### 2. `orchid_eol_urls.csv`
- 95,162 rows with columns:
  - `eol_page_id` - EOL species identifier
  - `taxonomy_id` - Database ID (mostly NULL - needs mapping!)
  - `eol_content_id` - EOL internal ID
  - `image_url` - Direct link to image
  - `source_url` - Original source
  - `image_license` - License info
  - `copyright_owner` - Attribution
  - `image_source` - "EOL"

### 3. `eol_taxonomy_mapping.csv`
- 1,543 species we already have mapped
- Shows the pattern: eol_page_id → taxonomy_id, genus, species
- Use as reference for what's already done

## Data Sources You Can Use

### Option 1: EOL Web Pages (Simplest)
Each EOL page ID corresponds to: `https://eol.org/pages/{page_id}`

Example: https://eol.org/pages/1101356
- Scrape the scientific name from the page title or meta tags
- Parse into genus + species

### Option 2: Encyclopedia of Life API
- Endpoint: `https://eol.org/api/pages/1.0/{page_id}.json`
- Note: Replit Agent had SSL issues, but you might have better luck

### Option 3: Cross-Reference Other Sources
- GBIF API: Search by EOL page ID or scientific name
- Tropicos: Missouri Botanical Garden taxonomy
- Any other botanical database you know

## What You Need to Deliver

### CSV File: `julius_taxonomy_results.csv`
Columns:
```csv
eol_page_id,scientific_name,genus,species,family,data_source
1000464,Aa achalensis,Aa,achalensis,Orchidaceae,EOL
```

### Requirements:
- All 13,429 EOL page IDs (or as many as possible)
- Accurate scientific names
- Parsed genus and species fields
- Family should be "Orchidaceae" for all
- Note which data source you used for each

## Success Metrics
- **Current**: 422 species mapped (1.3% of ~33,494 total orchids)
- **Target**: 13,429 species mapped (40% coverage!)
- **Stretch Goal**: All ~33,494 orchid species eventually

## Why This Matters
The Orchid Continuum aims to be the most comprehensive orchid database ever built. Every species added helps:
- Students learning orchid taxonomy
- Researchers studying orchid distribution
- Conservationists tracking endangered species
- The BloomBuilder educational widget

## Notes
- Take your time - accuracy > speed
- If some page IDs fail, that's okay - document which ones
- You're better at data wrangling than web scraping tools
- This is exactly the kind of systematic data organization you excel at

## Questions?
Tag Jen in the chat if you need clarification on any of this!

---
**Prepared by**: Replit Agent  
**Date**: November 4, 2025  
**Status**: Ready for Julius processing
