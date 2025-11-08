# Widget Catalog - Part 3: Research & Analysis Tools
**Section 3 of 5**

---

## 31. AI Orchid Identifier
**File:** `templates/widgets/ai_identifier.html`
**Route:** `/widgets/ai-identify/`
**Status:** ✅ Production AI tool (guarded by kill-switch)

**What it does:**
Uses OpenAI Vision API to identify orchid species from uploaded photos with confidence scoring.

**Features:**
- Image upload or camera capture
- AI species identification
- Confidence percentage
- Similar species suggestions
- Expert review flagging (low confidence)
- Identification history

**AI Cost:** ~$0.01-0.03 per image  
**Kill-Switch:** Disabled when `ORCHID_AI_ENABLED=false`  
**Fallback:** Shows manual identification guide when AI disabled

**Deployment:** Research widget
**Database Table:** `ai_identifications` (stores results)

---

## 32. AI Breeder Pro Widget
**File:** `templates/widgets/ai_breeder_pro.html`
**Route:** `/widgets/ai-breeder/`
**Status:** ✅ Hybrid prediction tool

**What it does:**
Predicts potential offspring characteristics when crossing two orchid species using AI analysis of parent traits.

**Features:**
- Parent species selection
- Trait inheritance prediction
- Color/pattern forecasting
- Vigor estimation
- Success probability
- Breeding recommendations

**AI Cost:** ~$0.02 per prediction  
**Kill-Switch:** Guarded by ORCHID_AI_ENABLED

**Deployment:** Advanced research widget
**AI Cost:** Optional AI enhancement

---

## 33. Habitat Suitability Analyzer
**File:** `templates/widgets/habitat_analyzer.html`
**Route:** `/widgets/habitat-analysis/`
**Status:** ✅ Climate matching tool

**What it does:**
Analyzes environmental data to determine which orchid species can thrive in a given location.

**Features:**
- Location input (GPS or manual)
- Climate data integration
- Species suitability scoring
- Growing difficulty ratings
- Microclimate tips
- Seasonal considerations

**External API:** OpenWeather (free tier)
**Deployment:** Grower tool widget
**AI Cost:** FREE

---

## 34. Phenology Calendar Widget
**File:** `templates/widgets/phenology_calendar.html`
**Route:** `/widgets/phenology/`
**Status:** ✅ Bloom time tracker

**What it does:**
Visualizes blooming periods for orchid species by month with geographic variations.

**Features:**
- Month-by-month calendar
- Species bloom windows
- Geographic filtering
- Multiple species overlay
- Peak bloom highlighting
- Planning tool for gardens

**Database Field:** `bloom_season`
**Deployment:** Planning widget
**AI Cost:** FREE

---

## 35. EXIF Data Analyzer
**File:** Component in `templates/widgets/comparison_tool.html`
**Route:** `/widgets/exif-analysis/`
**Status:** ✅ Photography analysis

**What it does:**
Extracts and analyzes EXIF data from orchid photos including GPS, camera settings, and timestamps.

**Features:**
- EXIF extraction
- GPS coordinate mapping
- Camera settings display
- Timestamp analysis
- Copyright detection
- Metadata export

**Python Library:** `exifread`
**Deployment:** Photography widget
**AI Cost:** FREE

---

## 36. Citation Generator Widget
**File:** `templates/widgets/citation_generator.html`
**Route:** `/widgets/citations/`
**Status:** ✅ Academic tool

**What it does:**
Generates academic citations for orchid data and images in multiple formats (APA, MLA, Chicago, BibTeX).

**Features:**
- Auto-populate from database
- Multiple citation styles
- BibTeX export
- DOI integration
- Batch citation generation
- Copy to clipboard

**Deployment:** Research tool
**AI Cost:** FREE

---

## 37. Research Document Library Widget
**File:** `templates/widgets/research_library.html`
**Route:** `/widgets/research-library/`
**Status:** ✅ PDF catalog system

**What it does:**
Catalogues academic PDFs and research documents with metadata indexing and searchable topics.

**Features:**
- PDF metadata extraction
- Topic tagging
- Genus-specific filtering
- DOI linking
- Citation management
- Full-text search

**Database Table:** `research_documents`
**Example:** "Medicinal Orchids of Asia" (Teoh, 2016)
**Deployment:** Academic widget
**AI Cost:** FREE

---

## 38. Taxonomy Browser Widget
**File:** `templates/widgets/taxonomy_browser.html`
**Route:** `/widgets/taxonomy/`
**Status:** ✅ Hierarchical explorer

**What it does:**
Interactive tree browser for orchid taxonomy hierarchy (Family → Subfamily → Tribe → Genus → Species).

**Features:**
- Expandable tree view
- Search within taxonomy
- Species count per genus
- Synonym display
- Authority citations
- Navigate to species pages

**Database:** `orchid_taxonomy` (35,320 species)
**Deployment:** Educational widget
**AI Cost:** FREE

---

## 39. GBIF Data Explorer Widget
**File:** `templates/widgets/gbif_explorer.html`
**Route:** `/widgets/gbif-data/`
**Status:** ✅ Occurrence data viewer

**What it does:**
Displays GBIF occurrence data for orchid species with interactive maps and download options.

**Features:**
- Interactive occurrence maps
- Temporal distribution charts
- Observer/institution credits
- Data quality indicators
- Export to CSV
- Filter by date/location

**External API:** GBIF API (FREE)
**Database Table:** `orchid_images` (GBIF metadata)
**Deployment:** Research widget
**AI Cost:** FREE

---

## 40. EOL Trait Data Widget
**File:** `templates/widgets/eol_traits.html`
**Route:** `/widgets/eol-traits/`
**Status:** ✅ Phenotypic database

**What it does:**
Displays Encyclopedia of Life trait data including vernacular names, descriptions, and phenotypic characteristics.

**Features:**
- Trait database browser
- Vernacular names (multiple languages)
- Phenotypic descriptions
- Habitat information
- Conservation notes
- Source attribution

**External API:** EOL API (FREE)
**Database Table:** `eol_enrichment_data`
**Deployment:** Educational widget
**AI Cost:** FREE

---

## 41. Interactive 3D Globe Widget
**File:** `templates/widgets/interactive_globe.html`
**Route:** `/widgets/globe/`
**Status:** ✅ Geographic visualization

**What it does:**
3D globe showing orchid biodiversity hotspots with 35th parallel overlay for educational content.

**Features:**
- Rotating 3D globe
- Biodiversity hotspot markers
- 35th parallel overlay
- Click for species info
- Region statistics
- Educational tooltips

**JavaScript Library:** Three.js or similar
**Deployment:** Homepage hero or educational widget
**AI Cost:** FREE

---

## 42. Weather/Habitat Comparison Advanced
**File:** `templates/widgets/weather_comparison.html`
**Route:** `/weather-habitat/widget`
**Status:** ✅ Climate analysis tool

**What it does:**
Advanced comparison of user location weather vs. orchid native habitat with AI-powered growing advice.

**Features:**
- Real-time weather data
- Climate compatibility scoring
- Interactive charts
- AI growing recommendations
- Microclimate tips
- Seasonal adjustments

**External API:** OpenWeather API
**AI Cost:** Optional AI advice (~$0.01 per query)
**Deployment:** Grower tool
**AI Cost:** Optional enhancement

---

## 43. Bulk Image Analyzer
**File:** Routes in `bulk_orchid_analyzer.py`
**Route:** `/bulk-analyze/`
**Status:** ✅ Batch processing tool

**What it does:**
Analyzes multiple orchid images simultaneously (ZIP upload) with AI identification and metadata extraction.

**Features:**
- ZIP file upload
- Batch AI processing
- Progress tracking
- Results export (CSV/JSON)
- Error handling
- Download analyzed data

**AI Cost:** ~$0.01-0.03 per image × batch size
**Kill-Switch:** Guarded by ORCHID_AI_ENABLED
**Deployment:** Research tool

---

## 44. Data Quality Dashboard
**File:** `data_quality_dashboard.py`, template in `templates/admin/`
**Route:** `/admin/data-quality`
**Status:** ✅ Admin monitoring tool

**What it does:**
Monitors database completeness, identifies missing fields, and suggests enrichment priorities.

**Features:**
- Completeness metrics
- Missing field reports
- Duplicate detection
- Data quality scoring
- Enrichment recommendations
- Automated reports

**Deployment:** Admin dashboard widget
**AI Cost:** FREE

---

## 45. Julius AI Integration Widget
**File:** Routes in `routes.py` for Julius API
**Route:** `/api/julius/orchid-data`
**Status:** ✅ Analytics connector

**What it does:**
Provides curated PostgreSQL data access for Julius AI analytics with intelligent enrichment pipeline.

**Features:**
- Direct PostgreSQL connection support
- Curated data API endpoint
- Query pattern learning
- Automated enrichment prioritization
- Analytics-ready data export
- Performance optimization

**Deployment:** API endpoint for external analytics
**AI Cost:** FREE (Julius AI separately billed)

---

**End of Part 3**
Next: Part 4 - Admin & System Widgets
