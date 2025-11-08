# Culture Sheet Widget - Frontend Build Request for Famous AI

## Project Overview
Build a beautiful, embeddable widget that generates **location-specific orchid culture sheets** by merging Baker methodology with AOS data, adapted to the user's geographic location and climate.

## What Already Exists (Backend - 100% Complete)

### API Endpoints (Ready to Use):
1. **GET `/culture/species`** - Returns list of available orchid species
2. **POST `/culture/generate`** - Generates custom culture sheet
   - Input: `{"species": "Phalaenopsis", "location": {"city": "San Luis Obispo", "state": "CA", "lat": 35.28, "lon": -120.66}}`
   - Output: Complete culture sheet with Baker data, AOS data, location adaptations, photoperiod calendar, expert comparison
3. **GET `/culture/demo`** - Demo culture sheet (for testing)

### Backend Files (Attached):
- `location_based_culture_system.py` - Core system (806 lines)
- `aos_baker_culture_routes.py` - API routes (158 lines)
- `baker_extrapolation_system.py` - Data extrapolation (262 lines)

## What You Need to Build (Frontend Widget)

### Widget Requirements:

#### 1. **User Interface Design**
- **FCOS purple/lavender color scheme** (#7B2CBF, #9D4EDD, #E0AAFF)
- Beautiful, modern design with smooth animations
- Responsive (works on mobile, tablet, desktop)
- Embeddable in Neon One website via iframe

#### 2. **Widget Flow (3 Steps)**

**Step 1: Select Orchid Species**
- Dropdown populated from `/culture/species` API
- Search/filter capability
- Show genus name for clarity

**Step 2: Enter Location** (with smart defaults)
- Auto-detect user location (browser geolocation API)
- OR manual entry: City, State, Zip
- Show detected location for confirmation
- Calculate lat/lon from city/zip (use geocoding)

**Step 3: Generate & Display Culture Sheet**
- Call `/culture/generate` API with species + location
- Beautiful display of results with sections:
  - **Orchid Info** (species name, native habitat, growth habit)
  - **Your Location Climate** (temp ranges, humidity, photoperiod)
  - **Baker's Recommendations** (original expert advice)
  - **AOS Recommendations** (American Orchid Society advice)
  - **Expert Comparison** (show differences/agreements between Baker & AOS)
  - **Location-Specific Adaptations** (how to adjust for YOUR climate)
  - **Monthly Calendar** (what to do each month in YOUR location)
  - **Watering Schedule** (adapted to YOUR humidity/temp)
  - **Light Requirements** (adapted to YOUR photoperiod)

#### 3. **Interactive Features**
- **Toggle between Baker vs AOS** - Show differences side-by-side
- **Monthly calendar view** - Visual calendar with care tasks
- **Download PDF** - Export culture sheet as PDF
- **Print-friendly** - CSS print styles
- **Share link** - Generate shareable URL with species+location

#### 4. **Weather Widget Integration** (Bonus)
- Pull current weather for user's location
- Show how current conditions compare to ideal
- Alerts: "Too dry today - water extra" or "Perfect humidity!"

#### 5. **Neon One Integration** (Future)
- Save culture sheets to member profile
- Track which orchids member is growing
- Monthly email reminders based on calendar

## Technical Specs

### Frontend Stack (Your Choice):
- **Vanilla HTML/CSS/JS** (easiest to embed)
- **React** (if you prefer - we can build/bundle)
- **Vue** (also fine)

### Files to Create:
1. `culture_sheet_widget.html` - Main widget file
2. `culture_sheet_widget.css` - Styles (FCOS purple theme)
3. `culture_sheet_widget.js` - Logic (API calls, interactivity)
4. `culture_sheet_embed.html` - Iframe embed code for Neon One

### API Integration Example:
```javascript
// Fetch available species
fetch('https://workspace.fcospresident.repl.co/culture/species')
  .then(res => res.json())
  .then(data => {
    // Populate dropdown with data.available_species
  });

// Generate culture sheet
fetch('https://workspace.fcospresident.repl.co/culture/generate', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    species: 'Phalaenopsis',
    location: {
      city: 'San Luis Obispo',
      state: 'CA',
      lat: 35.28,
      lon: -120.66
    }
  })
})
  .then(res => res.json())
  .then(cultureSheet => {
    // Display culture sheet beautifully
  });
```

## Design Inspiration

### Layout Structure:
```
┌─────────────────────────────────────────────┐
│  🌺 Custom Orchid Culture Sheet Generator   │
│                                             │
│  Step 1: Select Your Orchid                │
│  [Dropdown: Choose species ▼]              │
│                                             │
│  Step 2: Enter Your Location               │
│  [Auto-detected: San Luis Obispo, CA] Edit │
│                                             │
│  [Generate My Culture Sheet]               │
└─────────────────────────────────────────────┘

After generation:
┌─────────────────────────────────────────────┐
│  Culture Sheet: Phalaenopsis                │
│  Location: San Luis Obispo, CA              │
│                                             │
│  📊 Your Climate vs Ideal                   │
│  ├─ Temperature: 65-75°F (Ideal: 70-85°F)  │
│  ├─ Humidity: 45% (Ideal: 50-70%)          │
│  └─ Sunlight: 12.5 hrs (Ideal: 12-14 hrs)  │
│                                             │
│  👨‍🌾 Expert Recommendations                  │
│  [Toggle: Baker | AOS | Both]               │
│                                             │
│  📅 Your Monthly Care Calendar              │
│  [Jan] [Feb] [Mar] ... [Dec]                │
│                                             │
│  [Download PDF] [Print] [Share]             │
└─────────────────────────────────────────────┘
```

### Color Palette (FCOS Purple):
- Primary: #7B2CBF (deep purple)
- Secondary: #9D4EDD (medium purple)
- Accent: #E0AAFF (light lavender)
- Background: #F8F7FF (very light purple)
- Text: #2D1B4E (dark purple)

## Testing Instructions

1. Test with these species (known to have Baker + AOS data):
   - Phalaenopsis
   - Cattleya
   - Dendrobium
   - Paphiopedilum

2. Test with these locations:
   - San Luis Obispo, CA (35.28, -120.66)
   - Miami, FL (25.76, -80.19) - tropical
   - Seattle, WA (47.60, -122.33) - cool/humid
   - Phoenix, AZ (33.45, -112.07) - hot/dry

3. Verify expert comparison shows differences between Baker and AOS

4. Test download/print functionality

## Deliverables

Please create and send back:
1. `culture_sheet_widget.html` - Complete standalone widget
2. `culture_sheet_widget.css` - Styles
3. `culture_sheet_widget.js` - JavaScript
4. `culture_sheet_embed.html` - Iframe embed code
5. `WIDGET_DEMO_LINK.txt` - Link to live demo on your end
6. Screenshots of the finished widget

## Questions?

The backend is 100% complete and tested. You have full creative freedom on the frontend design - just follow the FCOS purple color scheme and make it beautiful and user-friendly!

The goal: A member visits FCOS website, enters their orchid + location, and gets a personalized culture sheet adapted to their exact climate. Magic! 🌺

---
**Priority:** Medium (no rush, but this is a high-value feature)
**Estimated Time:** 4-6 hours for a polished widget
**Backend Status:** ✅ Complete and ready
