# 🚀 Start Here: Google Drive Storage Setup

## The Simple 3-Step Plan

### STEP 1: Process EOL Data on Replit (30 minutes, one-time, FREE)

Run these commands in Replit Shell:

```bash
# Download EOL datasets from Zenodo (automatic, ~3GB)
bash validation/setup_eol_data_on_render.sh

# Extract image URLs from CSVs
python validation/extract_eol_images_from_csv.py

# Process trait data
python validation/process_eol_traits.py

# Link images to traits
python validation/link_eol_data.py
```

**What happens**: Downloads 5.6M EOL image URLs and 3M trait records, processes them, links them together.

**Cost**: $0 (uses Replit's free processing)

---

### STEP 2: Upload Everything to Your Google Drive (20 minutes, FREE)

First, set up Google Drive access (one-time):

```bash
# Install Google Drive library
pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

Then upload:

```bash
python validation/upload_eol_to_drive.py
```

**What happens**: Creates folder "OrchidContinuum" on your Drive, uploads all files.

**Storage used**: ~3-5 GB (you have 2000 GB!)

---

### STEP 3: Access Your Data Anywhere

#### On iPad:
1. Open Google Drive app
2. Go to: OrchidContinuum → database
3. Download `orchid_continuum.db`
4. Open in any SQLite app (SQLiteFlow, etc.)
5. Query your 5.6M orchid images!

#### With Julius AI:
1. Sign up at https://julius.ai
2. Upgrade to Pro ($45/month)
3. Upload your database file
4. Ask: "Show me orchid species by country"
5. Get instant visualizations!

#### On Computer:
1. Download database from Drive
2. Open in DB Browser for SQLite (free)
3. Run any SQL queries you want
4. Upload back to Drive when done

---

## What You Get

✅ **5.6 MILLION** EOL orchid image URLs  
✅ **3 MILLION** phenotypic trait records  
✅ **35,320** authoritative taxonomy entries  
✅ **8,517+** GBIF wild occurrence images  
✅ All linked together by species  

**Stored on YOUR Google Drive - FREE forever!**

---

## After Setup: Independence from Replit

Once data is on Drive, you can:

- ✅ Cancel Replit (or keep free tier)
- ✅ Work locally on iPad/computer
- ✅ Use Julius AI for analysis
- ✅ Build new widgets only when needed
- ✅ Never lose your data (it's on Drive!)

**Replit becomes optional, not required!**

---

## Cost Breakdown

| What | Cost |
|------|------|
| Google Drive (2TB) | $0 (you own it) |
| Processing on Replit | $0 (free tier) |
| EOL/GBIF data | $0 (public APIs) |
| Julius AI (optional) | $45/month |
| **TOTAL for storage** | **$0** |

---

## Ready to Start?

Just say **"let's process the data"** and I'll guide you through STEP 1!

Or if you want to skip straight to it, run:
```bash
bash validation/setup_eol_data_on_render.sh
```

This downloads everything from Zenodo and you're on your way! 🌸
