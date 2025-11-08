#!/bin/bash
echo "🧹 Removing large data files from git..."
echo "=========================================="

# Remove large data directories from git tracking (keeps files on disk)
git rm -r --cached external_databases/ 2>/dev/null || echo "  external_databases/ not tracked"
git rm -r --cached validation/ 2>/dev/null || echo "  validation/ not tracked"
git rm --cached occurrences_manual 2>/dev/null || echo "  occurrences_manual not tracked"

echo ""
echo "📦 Committing .gitignore update..."
git add .gitignore
git commit -m "Exclude large data files from git" || echo "Already committed"

echo ""
echo "🚀 Pushing CODE ONLY to GitHub (no data files)..."
git push --force origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "============================================"
    echo "✅ SUCCESS! Code pushed to GitHub!"
    echo "Check: https://github.com/jsp1440/Orchid_Continuum_Online"
    echo ""
    echo "Note: Large data files excluded (they stay in database)"
    echo "============================================"
else
    echo ""
    echo "❌ Push failed - see error above"
fi
