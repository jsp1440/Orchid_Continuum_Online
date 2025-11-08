# Google Drive Storage Plan - The Orchid Continuum

## Overview
Store all your EOL data and database on your 2TB Google Drive account - FREE, permanent, and accessible anywhere!

---

## What You'll Store on Google Drive

### 1. EOL Data Files
- `eol_extracted_images.jsonl` (1.6 GB) - 5.6M image URLs
- `orchid_eol_traits.jsonl` (~500 MB) - 3M trait records  
- `eol_linked_data.jsonl` (~2 GB) - Images + traits combined

### 2. Database Files
- `orchid_continuum.db` (SQLite database) - Your entire orchid database
- Backups with timestamps

### 3. Processing Scripts
- Download/upload utilities
- Data processing scripts

---

## Advantages of This Approach

✅ **FREE** - You already have 2TB  
✅ **PERMANENT** - Won't expire or get deleted  
✅ **PORTABLE** - Access from iPad, computer, anywhere  
✅ **SHAREABLE** - Can give read access to Julius AI  
✅ **INDEPENDENT** - Not tied to Replit subscription  
✅ **BACKUP-READY** - Automatic versioning  
✅ **FLEXIBLE** - Download database locally to work, upload when done  

---

## The Workflow

### Phase 1: Process Data on Replit (One-Time Setup)

1. Download EOL datasets from Zenodo
2. Process and link the data
3. Import to local SQLite database
4. Upload everything to Google Drive

### Phase 2: Daily Usage (After Setup)

**Option A: Work Locally**
1. Download `orchid_continuum.db` from Drive to your iPad/computer
2. Open with SQLite browser or connect Julius AI
3. Make changes
4. Upload back to Drive

**Option B: Work on Replit**
1. Download database from Drive
2. Make widgets or run scripts
3. Upload updated database back to Drive

**Option C: Julius AI Access**
1. Share Drive folder with Julius
2. Julius reads database directly from Drive
3. No downloads needed!

---

## Setup Steps

### Step 1: Authenticate Google Drive (Already Done!)

You already have Google Drive integration. Just verify it works:

```python
from google_drive_utils import get_drive_service
drive_service = get_drive_service()
print("✅ Google Drive connected!")
```

### Step 2: Create Orchid Continuum Folder on Drive

We'll create this structure:
```
Google Drive/
└── OrchidContinuum/
    ├── data/
    │   ├── eol_extracted_images.jsonl
    │   ├── orchid_eol_traits.jsonl
    │   └── eol_linked_data.jsonl
    ├── database/
    │   ├── orchid_continuum.db (current)
    │   └── backups/
    │       ├── orchid_continuum_2025-01-20.db
    │       └── orchid_continuum_2025-01-21.db
    └── scripts/
        └── (processing scripts)
```

### Step 3: Download & Process EOL Data

Run on Replit (one time):

```bash
# Download EOL datasets
bash validation/setup_eol_data_on_render.sh

# Process traits
python validation/process_eol_traits.py

# Link images to traits
python validation/link_eol_data.py
```

### Step 4: Upload to Google Drive

```python
python validation/upload_to_drive.py
```

This will:
- Create folder structure
- Upload all EOL data files
- Upload your SQLite database
- Set sharing permissions

---

## Using Your Data from Anywhere

### On iPad (Using Database App)

1. Download `orchid_continuum.db` from Google Drive app
2. Open in any SQLite browser app (SQLiteFlow, SQLite Mobile, etc.)
3. Query your data!
4. Upload back to Drive when done

### On Computer

1. Download database from Drive
2. Open in:
   - DB Browser for SQLite (free)
   - TablePlus
   - DBeaver
   - Any SQLite tool
3. Connect Julius AI to local file
4. Upload changes back to Drive

### With Julius AI (Direct Connection)

**Option 1: Download Database**
1. Download `orchid_continuum.db` from Drive
2. Upload to Julius (drag & drop)
3. Ask questions!

**Option 2: Share Drive Folder** (Advanced)
1. Share OrchidContinuum folder with Julius service account
2. Julius reads directly from Drive
3. No uploads needed!

---

## Backup Strategy

### Automatic Daily Backups

Set up a simple backup script:

```bash
# Runs daily, saves timestamped copy
python validation/backup_to_drive.py
```

Keeps:
- Last 7 daily backups
- Last 4 weekly backups
- Last 12 monthly backups

### Manual Backups

Before major changes:
```python
python validation/backup_to_drive.py --name "before_eol_import"
```

---

## Cost Comparison

| Solution | Storage | Database | Monthly Cost |
|----------|---------|----------|--------------|
| **Google Drive** | 2 TB | SQLite | **$0** |
| Render | 1 GB | PostgreSQL | $7 |
| Supabase Free | 500 MB | PostgreSQL | $0 (limited) |
| Supabase Paid | 8 GB | PostgreSQL | $25 |

**Winner: Google Drive!** You get 4000x more storage for free!

---

## Database Size Estimates

Current:
- Taxonomy: 35K entries (~5 MB)
- Images (GBIF): 8.5K records (~10 MB)
- EOL Images: 5.6M URLs (~600 MB)
- EOL Traits: 3M records (~400 MB)
- **Total**: ~1 GB SQLite file

Future (with all data):
- 200K GBIF images
- 5.6M EOL images
- 3M traits
- **Total**: ~3-5 GB SQLite file

**Still fits easily in 2TB Drive!**

---

## Working Without Replit

Once your data is on Drive, you can:

1. **Cancel Replit** (or use free tier)
2. **Download database** anytime
3. **Work locally** on iPad/computer
4. **Use Julius AI** for queries
5. **Build new widgets** only when needed

**Replit becomes optional, not required!**

---

## Migration Path

### Now: Development on Replit
- Build widgets
- Process data
- Test features

### After Setup: Data on Drive
- Database lives on Drive
- Download when you need to work
- Upload when done
- Always backed up

### Future: Full Independence
- Static website (free hosting)
- Database on Drive
- Julius AI for analysis
- Replit only for new development

---

## Next Steps

Ready to set this up? I'll create the upload scripts and we can:

1. ✅ Process EOL data on Replit (free, one-time)
2. ✅ Upload everything to your Drive (free, permanent)
3. ✅ Show you how to access from iPad
4. ✅ Connect Julius AI
5. ✅ Make Replit optional!

**Say "let's start" and I'll begin processing the EOL data!**
