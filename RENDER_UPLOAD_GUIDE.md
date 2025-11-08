# 🚀 Get Your Data Into Render - Simple Guide

You have 1.6 GB of EOL image data ready. Here's how to get it onto Render in 3 easy steps.

---

## STEP 1: Deploy Your App to Render (15 minutes)

### 1A. Push Code to GitHub (Skip if already done)

```bash
# Add large files to .gitignore
echo "validation/eol_extracted_images.jsonl" >> .gitignore
echo "validation/orchid_eol_traits.jsonl" >> .gitignore
echo "external_databases/eol_traitbank/" >> .gitignore

# Commit and push your code
git add .
git commit -m "Prepare for Render deployment"
git push origin main
```

### 1B. Create Render PostgreSQL Database

1. Go to https://render.com/dashboard
2. Click **"New +"** → **"PostgreSQL"**
3. Configure:
   - **Name**: `orchid-db`
   - **Database**: `orchid_continuum`
   - **Region**: Oregon (US West)
   - **Plan**: **Starter** ($7/month)
4. Click **"Create Database"**
5. **IMPORTANT**: Copy the **"External Database URL"** 
   - It looks like: `postgres://user:pass@dpg-xxxxx.oregon-postgres.render.com/orchid_continuum`
   - Save it to a text file!

### 1C. Deploy Web Service from GitHub

1. Click **"New +"** → **"Web Service"**
2. Click **"Connect a repository"** → Select your GitHub repo
3. Configure:
   - **Name**: `orchid-continuum`
   - **Region**: Oregon (same as database)
   - **Branch**: `main`
   - **Runtime**: **Python 3**
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn -w 4 -b 0.0.0.0:$PORT main:app`
   - **Plan**: **Starter** ($7/month) or **Free** (slower)
4. **Environment Variables** - Click "Add Environment Variable":
   ```
   DATABASE_URL = [paste the URL from step 1B]
   SESSION_SECRET = any_random_string_here_abc123xyz
   FLASK_ENV = production
   ORCHID_AI_ENABLED = false
   ```
5. Click **"Create Web Service"**

**Wait 5-10 minutes for deployment...**

Your app will be live at: `https://orchid-continuum.onrender.com`

---

## STEP 2: Upload Your Data Files (2 Options)

You have a **1.6 GB file** that's too big for GitHub. Choose ONE method:

### OPTION A: Upload via Cloud Link (RECOMMENDED - Easiest!)

This is the fastest method. Upload to temporary cloud storage, then download on Render.

#### Step 2A-1: Upload to Cloud Storage

Pick ANY of these free options:

**Google Drive:**
1. Go to https://drive.google.com
2. Click **"New"** → **"File Upload"**
3. Upload `validation/eol_extracted_images.jsonl`
4. Right-click the file → **"Get Link"**
5. Set to **"Anyone with the link"** → Copy link
6. **Convert to direct download**:
   - Original: `https://drive.google.com/file/d/FILE_ID/view?usp=sharing`
   - Change to: `https://drive.google.com/uc?export=download&id=FILE_ID`

**Dropbox:**
1. Go to https://dropbox.com
2. Upload file
3. Click **"Share"** → **"Create link"**
4. Copy link and change `?dl=0` to `?dl=1` at the end

**WeTransfer (No Account Needed!):**
1. Go to https://wetransfer.com
2. Upload file
3. Enter your own email
4. Download and get the direct link from email

#### Step 2A-2: Download on Render

1. In Render dashboard, go to your **orchid-continuum** web service
2. Click **"Shell"** tab (opens terminal)
3. Run these commands:

```bash
# Create directory
mkdir -p validation

# Download your file (replace URL!)
curl -L -o validation/eol_extracted_images.jsonl \
  "YOUR_CLOUD_STORAGE_URL_HERE"

# Verify it worked
ls -lh validation/eol_extracted_images.jsonl
# Should show: 1.6G
```

**Done!** Your images are on Render.

---

### OPTION B: Direct Upload via Render Shell

If you prefer not to use cloud storage, you can upload smaller chunks.

1. Split the file locally:
```bash
# Split into 500 MB chunks
split -b 500M validation/eol_extracted_images.jsonl eol_part_
```

2. Upload each part via Render Shell file upload (drag & drop)
3. Reassemble on Render:
```bash
cat eol_part_* > validation/eol_extracted_images.jsonl
rm eol_part_*
```

**Note**: This is slower and more tedious. Use Option A if possible!

---

## STEP 3: Process the Data on Render

Now that your data is uploaded, let's process it!

### 3A. Download TraitBank (Fresh Download)

In Render Shell, run:

```bash
# Create directory
mkdir -p external_databases/eol_traitbank

# Download TraitBank (565 MB)
cd external_databases/eol_traitbank
curl -L -o traits_all.zip \
  "https://zenodo.org/records/13305577/files/traits_all.zip?download=1"

# Unzip
unzip -q traits_all.zip

# Verify
ls -lh trait_bank/
# Should show multiple CSV files

cd ../..
```

### 3B. Process TraitBank to Extract Orchid Traits

```bash
python validation/process_eol_traits.py
```

This will:
- Read the TraitBank CSVs
- Extract only orchid-related traits
- Save to `validation/orchid_eol_traits.jsonl`
- Takes ~10-15 minutes

### 3C. Link Images to Traits

```bash
python validation/link_eol_data.py
```

This will:
- Match EOL images to traits using page_id
- Create unified dataset
- Save to `validation/eol_linked_data.jsonl`
- Takes ~5-10 minutes

### 3D. Import to Database

```bash
python validation/import_eol_to_db.py
```

This will:
- Import linked data to PostgreSQL
- Populate orchid_images table
- Create trait associations
- Takes ~20-30 minutes

---

## STEP 4: Start GBIF Worker (Optional - Runs 24/7)

1. In Render dashboard, click **"New +"** → **"Background Worker"**
2. Connect same GitHub repo
3. Configure:
   - **Name**: `orchid-gbif-worker`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python -u validation/enrich_gbif_stable.py`
   - **Plan**: Free or Starter
4. Add environment variable:
   ```
   DATABASE_URL = [same as web service]
   ```
5. Click **"Create Background Worker"**

**Done!** Worker will collect GBIF images 24/7.

---

## Quick Command Reference

Once data is uploaded, run these **in order** in Render Shell:

```bash
# 1. Download TraitBank
mkdir -p external_databases/eol_traitbank && cd external_databases/eol_traitbank
curl -L -o traits_all.zip "https://zenodo.org/records/13305577/files/traits_all.zip?download=1"
unzip -q traits_all.zip && cd ../..

# 2. Process traits
python validation/process_eol_traits.py

# 3. Link images to traits
python validation/link_eol_data.py

# 4. Import to database
python validation/import_eol_to_db.py

# 5. Check results
python -c "from app import app, db; app.app_context().push(); from models import OrchidImage; print(f'Total images: {OrchidImage.query.count()}')"
```

---

## Troubleshooting

**Problem**: "curl: command not found"  
**Solution**: Render has curl installed. Try `which curl` to verify.

**Problem**: "No space left on device"  
**Solution**: Delete large zip files after extracting: `rm traits_all.zip`

**Problem**: "Database connection refused"  
**Solution**: Check DATABASE_URL is set correctly in environment variables.

**Problem**: "File upload fails"  
**Solution**: Use Option A (cloud storage) instead of direct upload.

---

## What You'll Have After This

✅ Live website at `https://orchid-continuum.onrender.com`  
✅ PostgreSQL with 35K taxonomy + 5.6M EOL images  
✅ 3M+ trait records linked to images  
✅ GBIF worker collecting new images 24/7  
✅ Ready for Julius AI connection  

**Total Cost**: $7-14/month (database + web service)

---

## Next Steps

After data is loaded:
- [ ] Connect Julius AI (see `docs/JULIUS_AI_SETUP_GUIDE.md`)
- [ ] Test widgets on live site
- [ ] Send email to Jen with your Render URL
- [ ] Monitor GBIF collection progress

---

**Ready to start?** Begin with **STEP 1** and let me know if you hit any issues!
