# 🌿 Neon One Embed Snippets (copy-paste)

## Orchid-of-the-Day
```html
<div id="orchid-ootd" data-tenant="fcos" data-api-base="https://orchid-api.onrender.com"></div>
<script src="https://cdn.example.org/orchid/widgets/orchidOfTheDay.js" defer></script>
```

## Themed Galleries
```html
<div id="orchid-themed-gallery" data-tenant="fcos" data-theme="cloud-forest" data-api-base="https://orchid-api.onrender.com"></div>
<script src="https://cdn.example.org/orchid/widgets/themedGalleries.js" defer></script>
```

## My Collection
```html
<div id="orchid-my-collection" data-tenant="fcos" data-user="CURRENT_USER_ID" data-api-base="https://orchid-api.onrender.com"></div>
<script src="https://cdn.example.org/orchid/widgets/myCollection.js" defer></script>
```

## Hollywood Blooms
```html
<div id="orchid-hollywood" data-tenant="fcos" data-api-base="https://orchid-api.onrender.com"></div>
<script src="https://cdn.example.org/orchid/widgets/hollywoodBlooms.js" defer></script>
```

## Philosophy Quiz
```html
<div id="orchid-philosophy-quiz" data-tenant="fcos" data-api-base="https://orchid-api.onrender.com"></div>
<script src="https://cdn.example.org/orchid/widgets/philosophyQuiz.js" defer></script>
```

## Setup Instructions

1. **Replace CDN URL**: Change `https://cdn.example.org/orchid` to your actual CDN base URL
2. **Customize data attributes**: Each widget supports custom `data-*` attributes for configuration
3. **Styling**: Widgets inherit your site's CSS - style the container divs as needed

## Widget Options

### ALL WIDGETS (Required)
- `data-api-base`: Your Render API URL (e.g., "https://orchid-api.onrender.com")
  - **IMPORTANT**: This must be set for widgets to work on external sites!
  - Default fallback: "https://orchid-api.onrender.com"

### Orchid of the Day
- `data-tenant`: Organization identifier (default: "fcos")

### Themed Galleries
- `data-theme`: Gallery theme (options: "cloud-forest", "madagascar", "fragrant", "night-blooming")

### My Collection
- `data-user`: User identifier to show their collection

### Hollywood Blooms
- `data-query`: Search query for specific movies/shows

### Philosophy Quiz
- No additional options - automatically loads random quiz

## Technical Details

- **Load Time**: Widgets load asynchronously and won't block page rendering
- **Caching**: Widget files are cached indefinitely (immutable)
- **Cross-Origin**: CORS is configured for `*.neonone.com` and `fcos.org`
- **Fallback**: If widget fails to load, container shows error message

## Example Integration

```html
<!-- Full example for Neon One CMS -->
<div class="orchid-widget-container">
  <h2>Featured Orchid</h2>
  <div id="orchid-ootd" data-tenant="fcos" data-api-base="https://orchid-api.onrender.com"></div>
  <script src="https://your-cdn.com/orchid/widgets/orchidOfTheDay.js" defer></script>
</div>

<style>
.orchid-widget-container {
  max-width: 600px;
  margin: 2rem auto;
  padding: 1rem;
  border: 1px solid #ddd;
  border-radius: 8px;
}
</style>
```
