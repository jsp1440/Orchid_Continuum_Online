#!/bin/bash
# Render Initialization Script - Downloads EOL datasets
# Runs automatically on first deploy

echo "=" | tr '=' '=' | head -c 80 && echo
echo "🌸 ORCHID CONTINUUM - Render Initialization"
echo "=" | tr '=' '=' | head -c 80 && echo
echo ""

# Create directories
mkdir -p validation external_databases/eol_traitbank

# Download EOL TraitBank (565 MB - phenotypic traits)
if [ ! -f external_databases/eol_traitbank/traits_all.zip ]; then
    echo "📥 Downloading EOL TraitBank (phenotypic trait data)..."
    echo "   Source: Zenodo record 13305577"
    echo "   Size: ~565 MB"
    echo ""
    
    cd external_databases/eol_traitbank
    curl -L --progress-bar -o traits_all.zip \
        "https://zenodo.org/records/13305577/files/traits_all.zip?download=1"
    
    if [ -f traits_all.zip ]; then
        echo ""
        echo "✅ TraitBank downloaded successfully"
        echo "📦 Extracting files..."
        unzip -q traits_all.zip
        echo "✅ Extraction complete"
        
        # Show what we got
        echo ""
        echo "Extracted files:"
        ls -lh trait_bank/*.csv 2>/dev/null | awk '{print "   " $9 " (" $5 ")"}'
    else
        echo "❌ TraitBank download failed"
    fi
    
    cd ../..
else
    echo "✅ EOL TraitBank already downloaded"
fi

echo ""
echo "=" | tr '=' '=' | head -c 80 && echo
echo "✅ INITIALIZATION COMPLETE"
echo "=" | tr '=' '=' | head -c 80 && echo
echo ""
echo "Next steps:"
echo "  1. Upload validation/eol_extracted_images.jsonl (1.6GB) via Render shell"
echo "  2. Run: python validation/process_eol_traits.py"
echo "  3. Run: python validation/link_eol_data.py"
echo ""
