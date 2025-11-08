# Orchid Continuum - Technical Manual
## Developer & System Administrator Guide

Version 2.0 | Last Updated: October 20, 2025

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Technology Stack](#technology-stack)
3. [Database Schema](#database-schema)
4. [API Integrations](#api-integrations)
5. [AI Systems](#ai-systems)
6. [Deployment](#deployment)
7. [Maintenance](#maintenance)
8. [Development Guide](#development-guide)
9. [Security](#security)
10. [Troubleshooting](#troubleshooting)

---

## System Architecture

### Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interface Layer                     │
│  Flask Templates, Bootstrap 5, Feather Icons, JavaScript    │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                   Application Layer                          │
│      Flask Routes, Business Logic, API Handlers             │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                      Data Layer                              │
│   PostgreSQL, SQLAlchemy ORM, Connection Pooling           │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                 External Services Layer                      │
│   GBIF API, EOL API, Tropicos API, OpenAI API, Google      │
└─────────────────────────────────────────────────────────────┘
```

### Design Principles

1. **Modular Architecture**: Separate concerns (routes, models, services)
2. **API-First**: RESTful endpoints for all major functions
3. **Data Integrity**: Atomic transactions, foreign key constraints
4. **Scalability**: Connection pooling, indexed queries, caching-ready
5. **Observability**: Comprehensive logging, error tracking

---

## Technology Stack

### Backend

**Core Framework:**
- **Flask 3.x**: Web application framework
- **Python 3.11**: Programming language
- **SQLAlchemy 2.x**: ORM for database access
- **Gunicorn**: WSGI HTTP server for production

**Database:**
- **PostgreSQL 15+**: Primary database
- **Neon**: Managed Postgres provider
- **psycopg2-binary**: PostgreSQL adapter

**Key Libraries:**
```python
# Data Processing
pandas, numpy, scipy

# Web Scraping
requests, beautifulsoup4, trafilatura

# Image Processing
Pillow, opencv-python, tesseract

# AI/ML
openai, anthropic

# Geospatial
folium, geopandas, geopy

# Authentication
flask-login, werkzeug.security
```

### Frontend

**UI Framework:**
- **Bootstrap 5.3**: Responsive design
- **Feather Icons**: Icon library
- **Custom CSS**: Dark theme with orchid styling

**JavaScript Libraries:**
- **Chart.js**: Data visualization
- **D3.js**: Complex visualizations
- **Leaflet/Folium**: Interactive maps

**Build Tools:**
- **Vite**: Module bundler (for widgets)
- **PostCSS**: CSS processing
- **Tailwind CSS**: Utility-first CSS (for widgets)

### Infrastructure

**Hosting:**
- **Replit**: Development environment
- **Render**: Production deployment
- **GitHub**: Version control

**CDN:**
- **Cloudflare R2/S3**: Widget distribution
- **GitHub Actions**: CI/CD pipelines

**Monitoring:**
- **Custom logging**: Application logs
- **Database logs**: Query performance
- **Error tracking**: Custom system

---

## Database Schema

### Core Tables

#### orchid_taxonomy
**Purpose**: Master taxonomy reference table

```sql
CREATE TABLE orchid_taxonomy (
    id SERIAL PRIMARY KEY,
    scientific_name VARCHAR(200) UNIQUE NOT NULL,
    genus VARCHAR(100) NOT NULL,
    species VARCHAR(100) NOT NULL,
    author VARCHAR(200),
    synonyms TEXT,
    common_names TEXT,
    
    -- Taxonomic Hierarchy
    kingdom VARCHAR(120),
    phylum VARCHAR(120),
    class VARCHAR(120),
    order VARCHAR(120),
    family VARCHAR(120),
    subspecies VARCHAR(120),
    variety VARCHAR(120),
    taxon_rank VARCHAR(50),
    taxonomic_status VARCHAR(50),
    
    -- External Database References
    gbif_taxon_key BIGINT,
    gbif_key INTEGER,
    gbif_canonical_name VARCHAR(200),
    gbif_taxonomic_status VARCHAR(50),
    gbif_occurrence_count INTEGER DEFAULT 0,
    gbif_last_synced_at TIMESTAMP,
    gbif_last_updated TIMESTAMP,
    
    eol_page_id VARCHAR(32),
    eol_last_synced_at TIMESTAMP,
    
    inaturalist_taxon_id INTEGER,
    inaturalist_common_name VARCHAR(200),
    inaturalist_observations_count INTEGER DEFAULT 0,
    inaturalist_last_updated TIMESTAMP,
    
    -- Flexible External Data
    external_ids JSONB,  -- Stores Tropicos, POWO, IPNI, etc.
    external_data_sources JSON,
    external_synonyms JSON,
    external_vernacular_names JSON,
    vernacular_names JSON,
    synonyms_json JSON,
    
    -- Audit Fields
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_taxonomic_update TIMESTAMP
);

CREATE INDEX idx_taxonomy_scientific_name ON orchid_taxonomy(scientific_name);
CREATE INDEX idx_taxonomy_genus ON orchid_taxonomy(genus);
CREATE INDEX idx_taxonomy_gbif_key ON orchid_taxonomy(gbif_taxon_key);
CREATE INDEX idx_taxonomy_eol_page ON orchid_taxonomy(eol_page_id);
```

#### orchid_images
**Purpose**: Multi-source image repository

```sql
CREATE TABLE orchid_images (
    id SERIAL PRIMARY KEY,
    taxonomy_id INTEGER REFERENCES orchid_taxonomy(id),
    
    -- Image Data
    image_url TEXT NOT NULL,
    image_source VARCHAR,
    image_license TEXT,
    image_rights_holder TEXT,
    image_description TEXT,
    
    -- Source-Specific Metadata
    gbif_occurrence_key VARCHAR,
    eol_data_object_id VARCHAR,
    tropicos_metadata JSONB,  -- NEW: Tropicos data
    occurrence_metadata JSONB,
    media_metadata JSONB,
    eol_metadata JSONB,
    
    -- Geographic Data
    latitude NUMERIC,
    longitude NUMERIC,
    coordinate_uncertainty NUMERIC,
    country VARCHAR,
    country_code VARCHAR,
    state_province VARCHAR,
    locality TEXT,
    continent VARCHAR,
    elevation_meters INTEGER,
    
    -- Observation Data
    observation_date TIMESTAMP,
    year_observed INTEGER,
    month_observed INTEGER,
    observer_name VARCHAR,
    
    -- Collection Data
    institution_code VARCHAR,
    individual_count INTEGER,
    sex VARCHAR,
    life_stage VARCHAR,
    reproductive_condition VARCHAR,
    iucn_red_list_category VARCHAR,
    
    -- Flags
    wild_specimen BOOLEAN DEFAULT TRUE,
    
    -- Audit
    downloaded_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_images_taxonomy ON orchid_images(taxonomy_id);
CREATE INDEX idx_images_gbif_key ON orchid_images(gbif_occurrence_key);
CREATE INDEX idx_images_eol_id ON orchid_images(eol_data_object_id);
CREATE INDEX idx_images_country ON orchid_images(country);
CREATE INDEX idx_images_wild ON orchid_images(wild_specimen);
```

#### traitbank_orchid_traits
**Purpose**: Morphological and ecological traits

```sql
CREATE TABLE traitbank_orchid_traits (
    id SERIAL PRIMARY KEY,
    page_id VARCHAR(50) NOT NULL,
    scientific_name VARCHAR(200),
    taxonomy_id INTEGER REFERENCES orchid_taxonomy(id),
    
    -- Trait Data
    trait_name VARCHAR(500),
    trait_value TEXT,
    trait_units VARCHAR(100),
    trait_measurement VARCHAR(200),
    predicate VARCHAR(500),
    object_page_id VARCHAR(50),
    
    -- Source Information
    source_citation TEXT,
    source_url TEXT,
    resource_id VARCHAR(100),
    
    -- Metadata
    eol_metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_traits_page_id ON traitbank_orchid_traits(page_id);
CREATE INDEX idx_traits_taxonomy ON traitbank_orchid_traits(taxonomy_id);
CREATE INDEX idx_traits_name ON traitbank_orchid_traits(scientific_name);
```

### Research Tables

#### research_insights
**Purpose**: AI-discovered traits and patterns

```sql
CREATE TABLE research_insights (
    id SERIAL PRIMARY KEY,
    taxonomy_id INTEGER REFERENCES orchid_taxonomy(id),
    insight_type VARCHAR(100),
    insight_text TEXT,
    confidence_score NUMERIC(5,4),
    supporting_data JSONB,
    source_system VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    verified_at TIMESTAMP,
    verified_by VARCHAR(100)
);
```

#### ai_sessions
**Purpose**: AI collaboration session management

```sql
CREATE TABLE ai_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_name VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    max_iterations INTEGER DEFAULT 10,
    iteration_count INTEGER DEFAULT 0,
    time_budget_min INTEGER DEFAULT 60,
    expires_at TIMESTAMP,
    cost_budget_usd NUMERIC(10,2) DEFAULT 20.00,
    cost_used_usd NUMERIC(10,2) DEFAULT 0.00,
    created_by VARCHAR(100),
    notes TEXT,
    started_at TIMESTAMP DEFAULT NOW()
);
```

### Full Schema Documentation

See `COMPREHENSIVE_SCHEMA_ANALYSIS.md` for complete table definitions, indexes, and relationships.

---

## API Integrations

### 1. GBIF (Global Biodiversity Information Facility)

**Base URL**: `https://api.gbif.org/v1/`

**Key Endpoints:**
- `species/match` - Match scientific name to taxon key
- `occurrence/search` - Search for occurrence records
- `occurrence/{key}/media` - Get media for occurrence

**Rate Limits**: None official, recommend 0.3s delay

**Implementation**: `validation/enrich_gbif_stable.py`

**Data Flow:**
1. Match name → Get taxon key
2. Search occurrences → Get occurrence records
3. Filter for images → Download metadata
4. Save to orchid_images table

### 2. EOL (Encyclopedia of Life)

**Base URL**: `https://eol.org/api/`

**Key Endpoints:**
- `search/1.0.json` - Search for species
- `pages/1.0/{id}.json` - Get page with images and data
- `traitbank` - Access trait data

**Rate Limits**: None official, recommend 0.3s delay

**Implementation**: `validation/enrich_eol_images.py`

**Data Flow:**
1. Search name → Get EOL page ID
2. Fetch page data → Get images and traits
3. Parse TraitBank data → Extract traits
4. Save to respective tables

### 3. Tropicos (Missouri Botanical Garden)

**Base URL**: `http://services.tropicos.org/`

**Key Endpoints:**
- `Name/Search` - Search for scientific names
- `Name/{id}` - Get name details
- `Name/{id}/Synonyms` - Get synonyms
- `Name/{id}/AcceptedNames` - Get accepted names
- `Image/Search` - Search for images
- `Name/{id}/Specimens` - Get specimen data

**Rate Limits**: None official, recommend 0.5s delay

**Authentication**: API key in query parameter

**Implementation**: `validation/enrich_tropicos.py`

**Data Flow:**
1. Search name → Get Tropicos name ID
2. Fetch details → Get taxonomic info
3. Get images → Download specimen photos
4. Save to external_ids JSONB field

### 4. OpenAI API

**Base URL**: `https://api.openai.com/v1/`

**Models Used:**
- `gpt-4o` - Vision analysis and identification
- `gpt-4-turbo` - Text processing

**Implementation**: Multiple modules
- `ai_orchid_identification.py`
- `ai_vision_enrichment.py`
- AI-to-AI collaboration system

**Cost Management:**
- Session budgets ($20 default)
- Cost tracking in ai_cost_ledger
- Automatic stops on limit

---

## AI Systems

### 1. Image Analysis & Identification

**Technology**: OpenAI GPT-4o Vision

**Capabilities:**
- Orchid species identification
- Morphological trait extraction
- Flower quality assessment
- Growing condition analysis

**Accuracy:**
- Genus level: 90%+
- Species level: 70-85%
- Trait extraction: 75-90%

**Implementation:**
```python
from openai import OpenAI
client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Identify this orchid..."},
                {"type": "image_url", "image_url": {"url": image_url}}
            ]
        }
    ]
)
```

### 2. AI-to-AI Collaboration

**Agents:**
- **Replit Agent**: Creates research tasks
- **Julius AI**: Executes tasks autonomously

**Safety Controls:**
- Kill switch (instant stop)
- Budget limits ($20 default)
- Iteration limits (10 tasks)
- Time limits (60 min session)
- Atomic database locking

**Database Queue:**
```sql
-- AI task queue
ai_communication table:
- status: pending → in_progress → completed
- Atomic claiming via get_next_task()
- Session tracking via session_id
```

**See**: `ai_collaboration/AI_TO_AI_USER_GUIDE.md`

### 3. Trait Discovery Pipeline

**Process:**
1. EOL TraitBank extraction (78,225 traits extracted)
2. Vision AI analysis of images
3. Cross-correlation with environmental data
4. New trait discovery and documentation

**Status**: Phase 1 complete, Phase 2 ready to deploy

---

## Deployment

### Development Environment (Replit)

**Setup:**
```bash
# Clone repository
git clone <repo_url>

# Environment variables
DATABASE_URL=postgresql://...
OPENAI_API_KEY=sk-...
TROPICOS_API_KEY=...
SESSION_SECRET=...

# Install dependencies
pip install -r requirements.txt

# Run migrations
python app.py  # Auto-creates tables

# Start server
python main.py  # Runs on port 5000
```

### Production Environment (Render)

**Services:**
1. **Web Service**: Flask application
2. **Worker Service**: Background enrichment
3. **PostgreSQL**: Neon database
4. **Redis**: Caching (optional)

**Configuration** (`render.yaml`):
```yaml
services:
  - type: web
    name: orchid-continuum
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn app:app --bind 0.0.0.0:5000
    
  - type: worker
    name: gbif-enrichment-worker
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python validation/enrich_gbif_stable.py
```

**Environment Secrets:**
- Add all API keys via Render dashboard
- Use secret scanning to prevent exposure

**See**: `RENDER_DEPLOYMENT_GUIDE.md`

### CDN Widget Distribution

**Build Process:**
```bash
cd widgets
npm run build
# Outputs to dist/

# Deploy to CDN
aws s3 sync dist/ s3://orchid-widgets/
```

**GitHub Actions** (`.github/workflows/deploy-widgets.yml`):
- Triggered on push to main
- Builds all widget bundles
- Deploys to S3/Cloudflare R2
- Invalidates CDN cache

---

## Maintenance

### Routine Tasks

**Daily:**
- [ ] Monitor enrichment workers
- [ ] Check error logs
- [ ] Verify backup completion

**Weekly:**
- [ ] Review database size
- [ ] Analyze slow queries
- [ ] Update dependencies (security patches)

**Monthly:**
- [ ] Full database backup
- [ ] Performance optimization
- [ ] API quota review

### Database Maintenance

**Vacuum & Analyze:**
```sql
VACUUM ANALYZE orchid_taxonomy;
VACUUM ANALYZE orchid_images;
VACUUM ANALYZE traitbank_orchid_traits;
```

**Index Maintenance:**
```sql
-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
ORDER BY idx_scan ASC;

-- Rebuild bloated indexes
REINDEX TABLE orchid_images;
```

**Query Performance:**
```sql
-- Identify slow queries
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

### Backup Strategy

**Automated Backups:**
- Neon: Daily automatic backups (14-day retention)
- Manual: Export via pg_dump weekly

**Backup Command:**
```bash
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql
```

**Restore:**
```bash
psql $DATABASE_URL < backup_20251020.sql
```

---

## Development Guide

### Project Structure

```
orchid-continuum/
├── app.py                 # Flask app initialization
├── main.py                # Entry point
├── models.py              # SQLAlchemy models (3982 lines!)
├── requirements.txt       # Python dependencies
│
├── templates/             # Jinja2 HTML templates
│   ├── base.html
│   ├── gallery.html
│   └── ...
│
├── static/                # Static assets
│   ├── css/
│   ├── js/
│   └── images/
│
├── validation/            # Data enrichment scripts
│   ├── enrich_gbif_stable.py
│   ├── enrich_eol_images.py
│   ├── enrich_tropicos.py
│   └── ...
│
├── ai_collaboration/      # AI-to-AI system
│   ├── ai_system_admin.py
│   ├── AI_TO_AI_USER_GUIDE.md
│   └── JULIUS_AUTONOMOUS_MODE.txt
│
├── docs/                  # Documentation
│   ├── ORCHID_CONTINUUM_USER_MANUAL.md
│   ├── ORCHID_CONTINUUM_TECHNICAL_MANUAL.md
│   ├── TROPICOS_INTEGRATION_GUIDE.md
│   └── ...
│
├── widgets/               # Embeddable widgets (Vite)
│   ├── src/
│   ├── vite.config.js
│   └── package.json
│
└── tests/                 # Test suites
    └── ...
```

### Adding New Features

**1. Create Route:**
```python
# In main.py or new route file
from flask import render_template
from app import app

@app.route('/new-feature')
def new_feature():
    return render_template('new_feature.html')
```

**2. Create Template:**
```html
<!-- templates/new_feature.html -->
{% extends "base.html" %}
{% block content %}
  <h1>New Feature</h1>
{% endblock %}
```

**3. Add Database Model (if needed):**
```python
# In models.py
class NewFeature(db.Model):
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(200))
```

**4. Run Migration:**
```python
# In Flask shell or script
from app import db
db.create_all()  # Creates new tables
```

### Adding API Integrations

**Template** (`validation/enrich_newapi.py`):
```python
#!/usr/bin/env python3
import requests
import time
import os
from contextlib import contextmanager

# Connection pool
def get_connection_pool():
    ...

# Get next species to process
def get_next_species():
    ...

# API calls with retry logic
def fetch_from_api(name, api_key):
    try:
        r = requests.get(url, params={...}, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.error(f"API error: {e}")
        return 'ERROR'

# Save to database
def save_data(tax_id, data):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT ...")
            conn.commit()

# Main loop
def main():
    while True:
        species = get_next_species()
        if not species:
            break
        # Process species...
```

### Coding Standards

**Python:**
- PEP 8 style guide
- Type hints encouraged
- Docstrings for all functions
- Error handling with try/except

**SQL:**
- Parameterized queries (prevent injection)
- Transactions for multi-step operations
- Indexes on frequently queried columns

**JavaScript:**
- ES6+ syntax
- Async/await for API calls
- Error boundaries in React-like components

---

## Security

### Authentication

**Current System:**
- Flask-Login for session management
- Password hashing with Werkzeug
- Admin-only areas protected

**Future Enhancements:**
- OAuth integration (Google, Facebook)
- Two-factor authentication
- JWT for API access

### API Keys

**Storage:**
- Environment variables (Replit Secrets)
- Never committed to repository
- Rotated periodically

**Usage:**
```python
# Correct
api_key = os.environ.get('API_KEY')

# NEVER do this
api_key = 'hardcoded-key-abc123'  # ❌ WRONG
```

### Database Security

**Practices:**
- Parameterized queries (SQL injection prevention)
- Least-privilege database roles
- SSL/TLS connections required
- Regular security audits

**SQL Injection Prevention:**
```python
# Correct
cur.execute("SELECT * FROM orchids WHERE name = %s", (user_input,))

# WRONG
cur.execute(f"SELECT * FROM orchids WHERE name = '{user_input}'")  # ❌
```

### Secrets Management

**Replit Secrets:**
- Encrypted at rest
- Access via `os.environ`
- Never logged or printed

**Rotation Schedule:**
- API keys: Every 6 months
- Database passwords: Every 3 months
- Session secrets: Every month

---

## Troubleshooting

### Common Issues

**Database Connection Errors:**
```
Error: psycopg2.OperationalError: could not connect to server
```
**Solution:**
- Check DATABASE_URL is correct
- Verify Neon database is running
- Check connection pool isn't exhausted

**API Rate Limiting:**
```
Error: 429 Too Many Requests
```
**Solution:**
- Increase delay between requests
- Implement exponential backoff
- Contact API provider for higher limits

**Memory Issues:**
```
Error: MemoryError
```
**Solution:**
- Process data in smaller batches
- Use pagination for large queries
- Increase worker memory allocation

**Image Loading Failures:**
```
Error: 404 Not Found (image URL)
```
**Solution:**
- Check image URL is valid
- Verify source website is accessible
- Update broken URLs via admin panel

### Debugging Tools

**Logging:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.debug("Debug message")
```

**Database Queries:**
```python
# Enable SQLAlchemy logging
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

**Flask Debug Mode:**
```python
# Only in development!
app.run(debug=True)
```

---

## Performance Optimization

### Database Optimization

**Indexes:**
```sql
-- Add indexes for frequently queried columns
CREATE INDEX idx_taxonomy_genus ON orchid_taxonomy(genus);
CREATE INDEX idx_images_country ON orchid_images(country);
```

**Query Optimization:**
```sql
-- Use EXPLAIN to analyze queries
EXPLAIN ANALYZE 
SELECT * FROM orchid_images 
WHERE country = 'Thailand' 
LIMIT 100;
```

**Connection Pooling:**
```python
from psycopg2.pool import SimpleConnectionPool
pool = SimpleConnectionPool(minconn=1, maxconn=5, dsn=DATABASE_URL)
```

### Caching Strategy

**Application-Level:**
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_orchid_by_id(orchid_id):
    return db.query(OrchidTaxonomy).get(orchid_id)
```

**Database-Level:**
- Materialized views for complex queries
- Redis for session storage (future)

### Image Optimization

**Lazy Loading:**
```html
<img src="placeholder.jpg" data-src="actual-image.jpg" loading="lazy">
```

**CDN Distribution:**
- Host images on CDN
- Optimize image sizes
- Use WebP format

---

## Monitoring & Logging

### Application Logs

**Location:** `/tmp/logs/`

**Log Files:**
- `gbif_stable.log` - GBIF enrichment
- `tropicos.log` - Tropicos enrichment
- `ai_system.log` - AI collaboration

**Log Format:**
```
2025-10-20 12:00:00 [INFO] Processing Phalaenopsis amabilis
2025-10-20 12:00:01 [DEBUG] GBIF API response: 200 OK
2025-10-20 12:00:02 [ERROR] Failed to save image: Duplicate key
```

### Database Logs

**Query Log:**
```sql
-- View recent queries
SELECT query, calls, mean_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC;
```

**Error Log:**
Check Neon dashboard for connection errors and slow queries.

### Metrics to Track

**Application:**
- Requests per minute
- Error rate
- Response time

**Database:**
- Query performance
- Connection count
- Table sizes

**Enrichment:**
- Images collected per day
- API success rate
- Processing speed

---

## Appendix

### Glossary

- **ORM**: Object-Relational Mapping (SQLAlchemy)
- **WSGI**: Web Server Gateway Interface (Gunicorn)
- **JSONB**: Binary JSON (PostgreSQL data type)
- **CDN**: Content Delivery Network
- **CI/CD**: Continuous Integration/Continuous Deployment

### Useful Commands

**Database:**
```bash
# Backup
pg_dump $DATABASE_URL > backup.sql

# Restore
psql $DATABASE_URL < backup.sql

# Connect
psql $DATABASE_URL
```

**Python Environment:**
```bash
# Install dependencies
pip install -r requirements.txt

# Freeze dependencies
pip freeze > requirements.txt

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows
```

**Git:**
```bash
# Commit changes
git add .
git commit -m "Description"
git push origin main

# Create branch
git checkout -b feature-name
```

---

## Support

### Documentation
- User Manual: `ORCHID_CONTINUUM_USER_MANUAL.md`
- API Guides: `docs/` directory
- Widget Docs: `widgets/README.md`

### Contact
- Technical issues: Bug report system
- Development questions: GitHub issues
- Security concerns: Private disclosure

---

**Last Updated**: October 20, 2025
**Platform Version**: 2.0
**Database Schema Version**: 15

*For user documentation, see: `ORCHID_CONTINUUM_USER_MANUAL.md`*
