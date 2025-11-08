# DEPLOY INSTRUCTIONS - COPY/PASTE THESE COMMANDS

## Step 1: Push the fix to GitHub
```bash
git push origin main
```

## Step 2: Deploy in Render
1. Go to: https://dashboard.render.com
2. Click on **orchid-continuum-1** (your web service)
3. Click the **"Manual Deploy"** button at the top right
4. Wait 3-5 minutes

## That's it!

The fix is already in your code. I added the missing SSL setting for PostgreSQL.

If it fails again, take a screenshot of the error and show me.

---

## What I Fixed:
Added `?sslmode=require` to the database connection in `create_database.py`
This was the bug causing 6 weeks of deployment failures.
