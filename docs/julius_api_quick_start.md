# Julius AI API - Quick Start Guide

**The Orchid Continuum API** provides secure access to botanical glossary, dichotomous keys, taxonomy, and GBIF image data for Julius AI analysis.

---

## 🔐 Authentication Setup

Your API key is stored in the environment as `JULIUS_API_KEY`.

**Two authentication methods supported (headers only for security):**

1. **Bearer Token** (Recommended - Standard OAuth format)
```bash
curl -H "Authorization: Bearer YOUR_KEY_HERE" \
     https://your-replit-url.repl.co/api/julius/health
```

2. **X-API-Key Header** (Also supported for backward compatibility)
```bash
curl -H "X-API-Key: YOUR_KEY_HERE" \
     https://your-replit-url.repl.co/api/julius/health
```

⚠️ **SECURITY NOTE:** Query parameter authentication (`?api_key=...`) is supported but **strongly discouraged** for production use. Always use header-based authentication to prevent credentials from appearing in logs, browser history, or proxy caches.

---

## 📚 Available Endpoints

### Health Check
```bash
GET /api/julius/health
```

### Platform Statistics
```bash
GET /api/julius/stats/overview
```
Returns: Total records, genera, species, enrichment counts

### Botanical Glossary (1,763 terms)
```bash
GET /api/julius/glossary
GET /api/julius/glossary?category=morphology&has_etymology=true&per_page=100
```
**Filters:** `category`, `search`, `has_etymology`, `page`, `per_page` (max: 500)

### Dichotomous Keys (90 sources, 27 genera)
```bash
GET /api/julius/keys
GET /api/julius/keys?genus=Cattleya
GET /api/julius/keys?region=California&key_type=species_key
```
**Filters:** `genus`, `region`, `key_type`, `page`, `per_page` (max: 200)

### GBIF Image Metadata (10,534 images)
```bash
GET /api/julius/images/gbif
GET /api/julius/images/gbif?genus=Dendrobium&has_coordinates=true
```
**Filters:** `genus`, `has_coordinates`, `page`, `per_page` (max: 200)

### Enrichment Data
```bash
GET /api/julius/stats/by-genus?limit=50
GET /api/julius/stats/enrichment-status
GET /api/julius/orchids/search?genus=Phalaenopsis&gbif_enriched=true
```

---

## 🐍 Python Example

```python
import requests
import os

# Load API key from environment
API_KEY = os.environ.get('JULIUS_API_KEY')
BASE_URL = "https://your-replit-url.repl.co/api/julius"

# Configure headers
headers = {
    "Authorization": f"Bearer {API_KEY}"
}

# Example 1: Get glossary terms with etymology
response = requests.get(
    f"{BASE_URL}/glossary",
    headers=headers,
    params={
        "has_etymology": "true",
        "category": "morphology",
        "per_page": 50
    }
)
data = response.json()
print(f"Found {data['data']['pagination']['total']} morphology terms")

# Example 2: Find dichotomous keys for California natives
response = requests.get(
    f"{BASE_URL}/keys",
    headers=headers,
    params={
        "region": "California",
        "key_type": "species_key"
    }
)
keys = response.json()['data']['keys']
print(f"California species keys: {len(keys)}")

# Example 3: Get georeferenced GBIF images
response = requests.get(
    f"{BASE_URL}/images/gbif",
    headers=headers,
    params={
        "genus": "Cypripedium",
        "has_coordinates": "true",
        "per_page": 100
    }
)
images = response.json()['data']['images']
for img in images[:5]:
    print(f"{img['scientific_name']}: {img['country']} ({img['latitude']}, {img['longitude']})")
```

---

## 📊 Response Format

All endpoints return JSON with this structure:

```json
{
  "status": "success",
  "data": {
    "items": [...],
    "pagination": {
      "page": 1,
      "per_page": 100,
      "total": 1763,
      "pages": 18,
      "has_next": true,
      "has_prev": false
    }
  }
}
```

**Error responses:**
```json
{
  "error": "Invalid API key",
  "message": "Authentication failed"
}
```

---

## 🎯 Analysis Use Cases

### Coverage Gap Analysis
**Goal:** Find genera in taxonomy database that lack dichotomous keys

```python
# Get all genera with keys
keys_response = requests.get(f"{BASE_URL}/keys", headers=headers, params={"per_page": 200})
genera_with_keys = set(k['genus'] for k in keys_response.json()['data']['keys'])

# Get all taxonomy genera
tax_response = requests.get(f"{BASE_URL}/stats/by-genus", headers=headers, params={"limit": 1000})
all_genera = set(g['genus'] for g in tax_response.json()['genera'])

# Calculate gaps
missing_keys = all_genera - genera_with_keys
print(f"Genera without keys: {len(missing_keys)}")
print(f"Coverage: {len(genera_with_keys)/len(all_genera)*100:.1f}%")
```

### Etymology Completeness
**Goal:** Analyze which glossary categories have best etymology coverage

```python
categories = ['morphology', 'anatomy', 'ecology', 'taxonomy']
for category in categories:
    response = requests.get(
        f"{BASE_URL}/glossary",
        headers=headers,
        params={"category": category, "per_page": 500}
    )
    terms = response.json()['data']['terms']
    with_etymology = sum(1 for t in terms if t['etymology'])
    coverage = (with_etymology / len(terms) * 100) if terms else 0
    print(f"{category}: {coverage:.1f}% ({with_etymology}/{len(terms)})")
```

### Geographic Distribution Analysis
**Goal:** Map GBIF specimen collection hotspots

```python
response = requests.get(
    f"{BASE_URL}/images/gbif",
    headers=headers,
    params={"has_coordinates": "true", "per_page": 200}
)

images = response.json()['data']['images']
countries = {}
for img in images:
    country = img.get('country', 'Unknown')
    countries[country] = countries.get(country, 0) + 1

# Top 10 countries by specimen count
sorted_countries = sorted(countries.items(), key=lambda x: x[1], reverse=True)[:10]
for country, count in sorted_countries:
    print(f"{country}: {count} specimens")
```

---

## 🔍 Key Database Coverage

**27 genera with dichotomous keys:**

### California Natives (Jepson eFlora)
Calypso, Cephalanthera, Corallorhiza, Cypripedium, Epipactis, Goodyera, Listera, Piperia, Platanthera, Spiranthes, Neottia, Malaxis

### Top Cultivated Genera
Cattleya, Dendrobium, Phalaenopsis, Paphiopedilum, Bulbophyllum, Oncidium, Cymbidium, Vanda, Masdevallia, Pleurothallis, Maxillaria, Lycaste, Miltonia, Odontoglossum, Zygopetalum

---

## 📖 Complete API Documentation

For complete endpoint documentation with all parameters and examples, visit:
```
GET /api/julius/docs
```

---

## 💡 Tips for Julius AI

1. **Batch requests** - Use high `per_page` values to minimize API calls
2. **Filter at source** - Use query parameters instead of filtering results client-side
3. **Cache static data** - Glossary and keys change infrequently
4. **Pagination aware** - Check `pagination.has_next` before requesting more pages
5. **Error handling** - Always check HTTP status codes (200, 401, 403, 500)

---

## 🚀 Getting Started Checklist

- ✅ API key configured in environment (`JULIUS_API_KEY`)
- ✅ Test authentication with `/api/julius/health`
- ✅ Review available endpoints at `/api/julius/docs`
- ✅ Start with overview stats: `/api/julius/stats/overview`
- ✅ Explore glossary: `/api/julius/glossary?per_page=10`
- ✅ Check key coverage: `/api/julius/keys?per_page=50`

**Next Steps:** See `docs/julius_briefing_key_database.md` for comprehensive analysis requests and project context.
