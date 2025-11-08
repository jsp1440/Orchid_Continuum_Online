# GOOGLE SHARED DRIVE SETUP FOR IMAGE PRESERVATION

## 🎯 Goal
Preserve 10,534+ GBIF orchid images to Google Shared Drive for scientific research and data preservation.

---

## ⚡ QUICK SETUP (10 Minutes)

### Step 1: Create Google Shared Drive
1. Go to **https://drive.google.com**
2. Click **"Shared drives"** (left sidebar)
3. Click **"+ New"** (top left)
4. Name it: **"Orchid Research Archive"**
5. Click **"Create"**

### Step 2: Get the Shared Drive ID
1. Click on your **"Orchid Research Archive"** shared drive
2. Look at browser URL:
   ```
   https://drive.google.com/drive/folders/XXXXXXXXXXXXXXXXXXXXX
                                           ↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑
                                           This is the ID!
   ```
3. **Copy the long ID** (everything after `/folders/`)

### Step 3: Add Service Account to Shared Drive
1. In the Shared Drive, click **⚙️ (settings/manage members)**
2. Click **"Add members"**
3. Paste this email:
   ```
   google-service-account@orchid-photo-studio.iam.gserviceaccount.com
   ```
4. Change permission to **"Content manager"**
5. **Uncheck** "Notify people" (it's a service account)
6. Click **"Done"**

### Step 4: Add Shared Drive ID to Replit Secrets
1. In Replit, click **"Tools"** → **"Secrets"**
2. Click **"+ New Secret"**
3. Key: `SHARED_DRIVE_ID`
4. Value: (paste the long ID from Step 2)
5. Click **"Add secret"**

---

## 🚀 HOW TO RUN THE PRESERVATION SYSTEM

Once setup is complete, run:
```bash
python3 batch_download_to_shared_drive.py
```

### What It Does:
1. ✅ Downloads **100 images** from GBIF
2. ✅ Uploads them to your **Shared Drive**
3. ✅ **Clears temp storage** (prevents running out of space)
4. ✅ **Repeats** until all 10,534 images preserved
5. ✅ **Auto-resumes** if interrupted
6. ✅ **Logs everything** to `image_preservation.log`

### Run in Background:
```bash
nohup python3 batch_download_to_shared_drive.py > preservation_output.log 2>&1 &
```

This runs continuously even if you close Replit!

---

## 📊 MONITOR PROGRESS

### Check Current Status:
```bash
tail -f image_preservation.log
```

### Check Database Progress:
```sql
SELECT 
  COUNT(*) FILTER (WHERE download_status = 'preserved') as preserved,
  COUNT(*) FILTER (WHERE download_status IS NULL) as remaining,
  COUNT(*) as total
FROM orchid_images
WHERE image_source LIKE '%GBIF%';
```

### View Preserved Images:
Go to your **"Orchid Research Archive"** Shared Drive  
→ **"Orchid_Species_Archive"** folder  
→ All preserved images with unique filenames

---

## 🎯 WHAT GETS PRESERVED

### Image Naming:
```
orchid_{gbif_occurrence_key}_{database_id}.jpg
```
Example: `orchid_4462959843_12345.jpg`

### Metadata Stored in Database:
- ✅ SHA256 hash (verify integrity)
- ✅ Perceptual hash (detect duplicates)
- ✅ Google Drive URL
- ✅ Download timestamp
- ✅ Preservation status

### Database Fields Updated:
- `local_path` → Google Drive URL
- `file_sha256` → File hash
- `perceptual_hash` → Image fingerprint
- `download_status` → "preserved"
- `downloaded_at` → Timestamp

---

## ⏯️ STOP/RESUME

### Stop Gracefully:
Press `Ctrl+C` in terminal (script saves progress)

### Resume Later:
Just run the script again:
```bash
python3 batch_download_to_shared_drive.py
```
It automatically continues where it left off!

---

## 🛡️ DATA PROTECTION FEATURES

### Automatic Retry:
- Failed downloads retry 3 times with backoff
- Network errors don't lose progress
- Database tracks every attempt

### Deduplication:
- Skips images already preserved
- Uses `is_duplicate` flag
- Prevents wasting storage

### Verification:
- SHA256 ensures file integrity
- Perceptual hash detects visual duplicates
- Image validation before upload

### Protected Images:
- Skips Tropicos "imageprotected.jpg" placeholders
- Logs failures for manual review
- Continues processing other images

---

## 📈 ESTIMATED COMPLETION TIME

**Total Images:** 10,534 GBIF images  
**Batch Size:** 100 images  
**Batches Needed:** ~106 batches  
**Time per Image:** ~3-5 seconds (download + upload)  
**Total Time:** ~8-14 hours (continuous running)

**Run overnight!** The script is designed for long-running operation.

---

## 🆘 TROUBLESHOOTING

### "SHARED_DRIVE_ID not set"
→ Add it to Replit Secrets (see Step 4 above)

### "Service account has no access"
→ Make sure you added the service account as "Content manager" (Step 3)

### "Storage quota exceeded"
→ This shouldn't happen with Shared Drive! Double-check the Drive ID is correct.

### "SSL connection closed"
→ Normal temporary error, script auto-retries

### Script stops unexpectedly
→ Just run it again, it resumes automatically

---

## ✅ SUCCESS CHECKLIST

After preservation completes:
- [ ] Check Shared Drive has ~10,000+ images
- [ ] Verify database shows `download_status = 'preserved'`
- [ ] Review `image_preservation.log` for errors
- [ ] Spot-check a few Drive URLs work
- [ ] Celebrate data preservation! 🎉

---

## 📧 YOUR SHARED DRIVE INFO

**Service Account Email:**
```
google-service-account@orchid-photo-studio.iam.gserviceaccount.com
```

**Shared Drive Name:** Orchid Research Archive  
**Folder Name:** Orchid_Species_Archive  
**Your Drive ID:** (you'll add this to Replit Secrets)

---

## 🌍 MISSION ACCOMPLISHED

You're preserving critical biodiversity data for:
- ✅ Scientific research
- ✅ AI vision analysis
- ✅ Species identification
- ✅ Data protection from loss
- ✅ Educational purposes
- ✅ Future generations

**This is important work.** Thank you for protecting orchid biodiversity data! 🌺
