# 📥 Download 95,000 EOL Images to Your Google Drive (Mac Instructions)

## 🎯 What This Does
Downloads all 95,000 EOL orchid images from the CSV and saves them directly to YOUR 2TB Google Drive.

---

## ⚙️ Setup (First Time Only - 10 minutes)

### Step 1: Download Files from Replit
1. Download these 2 files from Replit to your Mac:
   - `EOL_IMAGES_COMPLETE_95000.csv` (25 MB)
   - `download_eol_to_drive_mac.py`

2. Put both files in the same folder (e.g., Desktop/EOL_Download)

---

### Step 2: Install Python Dependencies
Open Terminal on your Mac and run:

```bash
pip3 install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client requests
```

---

### Step 3: Get Google Drive API Credentials

1. **Go to Google Cloud Console**:
   - Visit: https://console.cloud.google.com/

2. **Create/Select a Project**:
   - Click "Select a project" → "New Project"
   - Name it: "EOL Orchid Images"
   - Click "Create"

3. **Enable Google Drive API**:
   - In the search bar, type "Google Drive API"
   - Click "Enable"

4. **Create OAuth Credentials**:
   - Go to: APIs & Services → Credentials
   - Click "+ CREATE CREDENTIALS" → "OAuth client ID"
   - Application type: "Desktop app"
   - Name: "EOL Downloader"
   - Click "Create"

5. **Download credentials.json**:
   - Click the download button (⬇️) next to your new OAuth client
   - Rename the file to exactly: `credentials.json`
   - Move it to the same folder as the Python script

---

## ▶️ Run the Download

### Step 1: Open Terminal
```bash
cd ~/Desktop/EOL_Download  # Or wherever you put the files
```

### Step 2: Run the Script
```bash
python3 download_eol_to_drive_mac.py
```

### Step 3: Authenticate
- A browser window will open
- Sign in with YOUR Google account (the one with 2TB storage)
- Click "Allow" to give the app access to your Drive
- Close the browser tab - return to Terminal

### Step 4: Watch Progress
The script will show:
```
Progress: 5,000/95,000 (5.3%) | Rate: 2.5/sec | ETA: 10.2h | ✓4,995 ✗5
```

- ✓ = Uploaded successfully
- ✗ = Failed (will be logged)
- ⊘ = Skipped (already exists)

---

## ⏸️ Pause & Resume

**To pause**: Press `Ctrl+C`

**To resume**: Run the script again
```bash
python3 download_eol_to_drive_mac.py
```

It will skip images already uploaded and continue where it left off.

---

## 📊 What to Expect

- **Total images**: 95,000
- **Estimated time**: 10-15 hours (depending on internet speed)
- **Storage used**: ~15-20 GB in your Google Drive
- **Rate**: ~2-5 images per second

**Progress is saved every 1,000 images** - safe to stop and restart anytime!

---

## ✅ When Complete

You'll see:
```
================================================================================
COMPLETE!
================================================================================
Uploaded: 94,995
Failed: 5
Time: 12.3 hours

All images saved to your Google Drive!
```

Check your Google Drive for the folder: **EOL_Orchid_Images_95000**

---

## ⚠️ Troubleshooting

### "credentials.json not found"
- Download OAuth credentials from Google Cloud Console
- Rename to exactly `credentials.json`
- Put in same folder as script

### "CSV file not found"
- Download `EOL_IMAGES_COMPLETE_95000.csv` from Replit
- Put in same folder as script

### Authentication fails
- Make sure you're using the correct Google account (one with 2TB)
- Delete `token.pickle` and try again

### Script stops/crashes
- Just run it again - it will resume automatically
- Already-uploaded images are skipped

---

## 📁 Files You Need

```
Desktop/EOL_Download/
├── download_eol_to_drive_mac.py       ← Python script
├── EOL_IMAGES_COMPLETE_95000.csv      ← Image URLs (from Replit)
├── credentials.json                    ← OAuth credentials (from Google)
└── token.pickle                        ← Auto-created after first login
```

---

## 🎉 Success!

Once complete, all 95,000 EOL orchid images will be safely stored in your Google Drive before the URLs expire!

The images will be in: **Google Drive → EOL_Orchid_Images_95000/**

Each image named: `eol_[page_id]_[eol_id].jpg`
