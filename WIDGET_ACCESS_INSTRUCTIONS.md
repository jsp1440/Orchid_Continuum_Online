# 🌺 How to Access the BloomBuilder Widget

## Quick Start (2 Steps)

### Step 1: Start the Server
Click the **"Run"** button at the top of your Replit workspace.

You'll see output like:
```
🌺 BloomBuilder - The Orchid Continuum
Widget URL: http://0.0.0.0:5000/widget
API Docs: http://0.0.0.0:5000/bloombuilder
Running on http://127.0.0.1:5000
```

### Step 2: Open the Widget
Once the server is running, click this link in the Replit webview:
**http://0.0.0.0:5000/widget**

Or open in a new browser tab:
**http://localhost:5000/widget**

## What You'll See

1. **BloomBuilder Widget Card**
   - Orchid Continuum logo
   - "BloomBuilder: Continue the Sequence — Build Your Bloom"
   
2. **Click to Expand**
   - Opens full-page modal with Famous AI's beautiful design
   
3. **Species Selection**
   - Grid of 10 REAL orchid species from your database:
     - Kovach's Phragmipedium
     - Crimson Cattleya
     - Pink Lady's Slipper
     - White Bog Orchid
     - Water-Spider Orchid
     - Vanilla Vanilla planifolia
     - And 4 more!

## How It Works

```
React UI (Famous AI) 
    ↓
Flask Backend (/bloombuilder/api/*)
    ↓
PostgreSQL Database
    ↓
Returns Real Orchid Data
```

## Available Endpoints

- **Widget**: `/widget` - React app
- **Species**: `/bloombuilder/api/species/all` - Get all species
- **Images**: `/bloombuilder/api/images/{id}` - Herbarium, plates, photos
- **Traits**: `/bloombuilder/api/traits/{id}` - EOL TraitBank data
- **Backend Dashboard**: `/bloombuilder` - Flask template interface

## Troubleshooting

### "404 Error"
- ✅ **FIXED!** Widget route added to main app.py
- Make sure server is running (click "Run" button)

### "Cannot connect"
- Wait 5-10 seconds after clicking "Run" for server to start
- Check console output for "Running on http://127.0.0.1:5000"

### "No species showing"
- Database connection verified ✅
- API returns 10 species ✅
- Check browser console (F12) for any errors

## Files Modified

- `app.py` - Added `/widget` route (lines 527-538)
- `static/bloombuilder_app/` - React build output
- `bloombuilder_frontend/` - Source React code

## Next Steps

The species selection is working! Next phases to integrate:
1. **Image Gallery** - Connect to `/bloombuilder/api/images/{id}`
2. **Workbench** - Interactive trait toggles
3. **Save & Export** - PNG/PDF export with acknowledgments

---

**Status**: ✅ Integration complete and tested
**Your Action**: Click "Run" → Open `/widget` → Enjoy! 🌺
