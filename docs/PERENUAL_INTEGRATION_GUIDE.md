# Perenual API Integration Guide
## Plant Care & Growing Information for Orchid Enthusiasts

Last Updated: October 20, 2025

---

## Overview

The Orchid Continuum now integrates with **Perenual**, a comprehensive plant care database providing practical growing information for **3,000+ plant species** including orchids.

### What is Perenual?

Perenual is a modern plant care API that provides:

- **Care Guides**: Watering schedules, sunlight requirements, soil preferences
- **Hardiness Zones**: USDA hardiness zone mapping for growing regions
- **Plant Characteristics**: Growth rate, flowering season, maintenance level
- **Disease Information**: Common plant diseases and prevention (100+ diseases)
- **Safety Data**: Toxicity information for humans and pets

---

## API Capabilities

### Free Tier Features

Your current plan includes:
- ✅ **100 API requests per day**
- ✅ **Access to 3,000 species data**
- ✅ **Complete care guides & FAQs**
- ✅ **Hardiness zone maps**
- ✅ **100 plant diseases database**

### Key Endpoints

**1. Species Search**
```
GET /api/species-list?key=API_KEY&q=Phalaenopsis
```
Returns: Basic species information, common names, cycle

**2. Species Details**
```
GET /api/species/details/{id}?key=API_KEY
```
Returns: Comprehensive data including hardiness, care level, dimensions

**3. Care Guides**
```
GET /api/species-care-guide-list?key=API_KEY&species_id={id}
```
Returns: Detailed care instructions with sections for each requirement

**4. Hardiness Data**
Included in species details endpoint - no separate call needed

---

## Data Structure

### Basic Species Info
```json
{
  "id": 12345,
  "common_name": "Moth Orchid",
  "scientific_name": ["Phalaenopsis amabilis"],
  "other_name": ["Moon Orchid"],
  "cycle": "Perennial",
  "watering": "Average",
  "sunlight": ["part shade", "filtered light"]
}
```

### Detailed Care Data
```json
{
  "care_level": "Medium",
  "growth_rate": "Slow",
  "maintenance": "Moderate",
  "hardiness": {
    "min": "10",
    "max": "12"
  },
  "watering_period": "Every 7-10 days",
  "watering_general_benchmark": {
    "value": "1-2",
    "unit": "cups"
  },
  "sunlight": ["Bright indirect light"],
  "soil": ["Well-drained", "Orchid bark mix"],
  "flowering_season": ["Spring", "Summer"],
  "indoor": true,
  "tropical": true,
  "poisonous_to_pets": false,
  "poisonous_to_humans": false
}
```

---

## Integration Architecture

### Data Flow

```
1. Orchid Taxonomy Database (35,320 species)
   ↓
2. Search Perenual API by scientific name
   ↓
3. Retrieve:
   - Basic species info
   - Detailed care guide
   - Hardiness zones
   ↓
4. Store in PostgreSQL:
   - orchid_taxonomy.external_ids['perenual'] (JSONB)
   - Tracks API usage in perenual_api_log
```

### Database Schema

#### orchid_taxonomy.external_ids['perenual']
```json
{
  "perenual": {
    "status": "success",
    "perenual_id": 12345,
    "common_name": "Moth Orchid",
    "watering": "Average",
    "sunlight": ["part shade", "filtered light"],
    "care_level": "Medium",
    "hardiness": {"min": "10", "max": "12"},
    "indoor": true,
    "tropical": true,
    "flowering_season": ["Spring", "Summer"],
    "poisonous_to_pets": false,
    "last_updated": "2025-10-20T12:00:00"
  }
}
```

#### perenual_api_log
Tracks API usage for quota management:
```sql
CREATE TABLE perenual_api_log (
    id SERIAL PRIMARY KEY,
    endpoint VARCHAR(200),
    success BOOLEAN,
    error_message TEXT,
    request_time TIMESTAMP DEFAULT NOW()
);
```

---

## Setup & Usage

### 1. API Key Configuration

Your API key is already stored in Replit Secrets:
- **Key name**: `BOTANICAL_API`
- **Access via**: Replit Secrets (Tools → Secrets)

**SECURITY**: Never share your API key publicly!

### 2. Run Enrichment

Execute the Perenual enrichment script:

```bash
python validation/enrich_perenual.py
```

**What it does:**
- Checks daily quota (100 requests/day)
- Searches orchid species in Perenual database
- Retrieves care guides and hardiness data
- Updates taxonomy records with practical growing info
- Logs all requests for quota tracking

### 3. Monitor Progress

Real-time progress display:
```
================================================================================
🌿 PERENUAL CARE GUIDE COLLECTOR
Plant Care & Growing Information - 100 requests/day
================================================================================
API quota: 95/100 requests remaining today

    1 | Phalaenopsis amabilis    | Care: Medium    | Water: Average    | 1.2 sp/min | Quota: 94/100
    2 | Dendrobium nobile        | Care: Medium    | Water: Minimum    | 1.5 sp/min | Quota: 93/100
...
```

### 4. Check Quota Status

```bash
# Check API usage
psql $DATABASE_URL -c "SELECT COUNT(*) FROM perenual_api_log WHERE request_time > NOW() - INTERVAL '24 hours'"
```

---

## API Rate Limits & Best Practices

### Daily Quota Management

**Free Tier**: 100 requests per day
- Resets 24 hours after first request
- Script automatically tracks usage
- Stops when quota exhausted (with 5-request buffer)

**Quota Tracking:**
```python
# Check remaining quota
has_quota, remaining = check_daily_quota()
if not has_quota:
    print("Daily quota exhausted. Try again tomorrow.")
```

### Request Optimization

**1. Prioritize Popular Genera:**
- Phalaenopsis, Dendrobium, Cattleya processed first
- Maximizes value from limited daily quota

**2. Batch Processing:**
- Process ~100 species per day
- Complete enrichment of 35,320 species in ~353 days
- Can upgrade to paid plan for faster completion

**3. Smart Caching:**
- Only process species once
- Status-based retry (success/error/not_found)
- Preserves quota for new species

---

## Features & Benefits

### For Orchid Growers

✅ **Care Requirements**: Water, light, temperature needs
✅ **Hardiness Zones**: Know which orchids grow in your area
✅ **Maintenance Level**: Easy/Medium/Difficult ratings
✅ **Safety Information**: Pet and child safety data
✅ **Growing Conditions**: Indoor/outdoor, tropical status

### For the Platform

✅ **Practical Data**: Complements scientific taxonomy
✅ **User-Friendly**: Non-technical growing advice
✅ **Comprehensive**: 60+ data fields per species
✅ **FREE Access**: 100 requests/day on free tier
✅ **Automatic Tracking**: Built-in quota management

---

## Data Quality

### Strengths
- ✅ User-friendly care instructions
- ✅ Practical watering/lighting guides
- ✅ Safety information (toxicity)
- ✅ Hardiness zone accuracy
- ✅ Modern API with JSON responses

### Limitations
- ⚠️ Limited to 3,000 species (free tier)
- ⚠️ May not have rare/endemic orchids
- ⚠️ 100 requests/day quota
- ⚠️ Generic care info (not cultivation-specific)

### Recommended Use
- **Primary**: General care guides for common orchids
- **Secondary**: Supplement with GBIF wild data
- **Combined with**: 
  - GBIF → Wild habitat conditions
  - EOL → Scientific traits
  - Tropicos → Herbarium specimens
  - Perenual → Practical growing advice

---

## Integration with Other Sources

### GBIF (Wild Occurrence Data)
- **GBIF**: Where orchids grow naturally
- **Perenual**: How to grow them at home
- **Synergy**: Match wild conditions to home care

### EOL (Trait Data)
- **EOL**: Morphological measurements
- **Perenual**: Growing characteristics
- **Synergy**: Scientific + practical knowledge

### Tropicos (Herbarium Specimens)
- **Tropicos**: Scientific nomenclature
- **Perenual**: Common names & care
- **Synergy**: Academic + hobbyist audiences

### Combined Power
```
GBIF (104K+ wild images)
  + EOL (5.8M images + 78K traits)
  + Tropicos (4.2M specimens)
  + Perenual (3K care guides)
  = Complete orchid knowledge platform
```

---

## Upgrade Options

### Paid Plans

If you need more than 100 requests/day, Perenual offers:

**Premium Plan** (~$20/month):
- 5,000 API requests/month
- Faster enrichment
- Same feature access

**Enterprise** (Custom pricing):
- Unlimited requests
- Priority support
- Bulk data access

### Current Status
Your free tier provides excellent value:
- 100 orchids/day = 3,000/month
- Perfect for gradual enrichment
- Upgrade when database grows

---

## Technical Implementation

### Script Location
`validation/enrich_perenual.py`

### Key Functions

**search_perenual_species()**
- Searches by scientific name
- Returns: Species ID, common name, basic care
- Handles: Rate limits, quota checks

**get_species_details()**
- Retrieves comprehensive data
- Extracts: 60+ data fields
- Includes: Hardiness, dimensions, characteristics

**get_care_guide()**
- Fetches detailed care instructions
- Returns: Watering, lighting, soil guides
- Format: Structured sections

**update_taxonomy_perenual()**
- Merges Perenual data into external_ids
- Preserves: Existing GBIF, EOL, Tropicos data
- Status tracking: success/error/not_found

### Error Handling
- ✅ Daily quota enforcement
- ✅ Automatic request logging
- ✅ Graceful degradation on errors
- ✅ 404 handling (species not found)
- ✅ Rate limiting (1 second delay)

---

## Example API Calls

### Search for Orchid
```bash
curl "https://perenual.com/api/species-list?key=YOUR_KEY&q=Phalaenopsis"
```

**Response:**
```json
{
  "data": [
    {
      "id": 12345,
      "common_name": "Moth Orchid",
      "scientific_name": ["Phalaenopsis amabilis"],
      "watering": "Average",
      "sunlight": ["part shade"]
    }
  ]
}
```

### Get Care Guide
```bash
curl "https://perenual.com/api/species/details/12345?key=YOUR_KEY"
```

**Response:**
```json
{
  "id": 12345,
  "care_level": "Medium",
  "watering_period": "Every 7-10 days",
  "hardiness": {"min": "10", "max": "12"},
  "indoor": true,
  "flowering_season": ["Spring", "Summer"]
}
```

---

## Troubleshooting

### Problem: "Daily quota exhausted"
**Cause**: Used 100 API requests in 24 hours
**Solution**: Wait until 24 hours after first request, then retry
**Prevention**: Monitor quota with `check_daily_quota()`

### Problem: "Species not found"
**Cause**: Orchid not in Perenual's 3,000 species database
**Solution**: Normal - rare/endemic species may not be included
**Alternative**: Use GBIF/EOL for those species

### Problem: "API key invalid"
**Cause**: BOTANICAL_API secret not set correctly
**Solution**: Check Replit Secrets, verify key is active

### Problem: "Slow processing"
**Cause**: 1-second rate limit between requests
**Solution**: Normal - prevents API overload. Consider paid plan for faster access.

---

## Use Cases

### 1. Beginner Orchid Grower
**Question**: "Is this orchid easy to grow?"
**Answer**: Check care_level field
- Easy: Great for beginners
- Medium: Some experience needed
- Difficult: Expert growers only

### 2. Indoor Gardener
**Question**: "Can I grow this orchid indoors?"
**Answer**: Check indoor field
- true: Suitable for indoor growing
- false: Needs outdoor conditions

### 3. Regional Grower
**Question**: "Will this orchid survive my climate?"
**Answer**: Check hardiness zones
- Match to USDA zone map
- Consider indoor growing if outside range

### 4. Pet Owner
**Question**: "Is this orchid safe for my cat?"
**Answer**: Check poisonous_to_pets field
- false: Safe for pets
- true: Keep away from animals

---

## Future Enhancements

### Planned Features
- [ ] Care guide widget for species pages
- [ ] Hardiness zone map visualization
- [ ] Watering schedule calendar
- [ ] Growing difficulty filter
- [ ] Pet-safe orchid gallery

### Integration Ideas
- [ ] Combine with weather data for location-specific advice
- [ ] Link to local nursery availability
- [ ] Create beginner-friendly orchid recommendations
- [ ] Seasonal care reminders

---

## Resources

### Official Documentation
- **API Docs**: https://perenual.com/docs/api
- **Main Site**: https://perenual.com/
- **Pricing**: https://perenual.com/pricing

### Support
- **API Questions**: support@perenual.com
- **Bug Reports**: Use Orchid Continuum bug report system
- **Feature Requests**: Contact via platform

---

## License & Attribution

### Data License
Perenual data is provided under their standard API terms of service.

### Attribution
When using Perenual data in public displays:
```
Plant care data provided by Perenual
https://perenual.com/
```

### Citation Format
For academic papers:
```
Perenual. [Year]. Plant Care Database. 
Retrieved [Date] from https://perenual.com/api
```

---

## Summary

✅ **3,000 species** with practical care guides
✅ **100 requests/day** on free tier (upgradable)
✅ **60+ data fields** per species including hardiness, care level, safety
✅ **Automatic quota tracking** prevents overuse
✅ **Seamless integration** with existing GBIF, EOL, Tropicos data

**Start enriching now:**
```bash
python validation/enrich_perenual.py
```

Perenual adds the practical growing knowledge that orchid enthusiasts need! 🌸

---

## Quick Reference

### Commands
```bash
# Run enrichment
python validation/enrich_perenual.py

# Check quota
psql $DATABASE_URL -c "SELECT COUNT(*) FROM perenual_api_log WHERE request_time > NOW() - INTERVAL '24 hours'"

# View recent requests
psql $DATABASE_URL -c "SELECT endpoint, success, request_time FROM perenual_api_log ORDER BY request_time DESC LIMIT 10"
```

### Key Files
- **Enrichment script**: `validation/enrich_perenual.py`
- **Documentation**: `docs/PERENUAL_INTEGRATION_GUIDE.md`
- **API key**: Replit Secrets → `BOTANICAL_API`
- **Logs**: `/tmp/perenual.log`

### Important URLs
- **API base**: https://perenual.com/api
- **Docs**: https://perenual.com/docs/api
- **Dashboard**: https://perenual.com/user/api-key
