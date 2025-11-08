# Widget Manifest System - Testing Guide

## Quick Test Commands

### Test the JSON API endpoint:
```bash
curl http://localhost:5000/api/manifest
```

### Test the human-readable dashboard:
```bash
# Open in browser:
http://localhost:5000/manifest
```

### Test helper functions in Python:
```python
from app.manifest import is_widget_active, active_widgets_for

# Check if a widget is active
is_widget_active("Orchid of the Day")  # Returns: True

# Get all active widgets for a page
widgets = active_widgets_for("Home")  
# Returns: [{"name": "Orchid of the Day", ...}, {"name": "Themed Gallery", ...}]
```

## Expected Results

### /api/manifest endpoint returns:
```json
{
  "pages": [...],
  "widgets_flat": [
    {"name": "Orchid of the Day", "type": "Gallery", "delivery": "cdn", "status": "active", ...},
    {"name": "Themed Gallery", "type": "Gallery", "delivery": "cdn", "status": "active", ...},
    ...10 widgets total
  ],
  "errors": []
}
```

### /manifest dashboard shows:
- 5 page sections (Home, Explore Orchids, Learn & Play, Member Tools, FCOS Board)
- 10 total widgets with status badges
- Green badges for active/restricted widgets
- Delivery method (CDN vs backend) clearly labeled

## Features

✅ Hot-reload in dev (Replit) - changes to WIDGET_DEPLOYMENT_MANIFEST.json reload automatically
✅ Cached in production - set APP_ENV=prod to enable caching
✅ Safe failures - missing/invalid manifest returns empty list with error message
✅ No dependencies - uses only Python stdlib + Flask

## Integration Example

Other routes can now check widget status:

```python
from app.manifest import is_widget_active

@app.route('/some-widget')
def some_widget():
    if not is_widget_active("Widget Name"):
        return "Widget not deployed", 404
    # ... render widget
```
