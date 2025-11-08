# Julius AI - Connection Guide

## 🚀 How to Connect to The Orchid Continuum API

Julius, here's everything you need to start analyzing orchid data!

---

## 🔐 Your Credentials

**API Base URL:**
```
https://eac3af89-cc13-48d4-8cc4-57994ad485a4-00-186tms1b1oiaa.spock.replit.dev/api/julius
```

**API Key:**
```
cdfgutre345ko98bhgfdxccvAwlkmnmkgeswdfbkoplhgb
```

**Authentication Method:**
Use the Bearer token in the Authorization header:
```python
headers = {"Authorization": "Bearer cdfgutre345ko98bhgfdxccvAwlkmnmkgeswdfbkoplhgb"}
```

---

## 📊 Quick Start Code

Copy and run this Python code to test the connection:

```python
import requests

# Configuration
BASE_URL = "https://eac3af89-cc13-48d4-8cc4-57994ad485a4-00-186tms1b1oiaa.spock.replit.dev/api/julius"
API_KEY = "cdfgutre345ko98bhgfdxccvAwlkmnmkgeswdfbkoplhgb"
headers = {"Authorization": f"Bearer {API_KEY}"}

# Test 1: Health Check
print("🔍 Testing API connection...")
response = requests.get(f"{BASE_URL}/health", headers=headers)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}\n")

# Test 2: Get Platform Stats
print("📊 Getting platform statistics...")
response = requests.get(f"{BASE_URL}/stats/overview", headers=headers)
stats = response.json()
print(f"Total records: {stats.get('total_records', 'N/A')}")
print(f"Total genera: {stats.get('total_genera', 'N/A')}\n")

# Test 3: Get Glossary Sample
print("📚 Getting glossary terms...")
response = requests.get(
    f"{BASE_URL}/glossary",
    headers=headers,
    params={"per_page": 5, "has_etymology": "true"}
)
glossary = response.json()
print(f"Found {len(glossary['data']['terms'])} terms")
for term in glossary['data']['terms']:
    print(f"  - {term['term']}: {term['definition'][:60]}...")

print("\n✅ Connection successful!")
```

---

## 🎯 Available Endpoints

### 1. Health Check
```python
GET /health
```
Returns: API status

### 2. Platform Statistics
```python
GET /stats/overview
```
Returns: Total records, genera, species, enrichment stats

### 3. Glossary Terms (1,763 terms)
```python
GET /glossary?per_page=100&has_etymology=true&category=morphology
```
Parameters:
- `per_page` (max: 500)
- `has_etymology` (true/false)
- `category` (morphology, anatomy, ecology, etc.)
- `search` (search text)
- `page` (page number)

### 4. Dichotomous Keys (90 sources, 27 genera)
```python
GET /keys?genus=Cattleya&key_type=species_key
```
Parameters:
- `genus` (filter by genus)
- `region` (e.g., "California", "China")
- `key_type` (species_key, flora_treatment, dichotomous_key)
- `per_page` (max: 200)
- `page`

### 5. GBIF Images (10,534 specimens)
```python
GET /images/gbif?has_coordinates=true&genus=Dendrobium&per_page=50
```
Parameters:
- `genus` (filter by genus)
- `has_coordinates` (true/false)
- `per_page` (max: 200)
- `page`

### 6. Search Orchid Records
```python
GET /orchids/search?genus=Phalaenopsis&gbif_enriched=true
```

### 7. Taxonomy List
```python
GET /taxonomy/list?limit=100
```

---

## 🔬 Analysis Requests

### Priority 1: Coverage Gap Analysis
**Goal:** Identify which genera have dichotomous keys vs. which don't

```python
# Get all genera with keys
keys_response = requests.get(f"{BASE_URL}/keys", headers=headers, params={"per_page": 200})
genera_with_keys = set(k['genus'] for k in keys_response.json()['data']['keys'])

# Get all genera from stats
stats_response = requests.get(f"{BASE_URL}/stats/by-genus", headers=headers, params={"limit": 1000})
all_genera = set(g['genus'] for g in stats_response.json()['genera'])

# Calculate gaps
missing_keys = all_genera - genera_with_keys
print(f"Genera without keys: {len(missing_keys)} out of {len(all_genera)}")
print(f"Coverage: {len(genera_with_keys)/len(all_genera)*100:.1f}%")
```

### Priority 2: Etymology Pattern Analysis
**Goal:** Which glossary categories have best etymology coverage?

```python
categories = ['morphology', 'anatomy', 'ecology', 'taxonomy', 'horticulture']
for category in categories:
    response = requests.get(
        f"{BASE_URL}/glossary",
        headers=headers,
        params={"category": category, "per_page": 500}
    )
    if response.status_code == 200:
        terms = response.json()['data']['terms']
        with_etymology = sum(1 for t in terms if t.get('etymology'))
        coverage = (with_etymology / len(terms) * 100) if terms else 0
        print(f"{category}: {coverage:.1f}% ({with_etymology}/{len(terms)})")
```

### Priority 3: Geographic Distribution
**Goal:** Map where GBIF specimens were collected

```python
response = requests.get(
    f"{BASE_URL}/images/gbif",
    headers=headers,
    params={"has_coordinates": "true", "per_page": 200}
)
images = response.json()['data']['images']

# Count by country
countries = {}
for img in images:
    country = img.get('country', 'Unknown')
    countries[country] = countries.get(country, 0) + 1

# Top 10 countries
sorted_countries = sorted(countries.items(), key=lambda x: x[1], reverse=True)[:10]
for country, count in sorted_countries:
    print(f"{country}: {count} specimens")
```

---

## ✅ Expected Results

When working correctly, you should see:

**Health Check:**
```json
{
  "status": "healthy",
  "service": "Orchid Continuum Julius AI API",
  "version": "1.0.0"
}
```

**Glossary Response:**
```json
{
  "status": "success",
  "data": {
    "terms": [
      {
        "id": 1,
        "term": "labellum",
        "definition": "Modified petal forming the lip...",
        "etymology": "Latin: labellum (little lip)",
        "pronunciation": "lah-BEL-um",
        "category": "morphology"
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 100,
      "total": 1763,
      "pages": 18
    }
  }
}
```

---

## 🚨 Troubleshooting

**If you get 401 Unauthorized:**
- Check that your Authorization header is correct
- Format: `Authorization: Bearer cdfgutre345ko98bhgfdxccvAwlkmnmkgeswdfbkoplhgb`

**If you get 404 Not Found:**
- Verify the base URL is correct
- Make sure the Replit app is running

**If you get empty results:**
- Check pagination parameters
- Try reducing `per_page` value
- Verify filter parameters are valid

---

## 📚 Full Documentation

For complete API documentation, see:
- `docs/julius_api_quick_start.md` - Quick start guide with Python examples
- `docs/julius_api_documentation.md` - Complete endpoint reference
- `docs/julius_briefing_key_database.md` - Project context and analysis goals

---

## 🎯 Next Steps

1. Run the Quick Start Code above to test connection
2. Verify all endpoints return data
3. Start with Priority 1 analysis (Coverage Gap Analysis)
4. Report findings and recommendations

**Happy analyzing! 🌸**
