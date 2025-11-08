# 🔧 BloomBuilder Trait System - API Documentation

## Base URL
```
http://localhost:5000/bloombuilder/api/traits
```

## Endpoints

### 1. Get Species Traits
**GET** `/species/{species_id}`

Returns all available trait categories and values for toggling.

**Response:**
```json
{
  "species": "Dendrophylax lindenii",
  "trait_categories": {
    "spur_length": [
      {
        "value": "very_long",
        "description": "Extremely long spur (12-15cm)",
        "image_url": "/images/ghost-orchid-spur.jpg",
        "pollinator": "Giant sphinx moth",
        "significance": "Coevolution with moth's long tongue"
      }
    ],
    "flower_color": [...]
  },
  "available_toggles": ["spur_length", "flower_color"]
}
```

---

### 2. Toggle Trait
**POST** `/toggle`

Switch to a specific trait variant and get updated visual.

**Request Body:**
```json
{
  "species_id": 1,
  "trait_category": "spur_length",
  "trait_value": "very_long"
}
```

**Response:**
```json
{
  "trait": {
    "id": 1,
    "species_id": 1,
    "trait_category": "spur_length",
    "trait_value": "very_long"
  },
  "image_url": "/images/ghost-orchid-long-spur.jpg",
  "description": "Extremely long spur adapted for sphinx moth",
  "pollinator_effect": "Attracts giant sphinx moth (Cocytius antaeus)",
  "evolution_note": "Classic example of Darwin's prediction"
}
```

---

### 3. Compare Traits
**GET** `/compare/{species_id}`

Get comparative data for educational visualizations.

**Response:**
```json
{
  "species_id": 1,
  "trait_variations": [
    {
      "variant_name": "Short vs Long Spur",
      "type": "morphology",
      "geographic_distribution": "Long spurs in moth-rich areas",
      "selective_pressure": "Pollinator tongue length drives spur evolution"
    }
  ]
}
```

---

### 4. Pollinator Correlation
**GET** `/pollinator-correlation/{species_id}`

Show how each trait connects to specific pollinators.

**Response:**
```json
{
  "species_id": 1,
  "pollinator_correlations": {
    "Giant sphinx moth": [
      {
        "trait_category": "spur_length",
        "trait_value": "very_long",
        "how_it_helps": "Only moths with 12cm+ tongues can reach nectar"
      },
      {
        "trait_category": "flower_color",
        "trait_value": "white",
        "how_it_helps": "White reflects moonlight for nocturnal pollination"
      }
    ],
    "Bumblebees": [...]
  }
}
```

---

## Data Models

### OrchidTrait
```python
{
  "id": int,
  "species_id": int,
  "trait_category": str,  # spur_length, labellum_shape, flower_color
  "trait_value": str,  # very_long, deep_pouch, orange
  "trait_description": str,
  "image_url": str,
  "pollinator_association": str,
  "evolutionary_significance": str
}
```

### Available Trait Categories
- `spur_length`: short, medium, long, very_long
- `labellum_shape`: flat, pouch, fringed, inflated
- `flower_color`: white, pink, orange, purple, yellow
- `petal_shape`: narrow, broad, fringed
- `column_structure`: simple, complex, hood_like

---

## Integration Example

### JavaScript (Fetch API)
```javascript
// Get all traits for Ghost Orchid (ID: 1)
async function loadSpeciesTraits(speciesId) {
  const response = await fetch(`/bloombuilder/api/traits/species/${speciesId}`);
  const data = await response.json();
  
  // Display trait toggles
  displayTraitToggles(data.trait_categories);
}

// Toggle to specific trait
async function toggleTrait(speciesId, category, value) {
  const response = await fetch('/bloombuilder/api/traits/toggle', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      species_id: speciesId,
      trait_category: category,
      trait_value: value
    })
  });
  
  const data = await response.json();
  
  // Update image and description
  updateDisplay(data);
}
```

### Python (Requests)
```python
import requests

# Get traits
response = requests.get('http://localhost:5000/bloombuilder/api/traits/species/1')
traits = response.json()

# Toggle trait
toggle_data = {
    'species_id': 1,
    'trait_category': 'spur_length',
    'trait_value': 'very_long'
}
response = requests.post(
    'http://localhost:5000/bloombuilder/api/traits/toggle',
    json=toggle_data
)
result = response.json()
```

---

## Error Handling

### 404 - Trait Not Found
```json
{
  "error": "Trait variant not found"
}
```

### 400 - Invalid Request
```json
{
  "error": "Missing required field: trait_category"
}
```

---

## Sample Data

### Ghost Orchid (ID: 1)
- **Spur Length**: very_long (12-15cm)
- **Flower Color**: white
- **Pollinator**: Giant sphinx moth

### Pink Lady's Slipper (ID: 2)
- **Labellum Shape**: deep_pouch
- **Flower Color**: pink_magenta
- **Pollinator**: Bumblebees

### Orange Fringed Orchid (ID: 4)
- **Labellum Shape**: deeply_fringed
- **Spur Length**: long (2-3cm)
- **Flower Color**: flame_orange
- **Pollinator**: Butterflies

---

## Testing the API

### Using cURL
```bash
# Get traits for species 1
curl http://localhost:5000/bloombuilder/api/traits/species/1

# Toggle trait
curl -X POST http://localhost:5000/bloombuilder/api/traits/toggle \
  -H "Content-Type: application/json" \
  -d '{"species_id": 1, "trait_category": "spur_length", "trait_value": "very_long"}'
```

### Using Postman
1. Import collection from `postman_collection.json`
2. Test all endpoints
3. View sample responses

---

## Rate Limiting
- **No rate limits** for local development
- Production: 100 requests/minute per IP

## Authentication
- **None required** for GET endpoints
- POST endpoints may require session authentication (configured in app.py)

---

**Backend ready! Build amazing frontend! 🎨**
