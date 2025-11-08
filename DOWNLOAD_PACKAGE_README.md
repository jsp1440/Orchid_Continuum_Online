# 🌺 ORCHID IMAGE DOWNLOADER PACKAGE

This package downloads **105,534 orchid images** (10,534 GBIF + 95,000 EOL) with full metadata.

---

## 📦 FILES TO DOWNLOAD FROM REPLIT

1. **download_to_static.py** (23 KB) - GBIF image downloader
2. **download_eol_images.py** (12 KB) - EOL image downloader with API enrichment
3. **mac_requirements.txt** (300 bytes) - Python dependencies
4. **EOL_IMAGES_COMPLETE_95000.csv** (12 MB) - List of 95,000 EOL images
5. **MAC_DOWNLOAD_INSTRUCTIONS.md** (This file) - Complete setup guide

**Download Method:**
- In Replit file tree, click each file
- Click three dots menu (⋮) → Download
- Save all files to same folder (e.g., `~/orchid_downloads/`)

---

## ⚡ QUICK START

```bash
# 1. Navigate to download folder
cd ~/orchid_downloads/

# 2. Install dependencies
pip3 install -r mac_requirements.txt

# 3. Create folders
mkdir -p static/images/orchid static/images/eol

# 4. Set database URL (get from Replit Secrets)
export DATABASE_URL="postgresql://your_database_url_here"

# 5. Run GBIF download (Terminal 1)
python3 download_to_static.py

# 6. Run EOL download (Terminal 2, optional simultaneous)
python3 download_eol_images.py
```

---

## 🎯 WHAT YOU'LL GET

**After 8-40 hours of downloading:**

✅ **105,534 orchid images** preserved locally  
✅ **GBIF images:** 10,534 wild orchid photos with GPS data  
✅ **EOL images:** 95,000 specimens with taxonomy + traits  
✅ **SHA256 hashes** for file integrity verification  
✅ **Perceptual hashes** for duplicate detection  
✅ **Database records** with full metadata  
✅ **Protected from deletion** - your digital ark!

**Storage needed:** ~100-200 GB

---

## 📖 DETAILED INSTRUCTIONS

See **MAC_DOWNLOAD_INSTRUCTIONS.md** for:
- Complete setup steps
- Troubleshooting guide
- Progress monitoring
- Upload back to Replit
- Resume after interruption

---

## ⚙️ SYSTEM REQUIREMENTS

- **OS:** macOS (tested on 10.15+)
- **Python:** 3.8 or higher
- **Storage:** 100-200 GB free space
- **Internet:** Stable broadband connection
- **Time:** 8-40 hours (can run overnight)
- **Database:** PostgreSQL connection to Replit

---

## 🔒 YOUR DATABASE URL

**From Replit Secrets:**
```
postgresql://neondb_owner:npg_feOt1Ek0KLrF@ep-snow...
```

Copy your full DATABASE_URL from:
1. Replit → Tools → Secrets
2. Find `DATABASE_URL`
3. Copy entire value (starts with `postgresql://`)
4. Use in `export DATABASE_URL="..."` command

---

## ✅ VERIFICATION

**Check if Python is installed:**
```bash
python3 --version
# Should show: Python 3.8 or higher
```

**Check if pip is installed:**
```bash
pip3 --version
# Should show: pip 20.0 or higher
```

**If not installed:**
```bash
brew install python3
```

---

## 🚀 NEXT STEPS AFTER DOWNLOAD

1. **Verify downloads completed:**
   - GBIF: 10,534 images in `static/images/orchid/`
   - EOL: 95,000 images in `static/images/eol/`

2. **Upload back to Replit:**
   - Use Replit file upload (batches)
   - Or use rsync/rclone for bulk transfer
   - Or keep on Mac and deploy from local

3. **Deploy to Render:**
   - Images auto-deploy with Flask app
   - Widgets access via static URLs
   - Full 105,534 image library online!

---

**Questions?** Check MAC_DOWNLOAD_INSTRUCTIONS.md for detailed troubleshooting!
