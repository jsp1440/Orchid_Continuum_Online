# Julius AI API Documentation

**Base URL**: `https://your-replit-domain.repl.co/api/julius`  
**Authentication**: Bearer token using `JULIUS_API_KEY`

---

## Authentication

All endpoints require authentication via Bearer token in the Authorization header:

```bash
Authorization: Bearer <JULIUS_API_KEY>
```

**Example with curl (Recommended - Bearer Token):**
```bash
curl -H "Authorization: Bearer julius_orchid_your_key_here" \
     https://your-domain.repl.co/api/julius/health
```

**Example with curl (X-API-Key Header):**
```bash
curl -H "X-API-Key: julius_orchid_your_key_here" \
     https://your-domain.repl.co/api/julius/health
```

⚠️ **Security Warning:** Do not use query parameter authentication (`?api_key=...`) in production. Query parameters are logged and may expose credentials.

**Example with Python:**
```python
import requests

API_KEY = "julius_orchid_your_key_here"
BASE_URL = "https://your-domain.repl.co/api/julius"

headers = {"Authorization": f"Bearer {API_KEY}"}
response = requests.get(f"{BASE_URL}/glossary", headers=headers)
data = response.json()
```

---

## Endpoints

### 1. Health Check

**GET** `/ping`

Test API connectivity and authentication.

**Response:**
```json
{
  "status": "success",
  "message": "Julius API is operational",
  "version": "1.0"
}
```

---

### 2. Glossary Terms

**GET** `/glossary`

Retrieve botanical glossary terms with pagination and filtering.

**Query Parameters:**
- `page` (int, default: 1) - Page number
- `per_page` (int, default: 100, max: 500) - Items per page
- `category` (string) - Filter by category
- `search` (string) - Search in term or definition
- `has_etymology` (boolean) - Filter terms with etymology

**Example Request:**
```bash
GET /api/julius/glossary?category=morphology&has_etymology=true&page=1&per_page=50
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "terms": [
      {
        "id": 1,
        "term": "labellum",
        "definition": "Modified petal forming the lip of an orchid flower",
        "etymology": "Latin: labellum (little lip)",
        "pronunciation": "lah-BEL-um",
        "category": "morphology",
        "related_terms": ["lip", "petal", "perianth"]
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 50,
      "total": 1763,
      "pages": 36,
      "has_next": true,
      "has_prev": false
    }
  }
}
```

---

### 3. Single Glossary Term

**GET** `/glossary/<term_id>`

Get a single glossary term by ID.

**Response:**
```json
{
  "status": "success",
  "data": {
    "id": 1,
    "term": "labellum",
    "definition": "Modified petal forming the lip of an orchid flower",
    "etymology": "Latin: labellum (little lip)",
    "pronunciation": "lah-BEL-um",
    "category": "morphology",
    "related_terms": ["lip", "petal"],
    "view_count": 142
  }
}
```

---

### 4. Dichotomous Keys

**GET** `/keys`

Access dichotomous key sources for species identification.

**Query Parameters:**
- `genus` (string) - Filter by genus name
- `region` (string) - Filter by region (e.g., 'California', 'China')
- `key_type` (string) - Filter by type: `species_key`, `flora_treatment`, `dichotomous_key`
- `page` (int, default: 1)
- `per_page` (int, default: 50, max: 200)

**Example Request:**
```bash
GET /api/julius/keys?genus=Cattleya&key_type=species_key
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "keys": [
      {
        "id": 1,
        "genus": "Cattleya",
        "species": null,
        "source": "Flora do Brasil (Reflora)",
        "url": "https://floradobrasil.jbrj.gov.br/...",
        "type": "species_key",
        "morphological_characters": [],
        "key_text": "Widely cultivated genus; reference key from available regional floras.",
        "metadata": {
          "region": "Cultivated / Global",
          "scope": "Species-level or regional key",
          "tags": "cultivated, epiphytic",
          "geo_tags": "Neotropics, South America"
        }
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 50,
      "total": 1,
      "pages": 1
    }
  }
}
```

---

### 5. Taxonomy Data

**GET** `/taxonomy`

Access orchid taxonomy (746 genera).

**Query Parameters:**
- `genus` (string) - Filter by genus
- `search` (string) - Search scientific or common names
- `page` (int, default: 1)
- `per_page` (int, default: 100, max: 500)

**Example Request:**
```bash
GET /api/julius/taxonomy?genus=Phalaenopsis&page=1
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "taxa": [
      {
        "id": 1,
        "scientific_name": "Phalaenopsis amabilis",
        "genus": "Phalaenopsis",
        "species": "amabilis",
        "subspecies": null,
        "variety": null,
        "author": "(L.) Blume",
        "common_names": "Moon Orchid, Moth Orchid",
        "family": "Orchidaceae",
        "subfamily": "Epidendroideae",
        "tribe": "Vandeae",
        "subtribe": "Aeridinae"
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 100,
      "total": 60,
      "pages": 1
    }
  }
}
```

---

### 6. GBIF Images

**GET** `/images`

Access GBIF orchid specimen images (10,534 images).

**Query Parameters:**
- `genus` (string) - Filter by genus
- `has_coordinates` (boolean) - Filter georeferenced images
- `page` (int, default: 1)
- `per_page` (int, default: 50, max: 200)

**Example Request:**
```bash
GET /api/julius/images?genus=Dendrobium&has_coordinates=true&page=1
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "images": [
      {
        "id": 1,
        "gbif_id": "1234567890",
        "image_url": "https://api.gbif.org/v1/image/...",
        "scientific_name": "Dendrobium nobile",
        "latitude": 27.7172,
        "longitude": 85.3240,
        "country": "Nepal",
        "locality": "Kathmandu Valley",
        "recorded_by": "J. Smith",
        "collection_date": "2023-05-15",
        "genus": "Dendrobium",
        "species": "nobile"
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 50,
      "total": 245,
      "pages": 5
    }
  }
}
```

---

### 7. Platform Statistics

**GET** `/stats`

Get comprehensive platform statistics.

**Response:**
```json
{
  "status": "success",
  "data": {
    "glossary": {
      "total_terms": 1763,
      "with_etymology": 1725,
      "etymology_coverage": 97.8
    },
    "keys": {
      "total_sources": 90,
      "genera_covered": 27,
      "species_keys": 23,
      "flora_treatments": 11
    },
    "taxonomy": {
      "total_taxa": 3542,
      "genera": 746,
      "families": 1
    },
    "images": {
      "total": 10534,
      "georeferenced": 8421,
      "coverage": 79.9
    }
  }
}
```

---

## Error Responses

### 401 Unauthorized
```json
{
  "error": "Missing Authorization header",
  "message": "Include Authorization: Bearer <JULIUS_API_KEY>"
}
```

### 403 Forbidden
```json
{
  "error": "Invalid API key",
  "message": "Authentication failed"
}
```

### 404 Not Found
```json
{
  "error": "Resource not found",
  "message": "The requested resource does not exist"
}
```

---

## Rate Limits

**Current:** No rate limits enforced  
**Recommended usage:** Batch requests when possible, use pagination efficiently

---

## Best Practices

1. **Use pagination** - Don't request all records at once
2. **Cache responses** - Stats endpoint data changes infrequently
3. **Filter at source** - Use query parameters instead of client-side filtering
4. **Handle errors gracefully** - Check HTTP status codes

---

## Analysis Use Cases

### Coverage Gap Analysis
```python
# Get all genera with keys
response = requests.get(
    f"{BASE_URL}/keys",
    headers=headers,
    params={"per_page": 500}
)
genera_with_keys = set(k['genus'] for k in response.json()['data']['keys'])

# Get all taxonomy genera
response = requests.get(
    f"{BASE_URL}/taxonomy",
    headers=headers,
    params={"per_page": 500}
)
all_genera = set(t['genus'] for t in response.json()['data']['taxa'])

# Find gaps
missing_keys = all_genera - genera_with_keys
print(f"Genera missing keys: {len(missing_keys)}")
```

### Etymology Coverage Analysis
```python
# Get all terms with etymology
all_terms = []
page = 1
while True:
    response = requests.get(
        f"{BASE_URL}/glossary",
        headers=headers,
        params={"page": page, "per_page": 500}
    )
    data = response.json()['data']
    all_terms.extend(data['terms'])
    
    if not data['pagination']['has_next']:
        break
    page += 1

# Analyze
with_etymology = sum(1 for t in all_terms if t['etymology'])
print(f"Etymology coverage: {with_etymology/len(all_terms)*100:.1f}%")
```

---

## Support

**Issues?** Contact via replit.md documented channels  
**API Version:** 1.0  
**Last Updated:** October 29, 2025
