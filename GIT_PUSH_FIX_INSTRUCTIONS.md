# Git Push Fix - Large Files Issue

## Problem
Git push failing because external_databases contains files >100MB (GitHub's limit)

## Files Blocking Push
- `external_databases/zenodo_data/media_manifest_2020_02_04.tgz`
- `external_databases/zenodo_data/provider_ids.csv.gz`
- `external_databases/eol_traitbank/traits_all.zip`
- `external_databases/eol_traitbank/trait_bank/*.csv` (multiple large files)

## ✅ Fix Applied
Updated `.gitignore` to exclude these large files

## 🔧 Manual Steps Required (Run These):

```bash
# Step 1: Remove large files from Git tracking (keeps files on disk)
cd /home/runner/workspace
git rm --cached -r external_databases/*.csv
git rm --cached -r external_databases/*.gz
git rm --cached -r external_databases/*.zip
git rm --cached -r external_databases/*.tgz
git rm --cached -r external_databases/eol_traitbank/
git rm --cached -r external_databases/zenodo_data/

# Step 2: Commit the .gitignore changes
git add .gitignore
git commit -m "Fix: Exclude large data files from Git (>100MB)"

# Step 3: Now push (should work!)
git push origin main
```

## Why This Works
- Files stay on your Replit server (needed for the app)
- Git no longer tracks them (prevents push errors)
- .gitignore prevents re-adding them
- GitHub only gets code, not massive data files

## After Push Succeeds
Render will auto-deploy with all the Render fixes!
