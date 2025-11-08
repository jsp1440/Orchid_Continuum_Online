#!/bin/bash
echo "🚀 Pushing Orchid Continuum to GitHub..."
echo "=========================================="
echo ""

# Try to push and capture the output
git push -v origin main 2>&1

# Check if it worked
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ SUCCESS! All files pushed to GitHub!"
else
    echo ""
    echo "❌ PUSH FAILED - See error above"
    echo ""
    echo "Common fixes:"
    echo "  1. If timeout: Need to push in smaller batches"
    echo "  2. If 500 error: GitHub is rejecting large push"
    echo "  3. If auth error: Token needs refresh"
fi
