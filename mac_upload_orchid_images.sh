#!/bin/bash
# Mac Script: Find and Package Orchid Images Downloaded This Week
# Run this on your Mac Terminal

echo "========================================="
echo "🌺 ORCHID IMAGE FINDER & PACKAGER"
echo "========================================="
echo ""

# Create output directory
OUTPUT_DIR="$HOME/Desktop/orchid_images_upload"
mkdir -p "$OUTPUT_DIR"

# Find images from the last 7 days
echo "🔍 Searching for orchid images downloaded in the last 7 days..."
echo ""

# Common download locations
SEARCH_PATHS=(
    "$HOME/Downloads"
    "$HOME/Desktop"
    "/tmp/eol_orchid_rescue"
    "$HOME/Documents/orchid_downloads"
)

# Counters
TOTAL_FOUND=0

# Search each location
for SEARCH_PATH in "${SEARCH_PATHS[@]}"; do
    if [ -d "$SEARCH_PATH" ]; then
        echo "📂 Searching: $SEARCH_PATH"
        
        # Find image files modified in last 7 days
        FOUND=$(find "$SEARCH_PATH" -type f \
            \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" \) \
            -mtime -7 \
            -not -path "*/.*" \
            2>/dev/null | wc -l | tr -d ' ')
        
        if [ "$FOUND" -gt 0 ]; then
            echo "  ✅ Found $FOUND images"
            
            # Copy to output directory
            find "$SEARCH_PATH" -type f \
                \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" \) \
                -mtime -7 \
                -not -path "*/.*" \
                -exec cp {} "$OUTPUT_DIR/" \; 2>/dev/null
            
            TOTAL_FOUND=$((TOTAL_FOUND + FOUND))
        fi
    fi
done

echo ""
echo "========================================="
echo "📊 RESULTS"
echo "========================================="
echo "Total images found: $TOTAL_FOUND"
echo ""

if [ "$TOTAL_FOUND" -eq 0 ]; then
    echo "❌ No images found from the last 7 days"
    echo ""
    echo "Try these commands to search manually:"
    echo "  find ~/Downloads -name '*.jpg' -mtime -14"
    echo "  find ~/Desktop -name '*.jpg' -mtime -14"
    exit 1
fi

# Create zip file
ZIP_FILE="$HOME/Desktop/orchid_images_$(date +%Y%m%d_%H%M%S).zip"
echo "📦 Creating archive..."
cd "$OUTPUT_DIR"
zip -r "$ZIP_FILE" . >/dev/null 2>&1

if [ -f "$ZIP_FILE" ]; then
    ZIP_SIZE=$(du -h "$ZIP_FILE" | cut -f1)
    echo "  ✅ Created: $(basename "$ZIP_FILE")"
    echo "  📏 Size: $ZIP_SIZE"
    echo ""
    echo "========================================="
    echo "📤 UPLOAD INSTRUCTIONS"
    echo "========================================="
    echo ""
    echo "1. Open your Replit workspace:"
    echo "   https://replit.com/@fcospresident"
    echo ""
    echo "2. Drag and drop this file into Replit:"
    echo "   $ZIP_FILE"
    echo ""
    echo "3. Tell the agent: 'I uploaded orchid_images.zip'"
    echo ""
    echo "========================================="
    
    # Clean up temp directory
    rm -rf "$OUTPUT_DIR"
    
    # Open the Desktop folder
    open "$HOME/Desktop"
else
    echo "❌ Error creating zip file"
    exit 1
fi
