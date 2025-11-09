# 🌺 Advanced Orchid Culture Sheet Widget - Complete Specification for Famous AI

---

## ⚠️ CRITICAL: FRONT-END ONLY - DO NOT BUILD BACKEND ⚠️

**YOUR JOB: HTML + CSS + JavaScript ONLY**

The backend is **ALREADY COMPLETE** and running. You are **ONLY** designing the user interface.

**DO THIS:**
✅ Create beautiful HTML/CSS/JavaScript files
✅ Design responsive layouts with Bootstrap 5
✅ Add interactive forms and user interactions
✅ Make API calls to the EXISTING endpoints (listed below)
✅ Handle UI state and loading animations
✅ Create print-friendly styles

**DO NOT DO THIS:**
❌ Create Flask/Python files
❌ Build API endpoints
❌ Create database models
❌ Write backend logic
❌ Set up servers
❌ Configure databases
❌ Create requirements.txt or package.json for backend

**THINK OF IT THIS WAY:**
You're building a beautiful storefront. The warehouse (backend) is already built and stocked. You just need to create the display windows and checkout counter (user interface).

---

## 📋 PROJECT OVERVIEW

**What You're Building:**
An interactive, beautiful mobile-responsive **FRONT-END INTERFACE** that connects to an existing backend API. This displays personalized orchid growing guides by calling pre-built endpoints.

**Deployment Targets:**
- Progressive Web App (PWA) - installable on phones
- Embeddable widget for Neon One CRM platform
- Responsive web interface

**Tech Stack YOU Use:**
- HTML5
- CSS3 (with Bootstrap 5)
- Vanilla JavaScript (or jQuery if preferred)
- Chart.js for charts
- Feather Icons for icons

---

## 🎨 DESIGN SYSTEM (MUST MATCH EXISTING PLATFORM)

### Brand Identity
- **Theme:** Dark botanical elegance
- **Primary Color:** `#1a1a2e` (deep navy background)
- **Accent Color:** `#9d4edd` (purple for orchid theme)
- **Text Color:** `#f8f9fa` (light text on dark)
- **Success Color:** `#28a745` (green for plant theme)

### Typography
- **Headings:** System fonts, bold
- **Body:** Clean, readable sans-serif
- **Botanical Names:** Italicized (scientific convention)

### Icons
- **Use:** Feather Icons library (already integrated)
- **Examples:** 
  - `search` for species lookup
  - `map-pin` for location
  - `download` for print/save
  - `heart` for save to collection
  - `globe` for public library
  - `thermometer` for temperature
  - `droplet` for water
  - `sun` for light

### UI Framework
- **Bootstrap 5** (dark theme variant)
- Mobile-first responsive design
- Touch-friendly controls (minimum 44px tap targets)

---

## 🏗️ BACKEND API INTEGRATION

**IMPORTANT:** These endpoints are **ALREADY BUILT**. You just call them from JavaScript.

**Base URL:** `https://orchid-continuum-online.onrender.com` (or localhost:5000 for testing)

### API Endpoints You'll Call (DO NOT BUILD - JUST USE):

#### 1. Search Species (Autocomplete)
```
GET /api/species/search?query={search_term}

Response:
{
  "results": [
    {
      "taxonomy_id": 7905,
      "species_name": "Cattleya mossiae",
      "common_name": "Easter Orchid",
      "genus": "Cattleya"
    }
  ]
}
```

#### 2. Generate Culture Sheet
```
POST /api/culture-sheets/generate

Request Body:
{
  "taxonomy_id": 7905,
  "latitude": 34.0522,
  "longitude": -118.2437,
  "city": "Los Angeles",
  "country": "USA",
  "sections": ["temperature", "light", "water", "humidity", "potting", "fertilizer"],
  "artwork_style": "scientific" // or "artistic", "coloring_page"
}

Response:
{
  "sheet_id": "uuid-here",
  "species_name": "Cattleya mossiae",
  "genus": "Cattleya",
  "temperature": {
    "day_range": "75-85°F (24-29°C)",
    "night_range": "60-65°F (16-18°C)",
    "guidance": "Warm-growing with 15°F day/night differential..."
  },
  "light": { ... },
  "water": { ... },
  "humidity": { ... },
  "potting": { ... },
  "fertilizer": { ... },
  "climate_comparison": {
    "native_temp": "82°F avg",
    "your_temp": "72°F avg",
    "monthly_chart_data": [ ... ]
  },
  "artwork_url": "data:image/png;base64,..." // AI-generated botanical illustration
}
```

#### 3. Save to My Collection
```
POST /api/my-collection/save

Request Body:
{
  "sheet_id": "uuid",
  "user_id": "optional-if-logged-in",
  "nickname": "My LA Cattleya" // user's custom name
}

Response:
{
  "success": true,
  "collection_id": "uuid"
}
```

#### 4. Get My Collection
```
GET /api/my-collection?user_id={user_id}

Response:
{
  "sheets": [
    {
      "collection_id": "uuid",
      "species_name": "Cattleya mossiae",
      "nickname": "My LA Cattleya",
      "location": "Los Angeles, USA",
      "created_at": "2025-11-09",
      "thumbnail_url": "..."
    }
  ]
}
```

#### 5. Public Library
```
GET /api/public-library?sort=popular&page=1

Response:
{
  "sheets": [
    {
      "sheet_id": "uuid",
      "species_name": "Cattleya mossiae",
      "location": "Miami, USA",
      "creator": "Anonymous",
      "views": 1250,
      "saves": 89,
      "created_at": "2025-10-15"
    }
  ],
  "total_pages": 15
}
```

#### 6. Get Data Sources & Citations
```
GET /api/culture-sheets/{taxonomy_id}/sources

Response:
{
  "species_name": "Cattleya mossiae",
  "total_images": 245,
  "source_breakdown": {
    "sources": [
      {
        "name": "GBIF",
        "url": "https://www.gbif.org",
        "image_count": 180,
        "percentage": 73.5,
        "metadata_completeness": {
          "gps_coordinates": 156,
          "elevation": 142,
          "observation_date": 175
        }
      },
      {
        "name": "iNaturalist",
        "image_count": 65,
        "percentage": 26.5,
        ...
      }
    ]
  }
}
```

---

## 📱 USER INTERFACE SCREENS

### Screen 1: MAIN GENERATOR
**Layout:** Single page, scrollable

**Components:**

1. **Header**
   ```
   🌺 Orchid Culture Sheet Generator
   [My Collection Button] [About Button]
   ```

2. **Species Search** (prominent, top section)
   ```
   ┌─────────────────────────────────────────┐
   │ 🔍 Search for your orchid species...   │
   │ [Autocomplete dropdown as you type]     │
   └─────────────────────────────────────────┘
   
   Example: Try "Cattleya", "Phalaenopsis", "Vanda"
   ```

3. **Location Input** (below species search)
   ```
   Your Growing Location:
   
   ○ Use My GPS Location [📍 Detect] 
   ○ Enter Manually:
     City: [____________]
     Country: [____________]
     
   OR coordinates:
     Latitude: [____] Longitude: [____]
   ```

4. **Customization Options** (collapsible/expandable section)
   ```
   ⚙️ Customize Your Sheet
   
   Sections to Include:
   ☑ Temperature & Climate
   ☑ Light Requirements
   ☑ Watering Schedule
   ☑ Humidity Needs
   ☑ Potting Media & Repotting
   ☑ Fertilizer Program
   
   Artwork Style:
   ○ Scientific Line Drawing (black & white, educational)
   ○ Artistic Watercolor (beautiful, decorative)
   ○ Coloring Page (outline for kids/artists)
   ○ No Artwork
   ```

5. **Generate Button** (big, prominent)
   ```
   ┌─────────────────────────────────────┐
   │  🌸 Generate My Culture Sheet       │
   └─────────────────────────────────────┘
   ```

6. **Loading State** (when generating)
   ```
   🔄 Generating your personalized culture sheet...
   
   ✓ Analyzing 245 wild habitat images
   ✓ Comparing native climate to Los Angeles
   ✓ Generating AI botanical illustration
   ✓ Synthesizing growing recommendations
   ```

---

### Screen 2: GENERATED CULTURE SHEET DISPLAY

**Layout:** Beautiful, printable format

**Header Section:**
```
═══════════════════════════════════════════════════
        Cattleya mossiae Hook.
        (Easter Orchid)
        
[AI-Generated Botanical Illustration - centered, beautiful]

Family: Orchidaceae
Native to: Venezuela (coastal mountains)
Growing Guide for: Los Angeles, California, USA
Generated: November 9, 2025
═══════════════════════════════════════════════════
```

**Action Buttons** (top-right, hidden when printing):
```
[💾 Save to My Collection]  [🖨️ Print]  [📤 Share]  [📊 View Data Sources]
```

**Content Sections** (each with icon):
```
🌡️ TEMPERATURE & CLIMATE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Day: 75-85°F (24-29°C)
Night: 60-65°F (16-18°C)

[Beautiful chart comparing native vs. your climate]

Guidance: Cattleya mossiae is warm-growing...
[Full detailed text here]

☀️ LIGHT REQUIREMENTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Intensity: Bright, filtered light (30-40% shade)
Duration: 12-14 hours
Best Position: East or south window...

💧 WATERING SCHEDULE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Content]

💨 HUMIDITY NEEDS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Content]

🪴 POTTING MEDIA & REPOTTING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Content]

🌱 FERTILIZER PROGRAM
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Content]
```

**Footer:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Data Sources: 245 wild habitat images analyzed
View detailed citations: [Link]

The Orchid Continuum • orchidcontinuum.org
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### Screen 3: MY COLLECTION

**Header:**
```
💾 My Saved Culture Sheets
[← Back to Generator]  [🔍 Search My Collection]
```

**Grid Layout** (responsive - 3 columns desktop, 1 column mobile):
```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ [Thumbnail]     │  │ [Thumbnail]     │  │ [Thumbnail]     │
│ Cattleya        │  │ Phalaenopsis    │  │ Vanda           │
│ mossiae         │  │ amabilis        │  │ coerulea        │
│                 │  │                 │  │                 │
│ Los Angeles, CA │  │ Miami, FL       │  │ Houston, TX     │
│ Saved: Nov 9    │  │ Saved: Nov 5    │  │ Saved: Oct 28   │
│                 │  │                 │  │                 │
│ [View] [Delete] │  │ [View] [Delete] │  │ [View] [Delete] │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

**Empty State** (if no saved sheets):
```
📭 No saved culture sheets yet

Generate your first culture sheet and 
save it to your collection!

[🌸 Create Culture Sheet]
```

---

### Screen 4: PUBLIC LIBRARY

**Header:**
```
🌍 Public Culture Sheet Library
Browse culture sheets shared by the community

Sort by: [🔥 Popular ▼]  [🆕 Recent]  [🔤 Alphabetical]
Search: [_____________]
```

**List View:**
```
┌──────────────────────────────────────────────────┐
│ [Thumb] Cattleya mossiae                         │
│         Miami, Florida, USA                      │
│         👁️ 1,250 views  •  💾 89 saves           │
│         by OrchidLover23  •  Oct 15, 2025        │
│         [📖 View Sheet]  [💾 Save to Collection] │
└──────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────┐
│ [Thumb] Phalaenopsis amabilis                    │
│         Singapore                                │
│         👁️ 892 views  •  💾 45 saves             │
│         [📖 View Sheet]  [💾 Save to Collection] │
└──────────────────────────────────────────────────┘

[Load More...]
```

---

### Screen 5: DATA SOURCES & CITATIONS

**Already designed** - you can reference this existing page:
```
/culture-sheets/{taxonomy_id}/sources
```

Shows:
- Total images analyzed
- Breakdown by data source (GBIF, iNaturalist, etc.)
- Metadata completeness badges
- Links to original sources
- Scientific attribution

---

## 🎨 AI ARTWORK INTEGRATION

**OpenAI DALL-E 3 is available** for generating botanical illustrations

### Artwork Styles:

1. **Scientific Line Drawing**
   - Black & white botanical illustration
   - Educational, precise detail
   - Perfect for printing/studying

2. **Artistic Watercolor**
   - Beautiful colored botanical art
   - Curtis's Botanical Magazine style
   - Decorative, museum-quality

3. **Coloring Page**
   - Bold outlines
   - Kid-friendly
   - Perfect for artists to color

**Backend handles generation** - you'll receive artwork as base64 data URL in API response

---

## 🔧 TECHNICAL REQUIREMENTS

### Progressive Web App (PWA) Features:
```javascript
// manifest.json (you should create this)
{
  "name": "Orchid Culture Sheet Generator",
  "short_name": "Orchid Sheets",
  "description": "Generate personalized orchid growing guides",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#1a1a2e",
  "theme_color": "#9d4edd",
  "icons": [
    {
      "src": "/icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/icon-512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
```

### Service Worker (for offline capability):
```javascript
// Basic caching for offline access
// Cache generated sheets for viewing without internet
```

### Widget Embedding (for Neon One):
```html
<!-- Embeddable iframe code -->
<iframe 
  src="https://orchidcontinuum.org/widget/culture-sheets"
  width="100%"
  height="800px"
  frameborder="0"
  allowfullscreen
></iframe>
```

**Widget-specific features:**
- Compact mode (fits in sidebar)
- No header/footer (just generator)
- PostMessage API for parent communication

---

## 📊 USER SETTINGS & PREFERENCES

**Store in localStorage or user profile:**

```javascript
{
  "default_location": {
    "city": "Los Angeles",
    "country": "USA",
    "latitude": 34.0522,
    "longitude": -118.2437
  },
  "default_sections": [
    "temperature",
    "light", 
    "water",
    "humidity",
    "potting",
    "fertilizer"
  ],
  "preferred_artwork_style": "artistic",
  "theme": "dark",
  "units": "imperial" // or "metric"
}
```

**Settings Panel** (accessible from menu):
```
⚙️ PREFERENCES

Default Location:
  City: [Los Angeles]
  Country: [USA]
  
Default Sections:
  ☑ All sections
  
Preferred Artwork:
  ○ Scientific  ● Artistic  ○ Coloring  ○ None
  
Temperature Units:
  ● Fahrenheit (°F)  ○ Celsius (°C)
  
Theme:
  ● Dark  ○ Light

[Save Preferences]
```

---

## 🎯 KEY FEATURES TO IMPLEMENT

### 1. Autocomplete Species Search
- Debounced search (wait 300ms after typing stops)
- Show genus + species name
- Display common name if available
- Show small thumbnail if available
- Highlight matching text

### 2. GPS Location Detection
- Browser geolocation API
- Reverse geocoding to get city/country name
- Fallback to manual entry if denied

### 3. Climate Comparison Chart
- Interactive line chart (use Chart.js)
- Compare native habitat temps to user location
- Month-by-month overlay
- Responsive, mobile-friendly

### 4. Print Optimization
```css
@media print {
  .no-print { display: none; } /* Hide buttons */
  .page-break { page-break-after: always; }
  body { background: white; color: black; }
}
```

### 5. Share Functionality
- Copy link to clipboard
- Generate shareable URL
- Optional: Social media sharing

### 6. Responsive Design Breakpoints
```
Mobile: < 768px (single column)
Tablet: 768px - 1024px (2 columns)
Desktop: > 1024px (3 columns for grid views)
```

---

## 🚀 MOBILE APP CONSIDERATIONS

### Touch Interactions:
- Minimum 44px tap targets
- Swipe to delete from collection
- Pull-to-refresh on library
- Native-feeling scrolling

### Performance:
- Lazy load images
- Cache API responses
- Compress artwork before saving
- Virtual scrolling for long lists

### Offline Support:
- Cache generated sheets
- Queue saves when offline
- Sync when reconnected

---

## 🎨 EXAMPLE COLOR PALETTE

```css
:root {
  --primary-bg: #1a1a2e;
  --secondary-bg: #16213e;
  --accent-purple: #9d4edd;
  --accent-pink: #e0aaff;
  --text-light: #f8f9fa;
  --text-muted: #adb5bd;
  --success: #28a745;
  --warning: #ffc107;
  --danger: #dc3545;
  --border: #495057;
  
  /* Semantic colors */
  --temperature-color: #ff6b6b;
  --light-color: #ffd93d;
  --water-color: #6bcbff;
  --humidity-color: #a8dadc;
  --potting-color: #8b4513;
  --fertilizer-color: #90ee90;
}
```

---

## 📝 FORM VALIDATION

### Species Search:
- ✅ Must select from autocomplete (not free text)
- ✅ Show error if invalid species

### Location:
- ✅ Either GPS OR manual entry required
- ✅ Validate latitude (-90 to 90)
- ✅ Validate longitude (-180 to 180)
- ✅ City/country if manual

### Generation:
- ✅ At least one section selected
- ✅ Disable button while generating
- ✅ Show loading state with progress

---

## 🔒 SECURITY & PRIVACY

- No passwords stored (use session tokens if auth needed)
- CORS already configured on backend
- Sanitize all user inputs
- Don't expose API keys in frontend
- HTTPS only for production

---

## 📚 LIBRARIES YOU SHOULD USE

**Already Available:**
- Bootstrap 5 (UI framework)
- Feather Icons (icon system)
- Chart.js (for climate charts)

**Recommended Additions:**
- Axios or Fetch (API calls)
- Lodash (debounce for search)
- Date-fns (date formatting)
- FileSaver.js (for downloads)

---

## 🎯 SUCCESS METRICS

**What makes this successful:**
1. ✅ User can generate sheet in < 2 minutes
2. ✅ Mobile-responsive (works on all devices)
3. ✅ Artwork loads and displays beautifully
4. ✅ Climate charts are clear and informative
5. ✅ Print output looks professional
6. ✅ Can save and recall sheets easily
7. ✅ Works offline after first visit (PWA)
8. ✅ Embeddable in Neon One widget area

---

## 🚢 DELIVERABLES

Please provide:

1. **HTML/CSS/JavaScript files** for all screens
2. **manifest.json** for PWA
3. **Service worker** (basic caching)
4. **Widget embed version** (iframe-friendly)
5. **README** with:
   - How to integrate with backend API
   - How to customize colors/branding
   - How to embed as widget
   - Dependencies needed

---

## 💬 QUESTIONS FOR FAMOUS AI

If anything is unclear, please ask:
- What specific API endpoints do you need?
- What data format do you prefer?
- Any specific JavaScript framework preference?
- Accessibility requirements?
- Browser compatibility targets?

---

## 🎨 DESIGN INSPIRATION

**Style References:**
- Scientific: Curtis's Botanical Magazine illustrations
- Modern: Minimal, clean interfaces like Notion or Linear
- Botanical: Elegant, nature-inspired like Atlas Obscura
- Dark theme: GitHub dark mode, VS Code dark theme

**User Flow:**
Think of it like:
1. Google search (simple, powerful search box)
2. → Weather app (location-aware, clear data visualization)
3. → Recipe site (printable, save favorites, beautiful presentation)

---

## ✅ FINAL CHECKLIST

Before submitting, ensure:
- [ ] All 5 screens designed
- [ ] Mobile responsive (test on phone)
- [ ] Print-friendly CSS
- [ ] API integration documented
- [ ] Loading states for all async operations
- [ ] Error handling (network failures, invalid inputs)
- [ ] Accessibility (ARIA labels, keyboard navigation)
- [ ] PWA manifest included
- [ ] Widget embed version works
- [ ] Beautiful artwork display
- [ ] Climate charts interactive
- [ ] Save/recall functionality works

---

**Questions? Need clarification on any feature? Ask!**

This is your complete specification. Build something beautiful! 🌺
