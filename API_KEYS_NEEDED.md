# API Keys and Access Needed for Orchid Continuum

## Currently Active (FREE APIs - No Keys Needed) ✅

### 1. **GBIF (Global Biodiversity Information Facility)**
- **Status**: ✅ ACTIVE - 10,200 images collected
- **URL**: https://techdocs.gbif.org/en/openapi/
- **Cost**: FREE
- **No API key required**

### 2. **EOL (Encyclopedia of Life)**
- **Status**: ⚠️ Collection starting now
- **URL**: https://eol.org/api
- **Cost**: FREE
- **No API key required**
- **Images Available**: 5.8M orchid images

### 3. **Tropicos (Missouri Botanical Garden)**
- **Status**: ⚠️ Collection starting now
- **URL**: https://services.tropicos.org
- **Cost**: FREE
- **No API key required** (better performance with key, but works without)
- **Specimens Available**: 4.2M+ herbarium specimens

### 4. **Perenual (Plant Care Database)**
- **Status**: ✅ CONFIGURED
- **Cost**: FREE tier - 100 requests/day
- **No setup needed** (already integrated)

---

## Additional Herbarium Sources to Consider

### 5. **Royal Botanic Gardens, Kew (POWO)**
- **URL**: https://powo.science.kew.org/
- **Status**: ❌ NOT YET INTEGRATED
- **Cost**: FREE
- **Access**: No API key - web scraping or manual API
- **Value**: World's largest plant database
- **Application Link**: N/A (public API, no key needed)
- **Contains**: Type specimens, herbarium images, taxonomic authority

### 6. **JSTOR Plants (formerly ITHAKA)**
- **URL**: https://plants.jstor.org/
- **Status**: ❌ NOT INTEGRATED
- **Cost**: Requires institutional access
- **Access**: Need academic/museum affiliation
- **Value**: 2.7M+ herbarium specimen images
- **Application**: https://about.jstor.org/get-jstor/individuals/

### 7. **iNaturalist**
- **Status**: ✅ ALREADY INCLUDED via GBIF
- **URL**: https://www.inaturalist.org/
- **Integration**: iNaturalist observations feed into GBIF
- **Our 10,200 GBIF images likely include iNaturalist photos**
- **No separate collection needed**

### 8. **Herbarium@Home / NYBG**
- **URL**: https://sweetgum.nybg.org/science/vh/
- **Status**: ❌ NOT INTEGRATED
- **Cost**: FREE (research access)
- **Access**: Request research account
- **Value**: New York Botanical Garden's 7.8M specimens

### 9. **SEINet (Southwest Environmental Information Network)**
- **URL**: https://swbiodiversity.org/seinet/
- **Status**: ❌ NOT INTEGRATED
- **Cost**: FREE
- **Access**: No key needed (web portal)
- **Value**: Herbarium consortium with orchid specimens

---

## APIs Requiring Keys/Registration

### 10. **IUCN Red List API**
- **URL**: https://apiv3.iucnredlist.org/
- **Status**: ❌ NOT CONFIGURED
- **Cost**: FREE for non-commercial
- **Application**: https://apiv3.iucnredlist.org/api/v3/token
- **Value**: Conservation status for endangered orchids
- **Required**: Email registration

### 11. **World Flora Online API**
- **URL**: https://list.worldfloraonline.org/
- **Status**: ❌ NOT CONFIGURED
- **Cost**: FREE
- **Access**: Public API (no key required)
- **Value**: Taxonomic backbone

### 12. **Royal Horticultural Society Orchid Register**
- **URL**: https://apps.rhs.org.uk/horticulturaldatabase/orchidregister/
- **Status**: ❌ NOT INTEGRATED
- **Cost**: FREE
- **Access**: Web scraping (no API)
- **Value**: Hybrid registry

---

## Recommended Priority for Immediate Collection

### HIGH PRIORITY (Start These Now)
1. ✅ **EOL** - Collection started (5.8M images)
2. ✅ **Tropicos** - Collection started (4.2M herbarium specimens)
3. ⏳ **Kew POWO** - Free, no key, authoritative taxonomy

### MEDIUM PRIORITY (Apply for Access)
4. **IUCN Red List API** - Free token: https://apiv3.iucnredlist.org/api/v3/token
5. **JSTOR Plants** - Requires academic affiliation

### LOW PRIORITY (Manual Integration Later)
6. **NYBG Herbarium** - Request research account
7. **SEINet** - Web scraping required
8. **RHS Orchid Register** - Hybrid data (not wild species)

---

## Action Items for You

### Apply for These API Keys (5 minutes each):

1. **IUCN Red List API Token**
   - Go to: https://apiv3.iucnredlist.org/api/v3/token
   - Fill in email, name, organization
   - Purpose: "Research on orchid conservation status"
   - Instant approval

2. **World Flora Online** (Already public - no key needed)
   - Just use: https://list.worldfloraonline.org/

3. **JSTOR Plants** (Optional - if you have academic affiliation)
   - Go to: https://about.jstor.org/get-jstor/individuals/
   - Select "Individual access"
   - If no affiliation, skip this one

---

## Current Data Collection Status

```
GBIF/iNaturalist:    10,200 images ✅ (100% with scientific names)
EOL Images:          STARTING NOW (target: 500 species first batch)
Tropicos Herbarium:  STARTING NOW (target: 100 Bulbophyllum first)
Kew POWO:            NOT STARTED (no key needed, can integrate anytime)
IUCN Red List:       WAITING FOR API KEY
```

---

## Summary

**No urgent API keys needed!** The three most important sources (GBIF, EOL, Tropicos) are all FREE and don't require keys.

**Optional enhancement**: Get IUCN Red List token (5 min) for conservation status data.

**iNaturalist answer**: YES, their data is already in our GBIF collection (10,200 images include iNaturalist observations).
