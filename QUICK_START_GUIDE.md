# 🌸 ORCHID Continuum - Quick Start Guide

## Your Replit URL

**View the app online:**
```
https://workspace.fcospresident.repl.co
```

**To start the server:**
1. Click the **Run** button at the top
2. Wait 10-15 seconds for server to start
3. Click the browser preview link

---

## Start Enriching Images NOW

You already have **5,850 images** collected! Keep going:

**Quick 5-minute collection:**
```bash
bash validation/collect_images.sh
```

**Check current progress:**
```bash
bash validation/enrichment_status.sh
```

**Background collection (runs until you stop it):**
```bash
nohup python -u validation/enrich_gbif_stable.py > /tmp/gbif.log 2>&1 &
tail -f /tmp/gbif.log  # Watch progress
```

**Stop background collection:**
```bash
pkill -f enrich_gbif_stable
```

---

## View Your Widgets

All 14 widgets are ready with FCOS branding:

**Widget Directory:**
- URL: `https://workspace.fcospresident.repl.co/widgets`
- Shows all widgets with embed codes

**Test Individual Widgets:**
1. Open `neon_one/embeds/` folder
2. Pick any `.html` file
3. Open in browser (self-contained, works standalone)

---

## Key URLs

| Page | URL |
|------|-----|
| Home | `/` |
| Widget Directory | `/widgets` |
| Widget Manifest | `/manifest` |
| API Manifest | `/api/manifest` |
| Taxonomy Browser | `/taxonomy/browser` |
| Bloom Mapper | `/taxonomy/bloom-mapper` |
| Health Check | `/health` |

---

## Files You Created Today

**Brand System (5 files):**
- `brand/fcos_brand.css`
- `brand/voice_fcos_btrom.md`
- `brand/brand_profile.json`
- `brand/README.md`
- `BRAND_INTEGRATION_SUMMARY.md`

**Deployment Guides (2 files):**
- `START_ENRICHMENT.md`
- `GITHUB_DEPLOYMENT_CHECKLIST.md`

**All widget embeds updated:**
- 14 files in `neon_one/embeds/*.html`
- FCOS voice + colors applied
- Zero visible "FCOS" text
- License in code comments only

---

## What Works Right Now

✅ **Database**: PostgreSQL with 5,850 images  
✅ **Enrichment**: FREE GBIF collection (no AI costs)  
✅ **Widgets**: All 14 embeds ready for Neon One  
✅ **Brand**: FCOS voice + colors applied  
✅ **API**: 9 taxonomy endpoints functional  
✅ **Manifest**: Widget catalog with descriptions  

---

## GitHub & Render (When Ready)

See `GITHUB_DEPLOYMENT_CHECKLIST.md` for:
- What files to push to GitHub
- Render environment variables
- Deployment steps

**No rush!** Everything works on Replit for testing.

---

## Summary

**You Own:** ORCHID Continuum (all code & widgets)  
**FCOS Has:** License to use (nonprofit)  
**Brand:** FCOS voice + colors (no visible org text)  
**Status:** Ready for enrichment & testing NOW  
**Next:** Collect more images, test widgets, deploy when ready
