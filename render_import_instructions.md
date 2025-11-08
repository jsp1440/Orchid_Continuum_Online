# Import Orchid Data to Render PostgreSQL

## What You Have

✅ **orchid_records.csv** (4.2MB) - 5,888 orchids
✅ **orchid_taxonomy.csv** (920KB) - 7,438 taxonomy entries

## How to Import to Render

### Step 1: Download CSV Files from Replit

1. In Replit file explorer, find these files:
   - `orchid_records.csv`
   - `orchid_taxonomy.csv`
2. Download both files to your computer

### Step 2: Upload to a Temporary Location

Option A: Use GitHub Gist (easiest)
1. Go to https://gist.github.com
2. Create a new secret gist
3. Upload both CSV files
4. Click "Create secret gist"
5. Click "Raw" for each file and copy the URLs

Option B: Use your own file hosting

### Step 3: Import to Render Database

1. Go to Render Dashboard → Your PostgreSQL Database
2. Click **"Connect"** → **"External Connection"**  
3. Copy the **psql** command (looks like: `psql postgresql://user:pass@host/db`)
4. Run in your local terminal OR use Render's Shell

### Step 4: Run Import Commands

**If you uploaded to GitHub Gist** (replace URLs with your actual raw gist URLs):

```bash
# Connect to Render database
psql postgresql://your-connection-string

# Then run these commands:

# Import taxonomy first (no foreign keys)
\copy orchid_taxonomy FROM PROGRAM 'curl https://gist.githubusercontent.com/YOUR_USERNAME/YOUR_GIST_ID/raw/orchid_taxonomy.csv' WITH CSV HEADER;

# Import orchid records
\copy orchid_record FROM PROGRAM 'curl https://gist.githubusercontent.com/YOUR_USERNAME/YOUR_GIST_ID/raw/orchid_records.csv' WITH CSV HEADER;
```

**If CSVs are on your computer:**

```bash
# From your computer terminal (where CSV files are downloaded):
psql postgresql://your-connection-string

# Then:
\copy orchid_taxonomy FROM 'orchid_taxonomy.csv' WITH CSV HEADER;
\copy orchid_record FROM 'orchid_records.csv' WITH CSV HEADER;
```

### Step 5: Verify Import

```sql
SELECT COUNT(*) FROM orchid_record;
-- Should return: 5888

SELECT COUNT(*) FROM orchid_taxonomy;  
-- Should return: 7438
```

### Step 6: Redeploy Your Service

After import completes:
1. Go to Render Dashboard → **orchid-continuum-1**
2. Click **"Manual Deploy"** → **"Deploy latest commit"**
3. Wait for deployment
4. Visit your site - gallery should show orchids! 🌸

## Troubleshooting

**If tables don't exist:**
Run this first to create tables (app.py does this automatically, but just in case):
```sql
-- Run your Flask app once to create tables
-- OR create manually if needed
```

**If you get duplicate key errors:**
```sql
-- Clear existing data first
TRUNCATE orchid_record, orchid_taxonomy CASCADE;
-- Then run import again
```
