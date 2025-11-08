#!/bin/bash
echo "🚀 Pushing Orchid Continuum to GitHub"
echo "======================================"
echo ""

# Step 1: Remove large files from git
echo "Step 1: Removing large data files from git..."
git rm -rf --cached external_databases/
git rm -rf --cached validation/
git rm -rf --cached attached_assets/
git rm -rf --cached .cache/
git rm -rf --cached .pythonlibs/
git rm -f --cached media_manifest_*.tgz 2>/dev/null
git rm -f --cached *.tgz 2>/dev/null
echo "✅ Large files removed"
echo ""

# Step 2: Add .gitignore
echo "Step 2: Updating .gitignore..."
git add .gitignore
git commit -m "Update gitignore to exclude large data files"
echo "✅ .gitignore updated"
echo ""

# Step 3: Add all code files
echo "Step 3: Adding all code files..."
git add .
git commit -m "Orchid Continuum: Complete project with all widgets and features"
echo "✅ Code files committed"
echo ""

# Step 4: Push to GitHub
echo "Step 4: Pushing to GitHub..."
git push --force origin main

echo ""
echo "======================================"
echo "✅ DONE! Check GitHub:"
echo "https://github.com/jsp1440/Orchid_Continuum_Online"
echo "======================================"
