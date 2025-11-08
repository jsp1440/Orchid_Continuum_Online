# Orchid Memory Match - Developer Notes

## Current Stack Discovery

### Two Existing Memory Game Systems

**System 1: Simple Memory Match** (Target for upgrade)
- **File**: `orchid_games.py` (Blueprint: `games_bp`)
- **Route**: `/games/memory-match`
- **Template**: `templates/games/memory_match.html`
- **API**: `/games/api/memory-cards`
- **Features**: Basic picture matching, 4x4 grid (8 pairs), vanilla JS
- **Why upgrade this**: Simpler codebase, easier to extend

**System 2: Advanced Memory Game** (Keep as-is)
- **File**: `orchid_memory_game.py` (Blueprint: `orchid_memory_bp`)
- **Routes**: `/games/memory`, `/games/memory/<difficulty>`
- **Templates**: `memory_game.html`, `memory_game_play.html`
- **Features**: 3 difficulty levels, scoring, session tracking
- **Why skip**: Already complex, different architecture

### Backend (Python/Flask)
- **Target File**: `orchid_games.py` - upgrade routes here
- **Database Models**: 
  - `OrchidRecord` - orchid data with photos
  - `GameScore` - leaderboard scores (will add rebus columns)
- **Game Data Source**: PostgreSQL via SQLAlchemy ORM
- **Image Storage**: OrchidRecord.image_url (direct URLs)

### Frontend (Template-based)
- **Stack**: Vanilla JavaScript (no bundler), Bootstrap 5, Feather Icons
- **Game Logic**: Embedded `<script>` in `memory_match.html`
- **Current Class**: `MemoryMatch` with flip/match mechanics
- **Styling**: Bootstrap dark theme + custom animations

### Current Features (memory_match.html)
- Basic picture matching (4x4 grid, 8 pairs)
- Card flip animations
- Move counter
- Match detection
- Win state
- Play again functionality

### Entry Points
- **Game Page**: `/games/memory-match`
- **API Endpoint**: `/games/api/memory-cards`
- **Widget**: `/games/widget/memory` (embeddable version)
- **Leaderboard**: `/games/leaderboard` (shared with other games)

---

## Upgraded Architecture

### New File Structure

```
static/
├── js/
│   └── memory-game/
│       ├── config.js              # Game constants (window globals, no imports)
│       ├── imagePreflight.js      # Image validation
│       ├── triviaBuilder.js       # Trivia card generator
│       ├── rebusGenerator.js      # Rebus puzzle system
│       ├── rebusRenderer.js       # Rebus visual display
│       ├── chatAndGuess.js        # Unified chat/guess UI
│       ├── settingsPanel.js       # Settings modal
│       ├── storageAdapter.js      # localStorage/Replit DB adapter
│       ├── memoryMatchCore.js     # Main game controller (extends existing)
│       └── data/
│           ├── orchid_trivia.json     # Orchid facts database
│           └── rebus_phrases.json     # Generated rebus puzzles
├── images/
│   ├── fcos-logo.png             # FCOS logo for tile backs
│   └── orchid-fallback.jpg       # Placeholder for broken images
└── css/
    └── memory-game.css           # Enhanced game styles

scripts/
└── build-phrases.py              # Content mining for rebus (Python, not Node)

templates/games/
└── memory_match.html             # Upgrade IN-PLACE (not new file)

orchid_games.py                   # Extend with trivia/rebus API routes
models.py                         # Add rebus columns to GameScore model
```

**Key Architectural Decisions:**
1. **No separate template** - Enhance `memory_match.html` in-place
2. **Vanilla JS** - No bundler, use window globals and `<script>` tags
3. **Python build script** - Use `build-phrases.py` not `.mjs` (no Node needed)
4. **Flask data attributes** - Pass config via HTML data-* attributes
5. **Backward compatible** - Existing `/games/memory-match` route unchanged

### Key Components

#### 1. Image Preflight (`imagePreflight.js`)
- Pre-loads all orchid images with 4s timeout
- Replaces failures with `/static/images/orchid-fallback.jpg`
- Shows banner if >10% fail

#### 2. Tile Backs (`memoryMatchCore.js`)
- FCOS logo background (from `VITE_FCOS_LOGO_URL` or `/static/images/fcos-logo.png`)
- Numbered overlay (1-N) for accessibility
- Toggle in settings: "Show Tile Numbers"

#### 3. Settings Panel (`settingsPanel.js`)
- **Storage**: `localStorage['orchid-memory-settings-v4']`
- **Options**:
  - Category filter (All/Species/Hybrids)
  - Game mode (Picture↔Picture or Picture↔Name)
  - Practice mode (10-20s preview)
  - Hints allowed (cap)
  - Show tile numbers
  - Leaderboard opt-in
  - Trivia behavior (Auto 5s or Click-to-dismiss)
  - Rebus difficulty (Easy/Med/Hard/Mixed)
  - Content-derived phrases (ON by default)
  - Guess cooldown (0-10s)

#### 4. Trivia System (`triviaBuilder.js`)
- **Data Model**:
```javascript
{
  id: string,
  imageUrl: string,
  name: string,
  type: 'species' | 'hybrid',
  trivia: {
    commonName?: string,
    originCountries?: string[],
    habitat?: string,
    discovery?: {by, year, notes},
    pollinators?: string[],
    bloomSeason?: string,
    fragrance?: string,
    distribution?: string,
    cultureNotes?: string,
    awards?: string[],
    funFact?: string,
    references?: [{label, url}],
    captionHtml?: string
  }
}
```
- Auto-fallback paragraph if no data
- Modal appears after each match
- Pauses game while open
- 2-paragraph limit

#### 5. Rebus Puzzle System

**Content Mining** (`scripts/build-phrases.py`)
- Scans `content/` directory (articles + glossary if exists)
- Extracts orchid terms, species names, idioms
- Filters 2-6 word phrases with orchid keywords
- Scores & dedupes → `static/js/memory-game/data/rebus_phrases.json`
- Run: `python scripts/build-phrases.py`

**Generator** (`rebusGenerator.js`)
- Loads `rebus_phrases.json`
- Recipes: emoji concat, minus letter, sounds-like, over/under, syllable split
- Output: `{phrase, steps: [{type, emoji, text}]}`
- Function: `generateRebusSet(limit=30, seed='orchid')`

**Renderer** (`rebusRenderer.js`)
- Draws emoji/text grid behind game tiles
- When ≥50% tiles cleared → enable "Guess the Rebus" button
- Visible through transparent matched tiles

#### 6. Chat + Rebus Guess (`chatAndGuess.js`)
- **Single input** with dual purpose:
  - Type normally → sends chat message
  - Prefix `guess:` or `/guess` → rebus guess mode
- **Message types**: chat | system | guess | guess-correct | guess-wrong
- **Guess logic**:
  1. Normalize guess → compare with `currentRebus.phrase`
  2. Correct & unsolved → award 10 bonus points, mark `solvedBy`
  3. Wrong → show feedback, 2s cooldown
- **Modes**:
  - Local: memory-based chat
  - Online: sync via storage adapter
  - AI partner: auto-guess after 2-4s delay

#### 7. Leaderboard (`leaderboard.html` + `orchid_memory_game.py`)
- **New columns**:
  - Rebus Solved (✓)
  - Solver Name
  - Guess Count
- **Sort**: Fastest → Rebus Bonus → Matches
- **Storage**: localStorage or Replit DB

#### 8. Storage Adapter (`storageAdapter.js`)
- **Functions**:
  - `appendChat(roomId, msg)`
  - `updateRoom(room)`
  - `saveLeaderboard(entry)`
- **Backends**: localStorage or Replit DB (`REPLIT_DB_URL`)

### Configuration (`static/js/memory-game/config.js`)

Since we're using vanilla JS (no bundler), configuration is plain objects:

```javascript
// Global config accessible via window.MEMORY_GAME_CONFIG
window.MEMORY_GAME_CONFIG = {
  IMAGE_LOAD_TIMEOUT_MS: 4000,
  HINTS_PER_GAME: 3,
  REBUS_GUESS_UNLOCK_PERCENT: 0.5,
  REBUS_BONUS_POINTS: 10,
  GUESS_COOLDOWN_MS: 2000,
  CHAT_RATE_LIMIT_MS: 1000,
  // Logo can be set via Flask template data-attribute or default
  TILE_BACK_LOGO: document.querySelector('[data-fcos-logo]')?.dataset.fcosLogo 
                  || '/static/images/fcos-logo.png',
  FALLBACK_IMAGE: '/static/images/orchid-fallback.jpg'
};
```

Flask template sets logo URL via data attribute:
```html
<div id="game-root" data-fcos-logo="{{ url_for('static', filename='images/fcos-logo.png') }}">
```

---

## Implementation Phases

### Phase 1: Core Enhancements (Tasks 1-6)
✅ DEV_NOTES.md created
⏳ Image validation + FCOS tile backs
⏳ Settings panel + persistence
⏳ Trivia data model + popup
⏳ Hints + practice mode + accessibility

### Phase 2: Rebus System (Tasks 7-8)
⏳ Content mining script
⏳ Rebus generator + renderer

### Phase 3: Multiplayer (Tasks 9-12)
⏳ Chat + guess unified panel
⏳ Leaderboard upgrades
⏳ Two-player modes
⏳ Storage adapter

### Phase 4: Polish (Tasks 13-14)
⏳ Asset integration (FCOS logo, placeholders)
⏳ E2E testing + acceptance verification

---

## How to Run/Test

### Development
1. **Start Flask server**: `gunicorn --bind 0.0.0.0:5000 --reload main:app`
2. **Access game**: http://localhost:5000/games/memory-match
3. **Build rebus phrases**: `python scripts/build-phrases.py` (when script ready)

### Testing Checklist
- [ ] All tiles load (no blanks)
- [ ] FCOS backs + numbers visible
- [ ] Settings persist across sessions
- [ ] Hints & Practice work
- [ ] Trivia cards appear after matches
- [ ] Tiles disappear → rebus visible
- [ ] "Guess the Rebus" functional via chat
- [ ] Scores update on leaderboard
- [ ] Local + Online + AI modes work
- [ ] Keyboard & screen-reader friendly

### Browser Console Commands
```javascript
// Test settings
localStorage.getItem('orchid-memory-settings-v4')

// Force reset
localStorage.removeItem('orchid-memory-settings-v4')

// Check rebus data
fetch('/static/js/memory-game/data/rebus_phrases.json').then(r=>r.json()).then(console.log)
```

---

## API Extensions

### New Backend Routes (in `orchid_games.py`)

```python
@games_bp.route('/api/orchid-trivia/<int:orchid_id>')
def get_orchid_trivia(orchid_id):
    """Returns enriched trivia for an orchid"""
    
@games_bp.route('/api/rebus-phrases')
def get_rebus_phrases():
    """Returns pre-generated rebus puzzles"""
    
@games_bp.route('/api/save-game-score', methods=['POST'])
def save_game_score():
    """Saves game result with rebus data to leaderboard"""
```

---

## Tech Stack Summary

**Backend**: Python 3.11, Flask, SQLAlchemy, PostgreSQL  
**Frontend**: Vanilla JS, Bootstrap 5, Feather Icons  
**Storage**: localStorage + optional Replit DB  
**Assets**: Direct image URLs + fallback images  
**Build Tools**: Python scripts for content processing (no Node.js needed)  
**Deployment**: Gunicorn on Replit → Render

---

## Notes
- No framework dependencies (React/Vue) - vanilla JS for simplicity
- Backward compatible with existing game routes
- Progressive enhancement - works offline after initial load
- WCAG AA accessible with keyboard navigation & ARIA
