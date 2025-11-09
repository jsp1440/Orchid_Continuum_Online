# The Orchid Continuum - Comprehensive Digital Botanical Research Platform

## Overview

The Orchid Continuum is a comprehensive digital platform for orchid research and education. It integrates historical botanical scholarship with AI technology and real-time climate data to bridge past and present botanical knowledge. The platform aims to honor pioneering orchidologists while advancing botanical education and conservation. Key features include historical-modern data integration, multi-source real-time data harvesting, climate-aware and customizable culture sheets, research-grade educational tools, AI-powered intelligence for identification and illustration, and comprehensive data management. The project envisions becoming the world's largest orchid image database with detailed, location-specific culture guidance and advanced educational resources for enthusiasts and researchers alike.

## User Preferences

-   **Communication Style**: Simple, everyday language
-   **Collaboration Workflow**: Replit Agent ↔ Julius AI parallel work with iterative review cycles (Build → Julius reviews → Revise → Push to GitHub → Manual Render deployment)
-   **Never wait for Julius**: Always work in parallel, send completed work for review, continue building while Julius analyzes
-   **Testing Philosophy**: Use real data for testing (24,865 images downloaded from GBIF, EOL, iNaturalist, iDigBio)

## System Architecture

### UI/UX Decisions
The platform features a responsive Bootstrap 5 dark theme with custom orchid styling and Feather Icons. It incorporates interactive JavaScript elements and a 3D globe with a 35th parallel overlay for educational purposes.

### Technical Implementations
The backend is built with Flask and SQLAlchemy ORM, supporting PostgreSQL. A cost-optimized Multi-Provider AI System (Google Gemini, Together AI, OpenAI fallback) handles AI tasks. Google Drive API is used for cloud storage, while `trafilatura` and `BeautifulSoup` automate web scraping. Jinja2 templates are used for the frontend. The database schema includes `orchid_taxonomy`, `orchid_images`, and `OrchidRecord`, designed for scalability with 12 high-performance indexes. Key features include AI-powered image analysis with confidence scoring, a robust citation system, and automated web scraping.

### System Design Choices
The **24/7 Multi-Source Harvesting Architecture** employs 17 dedicated worker processes distributed across 7 APIs (GBIF, iNaturalist, iDigBio, Tropicos, BHL, EOL+ALA) to prevent rate limiting and maximize image harvesting throughput (2,000-3,000 images/hour). A PostgreSQL-backed job queue uses `FOR UPDATE SKIP LOCKED` for race-condition-proof job distribution and automatic worker recovery.

**Core Features & Functionality**:
-   **Culture Sheet System**: Generates personalized, location-specific growing guides by synthesizing Baker species data, AOS guidelines, and local climate analysis (Open-Meteo API for historical and real-time weather). Features customizable print formats and smart caching.
-   **Educational Tools**: Includes "Orchid Continuum University" with a 1,763-term botanical glossary, a "Species Identification Key Database" with 90 dichotomous key sources, and "BloomBuilder Interactive Morphology Lab" for interactive anatomy education.
-   **AI Integration**: Features "Digital Botanist Vision AI" for research-grade identification with confidence scoring and a "4-Mode Botanical Illustration System" for generating scientific illustrations. An **AI-to-AI Collaboration** system uses a secure RESTful API for autonomous task delegation between Replit Agent and Julius AI.
-   **Data Management**: PostgreSQL with 12 indexes stores 35,327 orchid species taxonomy, 133,458+ images, and 3.5M phenotypic trait records. A 30-day intelligent caching strategy separates base culture data from location-specific weather.
-   **Widget Directory System**: Provides embeddable widgets like the Weather/Habitat Comparison and the FCOS Orchid Judge PWA.
-   **Geographic & Climate Tools**: Includes a 35th Parallel Educational System with an interactive 3D globe and detailed weather integration via Open-Meteo API.
-   **Research Attribution System**: Tracks all image sources and original contributors.
-   **Partner Collections Integration**: Automated import system for partner images (e.g., Roberta Fox, Chris Howard) with fuzzy taxonomy matching.

## External Dependencies

### APIs and Services
-   **Google Gemini API**: Primary vision AI.
-   **Together AI API**: Primary image generation.
-   **Hugging Face API**: Backup vision models.
-   **Replicate API**: Backup image generation.
-   **OpenAI API**: Fallback for vision and image generation.
-   **GBIF API**: Global Biodiversity Information Facility.
-   **iNaturalist API**: Community observations.
-   **iDigBio API**: Digitized herbarium specimens.
-   **EOL API**: Encyclopedia of Life (for trait data).
-   **ALA API**: Atlas of Living Australia.
-   **Tropicos API**: Missouri Botanical Garden.
-   **BHL API**: Biodiversity Heritage Library.
-   **Perenual API**: Plant care database.
-   **Google Drive API**: Cloud storage.
-   **Google Sheets API**: Programmatic sheet updates.
-   **Open-Meteo API**: Historical and real-time climate data.

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