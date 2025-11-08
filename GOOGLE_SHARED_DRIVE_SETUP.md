# 🌺 GOOGLE SHARED DRIVE UPLOAD - SETUP GUIDE

**This is MUCH EASIER than downloading to your Mac!**

---

## ✅ WHY THIS IS BETTER

**Mac Download Method:**
- ❌ Download to Mac (~8-40 hours)
- ❌ Keep Mac awake overnight
- ❌ Upload back to Replit
- ❌ Multiple manual steps

**Google Shared Drive Method:**
- ✅ Runs 24/7 on Replit automatically
- ✅ No Mac needed at all
- ✅ Direct cloud storage
- ✅ Access from anywhere
- ✅ Service accounts work with Shared Drives
- ✅ ONE command and forget it!

---

## 🔧 ONE-TIME SETUP

### Step 1: Get Your Service Account Key

You already have this set up! Just need to verify:

```bash
# Check if service account is configured
ls service-account-key.json
```

If missing, download from Google Cloud Console.

### Step 2: Share Drive Folder

✅ **Already done!** You have:
- Folder ID: `1VtKUMeQr_bAH6wpp37gsz3ecfwX1yS75`
- Shared Drive access configured

### Step 3: Install Google API Package

```bash
pip3 install google-api-python-client google-auth
```

---

## ▶️ RUN THE UPLOAD

### Upload GBIF Images (10,534 images)

```bash
python3 download_to_google_drive.py gbif
```

### Upload EOL Images (95,000 images) - Coming Soon

```bash
python3 download_to_google_drive.py eol
```

---

## 📊 WHAT IT DOES

For each image:
1. ✅ Downloads from GBIF/EOL
2. ✅ Verifies image integrity
3. ✅ Calculates SHA256 hash
4. ✅ Calculates perceptual hash
5. ✅ Uploads to Google Shared Drive
6. ✅ Updates database with Drive URL
7. ✅ Deletes temp file
8. ✅ Repeats for next image

**Result:** All images safely stored in your Google Shared Drive!

---

## 📁 FOLDER STRUCTURE

```
Your Shared Drive/
└── OrchidContinuum/
    ├── orchid_gbif/          (10,534 GBIF images)
    │   ├── gbif_1.jpg
    │   ├── gbif_2.jpg
    │   └── ...
    └── orchid_eol/           (95,000 EOL images)
        ├── eol_1.jpg
        ├── eol_2.jpg
        └── ...
```

---

## 🎯 PROGRESS MONITORING

**Watch in real-time:**
```
[1338] Downloading...
  ✅ Downloaded 1.49 MB
  ☁️  Uploaded to Google Drive
  💾 Database updated
```

**Check logs:**
```bash
tail -f gdrive_upload.log
```

**Check database:**
```sql
SELECT COUNT(*) FROM orchid_images 
WHERE download_status = 'google_drive_preserved';
```

---

## 🛑 PAUSE & RESUME

**Stop anytime:**
- Press `Ctrl+C`
- Script auto-resumes from last position

**Resume:**
```bash
python3 download_to_google_drive.py gbif
```

Script automatically skips already-uploaded images!

---

## 🚀 ADVANTAGES

**Cloud Storage Benefits:**
- ✅ 2TB Google Workspace storage
- ✅ Access from any device
- ✅ Automatic backup
- ✅ Version history
- ✅ Share with collaborators
- ✅ No local disk space needed

**Deployment Benefits:**
- ✅ Images stay in cloud forever
- ✅ Serve via Google Drive CDN
- ✅ Or download to Render when deploying
- ✅ Protected from any server crashes

---

## ⚡ COMPARISON

| Method | Time | Complexity | Storage |
|--------|------|------------|---------|
| **Mac Download** | 8-40 hours | High (3 steps) | Local 100GB |
| **Shared Drive** | 8-40 hours | Low (1 command) | Cloud 100GB |

**Winner:** Google Shared Drive! 🏆

---

## 🎉 FINAL RESULT

When complete:
- ✅ 105,534 images in Google Shared Drive
- ✅ Database has all Drive URLs
- ✅ Full metadata (taxonomy, traits, hashes)
- ✅ Protected from government deletion
- ✅ Accessible from anywhere
- ✅ Your digital ark is complete!

---

## 📝 NOTES

- Runs automatically on Replit 24/7
- No Mac needed
- No manual uploads
- Auto-resumes if interrupted
- Creates subfolders automatically
- Skips already-uploaded images

---

**Just run ONE command and let it work!** 🌺
