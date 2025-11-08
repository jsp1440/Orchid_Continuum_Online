# Widget Catalog - Part 2: Gallery & Display Widgets
**Section 2 of 5**

---

## 16. Gallery Hub (Central Dashboard)
**File:** `templates/gallery_hub.html`
**Route:** `/gallery-hub`
**Status:** ✅ Production central navigation

**What it does:**
Central navigation hub for all themed gallery collections with featured orchids and quick access links.

**Features:**
- Grid layout of themed galleries
- Featured orchid rotation
- Search integration
- Collection statistics
- Responsive design

**Deployment:** Main gallery landing page
**AI Cost:** FREE

---

## 17. Thailand Orchids Gallery
**File:** `templates/thailand_orchids.html`
**Route:** `/thailand-orchids`
**Status:** ✅ Geographic collection

**What it does:**
Curated gallery of orchids native to Thailand with cultural context and biodiversity information.

**Features:**
- Geographic filtering
- Native species focus
- Cultural significance notes
- Image grid with lightbox
- Export collection

**Database Query:** 
```python
OrchidRecord.query.filter(
    OrchidRecord.native_habitat.like('%Thailand%')
).all()
```

**Deployment:** Themed gallery page
**AI Cost:** FREE

---

## 18. Madagascar Orchids Gallery
**File:** `templates/madagascar_orchids.html`
**Route:** `/madagascar-orchids`
**Status:** ✅ Endemic species showcase

**What it does:**
Features orchids endemic to Madagascar with conservation status and biodiversity hotspot information.

**Features:**
- Endemic species highlighting
- Conservation status badges
- Biogeography education
- Threatened species awareness
- Research citations

**Deployment:** Conservation-focused gallery
**AI Cost:** FREE

---

## 19. Fragrant Orchids Gallery
**File:** `templates/fragrant_orchids.html`
**Route:** `/fragrant-orchids`
**Status:** ✅ Sensory-themed collection

**What it does:**
Showcases orchid species known for fragrance with scent descriptions and blooming information.

**Features:**
- Fragrance intensity ratings
- Scent descriptions
- Bloom time calendar
- Pollinator attraction info
- User favorites

**Database Field:** `fragrance_description`
**Deployment:** Themed gallery
**AI Cost:** FREE

---

## 20. Night-Blooming Orchids Gallery
**File:** `templates/night_blooming_orchids.html`
**Route:** `/night-blooming-orchids`
**Status:** ✅ Specialty collection

**What it does:**
Features orchids that bloom at night with pollination ecology and cultural significance.

**Features:**
- Nocturnal blooming calendar
- Moth pollination info
- Photography tips
- Cultural myths
- Rare species focus

**Deployment:** Educational gallery
**AI Cost:** FREE

---

## 21. Featured Orchids Display
**File:** `templates/featured_orchids.html`
**Route:** `/featured`
**Status:** ✅ Curated highlights

**What it does:**
Rotating display of hand-selected exceptional orchids with detailed descriptions.

**Features:**
- Admin-curated selection
- High-quality images
- Extended descriptions
- Expert commentary
- Share functionality

**Database Field:** `featured = TRUE`
**Deployment:** Homepage widget or standalone
**AI Cost:** FREE (or AI-enhanced descriptions if enabled)

---

## 22. Random Orchid of the Day
**File:** `templates/widgets/orchid_of_the_day.html`
**Route:** `/widgets/orchid-of-the-day/`
**Status:** ✅ Daily engagement widget

**What it does:**
Displays a randomly selected orchid each day with educational content and care tips.

**Features:**
- Daily rotation (seed-based)
- Social sharing
- Educational facts
- Care summary
- Archive of past featured orchids

**Database Query:**
```python
OrchidRecord.query.order_by(func.random()).first()
```

**Deployment:** Homepage widget, embeddable
**AI Cost:** FREE

---

## 23. Search Results Gallery
**File:** `templates/search_results.html`
**Route:** `/search`
**Status:** ✅ Advanced search interface

**What it does:**
Displays orchid search results with filtering, sorting, and advanced query options.

**Features:**
- Full-text search
- Multi-field filtering
- Sort options
- Pagination
- Save search queries
- Export results

**Search Fields:** genus, species, common_name, native_habitat
**Deployment:** Main search endpoint
**AI Cost:** FREE

---

## 24. My Collection Widget
**File:** `templates/widgets/my_collection.html`
**Route:** `/widgets/my-collection/`
**Status:** ✅ User collection manager

**What it does:**
Allows logged-in users to build and manage personal orchid collections with notes and care logs.

**Features:**
- Add to collection
- Care journal
- Blooming calendar
- Photo uploads
- Collection statistics
- Share collection publicly

**Database Table:** `user_collections`
**Deployment:** User dashboard widget
**AI Cost:** FREE

---

## 25. Comparison Tool Widget
**File:** `templates/widgets/comparison_tool.html`
**Route:** `/widgets/compare/`
**Status:** ✅ Side-by-side analysis

**What it does:**
Compares up to 4 orchid species side-by-side with detailed characteristic analysis.

**Features:**
- Multi-species selection
- Side-by-side image comparison
- Characteristic table
- Care requirement comparison
- EXIF data analysis (if available)
- Export comparison

**Deployment:** Research tool widget
**AI Cost:** FREE (or AI-enhanced if enabled)

---

## 26. Image Gallery with Lightbox
**File:** `templates/widgets/image_lightbox.html`
**Route:** Various (component)
**Status:** ✅ Reusable component

**What it does:**
Responsive image gallery with full-screen lightbox, zoom, and navigation.

**Features:**
- Touch-friendly swipe
- Zoom controls
- Keyboard navigation
- Download option
- Share functionality
- EXIF display

**Deployment:** Component used in multiple galleries
**AI Cost:** FREE

---

## 27. Thumbnail Grid Widget
**File:** `templates/widgets/thumbnail_grid.html`
**Route:** Component
**Status:** ✅ Reusable layout

**What it does:**
Masonry-style responsive grid for orchid image thumbnails with lazy loading.

**Features:**
- Lazy loading
- Responsive breakpoints
- Masonry layout
- Infinite scroll
- Click to expand

**Deployment:** Used across gallery pages
**AI Cost:** FREE

---

## 28. Slideshow Widget
**File:** `templates/widgets/slideshow.html`
**Route:** Component
**Status:** ✅ Auto-advancing display

**What it does:**
Auto-advancing slideshow of orchid images with customizable timing and transitions.

**Features:**
- Auto-advance (configurable)
- Manual controls
- Transition effects
- Caption overlay
- Pause on hover

**Deployment:** Homepage hero, gallery pages
**AI Cost:** FREE

---

## 29. Hollywood Blooms Gallery
**File:** `templates/widgets/hollywood_blooms.html`
**Route:** `/widgets/hollywood-blooms/`
**Status:** ✅ Celebrity orchid collection

**What it does:**
Showcases orchids named after celebrities and those featured in movies/TV shows.

**Features:**
- Celebrity orchid registry
- Movie/TV appearances
- Pop culture references
- Behind-the-scenes stories
- Photo galleries

**Deployment:** Entertainment-focused widget
**AI Cost:** FREE

---

## 30. Award-Winning Orchids
**File:** `templates/widgets/award_winners.html`
**Route:** `/widgets/award-winners/`
**Status:** ✅ Excellence showcase

**What it does:**
Features orchids that have won AOS (American Orchid Society) or other prestigious awards.

**Features:**
- Award badges
- Judging scores
- Award history
- Grower information
- High-quality images

**Database Field:** `awards` (JSON)
**Deployment:** Prestige collection
**AI Cost:** FREE

---

**End of Part 2**
Next: Part 3 - Research & Data Widgets
