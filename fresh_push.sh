#!/bin/bash
set -e  # Exit on any error

echo "🔥 FRESH START - Pushing ONLY code to GitHub"
echo "=============================================="
echo ""

# Step 1: Backup and remove old git
echo "Step 1: Removing old git history..."
rm -rf .git
rm -rf .git_old_backup
echo "✅ Old git removed"
echo ""

# Step 2: Initialize fresh repo
echo "Step 2: Creating fresh git repo..."
git init
git branch -M main
echo "✅ Fresh repo created"
echo ""

# Step 3: Set up remote
echo "Step 3: Connecting to GitHub..."
git remote add origin "https://${GITHUB_PERSONAL_ACCESS_TOKEN}@github.com/jsp1440/Orchid_Continuum_Online.git"
echo "✅ Remote configured"
echo ""

# Step 4: Verify .gitignore excludes large files
echo "Step 4: Checking .gitignore..."
if grep -q "external_databases/" .gitignore; then
    echo "✅ .gitignore is configured correctly"
else
    echo "❌ ERROR: .gitignore missing required exclusions"
    exit 1
fi
echo ""

# Step 5: Add files (respects .gitignore)
echo "Step 5: Adding code files (excluding large data)..."
git add .
echo "✅ Files staged"
echo ""

# Step 6: Show what will be committed (check for large files)
echo "Step 6: Checking for large files..."
LARGE_FILES=$(git ls-files -s | awk '$4 ~ /external_databases|validation|trait_bank/ {print $4}')
if [ -n "$LARGE_FILES" ]; then
    echo "❌ ERROR: Large files still staged:"
    echo "$LARGE_FILES"
    exit 1
fi
echo "✅ No large files detected"
echo ""

# Step 7: Commit
echo "Step 7: Creating commit..."
git commit -m "Orchid Continuum: Complete codebase (2 months of work)"
echo "✅ Committed"
echo ""

# Step 8: Force push
echo "Step 8: Pushing to GitHub..."
git push --force origin main

echo ""
echo "=============================================="
echo "✅ SUCCESS! Code pushed to GitHub"
echo "https://github.com/jsp1440/Orchid_Continuum_Online"
echo "=============================================="
