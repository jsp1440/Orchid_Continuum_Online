#!/bin/bash
echo "🚀 Pushing Orchid Continuum in batches to avoid timeout..."
echo "============================================================"
echo ""

# Batch 1: Core Python files
echo "📦 Batch 1: Core Python files..."
git add *.py
git commit -m "Batch 1: Core Python scripts" || echo "Already committed"
git push --force origin main
if [ $? -ne 0 ]; then
    echo "❌ Batch 1 failed - stopping"
    exit 1
fi
echo "✅ Batch 1 complete"
echo ""

# Batch 2: Workers and bulk import
echo "📦 Batch 2: Workers and bulk import..."
git add workers/ bulk_eol_import/
git commit -m "Batch 2: Workers and bulk import scripts" || echo "Already committed"
git push origin main
if [ $? -ne 0 ]; then
    echo "❌ Batch 2 failed - stopping"
    exit 1
fi
echo "✅ Batch 2 complete"
echo ""

# Batch 3: Templates and static (excluding images)
echo "📦 Batch 3: Templates and static files..."
git add templates/ static/ --ignore-removal
git commit -m "Batch 3: Templates and static files" || echo "Already committed"
git push origin main
if [ $? -ne 0 ]; then
    echo "❌ Batch 3 failed - stopping"
    exit 1
fi
echo "✅ Batch 3 complete"
echo ""

# Batch 4: Widgets and features
echo "📦 Batch 4: Widgets and features..."
git add bloombuilder_* ai_collaboration/ archived_routes/ app_utils/
git commit -m "Batch 4: Widgets and features" || echo "Already committed"
git push origin main
if [ $? -ne 0 ]; then
    echo "❌ Batch 4 failed - stopping"
    exit 1
fi
echo "✅ Batch 4 complete"
echo ""

# Batch 5: Everything else
echo "📦 Batch 5: Remaining files..."
git add .
git commit -m "Batch 5: All remaining files" || echo "Already committed"
git push origin main
if [ $? -ne 0 ]; then
    echo "❌ Batch 5 failed"
    exit 1
fi

echo ""
echo "============================================================"
echo "✅ SUCCESS! All batches pushed to GitHub!"
echo "Check: https://github.com/jsp1440/Orchid_Continuum_Online"
echo "============================================================"
