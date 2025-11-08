#!/bin/bash
# Create Clean Export for Fresh GitHub Repo
# Run this in Replit Shell: bash create_clean_repo.sh

echo "🚀 Creating clean export for fresh GitHub repo..."
echo ""

# Step 1: Create export directory
echo "Step 1: Creating export directory..."
cd /home/runner
rm -rf orchid_clean_export
mkdir orchid_clean_export
cd /home/runner/workspace

# Step 2: Copy only essential files (NOT the large ones)
echo "Step 2: Copying code files (this may take a minute)..."

# Copy Python files
cp *.py /home/runner/orchid_clean_export/ 2>/dev/null

# Copy templates
cp -r templates /home/runner/orchid_clean_export/

# Copy static
cp -r static /home/runner/orchid_clean_export/

# Copy essential directories
for dir in ai_collaboration ai_orchid_identification docs migration_package routes utils validation; do
    if [ -d "$dir" ]; then
        cp -r "$dir" /home/runner/orchid_clean_export/
    fi
done

# Copy config files
cp requirements.txt /home/runner/orchid_clean_export/ 2>/dev/null
cp render.yaml /home/runner/orchid_clean_export/ 2>/dev/null
cp .gitignore /home/runner/orchid_clean_export/ 2>/dev/null
cp Procfile /home/runner/orchid_clean_export/ 2>/dev/null
cp replit.md /home/runner/orchid_clean_export/ 2>/dev/null

# Copy external_databases (but NOT the large folders!)
mkdir -p /home/runner/orchid_clean_export/external_databases
cp external_databases/*.py /home/runner/orchid_clean_export/external_databases/ 2>/dev/null

echo ""
echo "Step 3: Checking size..."
du -sh /home/runner/orchid_clean_export

echo ""
echo "✅ Clean export created!"
echo ""
echo "📋 NEXT STEPS:"
echo ""
echo "1. Create new GitHub repo at: https://github.com/new"
echo "   - Name: orchid-continuum-clean (or any name)"
echo "   - Private repo"
echo "   - Don't initialize with README"
echo ""
echo "2. Run these commands:"
echo ""
echo "   cd /home/runner/orchid_clean_export"
echo "   git init"
echo "   git add ."
echo "   git commit -m 'Initial deploy: 7 widgets + Render fixes'"
echo "   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git"
echo "   git push -u origin main"
echo ""
echo "3. Update Render to point at new repo"
echo ""
echo "Total time: ~15 minutes to deployment!"
echo ""
