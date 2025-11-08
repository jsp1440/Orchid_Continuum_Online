# GitHub & Render Deployment Checklist

## ✅ Your Current Status

**What's Working on Replit RIGHT NOW:**
- 📊 Database: 5,850 images across 155 species
- 🌸 Enrichment: FREE GBIF collection working
- 🎨 Widgets: All 14 embeds with FCOS branding
- 🎯 Brand: Complete FCOS voice + color system

---

## When You're Ready for GitHub & Render

### Files to Include in GitHub Repository

#### Core Application
```
✅ app.py
✅ main.py  
✅ models.py
✅ parentage_models.py
✅ requirements.txt
✅ init.sh
✅ render.yaml
```

#### Widget System (14 Embeds + Docs)
```
✅ neon_one/embeds/admin_dashboard.html
✅ neon_one/embeds/admin_widget_health.html
✅ neon_one/embeds/explore_bloom_mapper.html
✅ neon_one/embeds/explore_gbif_explorer.html
✅ neon_one/embeds/explore_taxonomy_browser.html
✅ neon_one/embeds/home_orchid_of_the_day.html
✅ neon_one/embeds/home_themed_gallery.html
✅ neon_one/embeds/learnplay_bingo.html
✅ neon_one/embeds/learnplay_mystery_orchid_quiz.html
✅ neon_one/embeds/learnplay_philosophy_quiz.html
✅ neon_one/embeds/learnplay_pollinator_game.html
✅ neon_one/embeds/member_habitat_weather.html
✅ neon_one/embeds/member_my_collection.html
✅ neon_one/embeds/membertools_linker.html
✅ neon_one/EMBED_DIRECTORY.html
✅ neon_one/README_NEON_ONE.md
✅ WIDGET_DEPLOYMENT_MANIFEST.json
```

#### Brand System
```
✅ brand/fcos_brand.css
✅ brand/voice_fcos_btrom.md
✅ brand/brand_profile.json
✅ brand/brand_profile.neutral.json
✅ brand/README.md
```

#### Routes & Backend
```
✅ app/routes_*.py (all route files)
✅ templates/*.html
✅ static/ (CSS, JS, images)
```

#### Enrichment System
```
✅ validation/enrich_gbif_stable.py
✅ validation/enrich_eol_images.py
✅ validation/enrichment_status.sh
✅ validation/collect_images.sh
✅ validation/check_progress.py
✅ validation/ENRICHMENT_GUIDE.md
```

#### Documentation
```
✅ replit.md
✅ BRAND_INTEGRATION_SUMMARY.md
✅ START_ENRICHMENT.md
✅ GITHUB_DEPLOYMENT_CHECKLIST.md
```

---

### What NOT to Include

Create a `.gitignore` file with:
```
__pycache__/
*.pyc
.env
temp/
*.log
/tmp/
.replit
.cache/
```

---

### Render Environment Variables (Set in Render Dashboard)

When you deploy to Render, configure these:

**Required:**
- `DATABASE_URL` → Render provides this (PostgreSQL)
- `SESSION_SECRET` → Generate random string (e.g., from random.org)
- `ADMIN_EMAIL` → Your admin email
- `ADMIN_PASSWORD` → Your admin password

**Optional:**
- `OPENAI_API_KEY` → Only if you want AI features (costs money)
- Leave blank for FREE mode (enrichment still works!)

---

### Deployment Flow

1. **Push code to GitHub** (you'll do this manually)
2. **Connect GitHub to Render** in Render dashboard
3. **Configure environment variables** in Render
4. **Deploy** - Render automatically:
   - Installs dependencies from `requirements.txt`
   - Runs `init.sh` (Flask + GBIF enrichment)
   - Provides HTTPS URL
   - Starts 24/7 service

---

## Questions Answered

### Q: Can I start enriching NOW on Replit?
**A: YES!** Run: `bash validation/collect_images.sh`

### Q: Do I need Render to enrich?
**A: NO!** Enrichment works on Replit. Render just gives 24/7 uptime.

### Q: Do I need Neon One integration first?
**A: NO!** Enrichment is independent. Widgets are ready when you are.

### Q: When should I move to Render?
**A: When you want:**
- 24/7 continuous enrichment
- Production-ready widget URLs for Neon One team
- More reliable public access

### Q: Can I test widgets on Replit?
**A: YES!** Click the Run button. URL: https://workspace.fcospresident.repl.co

---

## Next Steps (Your Choice)

**Option 1: Keep Testing on Replit**
- Run enrichment: `bash validation/collect_images.sh`
- Collect 50K-100K images before Render
- Test all widgets locally
- Wait for Render credits

**Option 2: Deploy to Render Now**
- Push files to GitHub (follow list above)
- Deploy to Render
- Start 24/7 enrichment
- Give Neon One team production URL

**Either way works!** No rush.
