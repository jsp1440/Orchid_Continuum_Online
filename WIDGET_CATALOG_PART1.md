# Widget Catalog - Part 1: Educational & Kids Content
**Total Widgets in Platform:** 70+
**This Section:** 15 widgets

---

## 1. FCOS Judge Widget (PWA)
**File:** `templates/widgets/fcos_judge.html`
**Route:** `/fcos-judge/`
**Status:** ✅ Production-ready standalone PWA

**What it does:**
Mobile-first orchid flower judging tool with OCR, AI analysis, symmetry scoring, and certificate generation. Used by Florida Crown Orchid Society judges.

**Features:**
- Camera integration with OCR text extraction
- AI-powered flower analysis (OpenAI Vision API)
- Automated symmetry scoring
- PDF certificate generation
- Offline-capable (PWA)

**Deployment:** Standalone page, can be embedded via iframe
**AI Cost:** ~$0.01 per analysis (guarded by ORCHID_AI_ENABLED flag)

---

## 2. Orchid Bingo Widget
**File:** `templates/widgets/orchid_bingo.html`
**Route:** `/widgets/orchid-bingo/`
**Status:** ✅ Ready for kids' programs

**What it does:**
Interactive bingo game for children learning orchid identification. Features auto-generated bingo cards with orchid images.

**Features:**
- Random bingo card generation
- Image-based squares (orchid photos)
- Click-to-mark interaction
- Win detection
- Score tracking (local storage)

**Deployment:** Embeddable widget, works standalone
**AI Cost:** FREE - no AI required

---

## 3. Orchid Memory Game
**File:** `templates/widgets/orchid_memory_game.html`
**Route:** `/widgets/orchid-memory/`
**Status:** ✅ Ready for educational programs

**What it does:**
Matching card game using orchid images to teach species recognition and memory skills.

**Features:**
- Flip-card animation
- Matching detection
- Timer and score tracking
- Difficulty levels (4x4, 6x6 grids)
- Educational content on match

**Deployment:** Standalone widget page
**AI Cost:** FREE

---

## 4. Orchid Trivia Widget
**File:** `templates/widgets/orchid_trivia_widget.html`
**Route:** `/widgets/orchid-trivia/`
**Status:** ✅ Production-ready quiz system

**What it does:**
Multiple-choice trivia game with 50+ questions about orchid biology, history, and conservation.

**Features:**
- Question randomization
- Score tracking
- Difficulty progression
- Educational explanations
- Leaderboard (if enabled)

**Deployment:** Embeddable widget
**AI Cost:** FREE - questions hardcoded

---

## 5. Philosophy Quiz Widget
**File:** `templates/widgets/philosophy_quiz.html`
**Route:** `/widgets/philosophy-quiz/`
**Status:** ✅ Unique engagement tool

**What it does:**
Personality quiz that matches users to orchid species based on philosophical questions.

**Features:**
- 10-question personality assessment
- Orchid species matching algorithm
- Share results
- Beautiful result cards

**Deployment:** Standalone page, embeddable
**AI Cost:** FREE

---

## 6. Mythology & Orchids Widget
**File:** `templates/widgets/mythology_orchids.html`
**Route:** `/widgets/mythology-orchids/`
**Status:** ✅ Educational content widget

**What it does:**
Explores connections between orchids and Greek/Roman mythology, including Orchis myth origin story.

**Features:**
- Illustrated mythology stories
- Orchid name etymology
- Historical context
- Cultural significance

**Deployment:** Content widget, embeddable
**AI Cost:** FREE - static content

---

## 7. Ethnobotany & Traditional Knowledge Widget
**File:** `templates/widgets/ethnobotany_info.html`
**Route:** `/widgets/ethnobotany/`
**Status:** ✅ Production database-backed

**What it does:**
Displays traditional medicinal uses, indigenous names, and cultural significance of orchids from academic sources.

**Features:**
- Database of traditional uses
- Citation management
- Regional filtering
- Academic source attribution
- Searchable by genus/region

**Database Table:** `ethnobotany_records`
**Deployment:** Responsive widget
**AI Cost:** FREE - database content

---

## 8. Ecosystem Explorer Widget
**File:** `templates/widgets/ecosystem_explorer_widget.html`
**Route:** `/widgets/ecosystem-explorer/`
**Status:** ✅ Interactive educational tool

**What it does:**
Visualizes orchid ecosystem relationships including pollinators, mycorrhizal fungi, and habitat dependencies.

**Features:**
- Interactive ecosystem diagrams
- Species relationship mapping
- Pollinator information
- Conservation context
- Educational overlays

**Deployment:** Standalone widget page
**AI Cost:** FREE

---

## 9. Orchid Anatomy Explorer
**File:** `templates/widgets/orchid_anatomy.html`
**Route:** `/widgets/anatomy/`
**Status:** ✅ Educational visualization

**What it does:**
Interactive diagram teaching orchid flower structure and terminology.

**Features:**
- Clickable anatomy parts
- Definitions and descriptions
- Zoom functionality
- Multiple species examples

**Deployment:** Educational widget
**AI Cost:** FREE

---

## 10. Orchid Care Guide Widget
**File:** `templates/widgets/care_guide.html`
**Route:** `/widgets/care-guide/`
**Status:** ✅ Beginner-friendly tool

**What it does:**
Provides species-specific care instructions including light, water, temperature, and humidity requirements.

**Features:**
- Search by species
- Care level indicators
- Troubleshooting tips
- Seasonal adjustments
- Beginner vs. expert modes

**Database:** Pulls from `orchid_record` table
**Deployment:** Embeddable widget
**AI Cost:** FREE - database content

---

## 11. Kids' Coloring Pages
**File:** `templates/widgets/coloring_pages.html`
**Route:** `/widgets/coloring/`
**Status:** ✅ Printable activities

**What it does:**
Generates printable orchid coloring pages with educational captions.

**Features:**
- SVG-based line drawings
- Print optimization
- Educational facts
- Multiple difficulty levels
- Download as PDF

**Deployment:** Activity generator
**AI Cost:** FREE

---

## 12. Orchid Word Search
**File:** `templates/widgets/word_search.html`
**Route:** `/widgets/word-search/`
**Status:** ✅ Educational game

**What it does:**
Auto-generates word search puzzles using orchid terminology and genus names.

**Features:**
- Dynamic puzzle generation
- Difficulty levels
- Printable format
- Answer key
- Educational definitions

**Deployment:** Game widget
**AI Cost:** FREE

---

## 13. Virtual Orchid Garden
**File:** `templates/widgets/virtual_garden.html`
**Route:** `/widgets/virtual-garden/`
**Status:** ✅ Interactive collection builder

**What it does:**
Allows users to "plant" and manage a virtual orchid collection with care reminders.

**Features:**
- Drag-and-drop planting
- Growth simulation
- Care reminder system
- Collection statistics
- Share garden feature

**Storage:** Browser local storage
**Deployment:** Standalone widget
**AI Cost:** FREE

---

## 14. Orchid Name Pronunciation Guide
**File:** `templates/widgets/pronunciation_guide.html`
**Route:** `/widgets/pronunciation/`
**Status:** ✅ Educational tool

**What it does:**
Teaches correct pronunciation of scientific orchid names with phonetic guides.

**Features:**
- Phonetic spelling
- Audio playback (if enabled)
- Etymology explanations
- Common mispronunciations
- Quiz mode

**Deployment:** Educational widget
**AI Cost:** FREE

---

## 15. Orchid Conservation Status Widget
**File:** `templates/widgets/conservation_status.html`
**Route:** `/widgets/conservation/`
**Status:** ✅ Awareness tool

**What it does:**
Displays IUCN conservation status for orchid species with actionable conservation information.

**Features:**
- IUCN Red List integration
- Threat level indicators
- Conservation actions
- Endangered species spotlight
- Geographic distribution maps

**Database:** `orchid_taxonomy` table (conservation_status field)
**Deployment:** Educational widget
**AI Cost:** FREE

---

**End of Part 1**
Next: Part 2 - Gallery & Display Widgets
