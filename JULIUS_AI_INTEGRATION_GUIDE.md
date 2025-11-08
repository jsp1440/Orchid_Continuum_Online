# Julius AI Integration Guide
## Connecting Julius AI to Orchid Continuum Data

This guide provides **two methods** to connect Julius AI (data analyst) to your Orchid Continuum orchid research platform.

---

## 📊 Available Data

Your platform contains:
- **5,915+ orchid records** with comprehensive metadata
- **645+ genera** with taxonomic classification
- **GBIF enrichment data** (occurrence, habitat, distribution)
- **EOL phenotypic traits** (descriptions, characteristics)
- Image URLs, bloom times, water/light requirements
- Research attribution and citations

---

## Method 1: Direct PostgreSQL Connection ⭐ (Recommended)

Julius AI has built-in PostgreSQL support for direct database queries.

### PostgreSQL Credentials

```
Host: ep-snowy-firefly-afvebui7.c-2.us-west-2.aws.neon.tech
Port: 5432
Database: neondb
Username: neondb_owner
Password: [Check your DATABASE_URL environment variable]
SSL Mode: require
```

### Full Connection String
```
postgresql://neondb_owner:npg_feOt1Ek0KLrF@ep-snowy-firefly-afvebui7.c-2.us-west-2.aws.neon.tech/neondb?sslmode=require
```

### Setup Steps in Julius AI

1. **Go to Julius AI** → **Data Connectors**
2. Click **"Create new Data Connector"** → Select **PostgreSQL**
3. **Fill in connection details:**
   - Host: `ep-snowy-firefly-afvebui7.c-2.us-west-2.aws.neon.tech`
   - Port: `5432`
   - Database: `neondb`
   - Username: `neondb_owner`
   - Password: `npg_feOt1Ek0KLrF`
   - SSL: `Enable` (required)

4. **Test connection** and save

### Example Queries in Julius

Once connected, you can ask Julius:

```
"Show me the top 10 orchid genera by number of records"
"Create a chart of orchid records with GBIF enrichment vs without"
"What percentage of orchids have habitat information?"
"Which genera have the best image coverage?"
"Show me enrichment success rates by data source (GBIF vs EOL)"
"Create a visualization of bloom time distribution across genera"
```

### Key Database Tables

- **`orchid_record`** - Main orchid data with images, habitat, bloom times
- **`orchid_taxonomy`** - Taxonomic classification and relationships
- **`orchid_parentage`** - Hybrid parentage and breeding data

---

## Method 2: Custom API Endpoint 🔐 (Maximum Control)

A secure RESTful API specifically designed for Julius AI integration.

### API Base URL
```
https://your-domain.replit.app/api/julius
```

### Authentication

The API uses API key authentication. Get your key from:

**Environment Variable:**
```bash
echo $JULIUS_API_KEY
```

**Or retrieve from admin dashboard:**
```
Visit: https://your-domain.replit.app/admin
Look for: "Julius AI Integration" section
```

### Authentication Methods

**Option 1: Header (Recommended)**
```bash
curl -H "X-API-Key: your_api_key" https://your-domain.replit.app/api/julius/stats/overview
```

**Option 2: Query Parameter**
```bash
curl "https://your-domain.replit.app/api/julius/stats/overview?api_key=your_api_key"
```

### Setup in Julius AI

1. **Go to Julius** → **Account** → **Secrets** (or Keys tab)
2. **Add new secret:**
   - Key name: `ORCHID_API_KEY`
   - Value: [Your Julius API key from above]
3. **In chat, tell Julius:**
   ```
   "Use my ORCHID_API_KEY secret to access https://your-domain.replit.app/api/julius/stats/overview"
   ```

### Available API Endpoints

#### 1. Health Check
```
GET /api/julius/health
```
Response:
```json
{
  "status": "healthy",
  "service": "Orchid Continuum Julius AI API",
  "version": "1.0.0"
}
```

#### 2. Overview Statistics
```
GET /api/julius/stats/overview
```
Response:
```json
{
  "total_records": 5915,
  "total_genera": 645,
  "total_species": 4821,
  "records_with_images": 3075,
  "image_coverage_percent": 52.0,
  "records_with_habitat": 1479,
  "habitat_coverage_percent": 25.0,
  "enrichment_stats": {
    "gbif_percent": 35.2,
    "eol_percent": 18.7
  }
}
```

#### 3. Statistics by Genus
```
GET /api/julius/stats/by-genus?limit=20
```
Returns top genera with record counts, species counts, and coverage metrics.

#### 4. Enrichment Status Breakdown
```
GET /api/julius/stats/enrichment-status
```
Shows distribution of enrichment sources (GBIF, EOL, both, neither).

#### 5. Search Orchids
```
GET /api/julius/orchids/search?genus=Phalaenopsis&has_image=true&page=1&per_page=50
```

**Query Parameters:**
- `genus` - Filter by genus name (partial match)
- `species` - Filter by species name (partial match)
- `has_image` - Filter by image presence (true/false)
- `gbif_enriched` - Filter by GBIF enrichment (true/false)
- `eol_enriched` - Filter by EOL enrichment (true/false)
- `page` - Page number (default: 1)
- `per_page` - Results per page (max: 500)

#### 6. Get Orchid Details
```
GET /api/julius/orchids/{id}
```
Returns complete details for a specific orchid.

#### 7. List Taxonomy
```
GET /api/julius/taxonomy/list?limit=100
```
Returns taxonomic classification data.

#### 8. API Documentation
```
GET /api/julius/docs
```
Returns full API documentation (no authentication required).

### Example Julius Queries with API

Once you've added the API key to Julius secrets:

```
"Fetch overview statistics from the Orchid API using my ORCHID_API_KEY"

"Get the top 20 genera from /api/julius/stats/by-genus and create a bar chart"

"Search for Phalaenopsis orchids with images using the Orchid API"

"Show me enrichment status breakdown and visualize it as a pie chart"
```

---

## Comparison: PostgreSQL vs API

| Feature | PostgreSQL Connection | Custom API |
|---------|---------------------|------------|
| **Setup Complexity** | Medium | Easy |
| **Data Access** | Full database access | Curated endpoints only |
| **Flexibility** | Unlimited SQL queries | Pre-defined queries |
| **Performance** | Direct database queries | Optimized API responses |
| **Security** | Read-only credentials | API key authentication |
| **Use Case** | Advanced analysis, custom queries | Quick stats, dashboards |

---

## Recommended Workflow

1. **Start with API** - Test Julius integration with simple API endpoints
2. **Explore with PostgreSQL** - Once comfortable, use direct database access for complex analysis
3. **Combine Both** - Use API for quick stats, PostgreSQL for deep dives

---

## Security Notes

- **PostgreSQL**: Use read-only credentials to prevent accidental modifications
- **API**: Rotate API keys regularly for security
- **Julius**: Your data stays private and is never used to train AI
- **Compliance**: SOC 2 Type II certified, GDPR compliant

---

## Example Analysis Projects

### 1. Enrichment Success Analysis
```sql
-- In Julius with PostgreSQL
SELECT 
  gbif_enriched,
  eol_enriched,
  COUNT(*) as count,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
FROM orchid_record
GROUP BY gbif_enriched, eol_enriched
ORDER BY count DESC;
```

### 2. Image Coverage by Genus
```python
# In Julius with API
response = requests.get(
  'https://your-domain.replit.app/api/julius/stats/by-genus?limit=30',
  headers={'X-API-Key': ORCHID_API_KEY}
)
data = response.json()
# Julius will auto-generate visualizations
```

### 3. Habitat Data Quality
```
Ask Julius: "What percentage of orchids have complete habitat information? 
Show me the breakdown by enrichment source."
```

---

## Troubleshooting

### PostgreSQL Connection Issues
- **SSL Error**: Ensure SSL mode is set to "require"
- **Timeout**: Check firewall settings and network connectivity
- **Authentication**: Verify credentials match environment variables

### API Issues
- **401 Unauthorized**: API key missing - add to headers or query params
- **403 Forbidden**: Invalid API key - verify key is correct
- **404 Not Found**: Check endpoint URL and method
- **Rate Limiting**: Space out requests if hitting limits

### Julius Integration
- **API Key Not Working**: Re-save in Julius secrets
- **Connection Timeout**: Check API endpoint is accessible
- **Query Errors**: Verify SQL syntax for PostgreSQL connection

---

## Support

For issues with:
- **Orchid Continuum API**: Check server logs and /api/julius/docs
- **Julius AI**: Visit https://julius.ai/docs or [email protected]
- **PostgreSQL**: Review Neon database dashboard

---

## Next Steps

1. ✅ Choose connection method (PostgreSQL or API)
2. ✅ Set up credentials in Julius AI
3. ✅ Test connection with simple query
4. ✅ Explore data with natural language questions
5. ✅ Build automated reports and visualizations

**Happy analyzing! 🌸📊**
