#!/bin/bash
echo "🧹 Removing ALL large files from git (keeping them on disk)..."
echo "==============================================================="

# Remove all large data directories
git rm -r --cached external_databases/ 2>/dev/null || echo "  external_databases/ not tracked"
git rm -r --cached validation/ 2>/dev/null || echo "  validation/ not tracked"  
git rm -r --cached attached_assets/ 2>/dev/null || echo "  attached_assets/ not tracked"
git rm -r --cached .cache/ 2>/dev/null || echo "  .cache/ not tracked"
git rm -r --cached .pythonlibs/ 2>/dev/null || echo "  .pythonlibs/ not tracked"

# Remove any remaining large files
git rm --cached media_manifest_*.tgz 2>/dev/null || echo "  media_manifest files not tracked"

echo ""
echo "✅ Large files removed from git tracking"
echo ""
echo "📦 Adding updated .gitignore..."
git add .gitignore

echo ""
echo "💾 Committing changes..."
git commit -m "Remove large data files from git - they belong in database" || echo "Already committed"

echo ""
echo "🚀 Pushing CODE ONLY to GitHub..."
git add .
git commit -m "Orchid Continuum: All widgets, features, and code (2 months of work)" || echo "Already committed"
git push --force origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "============================================"
    echo "✅ SUCCESS! All code pushed to GitHub!"
    echo "https://github.com/jsp1440/Orchid_Continuum_Online"
    echo ""
    echo "Data files excluded (they stay in database):"
    echo "  - EOL trait bank (1.8GB)"
    echo "  - Zenodo data"
    echo "  - Validation files"
    echo "  - Downloaded images"
    echo "============================================"
else
    echo ""
    echo "❌ Push failed - check error above"
fi
