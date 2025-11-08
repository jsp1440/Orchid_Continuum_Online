# FOR JULIUS AI: Orchid Continuum Coverage Expansion Collaboration

## 🎯 Mission: Achieve 100% AI-Ready Species Coverage

**Goal**: Get 30+ images for ALL 35,327 orchid species to enable statistically significant AI vision analysis

**Current Status** (as of Nov 5, 2025):
- **AI-Ready (30+ images)**: 106 species (0.3%)
- **Needs Work**: 35,221 species (99.7%)
- **Total Images**: 111,689
- **Images Needed**: ~1,053,030 (for 30 images/species)

---

## 🤝 How You Can Help

### Option 1: Use the REST API (Recommended)

I've built a secure REST API at `https://[replit-url]/api/` that you can call to:

1. **Get species lists** that need images
2. **Submit discovered image URLs** directly to the database
3. **Track progress** in real-time
4. **Coordinate work** so we don't duplicate efforts

#### API Authentication
```
Authorization: Bearer [JULIUS_API_KEY]
```
The API key is stored in the environment as `JULIUS_API_KEY`.

---

## 📡 API Endpoints

### 1. Get Coverage Summary
```http
GET /api/coverage/summary
Authorization: Bearer [API_KEY]
```

**Response:**
```json
{
  "total_species": 35327,
  "species_with_images": 422,
  "species_missing": 34905,
  "total_images": 111689,
  "coverage_percent": 1.19,
  "ai_readiness": {
    "no_images": 34905,
    "insufficient_1_9": 228,
    "minimum_10_29": 88,
    "ideal_30_49": 44,
    "excellent_50_plus": 62
  },
  "ai_ready_species": 106,
  "ai_ready_percent": 0.3
}
```

---

### 2. Get Species Needing Images
```http
GET /api/species/missing?limit=100&priority=CRITICAL
Authorization: Bearer [API_KEY]
```

**Parameters:**
- `limit`: Number of species to return (default: 100)
- `priority`: 
  - `CRITICAL` = 0 images (highest priority)
  - `HIGH` = 1-9 images
  - `MEDIUM` = 10-29 images

**Response:**
```json
{
  "priority": "CRITICAL",
  "count": 100,
  "species": [
    {
      "taxonomy_id": 1234,
      "scientific_name": "Phalaenopsis stuartiana",
      "genus": "Phalaenopsis",
      "species": "stuartiana",
      "current_images": 0,
      "images_needed": 30
    },
    ...
  ]
}
```

---

### 3. Get Priority Genera
```http
GET /api/genera/priority?limit=50
Authorization: Bearer [API_KEY]
```

**Response:**
```json
{
  "count": 50,
  "genera": [
    {
      "genus": "Bulbophyllum",
      "total_species": 2850,
      "species_no_images": 2810,
      "species_with_images": 40,
      "total_images": 156,
      "coverage_percent": 1.4
    },
    ...
  ]
}
```

---

### 4. Submit Discovered Images
```http
POST /api/images/submit
Authorization: Bearer [API_KEY]
Content-Type: application/json
```

**Request Body:**
```json
{
  "taxonomy_id": 1234,
  "images": [
    {
      "url": "https://example.com/image1.jpg",
      "source": "iNaturalist",
      "photographer": "Jane Doe",
      "license": "CC-BY-NC",
      "latitude": 14.5994,
      "longitude": 120.9842
    },
    {
      "url": "https://example.com/image2.jpg",
      "source": "GBIF",
      "photographer": "John Smith",
      "license": "CC-BY"
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "images_submitted": 2,
  "images_inserted": 2,
  "duplicates_skipped": 0
}
```

---

### 5. Get Daily Progress
```http
GET /api/progress/daily
Authorization: Bearer [API_KEY]
```

**Response:**
```json
{
  "period": "last_30_days",
  "daily_stats": [
    {
      "date": "2025-11-05",
      "images_added": 4511,
      "species_touched": 156
    },
    ...
  ]
}
```

---

## 🔍 Image Hunting Strategy

### Best Data Sources (Ranked)

1. **iNaturalist** (5M+ orchid observations)
   - API: https://api.inaturalist.org/v1/observations
   - Filter: `taxon_name=[scientific_name]&photos=true&quality_grade=research`
   - Best for: Common species, recent observations

2. **GBIF** (2M+ occurrences with images)
   - API: https://api.gbif.org/v1/occurrence/search
   - Filter: `scientificName=[name]&mediaType=StillImage`
   - Best for: Herbarium specimens, museum collections

3. **EOL** (Encyclopedia of Life)
   - API: https://eol.org/api
   - Best for: Curated, high-quality images

4. **Tropicos** (Missouri Botanical Garden)
   - API: https://services.tropicos.org
   - Best for: Type specimens, Central/South American species

5. **Regional Databases**
   - ALA (Atlas of Living Australia)
   - Chinese Virtual Herbarium
   - Euro+Med PlantBase

---

## 📋 Recommended Workflow for Julius

### Daily Batch Processing

```python
import requests

API_URL = "https://[replit-url]/api"
API_KEY = "[JULIUS_API_KEY]"
headers = {"Authorization": f"Bearer {API_KEY}"}

# 1. Get 50 species needing images
response = requests.get(
    f"{API_URL}/species/missing?limit=50&priority=CRITICAL",
    headers=headers
)
species_list = response.json()['species']

# 2. For each species, search external APIs
for species in species_list:
    scientific_name = species['scientific_name']
    taxonomy_id = species['taxonomy_id']
    
    # Search iNaturalist, GBIF, etc.
    images = search_for_images(scientific_name)
    
    # 3. Submit found images
    if images:
        requests.post(
            f"{API_URL}/images/submit",
            headers=headers,
            json={
                "taxonomy_id": taxonomy_id,
                "images": images
            }
        )

# 4. Check progress
progress = requests.get(f"{API_URL}/coverage/summary", headers=headers)
print(f"AI-Ready: {progress.json()['ai_ready_percent']}%")
```

---

## 🎯 Priority Targets

### Immediate Focus (Week 1)

**Target:** Top 50 most diverse genera with poor coverage

Run this to get the list:
```http
GET /api/genera/priority?limit=50
```

Expected high-priority genera:
- Bulbophyllum (~2,850 species, mostly missing)
- Pleurothallis (~1,200 species, mostly missing)
- Epidendrum (~1,500 species, mostly missing)
- Dendrobium (~1,800 species, good coverage but need 30+ each)

### Week 2-4: Regional Sweeps

1. **Southeast Asia** (highest diversity)
   - Philippines, Indonesia, Papua New Guinea
   - Focus on Phalaenopsis, Dendrobium, Bulbophyllum

2. **Central/South America** (second highest)
   - Colombia, Ecuador, Brazil
   - Focus on Epidendrum, Pleurothallis, Maxillaria

3. **Africa & Madagascar**
   - Focus on Angraecum, Aerangis, Polystachya

---

## 📊 Success Metrics

Track these daily:

1. **Species coverage %**: Target 100%
2. **AI-ready species**: Target 35,327 (100%)
3. **Average images per species**: Target 30+
4. **Daily ingestion rate**: Target 1,000-5,000 images/day

---

## 🚨 Important Notes

### Image Quality Requirements
- **Resolution**: Minimum 800px on shortest side
- **License**: CC-BY, CC-BY-NC, CC-BY-SA, or public domain
- **Content**: Clear view of flowers (diagnostic features)
- **Avoid**: Blurry, over-filtered, or heavily cropped images

### Deduplication
The system automatically handles duplicates via `image_url` uniqueness.
You can submit the same URLs multiple times - duplicates are silently skipped.

### Rate Limiting
- iNaturalist: ~100 requests/minute
- GBIF: No strict limit (be respectful)
- EOL: ~60 requests/minute

---

## 🎉 Goal Timeline

**With Julius AI helping:**

| Timeframe | Target | Daily Rate |
|-----------|--------|------------|
| Week 1 | 115,000 images | 5,000/day |
| Month 1 | 260,000 images | 5,000/day |
| Month 2 | 410,000 images | 5,000/day |
| Month 3 | 560,000 images | 5,000/day |
| Month 6 | 1,060,000 images | 5,000/day |

**At 5,000 images/day, we reach 1M+ images (AI-ready for all species) in ~6 months!**

---

## 📞 Coordination

**Files for Review:**
- `MISSING_SPECIES_PRIORITY.csv` - 35,221 species ranked by priority
- `GENUS_COVERAGE_SUMMARY.csv` - 746 genera with coverage stats

**Shared Goals:**
- Replit Agent: Build infrastructure, coordinate, database management
- Julius AI: Image discovery, API queries, batch processing
- User's Computer: Offline processing, rare species downloads

**Let's achieve 100% AI-ready coverage together!** 🌺🤖
