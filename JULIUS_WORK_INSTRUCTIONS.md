# Julius AI - Work Instructions

## 🎯 Your Mission
Analyze and enrich The Orchid Continuum database to maximize research value.

## 🔑 API Access
**Base URL**: To be provided by user (deployed on Render.com or Replit)
**API Key**: `JULIUS_API_KEY` (stored in secrets)

**Note**: The actual production URL will be provided separately. Use your deployment URL (e.g., https://your-app.onrender.com or https://your-app.replit.app)

**Authentication**:
```python
headers = {
    'Authorization': f'Bearer {JULIUS_API_KEY}',
    # OR
    'X-API-Key': JULIUS_API_KEY
}
```

## 📊 Available API Endpoints

### 1. Health Check
```
GET /api/julius/health
```

### 2. Platform Statistics
```
GET /api/julius/stats/overview
```
Returns: Total records, genera count, enrichment status

### 3. Botanical Glossary
```
GET /api/julius/glossary?limit=100&category=morphology
```
Access to 1,763 botanical terms with etymology

### 4. Dichotomous Keys
```
GET /api/julius/keys?genus=Cattleya
```
90 sources covering 27 genera

### 5. GBIF Images
```
GET /api/julius/images/gbif?limit=100&georeferenced=true
```
10,534 specimen images with metadata

### 6. Search Orchids
```
GET /api/julius/orchids/search?genus=Phalaenopsis&limit=50
```

### 7. Taxonomy Data
```
GET /api/julius/taxonomy/list?limit=100
```

## 🔧 Your Tasks

### Task 1: Database Gap Analysis (HIGH PRIORITY)
**Goal**: Identify which orchid records need enrichment

**Steps**:
1. Query `/api/julius/stats/overview` to get baseline
2. Query `/api/julius/orchids/search` with pagination to analyze all records
3. Identify records missing:
   - GBIF occurrence data
   - EOL trait data
   - Tropicos herbarium specimens
   - Geographic coordinates
   - Growth habit information
4. Create prioritized enrichment list

**Output**: CSV or JSON file with orchid IDs needing enrichment

### Task 2: GBIF Image Quality Assessment
**Goal**: Analyze the 10,534 GBIF images for research usability

**Steps**:
1. Query `/api/julius/images/gbif?limit=10534`
2. Analyze:
   - How many have GPS coordinates?
   - License distribution (CC0, CC-BY, etc.)
   - Image quality indicators
   - Species coverage gaps
3. Identify best images for herbarium quiz system

**Output**: Report on image dataset quality + recommended improvements

### Task 3: Taxonomy Completeness Check
**Goal**: Find missing taxonomy data

**Steps**:
1. Query `/api/julius/taxonomy/list` (all records)
2. Check for missing:
   - Family/Subfamily classifications
   - Synonym mappings
   - Author citations
   - Geographic distributions
3. Cross-reference with authoritative sources (WCSP, POWO)

**Output**: List of taxonomy records to update

### Task 4: Botanical Glossary Usage Analysis
**Goal**: Identify most important terms for education

**Steps**:
1. Query `/api/julius/glossary` (all 1,763 terms)
2. Analyze:
   - Which categories are most complete?
   - Which terms need better definitions?
   - Etymology coverage gaps
3. Recommend priority terms for interactive features

**Output**: Educational content recommendations

### Task 5: Dichotomous Key Coverage Analysis
**Goal**: Assess identification key completeness

**Steps**:
1. Query `/api/julius/keys` for all 90 sources
2. Analyze:
   - Geographic coverage (Flora treatments)
   - Genus coverage (27 genera - which are missing?)
   - Key quality (species-level vs genus-level)
3. Identify priority genera for new key addition

**Output**: Key acquisition priorities

## 📈 Expected Outputs

For each task, provide:
1. **Summary Stats**: Key metrics in simple format
2. **Data Quality Report**: Issues found, recommendations
3. **Action Items**: Specific database updates needed
4. **Prioritization**: What should be done first

## 💾 How to Submit Results

Since the Flask server isn't running, submit results via:

**Option 1**: Direct database updates (if you have PostgreSQL access)
**Option 2**: Generate SQL scripts for Replit Agent to run
**Option 3**: Create JSON/CSV files for manual import

## ⚠️ Important Notes

1. **Rate Limiting**: API calls are logged but no hard limits currently
2. **Data Freshness**: Database has 10,534+ records as of Oct 30, 2025
3. **Authentication**: All queries logged with credential scrubbing for security
4. **Pagination**: Use `?limit=100&offset=0` for large datasets

## 🚀 Start Here

**Immediate Priority**: Task 1 (Database Gap Analysis)

Run this first:
```python
import requests

# Get overview
response = requests.get(
    'https://your-domain.com/api/julius/stats/overview',
    headers={'X-API-Key': 'your-key-here'}
)
stats = response.json()
print(f"Total orchids: {stats['orchid_records']}")
print(f"Enrichment needed: {stats['enrichment_metrics']}")
```

Then proceed with full gap analysis across all records.

## 📊 Success Metrics

- [ ] Complete gap analysis of all orchid records
- [ ] Quality assessment of GBIF image dataset  
- [ ] Taxonomy completeness report
- [ ] Educational content recommendations
- [ ] Actionable enrichment priorities list

---

**Questions?** Document them and Replit Agent will clarify.
**Ready to start?** Begin with Task 1 - Database Gap Analysis!
