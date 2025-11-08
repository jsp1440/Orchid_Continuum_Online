#!/bin/bash
# Mac Setup Script for iNaturalist Orchid Downloader
# This script sets everything up automatically

echo ""
echo "========================================"
echo "🌺 iNaturalist Orchid Downloader Setup"
echo "========================================"
echo ""

# Create orchid_downloads folder in home directory
echo "📁 Creating ~/orchid_downloads folder..."
mkdir -p ~/orchid_downloads

# Move the downloader script to that folder
echo "📥 Moving downloader script..."
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cp "$SCRIPT_DIR/MAC_iNaturalist_Downloader.py" ~/orchid_downloads/

# Navigate to the folder
cd ~/orchid_downloads

echo ""
echo "✅ Setup complete!"
echo ""
echo "========================================"
echo "📊 Ready to Download Orchid Data"
echo "========================================"
echo "📁 Location: ~/orchid_downloads"
echo "📝 Script: MAC_iNaturalist_Downloader.py"
echo ""
echo "To start downloading:"
echo "  cd ~/orchid_downloads"
echo "  python3 MAC_iNaturalist_Downloader.py"
echo ""
echo "This will download:"
echo "  • ~20,000 orchid observations"
echo "  • ~30,000 images"
echo "  • 52 data fields per image"
echo ""
echo "Files will be saved to:"
echo "  • inaturalist_orchids/ (images)"
echo "  • orchid_data_52_fields.csv (data)"
echo "========================================"
echo ""
echo "Press Enter to start download now, or Ctrl+C to exit"
read

# Run the downloader
python3 MAC_iNaturalist_Downloader.py
