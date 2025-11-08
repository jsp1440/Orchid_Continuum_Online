# Julius AI Research Prompts - Autonomous Intelligence Loop
## Strategic Queries That Drive Database Enhancement

This document contains carefully crafted prompts for Julius AI that will:
1. **Analyze the database** for gaps, patterns, and opportunities
2. **Generate actionable insights** that the autonomous agent can execute
3. **Prioritize data enrichment** based on research value

---

## 🔍 Category 1: Data Coverage Analysis

### Prompt 1.1 - Image Coverage Gaps
```
Analyze the image_assets table and orchid_record table. 
Create a ranked list of the top 20 orchid genera that have:
- The most species in orchid_record
- The FEWEST images in image_assets

Format output as: Genus | Species Count | Image Count | Gap Score
Order by Gap Score (species_count - image_count) descending

This will identify which important genera need more image collection.
```

**Expected Action:** Agent prioritizes these genera in the autonomous scraper

---

### Prompt 1.2 - Geographic Distribution Gaps
```
Query the orchid_record table for geographic data (latitude, longitude, habitat_notes).
Identify which major biogeographic regions have the least orchid coverage:
- Tropical (within 23.5° of equator)
- Subtropical (23.5° - 35°)  
- Temperate (35° - 60°)
- Other regions

For each region, list the top 10 genera with missing location data.

Format: Region | Genus | Records Missing Location | Percentage Missing
```

**Expected Action:** Agent targets geographic-specific scraping for these genera

---

### Prompt 1.3 - Phenological Data Gaps
```
Analyze bloom_time_start and bloom_time_end fields in orchid_record.
Calculate what percentage of records have:
- Complete bloom data (both start and end)
- Partial bloom data (only start OR end)
- No bloom data

For records missing bloom data, identify the top 15 genera by:
1. Number of species
2. Scientific importance (count of records)
3. Missing bloom percentage

Output format: Genus | Total Records | Missing Bloom % | Priority Score
```

**Expected Action:** Agent prioritizes bloom time enrichment for these genera

---

## 📊 Category 2: Data Quality Analysis

### Prompt 2.1 - Enrichment Success Patterns
```
Analyze GBIF and EOL enrichment success rates:

SELECT 
  genus,
  COUNT(*) as total,
  COUNT(CASE WHEN gbif_occurrence_count > 0 THEN 1 END) as gbif_success,
  COUNT(CASE WHEN eol_traits IS NOT NULL THEN 1 END) as eol_success,
  ROUND(100.0 * COUNT(CASE WHEN gbif_occurrence_count > 0 THEN 1 END) / COUNT(*), 2) as gbif_rate,
  ROUND(100.0 * COUNT(CASE WHEN eol_traits IS NOT NULL THEN 1 END) / COUNT(*), 2) as eol_rate
FROM orchid_record
GROUP BY genus
HAVING COUNT(*) > 10
ORDER BY (gbif_rate + eol_rate) / 2 ASC
LIMIT 20;

Identify which genera have the LOWEST enrichment success rates.
```

**Expected Action:** Agent retries enrichment for these genera with alternative strategies

---

### Prompt 2.2 - Metadata Completeness Score
```
Create a metadata completeness score for each genus:

Score = (
  has_image * 20 +
  has_habitat * 15 +
  has_bloom_time * 15 +
  has_geographic * 15 +
  has_gbif_data * 15 +
  has_eol_traits * 10 +
  has_vernacular_names * 10
) / 100

Identify the top 20 genera with:
- High record count (>50 records)
- LOW completeness score (<40%)

These are high-value targets for comprehensive enrichment.
```

**Expected Action:** Agent creates comprehensive enrichment tasks for these genera

---

### Prompt 2.3 - Duplicate Detection Analysis
```
Find potential duplicate records that need consolidation:

SELECT 
  scientific_name,
  genus,
  species,
  COUNT(*) as record_count,
  COUNT(DISTINCT image_url) as unique_images,
  COUNT(DISTINCT source_url) as unique_sources
FROM orchid_record
GROUP BY scientific_name, genus, species
HAVING COUNT(*) > 1
ORDER BY record_count DESC
LIMIT 30;

Identify patterns in duplicates - are they from different sources? 
Different image URLs? This reveals consolidation opportunities.
```

**Expected Action:** Agent implements deduplication logic for these records

---

## 🌍 Category 3: Research Priority Discovery

### Prompt 3.1 - Endangered Species Coverage
```
Using the orchid_record metadata or conservation_status field:

1. Identify records that mention: "endangered", "threatened", "rare", "vulnerable" 
   in any text fields
2. Count how many of these have:
   - Image coverage
   - Geographic data
   - Habitat information
   - Recent observation data (via GBIF timestamps)

Create priority list: Species | Conservation Status | Data Completeness %

These need URGENT comprehensive documentation.
```

**Expected Action:** Agent flags these for priority collection and enrichment

---

### Prompt 3.2 - Phylogenetic Gap Analysis
```
Analyze taxonomic coverage across orchid subtribes/alliances:

Using orchid_taxonomy table, identify which major subtribes have:
- Fewest total records
- Lowest image-to-species ratio
- Missing phylogenetic relationships (parent/child linkages)

Output: Subtribe | Tribe | Genera Count | Avg Records per Genus | Gap Score

Focus on scientifically important but under-documented groups.
```

**Expected Action:** Agent targets these taxonomic groups in scraping priorities

---

### Prompt 3.3 - Temporal Data Patterns
```
Analyze when orchid records were last updated:

SELECT 
  genus,
  COUNT(*) as total_records,
  MAX(updated_at) as last_update,
  EXTRACT(DAYS FROM NOW() - MAX(updated_at)) as days_since_update,
  COUNT(CASE WHEN updated_at < NOW() - INTERVAL '6 months' THEN 1 END) as stale_records
FROM orchid_record
GROUP BY genus
HAVING COUNT(*) > 20
ORDER BY days_since_update DESC
LIMIT 25;

Identify genera with oldest data - these need refreshing.
```

**Expected Action:** Agent schedules re-enrichment for stale records

---

## 🔬 Category 4: Cross-Reference Opportunities

### Prompt 4.1 - Hybrid Parentage Opportunities
```
Analyze orchid_parentage and orchid_record tables:

1. Find hybrid orchids (scientific_name contains '×') in orchid_record
2. Check if they exist in orchid_parentage with parent linkages
3. Identify hybrids missing parentage data

Output: Hybrid Name | In Parentage Table? | Parent 1 | Parent 2 | Action Needed

These hybrids need parentage research and documentation.
```

**Expected Action:** Agent searches for parentage data for these hybrids

---

### Prompt 4.2 - Vernacular Name Coverage
```
Analyze vernacular (common) names coverage:

SELECT 
  genus,
  COUNT(*) as total_species,
  COUNT(CASE WHEN vernacular_names IS NOT NULL THEN 1 END) as has_common_names,
  ROUND(100.0 * COUNT(CASE WHEN vernacular_names IS NOT NULL THEN 1 END) / COUNT(*), 2) as coverage_pct
FROM orchid_record
GROUP BY genus
HAVING COUNT(*) > 15
ORDER BY coverage_pct ASC
LIMIT 20;

Identify genera needing common name enrichment.
```

**Expected Action:** Agent targets EOL API for vernacular name data

---

### Prompt 4.3 - Citation and Attribution Gaps
```
Check research attribution completeness:

SELECT 
  genus,
  COUNT(*) as records,
  COUNT(data_sources) as has_sources,
  COUNT(researcher_attribution) as has_attribution,
  ROUND(100.0 * COUNT(data_sources) / COUNT(*), 2) as source_pct
FROM orchid_record
GROUP BY genus
HAVING COUNT(*) > 30
ORDER BY source_pct ASC
LIMIT 20;

Find which genera lack proper research citations.
```

**Expected Action:** Agent adds source metadata during enrichment

---

## 🎯 Category 5: Actionable Insights Generation

### Prompt 5.1 - Weekly Enrichment Priorities
```
Create this week's top 10 enrichment priorities by combining:

1. High record count (scientific importance)
2. Low data completeness (opportunity)
3. Recent query activity (if julius_ai_queries table has data)
4. Conservation status (urgent need)

Score each genus: (record_count * 0.3) + ((100-completeness%) * 0.4) + (conservation_score * 0.3)

Output: Rank | Genus | Record Count | Completeness % | Action Items | Estimated Images Available
```

**Expected Action:** Agent uses this as the enrichment queue for the week

---

### Prompt 5.2 - Data Source Effectiveness Analysis
```
Compare data acquisition effectiveness across sources:

For image_assets table:
- Count images by source (iNaturalist, GBIF, Flickr, etc.)
- Calculate avg file size, avg quality score by source
- Measure genus diversity by source

Output: Source | Image Count | Avg Quality | Genus Diversity | Effectiveness Score

Identify which sources yield the best research-quality data.
```

**Expected Action:** Agent adjusts scraper priorities to favor effective sources

---

### Prompt 5.3 - Missing Hotspot Genera
```
Identify orchid genera found in biodiversity hotspots but missing from our database:

Cross-reference known hotspot genera (Phalaenopsis, Dendrobium, Bulbophyllum, etc.) 
against current database coverage.

For each hotspot region (Southeast Asia, Andes, Madagascar, etc.):
- Expected key genera
- Current coverage %
- Missing flagship species

Output: Region | Expected Genera | Present Genera | Missing Genera | Priority
```

**Expected Action:** Agent creates targeted collection campaigns for these genera

---

## 🤖 How This Works - The Intelligence Loop

### Step 1: Run Julius AI Queries (You)
```
1. Go to julius.ai
2. Connect to your PostgreSQL database (credentials in JULIUS_AI_INTEGRATION_GUIDE.md)
3. Run 2-3 prompts from above per day
4. Copy Julius's findings to julius_communication table
```

### Step 2: Agent Processes Insights (Automatic)
```python
# Autonomous enrichment agent monitors julius_communication table
# Parses insights and creates action items:

Example Julius insight:
"Paphiopedilum has 45 species but only 12 images (73% gap)"

Agent creates:
- Priority task: Scrape Paphiopedilum images
- Target: 35+ new images
- Data sources: iNaturalist, GBIF, Flickr
- Estimated completion: 2 hours
```

### Step 3: Agent Executes & Reports (Automatic)
```
Agent:
1. Adjusts scraper priorities based on insights
2. Executes enrichment tasks
3. Updates database
4. Logs results back to julius_communication
5. You see progress next time you check Julius
```

---

## 📋 Quick Start Workflow

### Daily Routine (5 minutes):
```
1. Log into Julius AI
2. Run prompt 5.1 (Weekly Enrichment Priorities)
3. Copy output to: INSERT INTO julius_communication (message_from_julius) VALUES ('...');
4. Agent automatically processes and acts on it
5. Check back tomorrow - see new data!
```

### Weekly Deep Dive (30 minutes):
```
1. Run prompts 1.1, 2.1, 3.1, 5.2 (gaps analysis)
2. Document findings in julius_communication
3. Agent creates week-long enrichment campaign
4. Monitor progress via autonomous dashboard
```

---

## 🎯 Expected Results

### Month 1:
- Julius identifies top 50 enrichment priorities
- Agent fills 10,000+ data gaps
- Database completeness: 60% → 85%

### Month 2:
- Julius discovers research patterns
- Agent auto-targets high-value genera
- 100,000+ images acquired in priority areas

### Month 3:
- Self-sustaining intelligence loop
- Julius → Agent → Database → Julius (repeat)
- World-class orchid research platform achieved

---

## 🔗 Integration Files

- **Julius Connection Guide**: `JULIUS_AI_INTEGRATION_GUIDE.md`
- **API Documentation**: `julius_ai_api.py`
- **Communication System**: `JULIUS_COMMUNICATION_SYSTEM.md`
- **Enrichment Agent**: `autonomous_enrichment_agent.py`

---

**Let Julius be your research director, and let the agent be your tireless research assistant!** 🌸🤖
