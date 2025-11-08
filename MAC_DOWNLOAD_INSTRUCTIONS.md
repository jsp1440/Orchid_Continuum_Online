# 🌺 ORCHID IMAGE DOWNLOADER - MAC SETUP GUIDE

**Total Images:** 105,534 (10,534 GBIF + 95,000 EOL)  
**Estimated Time:** 8-40 hours  
**Storage Needed:** ~100-200 GB

---

## 📦 STEP 1: DOWNLOAD FILES FROM REPLIT

Download these 4 files to a folder on your Mac (e.g., `~/orchid_downloads/`):

1. **download_to_static.py** - GBIF downloader
2. **download_eol_images.py** - EOL downloader  
3. **mac_requirements.txt** - Python dependencies
4. **EOL_IMAGES_COMPLETE_95000.csv** - EOL image list

**How to download from Replit:**
- Click each file in the Replit file tree
- Click the three dots menu (⋮) → Download
- Save all 4 files to the same folder on your Mac

---

## 🔧 STEP 2: SETUP (One-Time)

Open **Terminal** on your Mac and run these commands:

```bash
# Navigate to your download folder
cd ~/orchid_downloads/

# Install Python dependencies
pip3 install -r mac_requirements.txt

# Create folders for images
mkdir -p static/images/orchid
mkdir -p static/images/eol

# Set database connection (get from Replit Secrets)
export DATABASE_URL="your_postgresql_url_here"
```

**Get your DATABASE_URL from Replit:**
1. In Replit, go to Tools → Secrets
2. Copy the value of `DATABASE_URL`
3. Paste it in the export command above

---

## ▶️ STEP 3: RUN DOWNLOADS

### Option A: Run Both Downloads Simultaneously (Fastest)

**Terminal Window 1 - GBIF Images:**
```bash
cd ~/orchid_downloads/
export DATABASE_URL="your_postgresql_url_here"
python3 download_to_static.py
```

**Terminal Window 2 - EOL Images:**
```bash
cd ~/orchid_downloads/
export DATABASE_URL="your_postgresql_url_here"
python3 download_eol_images.py
```

### Option B: Run One at a Time

**First, run GBIF (~8-10 hours):**
```bash
cd ~/orchid_downloads/
export DATABASE_URL="your_postgresql_url_here"
python3 download_to_static.py
```

**Then, run EOL (~30-40 hours):**
```bash
python3 download_eol_images.py
```

---

## 📊 STEP 4: MONITOR PROGRESS

### Watch the Downloads
Both scripts show real-time progress in the terminal:
```
[1,206/10,534] ID 1338
  ✅ Downloaded 1.49 MB
  🔒 SHA256: 2e200590a17d6cba...
  📂 Saved: /static/images/orchid/orchid_1338.jpg
  💾 Database updated
```

### Check Image Counts
```bash
# GBIF images
ls static/images/orchid/ | wc -l

# EOL images  
ls static/images/eol/ | wc -l

# Total disk usage
du -sh static/images/
```

### Check Logs
```bash
# GBIF log
tail -f static_image_download.log

# EOL log
tail -f eol_download.log
```

---

## 🛑 IF YOU NEED TO STOP

**Safe Interruption:**
- Press `Ctrl+C` in the terminal
- Both scripts auto-resume where they left off
- Your progress is saved in the database

**Resume Later:**
```bash
# Just run the same command again
python3 download_to_static.py   # Resumes GBIF
python3 download_eol_images.py  # Resumes EOL
```

---

## ⬆️ STEP 5: UPLOAD BACK TO REPLIT

When downloads complete, upload the image folders back to Replit:

### Method 1: Direct Upload (Small Batches)
1. In Replit file tree, right-click `static/images/`
2. Select "Upload files"
3. Upload in batches (Replit has upload limits)

### Method 2: Use rsync/scp (Recommended for Large)
```bash
# From your Mac, sync to Replit
# (You'll need Replit's SSH/deploy key)
rsync -avz static/images/ replit:/path/to/static/images/
```

### Method 3: Upload to Google Drive First
```bash
# Install rclone on Mac
brew install rclone

# Configure Google Drive
rclone config

# Upload
rclone copy static/images/orchid/ gdrive:OrchidContinuum/orchid/
rclone copy static/images/eol/ gdrive:OrchidContinuum/eol/
```

---

## 🎯 WHAT EACH DOWNLOAD DOES

### GBIF Download (10,534 images)
- Downloads wild orchid photos from GBIF
- Calculates SHA256 hash for integrity
- Calculates perceptual hash for deduplication
- Saves to `static/images/orchid/`
- Updates database with static URLs

### EOL Download (95,000 images)
- Downloads orchid images from Encyclopedia of Life
- **Fetches taxonomy from EOL API** (genus, species, classification)
- **Fetches trait data from EOL API** (habitat, phenology, etc.)
- Calculates SHA256 + perceptual hashes
- Saves to `static/images/eol/`
- Updates database with full metadata

---

## ⚠️ TROUBLESHOOTING

### "pip3: command not found"
```bash
# Install Python 3 if needed
brew install python3
```

### "Permission denied"
```bash
# Make scripts executable
chmod +x download_to_static.py
chmod +x download_eol_images.py
```

### "Database connection failed"
- Double-check your DATABASE_URL is correct
- Make sure you copied the full URL from Replit Secrets
- Ensure your Mac can reach the Replit database (internet connection)

### Downloads are slow
- Normal! Each image takes ~1 second
- 10,534 images = ~3 hours minimum
- 95,000 images = ~26 hours minimum
- Plus API calls add extra time

### Mac goes to sleep
```bash
# Prevent sleep during downloads
caffeinate -i python3 download_to_static.py
```

---

## 📁 FINAL FOLDER STRUCTURE

After completion, you'll have:

```
~/orchid_downloads/
├── download_to_static.py
├── download_eol_images.py
├── requirements.txt
├── EOL_IMAGES_COMPLETE_95000.csv
├── static/
│   └── images/
│       ├── orchid/           (10,534 GBIF images)
│       │   ├── orchid_1.jpg
│       │   ├── orchid_2.jpg
│       │   └── ... 
│       └── eol/              (95,000 EOL images)
│           ├── eol_1.jpg
│           ├── eol_2.jpg
│           └── ...
├── static_image_download.log
└── eol_download.log
```

**Total Size:** ~100-200 GB

---

## ✅ SUCCESS CRITERIA

You'll know it's done when you see:

**GBIF Complete:**
```
🎉 DOWNLOAD COMPLETE!
Images downloaded: 10,534
Images failed: 0
```

**EOL Complete:**
```
🎉 EOL DOWNLOAD COMPLETE!
Images downloaded: 95,000
API enriched: 95,000
Images failed: 0
```

---

## 🎉 NEXT STEPS

After successful download and upload to Replit:

1. ✅ All 105,534 images preserved
2. ✅ Protected from government deletion
3. ✅ Ready for Render deployment
4. ✅ Ready for widget testing
5. ✅ Your digital ark is complete!

---

**Questions?** The scripts have detailed logging and will tell you exactly what's happening. Just let them run overnight! 🌙
