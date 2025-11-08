# The Orchid Continuum - Digital Platform Project

## Overview
The Orchid Continuum is a research-grade digital platform for orchid research and community management. It integrates authoritative taxonomy databases, AI-powered image analysis, and ecological pattern correlation discovery. The platform serves as an academic research hub, inspiring students in mycorrhizal networks, AI-biology interfaces, and orchid conservation by providing legitimate research opportunities. Its core capabilities include automated data ingestion, AI-driven identification, and real-time web widgets. The mission is to preserve and honor historical botanical work while creating a comprehensive educational platform that connects past and present botanical knowledge through detailed species information, historical specimens, botanical plates, and modern photographs.

## Recent Changes (November 8, 2025)
- **Source-Specific Worker Architecture:** Created dedicated worker scripts for each API source (GBIF, iNaturalist, iDigBio, Tropicos, BHL, EOL+ALA) to prevent rate limiting. Replaced multi-source workers with 17 specialized workers distributed across 7 APIs. Each worker has source-specific rate limiting (0.3-0.8s delays) to avoid overwhelming any single API.
- **Partner Collections Import System:** Built automated Google Drive scraper with intelligent filename parsing. Successfully imported 1,403 images from Roberta Fox (875) and Chris Howard (450) collections with 26% taxonomy match rate.
- **EOL Bulk Import:** Mapped 21,006 orchid species to EOL page IDs. Loaded 3.5M phenotypic trait records from EOL TraitBank covering 840,941 species.
- **Database Optimization:** Fixed schema issues by extending varchar columns to TEXT, preventing transaction aborts during bulk imports.
- **Current Database:** 114,997 images covering 2,121 species (6% of 35,327 goal). Species with 30+ images: 86 (0.2% of goal).
- **New Import Scripts:** Created `bulk_eol_import/4_import_partner_photos_with_names.py` (filename parser), `bulk_eol_import/5_backfill_partner_taxonomy.py` (taxonomy matcher), and supporting scripts for continuous harvesting.
- **Worker Management:** Master launcher script (`workers/launch_all.sh`) provides one-command deployment of all 17 workers with proper logging and monitoring.

## User Preferences
- **Communication Style**: Simple, everyday language
- **Collaboration Workflow**: Replit Agent ↔ Julius AI parallel work with iterative review cycles (Build → Julius reviews → Revise → Push to GitHub → Manual Render deployment)
- **Never wait for Julius**: Always work in parallel, send completed work for review, continue building while Julius analyzes
- **Testing Philosophy**: Use real data for testing (24,865 images downloaded from GBIF, EOL, iNaturalist, iDigBio)

## System Architecture

### UI/UX Decisions
The platform utilizes a Bootstrap 5 dark theme with custom orchid styling and Feather Icons, focusing on responsive design, interactive JavaScript features, and an interactive 3D globe with a 35th parallel overlay.

### Technical Implementations
The backend is built with Flask and SQLAlchemy ORM, supporting SQLite and PostgreSQL. AI integration uses a cost-optimized Multi-Provider AI System, prioritizing free/low-cost services like Google Gemini and Together AI, with OpenAI as a fallback. Google Drive API is used for cloud storage, and web scraping is automated with `trafilatura` and `BeautifulSoup`. Frontend uses Jinja2 templates. The database schema includes `orchid_taxonomy`, `orchid_images`, and `OrchidRecord`. Key features include AI-powered image analysis with confidence scoring, advanced comparison systems using EXIF data, a robust citation and research attribution system, automated web scraping, and continuous GBIF image enrichment. The system is designed to scale to 100,000-200,000 orchid records with 12 high-performance database indexes.

**Multi-Provider AI System**: This system intelligently routes requests to various AI providers based on cost and capability, including Google Gemini 2.0 Flash, Hugging Face, OpenAI GPT-4o Vision for vision AI, and Together AI FLUX, Replicate FLUX, and OpenAI DALL-E 3 for image generation.

### 24/7 Multi-Source Harvesting Architecture

**Source-Specific Worker Distribution**: The system uses dedicated worker processes for each image API to prevent rate limiting and maximize throughput. This architecture replaced the original multi-source workers that caused GBIF rate limiting when 100+ workers ran simultaneously.

**Worker Distribution (17 Total Workers)**:
- **GBIF Workers (8)**: Primary source handling 7 API calls per species (1 global + 6 country-specific). Rate limit: 0.5s delay between requests.
- **iNaturalist Workers (3)**: Community observations with research-grade quality filter. Rate limit: 0.3s delay.
- **iDigBio Workers (2)**: Digitized herbarium specimens from institutional collections. Rate limit: 0.4s delay.
- **Tropicos Workers (2)**: Missouri Botanical Garden herbarium images (requires API key). Rate limit: 0.6s delay.
- **BHL Worker (1)**: Biodiversity Heritage Library botanical plates (requires API key). Rate limit: 0.8s delay.
- **EOL+ALA Worker (1)**: Combined Encyclopedia of Life and Atlas of Living Australia. Rate limit: 0.5s delay.

**Job Queue System**: Workers lease jobs from the `harvest_jobs` PostgreSQL table using `FOR UPDATE SKIP LOCKED` for race-condition-proof job distribution. Jobs are automatically reclaimed after 7 minutes if a worker crashes. Each worker processes jobs in batches (5-8 species per cycle) and marks them complete after successful image imports.

**Performance Targets**: Expected throughput of 2,000-3,000 images/hour combined (48,000-72,000 images/day) across all workers, reaching the 1M image goal in 15-20 days.

**Deployment**: Workers are deployed on Render as background services using the master launcher script (`workers/launch_all.sh`). Each worker logs to separate files in `logs/` directory for independent monitoring and debugging.

### Feature Specifications
Key features include a **Digital Botanist Vision AI System** for research-grade botanical identification and a **4-Mode Botanical Illustration System** that generates various illustration types. **Orchid Continuum University** offers an online curriculum with a 1,763-term professional botanical glossary and a **Species Identification Key Database** providing access to 90 dichotomous key sources. Other features include automated GBIF and EOL image enrichment, Tropicos integration, Perenual care guide integration, an Orchid Data Enrichment System, a Widget Directory System (including the FCOS Orchid Judge PWA), an Advanced Comparison System, Citation and Research Attribution, Automated Web Scraping, File Upload and Management, Search and Gallery Systems, an Admin Dashboard, Weather/Habitat Comparison Widget, a 35th Parallel Educational Globe System, and an Ethnobotany & Traditional Knowledge System.

**Julius AI Integration**: A secure RESTful API provides Julius AI with programmatic access to Orchid Continuum data, including glossary, dichotomous keys, GBIF images, taxonomy, and enrichment data. An **AI-to-AI Autonomous Communication System** enables safe autonomous collaboration between Replit Agent and Julius AI.

**BloomBuilder: Interactive Orchid Morphology Lab**: An educational widget for interactive orchid anatomy annotation, featuring a 10-stage species verification and education workflow. This workflow includes species selection, photo comparison, herbarium sheet/botanical plate selection, side-by-side labeling with linked glossary terms, dichotomous key usage, a two-level validation system, trait toggles, 3D bloom assembly, and export/save functionalities.

## External Dependencies

### APIs and Services
-   **Google Gemini API**: Primary vision AI.
-   **Together AI API**: Primary image generation.
-   **Hugging Face API**: Backup vision models.
-   **Replicate API**: Backup image generation.
-   **OpenAI API**: Fallback for vision and image generation.
-   **GBIF API**: Global Biodiversity Information Facility for occurrence data (8 dedicated workers).
-   **iNaturalist API**: Community observations with research-grade filtering (3 dedicated workers).
-   **iDigBio API**: Digitized herbarium specimens from institutional collections (2 dedicated workers).
-   **EOL API**: Encyclopedia of Life for trait data (1 combined worker with ALA).
-   **ALA API**: Atlas of Living Australia for Australian orchid observations (1 combined worker with EOL).
-   **Tropicos API**: Missouri Botanical Garden for authoritative taxonomy and herbarium specimens (2 dedicated workers).
-   **BHL API**: Biodiversity Heritage Library for historical botanical plates (1 dedicated worker).
-   **Perenual API**: Plant care database.
-   **Google Drive API**: Cloud storage.
-   **Google Sheets API**: Programmatic sheet updates.

### Python Libraries
-   **Flask**: Web framework.
-   **SQLAlchemy**: ORM for database interactions.
-   **Pillow**: Image processing.
-   **Folium**: Interactive mapping.
-   **BeautifulSoup/trafilatura**: Web content extraction.
-   **Werkzeug**: File upload security.

### Frontend Libraries
-   **Bootstrap 5**: UI framework.
-   **Feather Icons**: Icon system.
-   **JavaScript**: For interactive features.