#!/bin/bash
# Git Push Fix Script
# Bypasses askpass authentication issue

echo "🔧 Git Push Fix for Orchid Continuum"
echo "====================================="

# Remove lock file if exists
rm -f .git/index.lock 2>/dev/null

# Disable askpass
unset GIT_ASKPASS
unset SSH_ASKPASS

# Configure git to use credential in URL
export GIT_TERMINAL_PROMPT=0

# Get the current remote URL
REMOTE_URL=$(git remote get-url origin 2>/dev/null)
echo "Current remote: $REMOTE_URL"

# Check if we have changes
git add -A
if git diff --cached --quiet; then
    echo "No new changes to commit."
else
    echo ""
    echo "Committing changes..."
    git commit -m "Update harvesters: source-first architecture, fix metadata

- Add source-first workers (GBIF, iNaturalist, iDigBio, ALA, EOL)  
- Fix metadata storage in all workers
- Use centralized taxonomy_mapper for data integrity"
fi

echo ""
echo "Attempting push..."

# Try push with credentials embedded in URL
git push origin main 2>&1

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ SUCCESS! Pushed to GitHub!"
    echo "Now redeploy on Render.com"
else
    echo ""
    echo "❌ Push failed. Try this manual approach:"
    echo ""
    echo "1. Open a new Shell tab"
    echo "2. Run: git push https://YOUR_TOKEN@github.com/jsp1440/Orchid_Continuum_Online.git main"
    echo ""
    echo "Or use GitHub Desktop / VS Code to push from your local machine."
fi
