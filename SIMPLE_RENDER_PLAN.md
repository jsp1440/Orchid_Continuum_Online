# Simple Render Deployment Plan

## What's Actually Happening

You DON'T need to upload anything from your computer. Everything downloads directly on Render from Zenodo.

---

## The 3-Step Process

### STEP 1: Deploy Your App (10 minutes)

1. **Push code to GitHub**
   ```bash
   git add .
   git commit -m "Ready for Render"
   git push origin main
   ```

2. **Create Render Database**
   - Go to https://render.com
   - New → PostgreSQL
   - Name: `orchid-db`
   - Plan: $7/month
   - Copy the database URL

3. **Deploy Web Service**
   - New → Web Service
   - Connect GitHub repo
   - Add environment variable:
     - `DATABASE_URL` = (paste from step 2)
   - Deploy!

---

### STEP 2: Download Data on Render (30 minutes)

Once deployed, open Render Shell and run:

```bash
# Download everything from Zenodo (runs automatically)
bash validation/setup_eol_data_on_render.sh
```

This downloads:
- ✅ EOL image URLs (3 GB of CSVs)
- ✅ EOL TraitBank (565 MB)

**No files from your computer needed!**

---

### STEP 3: Process and Import (1 hour)

Still in Render Shell:

```bash
# Extract image URLs from CSVs
python validation/extract_eol_images_from_csv.py

# Process trait data
python validation/process_eol_traits.py

# Link images to traits
python validation/link_eol_data.py

# Import to database
python validation/import_eol_to_db.py
```

**Done!** You'll have:
- 35K taxonomy entries
- 5.6M EOL image URLs
- 3M+ trait records
- All linked together

---

## Cost

- PostgreSQL: $7/month
- Web Service: $0 (free tier) or $7/month
- **Total: $7-14/month**

---

## Ready?

Just say "let's deploy" and I'll guide you through STEP 1!
