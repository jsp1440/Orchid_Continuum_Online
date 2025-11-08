# Multi-Source Orchid Data Enrichment Strategy

## Data Source Analysis & Implementation Plan

### Status: GBIF Phase 1 Running (~40 min remaining)
- **Progress**: 156/5,914 orchids (2.6%)  
- **Speed**: 104 orchids/minute
- **ETA**: Complete by 6:00 PM

---

## 🌍 DATA SOURCE COMPARISON

### 1. **GBIF** (Currently Running) ⚡
**Status**: ✅ ACTIVE  
**API**: https://api.gbif.org/v1/  
**Authentication**: None required  
**Data Provided**:
- ✅ Real specimen occurrence data
- ✅ Geographic coordinates (lat/long) - High precision Numeric
- ✅ Elevation data (meters)
- ✅ Institution codes & catalog numbers
- ✅ Collector information
- ✅ GBIF occurrence keys (BigInteger 64-bit)
- ❌ NO cultural/growing requirements
- ❌ NO morphological trait data

**Database Fields Updated**:
- `latitude`, `longitude`, `elevation_m`
- `gbif_occurrence_key`, `institution_code`, `catalog_number`
- `gbif_dataset_key`, `gbif_last_synced_at`

---

### 2. **Missouri Botanical Garden (Tropicos)** 🌺
**Status**: 🔍 Research Complete - Ready to Implement  
**API**: http://services.tropicos.org/  
**Authentication**: API Key required (free registration)  
**Orchid Project**: ID #47 (dedicated orchid collection)

**Data Provided**:
- ✅ Authoritative nomenclature
- ✅ Bibliographic records
- ✅ Specimen data (4.87M+ specimens)
- ✅ Type specimens
- ✅ Author citations
- ✅ Publication references
- ✅ High-quality images (685K+)

**Database Fields to Add**:
```sql
tropicos_name_id BIGINT
tropicos_specimen_id VARCHAR(100)
tropicos_author VARCHAR(500)
tropicos_publication TEXT
tropicos_type_specimen VARCHAR(200)
tropicos_images JSONB
tropicos_last_synced_at TIMESTAMP
```

**Implementation Priority**: HIGH (authoritative nomenclature)

---

### 3. **POWO (Kew Gardens - Plants of the World Online)** 🇬🇧
**Status**: ✅ Already Integrated! (We have this module)  
**API**: http://www.plantsoftheworldonline.org/  
**Authentication**: None required

**Data Provided**:
- ✅ **Gold standard taxonomy** (Kew is world authority)
- ✅ Accepted names & synonyms
- ✅ Geographic distribution (native ranges)
- ✅ Publication citations
- ✅ Basionym information
- ✅ Infraspecific taxa

**Database Fields** (Already Exists):
- `powo_taxon_id`, `powo_accepted_name`
- `powo_native_range` (JSONB)
- `powo_last_synced_at`

**Implementation Priority**: HIGH (run after GBIF completes)

---

### 4. **EOL (Encyclopedia of Life)** 🌿
**Status**: ⚠️ Has SSL Certificate Issues  
**API**: https://eol.org/api/  
**Authentication**: None required

**Data Provided**:
- ✅ Conservation genetics (TraitBank)
- ✅ Phenotypic traits & morphology
- ✅ Rich species descriptions
- ✅ Vernacular names (multilingual JSONB)
- ❌ NO specimen-level occurrence data

**Database Fields** (Already Exists):
- `eol_page_id`, `eol_descriptions` (JSONB)
- `vernacular_names` (JSONB)
- `conservation_genetics` (JSONB)
- `eol_last_synced_at`

**Implementation Priority**: MEDIUM (run when SSL fixed, or skip)

---

### 5. **orchidspecies.com (Jay's IOSPE)** 📸
**Status**: 🔍 Web Scraping Required (No API)  
**URL**: https://orchidspecies.com/  
**Authentication**: None (public site)  
**Data Source**: Compiled from Kew & Missouri databases

**Data Provided**:
- ✅ Cultural requirements (temperature, light, water)
- ✅ Blooming seasons
- ✅ Growing difficulty ratings
- ✅ High-quality photos (COPYRIGHTED - link only, don't download)
- ✅ Habitat descriptions
- ✅ Taxonomic synonyms

**Database Fields to Add**:
```sql
iospe_culture_temp VARCHAR(50)  -- "Cool to Intermediate"
iospe_culture_light VARCHAR(50)  -- "Bright indirect"
iospe_culture_water VARCHAR(50)  -- "Keep moist"
iospe_bloom_season VARCHAR(100)  -- "Spring to Summer"
iospe_difficulty VARCHAR(20)     -- "Easy", "Moderate", "Advanced"
iospe_photo_url TEXT             -- Link only (respect copyright)
iospe_habitat_description TEXT
iospe_last_synced_at TIMESTAMP
```

**Implementation Priority**: HIGH (cultural data is critical for growers)

---

### 6. **Andy's Orchids (andysorchids.com)** 🏪
**Status**: 🔍 E-commerce Scraping (No API)  
**URL**: https://andysorchids.com/  
**Authentication**: None (public catalog)

**Data Provided**:
- ✅ Commercial availability & pricing
- ✅ Size/mount information
- ✅ Care requirements
- ✅ Origin information
- ✅ Rare species identification

**Database Fields to Add**:
```sql
andys_available BOOLEAN
andys_price DECIMAL(10,2)
andys_size_info VARCHAR(200)
andys_care_notes TEXT
andys_last_checked_at TIMESTAMP
```

**Implementation Priority**: MEDIUM (commercial data useful but not scientific)

---

### 7. **Huntington Botanical Gardens** 🏛️
**Status**: ⚠️ No Public API (10,000+ plants, 1,600 species)  
**URL**: https://www.huntington.org/orchid-collection  
**Access**: Web-only interactive database

**Data Provided**:
- ✅ Living collection status
- ✅ Cultivation records
- ✅ Conservation status
- ❌ No API available

**Workaround**: Contact curator for data partnership OR use GBIF (they submit to GBIF)

**Implementation Priority**: LOW (data available through other sources)

---

## 📋 RECOMMENDED ENRICHMENT SEQUENCE

### **Phase 1: GBIF** ✅ (RUNNING NOW - 40 min remaining)
- Geographic occurrence data
- Specimen metadata
- Institution references

### **Phase 2: POWO (Kew Gardens)** (60 min)
- Authoritative taxonomy validation
- Accepted names & synonyms
- Native geographic ranges

### **Phase 3: Missouri Tropicos** (90 min)
- Nomenclatural verification
- Type specimens
- Publication citations
- Additional imagery

### **Phase 4: orchidspecies.com** (120 min)
- Cultural requirements (CRITICAL FOR GROWERS)
- Blooming seasons
- Growing difficulty
- Habitat descriptions

### **Phase 5: EOL** (when SSL fixed) (60 min)
- Conservation genetics
- TraitBank morphological data
- Vernacular names

### **Phase 6: AI Vision** (targeted - 120 min)
- Fill remaining visual analysis gaps
- Only for orchids missing key data

### **Phase 7: Andy's Orchids** (optional - 90 min)
- Commercial availability
- Pricing data (changes frequently)

---

## 🔧 IMPLEMENTATION APPROACH

### Database Schema Additions Required:

```sql
-- Missouri Tropicos fields
ALTER TABLE orchid_record ADD COLUMN tropicos_name_id BIGINT;
ALTER TABLE orchid_record ADD COLUMN tropicos_author VARCHAR(500);
ALTER TABLE orchid_record ADD COLUMN tropicos_publication TEXT;
ALTER TABLE orchid_record ADD COLUMN tropicos_last_synced_at TIMESTAMP;

-- Cultural data from orchidspecies.com
ALTER TABLE orchid_record ADD COLUMN culture_temperature VARCHAR(50);
ALTER TABLE orchid_record ADD COLUMN culture_light VARCHAR(50);
ALTER TABLE orchid_record ADD COLUMN culture_water VARCHAR(50);
ALTER TABLE orchid_record ADD COLUMN bloom_season VARCHAR(100);
ALTER TABLE orchid_record ADD COLUMN growing_difficulty VARCHAR(20);
ALTER TABLE orchid_record ADD COLUMN iospe_last_synced_at TIMESTAMP;

-- Andy's Orchids commercial data
ALTER TABLE orchid_record ADD COLUMN commercial_available BOOLEAN DEFAULT false;
ALTER TABLE orchid_record ADD COLUMN commercial_price DECIMAL(10,2);
ALTER TABLE orchid_record ADD COLUMN commercial_last_checked_at TIMESTAMP;
```

### Integration Modules to Create:

1. **`external_databases/tropicos_integration.py`**
   - API wrapper for Missouri Botanical Garden
   - Methods: search_species(), get_nomenclature(), get_specimens()

2. **`external_databases/iospe_scraper.py`**
   - Web scraper for orchidspecies.com
   - Respectful rate limiting (2-3 second delays)
   - Methods: get_cultural_data(), get_habitat_info()

3. **`external_databases/andys_scraper.py`** (optional)
   - E-commerce catalog scraper
   - Methods: check_availability(), get_pricing()

4. **`batch_sequential_enrichment.py`**
   - Orchestrates all enrichment phases
   - Tracks progress across sources
   - Generates comprehensive reports

---

## 🎯 DATA QUALITY BENEFITS

### Cross-Validation Strategy:
- **Taxonomy**: Compare GBIF → POWO → Tropicos → IOSPE
- **Geography**: Validate GBIF occurrence vs POWO native range
- **Cultural Info**: IOSPE provides what scientific databases lack
- **Confidence Scoring**: More sources confirming data = higher confidence

### Example Multi-Source Record:
```json
{
  "species": "Cattleya labiata",
  "gbif_occurrence": {
    "latitude": -7.123, 
    "longitude": -35.456,
    "elevation_m": 850,
    "institution": "NYBG"
  },
  "powo_taxonomy": {
    "accepted_name": "Cattleya labiata Lindl.",
    "native_range": ["Brazil Northeast"]
  },
  "tropicos": {
    "author": "Lindley",
    "publication": "Edwards's Bot. Reg. 23: sub t. 1947 (1837)"
  },
  "iospe_culture": {
    "temperature": "Intermediate to Warm",
    "light": "Bright indirect (2000-3000 fc)",
    "water": "Water when approaching dryness",
    "bloom_season": "Winter to Spring",
    "difficulty": "Easy"
  },
  "data_confidence": "HIGH (4 sources agree)"
}
```

---

## 📊 ESTIMATED TOTAL ENRICHMENT TIME

| Phase | Source | Time | Fields Added |
|-------|--------|------|--------------|
| 1 | GBIF | 1 hour | 10 fields |
| 2 | POWO | 1 hour | 8 fields |
| 3 | Tropicos | 1.5 hours | 12 fields |
| 4 | IOSPE | 2 hours | 15 fields |
| 5 | EOL | 1 hour | 8 fields |
| 6 | AI Vision | 2 hours | 5 fields |
| 7 | Andy's | 1.5 hours | 5 fields |
| **TOTAL** | **7 sources** | **10 hours** | **63 fields** |

**Combined with existing 87 fields = 150+ research-grade fields per orchid!**

---

## 🚀 NEXT STEPS

1. ✅ Let GBIF Phase 1 complete (~40 min)
2. 🔨 Create Tropicos integration module
3. 🔨 Create IOSPE scraper module  
4. 🔨 Add new database fields
5. 🔨 Build sequential enrichment orchestrator
6. ▶️ Run Phase 2-7 enrichments
7. 📊 Generate comprehensive data quality report
8. 🎉 Deploy enriched database to production

---

**Ready to build the world's most comprehensive orchid research database!** 🌺
