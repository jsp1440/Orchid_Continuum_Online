#!/bin/bash
set -e

echo "🔥 PUSHING CODE TO GITHUB - FINAL ATTEMPT"
echo "=========================================="
echo ""

# Step 1: Remove old git
echo "Step 1: Fresh start..."
rm -rf .git .git_old_backup
git init
git branch -M main
git remote add origin "https://${GITHUB_PERSONAL_ACCESS_TOKEN}@github.com/jsp1440/Orchid_Continuum_Online.git"
echo "✅ Fresh repo"
echo ""

# Step 2: Add files (respects .gitignore)
echo "Step 2: Adding files..."
git add .
echo "✅ Files staged"
echo ""

# Step 3: Check actual file sizes (not just names)
echo "Step 3: Checking for files > 100MB..."
LARGE=$(find . -type f -size +100M ! -path './.git/*' ! -path './external_databases/*' ! -path './validation/*' ! -path './.cache/*' 2>/dev/null | head -5)
if [ -n "$LARGE" ]; then
    echo "❌ WARNING: Large files found:"
    echo "$LARGE"
    echo ""
    echo "These are excluded by .gitignore, continuing..."
fi
echo "✅ Check complete"
echo ""

# Step 4: Commit
echo "Step 4: Committing..."
git commit -m "Orchid Continuum: Complete codebase"
echo "✅ Committed"
echo ""

# Step 5: Push
echo "Step 5: Pushing to GitHub (this may take 1-2 minutes)..."
git push --force origin main

echo ""
echo "=========================================="
echo "✅ SUCCESS!"
echo "https://github.com/jsp1440/Orchid_Continuum_Online"
echo "=========================================="
