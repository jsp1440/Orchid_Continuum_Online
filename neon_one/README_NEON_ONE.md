# Orchid Continuum - Neon One Integration Pack

**Version:** 1.0  
**Date:** October 20, 2025  
**Platform:** Neon One CMS for FCOS Website

---

## 📚 Table of Contents

1. [Quick Start](#quick-start)
2. [Widget Installation Guide](#widget-installation-guide)
3. [Cost & Performance Information](#cost--performance-information)
4. [Troubleshooting](#troubleshooting)
5. [Widget Descriptions](#widget-descriptions)
6. [Technical Support](#technical-support)

---

## Quick Start

### What's Included

This integration pack contains **10 self-contained widget embeds** ready for Neon One:

- **6 CDN widgets** (public-facing, cost-optimized)
- **2 backend widgets** (member tools)
- **2 restricted widgets** (admin/board only)

All widgets are:
- ✅ **Self-contained** (no external libraries needed)
- ✅ **Copy-paste ready** (one configuration change only)
- ✅ **Gracefully degrading** (show friendly messages if API offline)
- ✅ **Accessible** (WCAG 2.1 compliant with ARIA labels)
- ✅ **Responsive** (mobile-friendly design)

---

## Widget Installation Guide

### Step-by-Step Instructions

#### Step 1: Browse Available Widgets

Open **`EMBED_DIRECTORY.html`** in your browser to see all 10 widgets with descriptions, costs, and files.

#### Step 2: Select a Widget

Choose which widget you want to embed from the directory table.

#### Step 3: Open the Widget File

Navigate to the `embeds/` folder and open the corresponding HTML file. For example:
- Home page → `home_orchid_of_the_day.html`
- Explore page → `explore_taxonomy_browser.html`
- Learn & Play → `learnplay_bingo.html`

#### Step 4: Configure BASE_URL

At the top of each file, find the **CONFIG section**:

```javascript
// ============================================================================
// CONFIG - CHANGE ME
// ============================================================================
const CONFIG = {
  BASE_URL: 'https://your-orchid-app.onrender.com',  // CHANGE ME
};
// ============================================================================
```

**Replace** `https://your-orchid-app.onrender.com` with your actual deployed Orchid Continuum URL.

**Examples:**
- Render deployment: `https://orchid-continuum.onrender.com`
- Replit deployment: `https://orchid-continuum.replit.app`
- Custom domain: `https://orchids.fcos.org`

#### Step 5: Copy the Entire File

- Select all content (Ctrl+A or Cmd+A)
- Copy (Ctrl+C or Cmd+C)

#### Step 6: Paste into Neon One

1. Log into your Neon One CMS
2. Navigate to the page where you want the widget
3. Add a new **HTML Content Block**
4. Paste the entire widget code
5. **Save** the page

#### Step 7: Test the Widget

- View the page on your Neon One site
- Verify the widget loads correctly
- Test any interactive features (buttons, search, etc.)

---

## Cost & Performance Information

### Free Widgets (No API Calls)

These widgets run entirely in the browser with **zero backend costs**:

| Widget | File | Cost |
|--------|------|------|
| Orchid Bingo | `learnplay_bingo.html` | **$0/month** |
| Philosophy Quiz | `learnplay_philosophy_quiz.html` | **$0/month** |

**Total:** 2 widgets, fully client-side

---

### Database Widgets (Minimal Cost)

These widgets query the Orchid Continuum database:

| Widget | File | Database Cost |
|--------|------|--------------|
| Orchid of the Day | `home_orchid_of_the_day.html` | Included in hosting |
| Themed Gallery | `home_themed_gallery.html` | Included in hosting |
| Taxonomy Browser | `explore_taxonomy_browser.html` | Included in hosting |
| My Collection | `member_my_collection.html` | Included in hosting |
| Habitat/Weather | `member_habitat_weather.html` | Included in hosting |
| Admin Dashboard | `admin_dashboard.html` | Included in hosting |
| Widget Health | `admin_widget_health.html` | Included in hosting |

**Total:** 7 widgets  
**Cost:** Included in Render hosting ($5-20/month)

---

### External API Widgets (Free APIs)

These widgets call FREE external APIs:

| Widget | API Used | Cost |
|--------|----------|------|
| GBIF Data Explorer | GBIF API | **FREE** (public API) |
| Habitat/Weather | OpenWeather API | **FREE** (tier) |

**Total:** 2 widgets (1 unique + 1 shared)  
**Cost:** $0/month (free tier)

---

### AI Widgets (Currently Disabled)

**IMPORTANT:** All AI features are **DISABLED** by default to prevent unexpected costs.

- AI widgets: **0 active**
- AI cost: **$0/month**
- Kill-switch: `ORCHID_AI_ENABLED=false`

To enable AI features (not recommended for initial deployment):
1. Contact your technical administrator
2. Set environment variable `ORCHID_AI_ENABLED=true`
3. Monitor OpenAI usage costs

**Estimated AI Cost (if enabled):** ~$10-50/month depending on traffic

---

### Total Cost Summary

| Category | Monthly Cost |
|----------|-------------|
| Hosting (Render.com) | $5-20 |
| Database | Included |
| CDN (optional) | $5-15 |
| External APIs | $0 |
| AI Features | $0 (disabled) |
| **TOTAL ESTIMATE** | **$5-35/month** |

---

## Troubleshooting

### Widget Shows "Unable to Connect" Message

**Cause:** BASE_URL is incorrect or backend is offline

**Solution:**
1. Check the BASE_URL in the widget CONFIG section
2. Verify your Orchid Continuum app is deployed and running
3. Test the URL in a browser (should load the homepage)
4. Ensure URL has `https://` prefix and no trailing slash

---

### Widget Displays "API Unavailable" Banner

**Cause:** Specific API endpoint is missing or backend route not deployed

**Solution:**
1. This is normal graceful degradation
2. Widget will show a friendly message and link to full site
3. Contact technical administrator to verify endpoint exists
4. Check `manifest.preview.json` for required endpoints

---

### Widget Shows "AI Features Paused" Message

**Cause:** AI kill-switch is active (this is intentional)

**Solution:**
- **No action needed** - This is the default cost-saving mode
- Widget will continue to work without AI features
- AI-enhanced descriptions replaced with database content
- If AI needed, contact administrator to enable

---

### Admin Widgets Show "Access Required"

**Cause:** User is not logged in as admin

**Solution:**
1. Admin widgets (`admin_dashboard.html`, `admin_widget_health.html`) require authentication
2. Log in via the admin portal
3. These widgets are for FCOS Board members only
4. **Do not deploy these on public pages**

---

### Widget Not Responsive on Mobile

**Cause:** Neon One CSS conflicts

**Solution:**
1. All widgets are mobile-responsive by default
2. If issues occur, wrap widget in a `<div style="max-width:100%;overflow-x:auto;">` container
3. Contact Neon One support about CSS conflicts

---

## Widget Descriptions

### Home Page Widgets

#### 🌺 Orchid of the Day
**File:** `home_orchid_of_the_day.html`  
**Purpose:** Daily featured orchid to engage visitors  
**Features:**
- Random orchid from 35,000+ species
- Scientific name, common name, distribution
- "New Orchid" refresh button
- Checks AI status (shows banner if disabled)
- Beautiful gradient card design

**Best Used On:** Homepage hero section, sidebar widget

---

#### 🎨 Themed Gallery
**File:** `home_themed_gallery.html`  
**Purpose:** Curated orchid collections by theme  
**Features:**
- 4 themes: Fragrant, Night-Blooming, Madagascar, Thailand
- Tab-based navigation
- Grid display of 6 orchids per theme
- Falls back to links if API offline

**Best Used On:** Homepage content section, gallery pages

---

### Explore Orchids Widgets

#### 🌸 Taxonomy Browser
**File:** `explore_taxonomy_browser.html`  
**Purpose:** Search and browse orchid taxonomy database  
**Features:**
- Full-text search across 35,000+ species
- Genus filter dropdown
- Paginated results (12 per page)
- Scientific names, authors, distribution
- Previous/Next navigation

**Best Used On:** Research pages, educational content

---

#### 🌍 GBIF Data Explorer
**File:** `explore_gbif_explorer.html`  
**Purpose:** Display orchid occurrence data from GBIF  
**Features:**
- Search by genus
- Shows total occurrences, countries, specimens
- Top location statistics
- Link to full GBIF explorer
- **Uses FREE GBIF API**

**Best Used On:** Biodiversity pages, research sections

---

### Learn & Play Widgets

#### 🎯 Orchid Bingo
**File:** `learnplay_bingo.html`  
**Purpose:** Educational game for kids and public  
**Features:**
- 5x5 bingo grid with orchid genus names
- Click to mark cells
- FREE center space
- Score tracking
- New game generator
- **Fully client-side (no backend needed)**

**Best Used On:** Kids pages, educational programs, events

---

#### 🧠 Philosophy Quiz
**File:** `learnplay_philosophy_quiz.html`  
**Purpose:** Personality quiz to match users to orchid types  
**Features:**
- 3-question personality assessment
- Matches to orchid species (Cattleya, Phalaenopsis, etc.)
- Beautiful results card
- Retake functionality
- **Newsletter lead magnet potential**
- **Fully client-side (no backend needed)**

**Best Used On:** Homepage engagement, newsletter signup pages

---

### Member Tools Widgets

#### 📚 My Collection
**File:** `member_my_collection.html`  
**Purpose:** Personal orchid collection tracking  
**Features:**
- Add orchids with notes
- Acquisition date tracking
- Remove orchids
- localStorage fallback (works without backend)
- Optional auth integration

**Best Used On:** Member dashboard, profile pages

---

#### 🌤️ Habitat/Weather Comparison
**File:** `member_habitat_weather.html`  
**Purpose:** Compare local climate with orchid native habitat  
**Features:**
- Location + orchid name input
- Temperature comparison
- Humidity matching
- Match percentage score
- Growing tips
- **Uses FREE OpenWeather API**

**Best Used On:** Member tools, growing guides

---

### Admin/Board Widgets

#### 🔒 Admin Dashboard
**File:** `admin_dashboard.html`  
**Purpose:** System statistics for FCOS Board  
**Features:**
- Total users, members, orchid records
- Image collection count
- Recent activity log
- **Requires admin authentication**
- **Restricted access only**

**Best Used On:** Admin portal (NOT public pages)

---

#### 📊 Widget Health Monitor
**File:** `admin_widget_health.html`  
**Purpose:** Real-time widget performance monitoring  
**Features:**
- Uptime percentage for each widget
- Request counts
- Health status indicators
- Auto-refresh every 30 seconds
- **Requires admin authentication**
- **Restricted access only**

**Best Used On:** Admin portal (NOT public pages)

---

## Technical Support

### Documentation Resources

| Resource | Description | Location |
|----------|-------------|----------|
| **Embed Directory** | Visual table of all widgets | `EMBED_DIRECTORY.html` |
| **Manifest JSON** | Machine-readable deployment config | `manifest.preview.json` |
| **Widget Catalog** | Complete technical docs | `../WIDGET_CATALOG_PART5.md` |
| **Database Audit** | Cost & architecture details | `../DATABASE_AUDIT_SUMMARY.md` |

---

### Changing Active Widgets

To add or remove widgets from deployment:

1. Open `../WIDGET_DEPLOYMENT_MANIFEST.json`
2. Change widget `status` to:
   - `"active"` - Deploy this widget
   - `"inactive"` - Hide this widget
   - `"restricted"` - Admin access only
3. Save the file
4. Widget manifest API updates automatically

**Note:** Maximum 10 active widgets recommended for cost control

---

### Environment Variables

These control platform behavior:

| Variable | Default | Purpose |
|----------|---------|---------|
| `ORCHID_AI_ENABLED` | `false` | AI kill-switch (keep OFF) |
| `APP_ENV` | `dev` | Set to `prod` for caching |
| `DATABASE_URL` | (auto) | PostgreSQL connection |
| `SESSION_SECRET` | (auto) | Security key |

**Do not modify** these unless directed by technical administrator.

---

### Getting Help

**For widget questions:**
1. Check this README
2. Review `EMBED_DIRECTORY.html`
3. Consult `WIDGET_CATALOG_PART5.md`

**For technical issues:**
1. Verify BASE_URL configuration
2. Test widget on development site first
3. Check browser console for errors (F12)
4. Contact technical administrator

**For cost concerns:**
1. Review cost summary section above
2. Check `manifest.preview.json`
3. Consult `DATABASE_AUDIT_SUMMARY.md`

---

## Appendix: File Structure

```
neon_one/
├── README_NEON_ONE.md           ← You are here
├── EMBED_DIRECTORY.html         ← Widget catalog (open in browser)
├── manifest.preview.json        ← Deployment configuration
└── embeds/
    ├── home_orchid_of_the_day.html
    ├── home_themed_gallery.html
    ├── explore_taxonomy_browser.html
    ├── explore_gbif_explorer.html
    ├── learnplay_bingo.html
    ├── learnplay_philosophy_quiz.html
    ├── member_my_collection.html
    ├── member_habitat_weather.html
    ├── admin_dashboard.html
    └── admin_widget_health.html
```

---

## Quick Reference Card

### Installation Checklist

- [ ] Choose widget from `EMBED_DIRECTORY.html`
- [ ] Open widget file from `embeds/` folder
- [ ] Change `BASE_URL` in CONFIG section
- [ ] Copy entire file (Ctrl+A, Ctrl+C)
- [ ] Paste into Neon One HTML block
- [ ] Save page
- [ ] Test widget on live site

### Cost Reminder

- **Free widgets:** Bingo, Philosophy Quiz (client-side only)
- **Database widgets:** $0 extra (included in hosting)
- **External APIs:** GBIF, OpenWeather (both FREE)
- **AI:** Disabled ($0/month)
- **Total estimate:** $5-35/month (hosting + optional CDN)

---

**End of README**  
*For questions, consult the main Orchid Continuum repository documentation*

---

## Taxonomy Widget Suite (NEW!)

The **Taxonomy Widget Suite** provides 4 new widgets leveraging the 35,000+ orchid taxonomy database with educational and research-grade features.

### 📅 Bloom Calendar & Habitat Mapper
**File:** `explore_bloom_mapper.html`  
**Purpose:** Visual bloom calendar and geographic distribution  
**API Endpoints Used:**
- `GET /api/taxonomy/genera` - List of all orchid genera
- `GET /api/taxonomy/bloomdata?genus=` - Monthly bloom pattern
- `GET /api/taxonomy/distribution?genus=` - Geographic regions

**Features:**
- Select genus from dropdown (50+ genera)
- 12-month bloom bar chart
- Top 10 distribution regions by occurrence count
- Demo data fallback when real data unavailable
- Responsive SVG-style charts (no external libs)

**Best Used On:** Research pages, genus information pages

---

### 🐝 Pollinator Match Game
**File:** `learnplay_pollinator_game.html`  
**Purpose:** Educational game to guess orchid pollinators  
**API Endpoints Used:**
- `GET /api/taxonomy/pollinator?species=` - Pollinator quiz question

**Features:**
- Random orchid selection or search by species
- Multiple choice: Bee, Moth, Hummingbird, Fly, Wind, Unknown
- Reveal answer with ecological rationale
- Simple heuristic inference (night-blooming → moth)
- Works without AI (demo mode with educational explanations)

**Best Used On:** Educational pages, kids sections, Learn & Play

---

### 🔮 Mystery Orchid Quiz
**File:** `learnplay_mystery_orchid_quiz.html`  
**Purpose:** Guess the genus quiz with images  
**API Endpoints Used:**
- `GET /api/taxonomy/quiz/mystery` - Random quiz question

**Features:**
- Random orchid with hidden genus
- 4 multiple-choice options (1 correct + 3 distractors)
- Reveal shows: full name, author, image, distribution
- Image display when available (or friendly placeholder)
- Score tracking capability
- Educational reveal with taxonomy details

**Best Used On:** Learn & Play, educational engagement, trivia

---

### 🔗 Taxonomy Linker
**File:** `membertools_linker.html`  
**Purpose:** Batch resolve member plant names to taxonomy  
**API Endpoints Used:**
- `POST /api/member/taxonomy/resolve` - Batch name resolution

**Features:**
- Paste up to 50 plant names (one per line)
- Fuzzy matching: scientific names, genus, common names
- Confidence scores (high/medium)
- Shows: author, native region, habitat, images
- Handles multiple matches per input
- Clean, card-based results UI

**Best Used On:** Member dashboards, collection management, plant ID tools

---

## Taxonomy API Endpoints Reference

All endpoints are read-only and cached for performance:

| Endpoint | Method | Parameters | Purpose |
|----------|--------|------------|---------|
| `/api/taxonomy/genera` | GET | - | List all genera (cached 60min) |
| `/api/taxonomy/search` | GET | `q, genus, page, limit` | Search taxonomy (paginated) |
| `/api/taxonomy/random` | GET | - | Random orchid record |
| `/api/taxonomy/bloomdata` | GET | `genus` | Seasonal bloom pattern |
| `/api/taxonomy/distribution` | GET | `genus` | Geographic distribution |
| `/api/taxonomy/pollinator` | GET | `species` (optional) | Pollinator quiz |
| `/api/taxonomy/quiz/mystery` | GET | - | Mystery genus quiz |
| `/api/member/taxonomy/resolve` | POST | `{items: []}` | Batch name resolution |
| `/api/ai/status` | GET | - | AI feature status |

**Demo Data:**  
When real data is unavailable, endpoints return `"demo": true` in JSON response with friendly placeholder data. This ensures widgets never crash and always provide educational value.

---

**End of README**  
*For questions, consult the main Orchid Continuum repository documentation*
