#!/bin/bash
echo "🚀 Pushing Orchid Continuum to GitHub..."
echo "=========================================="
echo ""

# Remove stale lock file if exists
if [ -f ".git/index.lock" ]; then
    echo "Removing stale git lock file..."
    rm -f .git/index.lock
fi

# Stage all changes
echo "Staging all changes..."
git add -A

# Check if there are changes to commit
if git diff --cached --quiet; then
    echo "No changes to commit. Attempting push..."
else
    echo ""
    echo "Changes to commit:"
    git diff --cached --name-only | head -30
    echo ""
    
    # Commit changes
    echo "Committing changes..."
    git commit -m "Update harvesters: source-first workers, fix metadata storage

- Add source-first workers (GBIF, iNaturalist, iDigBio, ALA, EOL)
- Add high-throughput workers for each data source
- Update gbif_worker.py to use centralized taxonomy_mapper
- Fix metadata storage (country, coords, dates, JSONB fields)
- All harvesters now validate via taxonomy_mapper (no discovery)"
fi

echo ""
echo "Pushing to GitHub..."
git push -v origin main 2>&1

# Check if it worked
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ SUCCESS! All files pushed to GitHub!"
    echo ""
    echo "Next step: Redeploy on Render.com"
else
    echo ""
    echo "❌ PUSH FAILED - See error above"
    echo ""
    echo "Common fixes:"
    echo "  1. If timeout: Try 'git push --no-thin origin main'"
    echo "  2. If 500 error: Try pushing in smaller commits"
    echo "  3. If auth error: Token may need refresh"
    echo "  4. If conflicts: Run 'git pull origin main' first"
fi
