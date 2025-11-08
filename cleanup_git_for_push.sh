#!/bin/bash
# Git cleanup script to remove large files before push

echo "🧹 Git Cleanup Script - Removing large files from git tracking"
echo "================================================================"
echo ""
echo "This will:"
echo "  ✅ Keep all files on your disk (nothing deleted)"
echo "  ✅ Remove large images from git tracking"
echo "  ✅ Make git push much faster"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cancelled"
    exit 1
fi

echo ""
echo "Step 1: Removing large directories from git index..."
git rm -r --cached static/images/ 2>/dev/null || echo "  (static/images/ already removed or doesn't exist)"
git rm -r --cached static/uploads/ 2>/dev/null || echo "  (static/uploads/ already removed or doesn't exist)"
git rm -r --cached downloads/ 2>/dev/null || echo "  (downloads/ already removed or doesn't exist)"
git rm -r --cached attached_assets/ 2>/dev/null || echo "  (attached_assets/ already removed or doesn't exist)"

echo ""
echo "Step 2: Committing the .gitignore changes..."
git add .gitignore
git commit -m "Add large image directories to .gitignore" || echo "  (Already committed)"

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "Next steps:"
echo "  1. Commit your other code changes: git add . && git commit -m 'Your message'"
echo "  2. Push to GitHub: git push origin main"
echo ""
echo "Your git repo should now be much smaller and push successfully!"
