# ORCHID Continuum Voice Guidelines (FCOS Voice)

**Licensed to FCOS (501(c)(3)) for nonprofit use**

This voice guide defines the FCOS voice: scientific, whimsical, local, humorous, smart, trauma-informed, caring, polite, and community-focused. FCOS branding (colors) applied via design tokens—**no visible organization names or logos**.

---

## FCOS Voice Characteristics

**Core Traits:**
- **Scientific**: Evidence-based, accurate botanical information
- **Whimsical**: Playful, light touches (emojis, friendly phrasing)
- **Local**: Community-oriented, accessible to all knowledge levels
- **Humorous**: Gentle humor, never at user's expense
- **Smart**: Respect user intelligence, provide depth when relevant
- **Trauma-Informed**: No guilt, shame, or pressure; always supportive
- **Caring**: Empathetic, patient, helpful guidance
- **Polite**: Respectful, inclusive language
- **Community-Focused**: "We" language, collective learning

---

## BTROM Implementation (How We Apply FCOS Voice)

### 1. **Behavioral** - Guide Action
- Every widget has one clear primary action
- Button labels start with verbs: "Search orchids", "Show bloom pattern", "Try another quiz"
- Use imperative mood for instructions: "Select a genus", "Enter plant names"
- Provide clear next steps after errors or empty states

**Examples:**
- ✅ "Search orchids" (not "Search")
- ✅ "Load new question" (not "Next")
- ✅ "Try another orchid" (not "Refresh")

---

### 2. **Transparent** - Plain Language
- Show system status clearly: "Loading...", "Loaded ✓"
- When AI is paused: "AI is paused to save nonprofit costs. You can still browse."
- Mark demo data: "⚠️ Demo data - actual bloom times may vary"
- Use 6th–8th grade reading level for public widgets
- No jargon unless contextually necessary

**Examples:**
- ✅ "We couldn't reach the database. Try again soon." (not "API Error 500")
- ✅ "This uses sample data." (not "Heuristic fallback mode engaged")
- ✅ "Searching taxonomy..." (not "Querying orchid_taxonomy table")

---

### 3. **Respectful** - Positive & Inclusive
- Never blame the user: "No matches found" (not "You entered an invalid name")
- Assume good intent; provide helpful guidance
- Use gender-neutral, accessible language
- Science-first approach; educational, not preachy
- Celebrate small wins: "✓ Matched 8 of 10 plants"

**Examples:**
- ✅ "No orchids found for this theme yet." (not "Search failed")
- ✅ "Please enter at least one plant name." (not "Error: Empty input")
- ✅ "Great! Let's find the next orchid." (not "Correct! You win!")

---

### 4. **Outcome-Oriented** - Clear Goals
- One primary goal per widget (search, quiz, compare, link)
- Short labels: "Genus", "Pollinator", "Distribution"
- Helpful empty states: Show what the user should do next
- Success states: Confirm completion without excessive celebration

**Examples:**
- ✅ "Select a genus to see bloom patterns" (empty state)
- ✅ "✓ Found 12 orchids" (success)
- ✅ "Matched 3 of 5 plants" (partial success)

---

### 5. **Minimalist** - Concise & Scannable
- Short sentences (avg 10-15 words)
- One idea per sentence
- Use bullet points for lists
- Avoid redundant phrases: "Please note that" → just state the fact
- Icons > words where clear (🔍, ✓, ⚠️)

**Examples:**
- ✅ "Bloom pattern for Phalaenopsis" (not "This chart shows the seasonal blooming patterns...")
- ✅ "⚠️ API offline. Try again soon." (not "We are currently experiencing technical difficulties...")

---

## UI Copy Patterns

### Button Labels
- **Primary actions:** "Search orchids", "Show bloom data", "Reveal answer", "Match taxonomy"
- **Secondary actions:** "New orchid", "Next question", "Try again"
- **Destructive actions:** "Remove", "Clear list"

### Status Messages
- **Loading:** "🌸 Loading...", "🔍 Searching...", "🌍 Fetching data..."
- **Success:** "✓ Loaded", "✓ Found 12 matches", "✓ Resolved 8 plants"
- **Empty:** "No results yet. Try searching!", "Your collection is empty. Add your first orchid!"

### Error Banners
- **Offline:** "⚠️ Database offline. Try again in a moment."
- **No matches:** "No orchids found for this search."
- **Missing config:** "⚠️ Please configure BASE_URL in widget settings."
- **API failure:** "We couldn't load this data. Please try again."

### Educational Notes
- **Demo data:** "⚠️ Demo data - actual values may vary"
- **AI paused:** "ℹ️ AI is paused to save nonprofit costs. Core features still work!"
- **Beta feature:** "🧪 New feature - feedback welcome!"

### Tooltips & Help Text
- Keep under 10 words
- Use sentence fragments: "Search by name or genus"
- Provide examples: "Example: Phalaenopsis amabilis"

---

## Brand Expression Rules

### ✅ DO
- Use consistent colors (via CSS tokens)
- Apply standard spacing, radius, shadows
- Maintain friendly, educational tone
- Show license in code comments only

### ❌ DON'T
- Add visible "FCOS" text, logos, or watermarks
- Use organizational jargon in UI
- Assume technical knowledge
- Blame users for errors

---

## License Notice Placement

**Code comments only:**
```html
<!-- 
  ORCHID Continuum — Licensed to FCOS (501(c)(3)) for nonprofit use.
  FCOS branding (colors) applied via design tokens.
-->
```

**Ownership:** ORCHID Continuum and all widgets remain property of the original creator. FCOS holds a license to use, not ownership.

**Never in visible UI.**

---

## Accessibility Notes

- All interactive elements have clear `:focus-visible` outlines
- Color contrast meets WCAG AA (4.5:1 for text)
- Use `aria-label` for icon-only buttons
- Provide text alternatives for loading states

---

**Summary:** Be helpful, honest, and clear. Guide users to success. Keep the UI organization-agnostic—brand lives in the design tokens, not the text.
