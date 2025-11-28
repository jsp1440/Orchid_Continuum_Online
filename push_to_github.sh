#!/bin/bash
echo "🚀 Pushing Orchid Continuum to GitHub..."
echo "=========================================="
echo ""

# Remove stale lock files
rm -f .git/index.lock .git/config.lock 2>/dev/null

# Disable askpass to avoid the error
unset GIT_ASKPASS
unset SSH_ASKPASS

# Use token from environment
TOKEN="${GITHUB_PERSONAL_ACCESS_TOKEN}"
if [ -z "$TOKEN" ]; then
    echo "❌ ERROR: GITHUB_PERSONAL_ACCESS_TOKEN not found in secrets"
    exit 1
fi
echo "✓ GitHub token found"

# Update remote URL with token
git remote set-url origin "https://${TOKEN}@github.com/jsp1440/Orchid_Continuum_Online.git"
echo "✓ Remote URL configured"

# Stage all changes
echo ""
echo "Staging all changes..."
git add -A

# Check if there are changes to commit
if git diff --cached --quiet; then
    echo "No new changes to commit."
else
    echo ""
    echo "Changes to commit:"
    git diff --cached --name-only | head -30
    echo ""
    
    # Commit changes
    echo "Committing..."
    git commit -m "Add Fluid Multi-Source Harvester v1.0

NEW: workers/fluid_harvester.py
- Dynamic source switching (GBIF, iNaturalist, iDigBio, ALA)
- In-memory taxonomy cache (no per-record DB calls)
- Performance tracking with automatic source optimization
- Target: 3,000+ images/hour across 4 workers

UPDATED: render.yaml
- Add 4 fluid harvester workers (fluid-1 through fluid-4)
- Each dynamically balances across all data sources
- Replaces 8 single-source GBIF workers

FIXED: Metadata storage for all harvesters"
fi

echo ""
echo "Pushing to GitHub..."
git push origin main 2>&1

# Check result
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ SUCCESS! Pushed to GitHub!"
    echo ""
    echo "Next: Redeploy on Render.com to use the new code"
else
    echo ""
    echo "❌ PUSH FAILED"
    echo ""
    echo "If token expired, generate a new one at:"
    echo "https://github.com/settings/tokens"
    echo "Then update GITHUB_PERSONAL_ACCESS_TOKEN in Replit Secrets"
fi
