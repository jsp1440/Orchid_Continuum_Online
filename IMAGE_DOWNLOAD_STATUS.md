# ORCHID IMAGE DOWNLOAD STATUS

**Last Updated:** November 1, 2025

---

## 📊 CURRENT DOWNLOADS

### 1. GBIF Images (10,534 total)
- **Status:** Running in background
- **Downloaded:** 1,206 images (1.5GB)
- **Remaining:** ~9,300 images
- **Progress:** ~11%
- **ETA:** 8-10 hours
- **Script:** `download_to_static.py`
- **Location:** `static/images/orchid/`

### 2. EOL Images (95,000 total)
- **Status:** Ready to start
- **Downloaded:** 0 images
- **Remaining:** 95,000 images  
- **Progress:** 0%
- **ETA:** ~30-40 hours (if run)
- **Script:** `download_eol_images.py`
- **Location:** `static/images/eol/`

---

## 🚀 HOW TO RUN

### Start GBIF Download (Already Running)
```bash
python3 download_to_static.py
```

### Start EOL Download  
```bash
python3 download_eol_images.py
```

### Run Both Simultaneously
```bash
# Terminal 1
python3 download_to_static.py

# Terminal 2  
python3 download_eol_images.py
```

---

## 📁 FILE ORGANIZATION

```
static/
├── images/
    ├── orchid/          (GBIF images)
    │   ├── orchid_1.jpg
    │   ├── orchid_2.jpg
    │   └── ... (10,534 total)
    │
    └── eol/             (EOL images)
        ├── eol_1.jpg
        ├── eol_2.jpg
        └── ... (95,000 total)
```

---

## 🎯 WHAT EACH DOWNLOAD DOES

### GBIF Download (`download_to_static.py`)
- ✅ Downloads images from GBIF URLs
- ✅ Calculates SHA256 hashes
- ✅ Calculates perceptual hashes
- ✅ Saves to `/static/images/orchid/`
- ✅ Updates database with static URLs
- ✅ Status: `static_hosted`

### EOL Download (`download_eol_images.py`)
- ✅ Reads 95,000 images from CSV
- ✅ Downloads images from EOL URLs
- ✅ **Fetches taxonomy from EOL API**
- ✅ **Fetches traits from EOL API**
- ✅ Calculates SHA256 + perceptual hashes
- ✅ Saves to `/static/images/eol/`
- ✅ Updates database with full metadata
- ✅ Status: `eol_preserved`

---

## 📊 MONITOR PROGRESS

### Check GBIF Images
```bash
ls static/images/orchid/ | wc -l
du -sh static/images/orchid/
```

### Check EOL Images
```bash
ls static/images/eol/ | wc -l
du -sh static/images/eol/
```

### Check Logs
```bash
# GBIF log
tail -f static_image_download.log

# EOL log
tail -f eol_download.log
```

### Check Database
```sql
-- GBIF progress
SELECT COUNT(*) FROM orchid_images 
WHERE download_status = 'static_hosted';

-- EOL progress
SELECT COUNT(*) FROM orchid_images 
WHERE download_status = 'eol_preserved';
```

---

## 💾 STORAGE REQUIREMENTS

### GBIF Images
- **Total:** ~10-20 GB (10,534 images)
- **Average:** ~1-2 MB per image

### EOL Images  
- **Total:** ~95-190 GB (95,000 images)
- **Average:** ~1-2 MB per image

### Combined
- **Total:** ~105-210 GB for all 105,534 images
- **Replit:** May need to manage in batches
- **Render:** Upgrade to paid tier for full storage

---

## 🎉 FINAL RESULT

When both downloads complete, you'll have:

✅ **105,534 orchid images** preserved
✅ **All hosted** at static URLs  
✅ **Full metadata** (taxonomy, traits, licenses)
✅ **SHA256 hashes** for integrity
✅ **Perceptual hashes** for deduplication
✅ **Ready for deployment** to Render
✅ **Protected from government deletion**

---

## 📝 NOTES

- Both scripts auto-resume if interrupted
- Can run simultaneously (separate folders)
- EOL script enriches with API taxonomy data
- All images get proper attribution/licensing
- No Google Drive setup needed!
- Complete scientific data preservation

---

**This is your digital ark for orchid biodiversity!** 🌺
