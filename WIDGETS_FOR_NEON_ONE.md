# 5 Working Widgets for Neon One Integration
**Ready for Developer Meeting - Wednesday**

## Widget List

### 1. FCOS Orchid Judge PWA
**URL:** `/fcos-judge`
**Purpose:** Educational orchid judging tool with OCR, AI analysis, certificate generation
**Embed:** Iframe-ready, mobile-first design
**Status:** ✅ Active

### 2. Gallery Hub
**URL:** `/gallery-hub`
**Purpose:** Curated themed orchid galleries (Thailand, Madagascar, Fragrant, Night-Blooming)
**Embed:** Responsive gallery system with filtering
**Status:** ✅ Active

### 3. AI Breeder Assistant Pro
**URL:** `/ai-breeder-pro`
**Purpose:** Orchid breeding assistant with trait prediction, lineage analysis
**Embed:** Form-based widget with CSRF protection
**Status:** ✅ Active with Google Cloud integration

### 4. Orchid of the Day
**URL:** `/widgets/orchid-of-day` (or via Widget Directory)
**Purpose:** Daily featured orchid with facts and images
**Embed:** Simple, lightweight widget
**Status:** ✅ Active

### 5. Themed Galleries Widget
**URL:** `/widgets/themed-galleries`
**Purpose:** Rotating themed orchid collections
**Embed:** Carousel-style display
**Status:** ✅ Active

## Widget Directory
**URL:** `/widgets`
**Purpose:** Central catalog of ALL 12+ widgets
**Use:** Show developer the full widget ecosystem

## API Endpoints for Widgets

All widgets have corresponding API endpoints:
- `/api/taxonomy/*` - Taxonomy data
- `/api/manifest` - Widget deployment manifest
- `/manifest` - Widget configuration

## Embed Instructions

Each widget supports:
1. **Direct Iframe Embed**
   ```html
   <iframe src="https://YOUR-REPLIT-URL/fcos-judge" width="100%" height="800px"></iframe>
   ```

2. **CORS Enabled** for Neon One domains:
   - `*.neoncrm.com`
   - `*.app.neoncrm.com`
   - `fivecitiesorchidsociety.app.neoncrm.com`

3. **CSP Headers** configured for iframe embedding

## Next Steps for Developer Meeting

1. Click "Publish" to deploy
2. Get your Replit URL (e.g., `https://your-project.repl.co`)
3. Share these 5 widget URLs with developer:
   - `https://your-project.repl.co/fcos-judge`
   - `https://your-project.repl.co/gallery-hub`
   - `https://your-project.repl.co/ai-breeder-pro`
   - `https://your-project.repl.co/widgets/orchid-of-day`
   - `https://your-project.repl.co/widgets/themed-galleries`

4. Show Widget Directory: `https://your-project.repl.co/widgets`

## Technical Details for Developer

- **Framework:** Flask (Python)
- **Database:** PostgreSQL (35,320 orchid species)
- **Authentication:** Replit Auth + Admin system
- **APIs:** GBIF, EOL, Google Cloud
- **Embed-Safe:** All CORS + CSP headers configured

All widgets are production-ready and tested!
