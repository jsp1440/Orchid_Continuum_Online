# ORCHID Continuum Brand System

**FCOS Voice & Branding**

The ORCHID Continuum is **licensed to FCOS (501(c)(3)) for nonprofit use**. Ownership remains with the original creator. This brand system applies the **FCOS voice** (scientific, whimsical, local, humorous, smart, trauma-informed, caring, polite, community-focused) and **FCOS branding** (colors) via design tokens.

---

## Philosophy

1. **No Visible Org Names** - UI remains generic; widgets say "Orchid of the Day", not "FCOS Orchid of the Day"
2. **Token-Based Branding** - Colors, fonts, spacing define the look
3. **License in Code Only** - `<!-- Licensed to FCOS -->` in HTML comments, never displayed
4. **Easy Re-Skinning** - Another society can override tokens with their palette

---

## Files

```
brand/
├── fcos_brand.css              # FCOS design tokens
├── brand_profile.json          # FCOS palette + voice rules
├── brand_profile.neutral.json  # Generic neutral palette
├── voice_fcos_btrom.md         # BTROM voice guidelines
└── README.md                   # This file
```

---

## How Tokens Work

All embeds use CSS custom properties (variables):

```css
:root {
  --brand-bg: #fafafa;
  --brand-surface: #ffffff;
  --brand-text: #1f2937;
  --brand-accent: #3b82f6;
  --radius: 12px;
  --shadow: 0 2px 10px rgba(0,0,0,.06);
  --font-sans: system-ui, sans-serif;
}
```

Widgets reference these variables:

```css
.widget {
  background: var(--brand-surface);
  color: var(--brand-text);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  font-family: var(--font-sans);
}
```

---

## Overriding Tokens (For Other Societies)

### Option 1: Replace `fcos_brand.css`

1. Copy `brand_profile.neutral.json` to `brand_profile.custom.json`
2. Edit color values in `custom.json`
3. Generate new `custom_brand.css` from token values
4. Provide `custom_brand.css` to widget users instead of `fcos_brand.css`

### Option 2: Inline Token Override

Each widget defines fallback tokens in its `<style>` block. To override:

1. Open the widget `.html` file
2. Change the `:root` values in the `<style>` section
3. Deploy as-is (widgets are self-contained)

**Example:**

```html
<style>
  :root {
    --brand-accent: #10b981;  /* Change from blue to green */
    --radius: 8px;            /* Change from 12px to 8px */
  }
  /* Rest of styles... */
</style>
```

---

## Embed Structure

Every embed follows this pattern:

```html
<!-- 
  ORCHID Continuum — Licensed deployment for FCOS (501(c)(3)).
  Branding applied via tokens; UI text remains org-agnostic.
-->
<div id="widget-name" role="region" aria-label="Widget Name">
  <style>
    :root {
      /* Design tokens defined here */
      --brand-accent: #3b82f6;
      --radius: 12px;
      /* ... */
    }
    
    #widget-name {
      background: var(--brand-surface);
      color: var(--brand-text);
      /* ... */
    }
  </style>
  
  <!-- Widget UI (no org name visible) -->
  <h2>🌺 Orchid of the Day</h2>
  <!-- ... -->
</div>

<script>
  // Widget logic
  const CONFIG = {
    BASE_URL: 'https://your-orchid-app.com'  // CHANGE ME
  };
</script>
```

---

## Voice Guidelines (BTROM)

All microcopy follows BTROM principles:

- **Behavioral**: Action-oriented ("Search orchids", "Show bloom pattern")
- **Transparent**: Plain language ("AI is paused to save costs")
- **Respectful**: Positive, inclusive, no blame
- **Outcome-oriented**: One clear goal per widget
- **Minimalist**: Concise, 6th-8th grade reading level

See `voice_fcos_btrom.md` for full guidelines.

---

## License Notice Placement

**Code comments only:**

```html
<!-- ORCHID Continuum — Licensed to FCOS (501(c)(3)) -->
```

**NEVER in visible UI:**
- ❌ "Powered by FCOS"
- ❌ "© FCOS 2025"
- ❌ FCOS logo in widget

---

## Accessibility

All tokens meet WCAG AA contrast requirements:

- Text on background: 4.5:1 minimum
- Large text (18px+): 3:1 minimum
- Interactive elements: clear `:focus-visible` outlines

---

## File Sizes

- Each embed: ~180-220 lines (self-contained)
- No external CSS dependencies
- No build step required

---

## Testing

1. Open any embed `.html` file in a browser
2. Change `:root` token values in DevTools
3. See instant visual changes
4. No rebuild needed

---

## Support

For questions about tokens or re-skinning:
- Check `brand_profile.json` for current values
- See `voice_fcos_btrom.md` for copy guidelines
- All embeds are in `neon_one/embeds/`

**Remember:** Brand lives in the design tokens, not the text. Keep UI org-agnostic!
