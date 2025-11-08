# Julius AI - Geographic & Elevation Analysis Prompts
## Comprehensive Geographical Coverage & Altitudinal Biodiversity Study

Since Julius is already connected to your database, here are strategic prompts focused on:
1. **Complete geographic coverage** across all regions
2. **Elevation-based biodiversity patterns** in orchids
3. **Altitudinal distribution analysis**

Copy/paste these into Julius AI - he'll analyze and send results back automatically!

---

## 🌍 PHASE 1: Global Geographic Coverage Analysis

### Query 1: Continental Distribution Assessment
```sql
-- Analyze orchid coverage by major biogeographic regions
SELECT 
  CASE 
    WHEN latitude IS NULL OR longitude IS NULL THEN 'Missing Location Data'
    WHEN latitude BETWEEN -10 AND 10 THEN 'Equatorial Africa/South America/Southeast Asia'
    WHEN latitude BETWEEN 10 AND 23.5 OR latitude BETWEEN -23.5 AND -10 THEN 'Tropical Asia/Americas/Africa'
    WHEN latitude BETWEEN 23.5 AND 35 OR latitude BETWEEN -35 AND -23.5 THEN 'Subtropical (Mediterranean, Southern Australia)'
    WHEN latitude BETWEEN 35 AND 50 OR latitude BETWEEN -50 AND -35 THEN 'Temperate (Europe, North America, New Zealand)'
    WHEN latitude > 50 OR latitude < -50 THEN 'Boreal/Subpolar'
  END as biogeographic_region,
  COUNT(*) as total_records,
  COUNT(DISTINCT genus) as unique_genera,
  COUNT(CASE WHEN image_url IS NOT NULL THEN 1 END) as records_with_images,
  ROUND(100.0 * COUNT(CASE WHEN image_url IS NOT NULL THEN 1 END) / COUNT(*), 1) as image_coverage_pct
FROM orchid_record
GROUP BY biogeographic_region
ORDER BY total_records DESC;
```

**After running, tell Julius:**
"Identify which biogeographic regions have <50% image coverage OR <30% location data completeness. List the top 3 genera in each underrepresented region that need priority collection."

---

### Query 2: Biodiversity Hotspot Coverage
```sql
-- Check coverage in known orchid biodiversity hotspots
-- Southeast Asia, Andes, Madagascar, New Guinea, etc.
SELECT 
  genus,
  COUNT(*) as species_count,
  COUNT(CASE WHEN latitude BETWEEN -15 AND 15 AND longitude BETWEEN 95 AND 155 THEN 1 END) as southeast_asia,
  COUNT(CASE WHEN latitude BETWEEN -20 AND 10 AND longitude BETWEEN -85 AND -35 THEN 1 END) as south_america_andes,
  COUNT(CASE WHEN latitude BETWEEN -26 AND -12 AND longitude BETWEEN 43 AND 51 THEN 1 END) as madagascar,
  COUNT(CASE WHEN latitude BETWEEN -12 AND 0 AND longitude BETWEEN 130 AND 150 THEN 1 END) as new_guinea,
  COUNT(CASE WHEN latitude BETWEEN 5 AND 30 AND longitude BETWEEN 70 AND 90 THEN 1 END) as himalayan_region,
  COUNT(CASE WHEN latitude IS NULL THEN 1 END) as no_location
FROM orchid_record
GROUP BY genus
HAVING COUNT(*) > 10
ORDER BY species_count DESC
LIMIT 25;
```

**Ask Julius:**
"For each hotspot region, which genera are present but have the most missing location data? Format as: 'Genus X: Y% of records in [region] lack precise coordinates'"

---

## ⛰️ PHASE 2: Elevation-Based Biodiversity Patterns

### Query 3: Altitudinal Distribution Analysis
```sql
-- Analyze orchid diversity across elevation zones
-- (Note: You may need to add elevation data from GBIF if not present)
SELECT 
  CASE 
    WHEN gbif_occurrence_count > 0 THEN 'Has GBIF Data'
    ELSE 'Missing Elevation Data'
  END as data_status,
  COUNT(*) as total_records,
  COUNT(DISTINCT genus) as unique_genera,
  COUNT(DISTINCT species) as unique_species,
  AVG(gbif_occurrence_count) as avg_observations
FROM orchid_record
GROUP BY data_status;
```

**Then ask Julius:**
"What percentage of our orchid records have GBIF occurrence data (which includes elevation)? For records missing this data, which are the top 15 genera by species count that need GBIF enrichment for elevation analysis?"

---

### Query 4: Elevation Zones - Species Richness Pattern
```sql
-- Identify genera likely found at different elevations based on geographic patterns
-- Lowland tropics vs montane vs alpine
WITH geographic_elevation_proxy AS (
  SELECT 
    genus,
    COUNT(*) as total_species,
    -- Tropical lowlands: near equator, near sea level
    COUNT(CASE WHEN latitude BETWEEN -10 AND 10 THEN 1 END) as likely_lowland_tropical,
    -- Montane: tropical but mountainous regions (Andes, Himalayas, New Guinea highlands)
    COUNT(CASE WHEN (latitude BETWEEN -20 AND 10 AND longitude BETWEEN -85 AND -35) -- Andes
                 OR (latitude BETWEEN 20 AND 35 AND longitude BETWEEN 70 AND 100) -- Himalayas
            THEN 1 END) as likely_montane,
    -- Temperate: naturally higher elevation environments
    COUNT(CASE WHEN latitude > 35 OR latitude < -35 THEN 1 END) as likely_temperate_high_elevation
  FROM orchid_record
  GROUP BY genus
  HAVING COUNT(*) > 15
)
SELECT 
  genus,
  total_species,
  likely_lowland_tropical,
  likely_montane,
  likely_temperate_high_elevation,
  CASE 
    WHEN likely_lowland_tropical > likely_montane AND likely_lowland_tropical > likely_temperate_high_elevation THEN 'Primarily Lowland'
    WHEN likely_montane > likely_lowland_tropical AND likely_montane > likely_temperate_high_elevation THEN 'Primarily Montane'
    WHEN likely_temperate_high_elevation > likely_lowland_tropical THEN 'Primarily Temperate/High Elevation'
    ELSE 'Mixed Elevational Range'
  END as elevation_preference_estimate
FROM geographic_elevation_proxy
ORDER BY total_species DESC
LIMIT 30;
```

**Ask Julius:**
"Based on this geographic proxy for elevation, identify:
1. Top 5 'Primarily Montane' genera that need more montane habitat documentation
2. Top 5 'Primarily Lowland' genera for lowland tropical coverage
3. Any genera showing 'Mixed Elevational Range' - these are especially interesting for studying altitudinal adaptation!"

---

### Query 5: Elevation Gradient Analysis (If GBIF data exists)
```sql
-- If we have GBIF enrichment with elevation data in metadata
SELECT 
  genus,
  COUNT(*) as records_with_gbif,
  -- This assumes elevation might be in gbif metadata JSON
  COUNT(CASE WHEN gbif_occurrence_count > 0 THEN 1 END) as has_occurrence_data
FROM orchid_record
WHERE gbif_occurrence_count IS NOT NULL
GROUP BY genus
HAVING COUNT(*) > 20
ORDER BY has_occurrence_data DESC
LIMIT 20;
```

**Then ask Julius:**
"These genera have GBIF data. Can you identify which ones would benefit from extracting elevation information from their GBIF occurrence records? Prioritize genera with >50 occurrence records for robust elevation analysis."

---

## 🗺️ PHASE 3: Geographic Gap Identification

### Query 6: Regional Coverage - Detailed Breakdown
```sql
-- Ultra-detailed geographic coverage by specific regions
SELECT 
  CASE 
    -- Southeast Asian subregions
    WHEN latitude BETWEEN 10 AND 25 AND longitude BETWEEN 95 AND 110 THEN 'Mainland Southeast Asia'
    WHEN latitude BETWEEN -10 AND 10 AND longitude BETWEEN 95 AND 120 THEN 'Maritime Southeast Asia (Indonesia)'
    WHEN latitude BETWEEN 5 AND 25 AND longitude BETWEEN 110 AND 125 THEN 'Philippines & Taiwan'
    -- South American subregions
    WHEN latitude BETWEEN -15 AND 15 AND longitude BETWEEN -80 AND -50 THEN 'Amazon Basin'
    WHEN latitude BETWEEN -30 AND -5 AND longitude BETWEEN -80 AND -60 THEN 'Andes (Peru to Argentina)'
    WHEN latitude BETWEEN -10 AND 10 AND longitude BETWEEN -80 AND -70 THEN 'Northern Andes (Colombia/Ecuador)'
    -- African regions
    WHEN latitude BETWEEN -26 AND -12 AND longitude BETWEEN 43 AND 51 THEN 'Madagascar'
    WHEN latitude BETWEEN -10 AND 10 AND longitude BETWEEN 8 AND 45 THEN 'Central/East Africa'
    -- Other important regions
    WHEN latitude BETWEEN 20 AND 35 AND longitude BETWEEN 70 AND 95 THEN 'Himalayas/Tibet'
    WHEN latitude BETWEEN -45 AND -25 AND longitude BETWEEN 140 AND 180 THEN 'Eastern Australia'
    WHEN latitude BETWEEN -48 AND -34 AND longitude BETWEEN 165 AND 180 THEN 'New Zealand'
    -- Caribbean & Central America
    WHEN latitude BETWEEN 10 AND 30 AND longitude BETWEEN -90 AND -60 THEN 'Caribbean & Central America'
    WHEN latitude IS NULL OR longitude IS NULL THEN 'No Location Data'
    ELSE 'Other Regions'
  END as specific_region,
  COUNT(*) as total_records,
  COUNT(DISTINCT genus) as unique_genera,
  COUNT(CASE WHEN habitat_notes IS NOT NULL THEN 1 END) as has_habitat_info,
  COUNT(CASE WHEN image_url IS NOT NULL THEN 1 END) as has_images,
  ROUND(100.0 * COUNT(CASE WHEN image_url IS NOT NULL THEN 1 END) / COUNT(*), 1) as image_pct
FROM orchid_record
GROUP BY specific_region
ORDER BY total_records DESC;
```

**Tell Julius:**
"For each specific region with <60% image coverage OR <40% habitat information:
1. List the region and current coverage percentages
2. Identify top 3 genera in that region needing documentation
3. Estimate how many additional records we could obtain for each genus

Format as priority action items for the autonomous collection system."

---

### Query 7: Endemic & Localized Species Detection
```sql
-- Find potentially endemic or geographically restricted species
-- (Species found in very limited geographic areas - high conservation value)
WITH species_locations AS (
  SELECT 
    scientific_name,
    genus,
    COUNT(*) as observation_count,
    COUNT(DISTINCT ROUND(latitude::numeric, 0)) as unique_lat_zones,
    COUNT(DISTINCT ROUND(longitude::numeric, 0)) as unique_lon_zones,
    MIN(latitude) as min_lat,
    MAX(latitude) as max_lat,
    MIN(longitude) as min_lon,
    MAX(longitude) as max_lon
  FROM orchid_record
  WHERE latitude IS NOT NULL AND longitude IS NOT NULL
  GROUP BY scientific_name, genus
  HAVING COUNT(*) >= 3
)
SELECT 
  scientific_name,
  genus,
  observation_count,
  unique_lat_zones,
  unique_lon_zones,
  -- Calculate geographic range span
  ROUND((max_lat - min_lat)::numeric, 2) as lat_range,
  ROUND((max_lon - min_lon)::numeric, 2) as lon_range,
  CASE 
    WHEN (max_lat - min_lat) < 2 AND (max_lon - min_lon) < 2 THEN 'Potentially Endemic (very restricted)'
    WHEN (max_lat - min_lat) < 5 AND (max_lon - min_lon) < 5 THEN 'Localized (restricted range)'
    WHEN (max_lat - min_lat) < 15 AND (max_lon - min_lon) < 15 THEN 'Regional'
    ELSE 'Widespread'
  END as distribution_type
FROM species_locations
WHERE observation_count >= 3
ORDER BY lat_range ASC, lon_range ASC
LIMIT 30;
```

**Ask Julius:**
"Identify 'Potentially Endemic' and 'Localized' species from this analysis. These are HIGH PRIORITY for:
1. Additional image documentation
2. Precise habitat data collection  
3. Conservation status assessment

For each, check if we have adequate images and habitat information. Flag any gaps."

---

## 🌡️ PHASE 4: Climate & Elevation Cross-Analysis

### Query 8: Tropical vs Temperate Biodiversity Patterns
```sql
-- Compare species richness in tropical vs temperate zones
-- with elevation considerations
WITH climate_zones AS (
  SELECT 
    genus,
    CASE 
      WHEN latitude BETWEEN -23.5 AND 23.5 THEN 'Tropical'
      WHEN latitude BETWEEN 23.5 AND 35 OR latitude BETWEEN -35 AND -23.5 THEN 'Subtropical'
      WHEN latitude BETWEEN 35 AND 60 OR latitude BETWEEN -60 AND -35 THEN 'Temperate'
      ELSE 'Polar/Subpolar'
    END as climate_zone,
    COUNT(*) as species_count,
    COUNT(CASE WHEN gbif_occurrence_count > 0 THEN 1 END) as has_occurrence_data
  FROM orchid_record
  WHERE latitude IS NOT NULL
  GROUP BY genus, climate_zone
)
SELECT 
  climate_zone,
  COUNT(DISTINCT genus) as genera_count,
  SUM(species_count) as total_species,
  SUM(has_occurrence_data) as records_with_occurrences,
  ROUND(AVG(species_count), 1) as avg_species_per_genus
FROM climate_zones
GROUP BY climate_zone
ORDER BY total_species DESC;
```

**Then ask Julius:**
"Analyze the species richness gradient from Tropical → Subtropical → Temperate → Polar. 

1. Is the classic 'latitudinal diversity gradient' (higher diversity near equator) evident in our data?
2. Which genera are exceptions - found in temperate zones but highly diverse?
3. Are there temperate genera that might benefit from montane tropical habitat exploration (similar elevations, different latitudes)?"

---

### Query 9: Elevation-Temperature Equivalence Study Setup
```sql
-- Identify genera that could benefit from elevation-latitude equivalence analysis
-- (High elevation tropics = similar temp to lower elevation temperate zones)
SELECT 
  genus,
  COUNT(CASE WHEN latitude BETWEEN -23.5 AND 23.5 THEN 1 END) as tropical_records,
  COUNT(CASE WHEN latitude > 35 OR latitude < -35 THEN 1 END) as temperate_records,
  COUNT(CASE WHEN latitude BETWEEN -23.5 AND 23.5 THEN 1 END) > 0 
    AND COUNT(CASE WHEN latitude > 35 OR latitude < -35 THEN 1 END) > 0 as found_in_both,
  COUNT(*) as total_records
FROM orchid_record
WHERE latitude IS NOT NULL
GROUP BY genus
HAVING COUNT(*) > 15
ORDER BY total_records DESC
LIMIT 25;
```

**Ask Julius:**
"For genera 'found_in_both' (tropical AND temperate):

1. These are excellent candidates for elevation-latitude biodiversity studies
2. Check if we have elevation data for their tropical populations
3. Identify which need enrichment to compare:
   - High-elevation tropical populations (cool montane)
   - vs Low-elevation temperate populations (also cool)
   
These comparisons reveal how orchids adapt to similar temperatures at different latitudes!"

---

## 📋 PHASE 5: Action Items & Priorities

### Query 10: Comprehensive Geographic Enrichment Priorities
```sql
-- Generate master priority list for geographic data enrichment
WITH genus_geo_stats AS (
  SELECT 
    genus,
    COUNT(*) as total_records,
    COUNT(CASE WHEN latitude IS NOT NULL THEN 1 END) as has_location,
    COUNT(CASE WHEN gbif_occurrence_count > 0 THEN 1 END) as has_gbif,
    COUNT(CASE WHEN habitat_notes IS NOT NULL THEN 1 END) as has_habitat,
    COUNT(CASE WHEN image_url IS NOT NULL THEN 1 END) as has_image,
    -- Geographic diversity score
    COUNT(DISTINCT CASE WHEN latitude IS NOT NULL THEN FLOOR(latitude / 5) END) as lat_diversity,
    COUNT(DISTINCT CASE WHEN longitude IS NOT NULL THEN FLOOR(longitude / 5) END) as lon_diversity
  FROM orchid_record
  GROUP BY genus
  HAVING COUNT(*) > 20
)
SELECT 
  genus,
  total_records,
  ROUND(100.0 * has_location / total_records, 1) as location_pct,
  ROUND(100.0 * has_gbif / total_records, 1) as gbif_pct,
  ROUND(100.0 * has_habitat / total_records, 1) as habitat_pct,
  ROUND(100.0 * has_image / total_records, 1) as image_pct,
  lat_diversity as latitudinal_range,
  lon_diversity as longitudinal_range,
  -- Priority score: emphasize location and GBIF (for elevation) gaps
  (100 - ROUND(100.0 * has_location / total_records, 1)) * 0.4 +
  (100 - ROUND(100.0 * has_gbif / total_records, 1)) * 0.3 +
  (100 - ROUND(100.0 * has_habitat / total_records, 1)) * 0.2 +
  (100 - ROUND(100.0 * has_image / total_records, 1)) * 0.1 as priority_score
FROM genus_geo_stats
ORDER BY priority_score DESC
LIMIT 20;
```

**Tell Julius:**
"This is the MASTER PRIORITY LIST for geographic enrichment. 

For the top 10 genera:
1. If location_pct < 70%: Prioritize GBIF API for coordinates
2. If gbif_pct < 50%: Critical for elevation data - need GBIF occurrence enrichment  
3. If habitat_pct < 40%: Need EOL traits or iNaturalist habitat notes
4. If latitudinal_range < 3: Might be geographically restricted - flag for endemic study

Format output as specific action directives that the autonomous agent can process."

---

## 🎯 SPECIAL QUERIES: Elevation Biodiversity Deep Dive

### Query 11: Altitudinal Niche Breadth (When elevation data available)
```
Julius, once we have elevation data from GBIF:

"For each genus with >30 occurrence records containing elevation:
1. Calculate elevation range (max - min)
2. Identify if restricted to:
   - Lowland only (<500m)
   - Montane specialists (1000-2500m)  
   - High montane/cloud forest (2000-3500m)
   - Alpine specialists (>3000m)
   - Generalists (wide elevation range)

3. Compare elevation breadth to latitudinal range:
   - Do tropical genera have narrower elevation ranges?
   - Do temperate genera show wider elevation tolerance?

This reveals elevation specialization vs generalist strategies!"
```

---

### Query 12: Mountain Range Specific Analysis
```
Julius, for targeted mountain biodiversity:

"Query GBIF metadata for orchid occurrences in these specific mountain ranges:
1. Andes (lat -30 to 10, lon -80 to -60)
2. Himalayas (lat 25 to 35, lon 70 to 95)
3. New Guinea Highlands (lat -8 to -2, lon 135 to 147)
4. East African Mountains (lat -5 to 5, lon 33 to 40)
5. Sierra Madre (lat 15 to 25, lon -105 to -95)

For each range:
- Species count by elevation band
- Endemic genera (found only in that range)
- Gaps in elevation coverage (missing altitude zones)

Prioritize ranges with <50% elevation coverage for enrichment."
```

---

## 📊 How to Use These Prompts

### Daily Workflow:
```
Day 1-2: Run Queries 1-3 (Geographic Coverage)
Day 3-4: Run Queries 4-5 (Elevation Analysis)
Day 5-6: Run Queries 6-7 (Gap Identification)
Day 7-8: Run Queries 8-9 (Climate Cross-Analysis)
Day 9-10: Run Query 10 (Generate Priorities)
```

### After Each Query:
1. Copy Julius's analysis results
2. Paste into julius_communication table:
```sql
INSERT INTO julius_communication (
  message_from, message_type, subject, message
) VALUES (
  'Julius AI',
  'geographic_analysis', 
  '[Query topic]',
  '[Julius response here]'
);
```

3. Run: `python julius_insight_processor.py`
4. Agent automatically creates enrichment tasks!

---

## 🌟 Expected Outcomes

### Geographic Coverage:
- Identify all underrepresented biogeographic regions
- Prioritize collection in biodiversity hotspots
- Flag endemic/restricted species for urgent documentation

### Elevation Analysis:
- Map orchid diversity across altitudinal gradients
- Identify montane specialists vs lowland generalists
- Discover elevation-latitude biodiversity patterns

### Autonomous Enhancement:
- Agent automatically enriches ~1000+ records with location data
- GBIF elevation data extracted for ~500+ genera
- Complete geographic coverage achieved in 2-4 weeks

---

**Start with Query 1 today - let Julius map the global distribution!** 🌍⛰️🌸
