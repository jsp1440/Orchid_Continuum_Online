#!/bin/bash
# Check download progress

echo "📊 DOWNLOAD PROGRESS CHECK"
echo "======================================"
date
echo ""

# Check if processes are running
RUNNING=$(ps aux | grep -E "(import_gbif|download_idigbio|download_tropicos|download_eol)" | grep -v grep | wc -l)
echo "🔄 Active downloads: $RUNNING"
echo ""

# Check GBIF progress
if [ -f "attached_assets/gbif_52_columns" ]; then
    GBIF_COUNT=$(ls attached_assets/gbif_52_columns/*.jpg 2>/dev/null | wc -l)
    GBIF_SIZE=$(du -sh attached_assets/gbif_52_columns 2>/dev/null | cut -f1)
    echo "1️⃣  GBIF: $GBIF_COUNT images ($GBIF_SIZE)"
fi

# Check iDigBio progress
if [ -d "attached_assets/idigbio_herbarium" ]; then
    IDIGBIO_COUNT=$(ls attached_assets/idigbio_herbarium/*.jpg 2>/dev/null | wc -l)
    IDIGBIO_SIZE=$(du -sh attached_assets/idigbio_herbarium 2>/dev/null | cut -f1)
    echo "2️⃣  iDigBio: $IDIGBIO_COUNT images ($IDIGBIO_SIZE)"
fi

# Check Tropicos progress
if [ -d "attached_assets/tropicos_herbarium" ]; then
    TROPICOS_COUNT=$(ls attached_assets/tropicos_herbarium/*.jpg 2>/dev/null | wc -l)
    TROPICOS_SIZE=$(du -sh attached_assets/tropicos_herbarium 2>/dev/null | cut -f1)
    echo "3️⃣  Tropicos: $TROPICOS_COUNT images ($TROPICOS_SIZE)"
fi

# Check EOL Batch 2 progress
if [ -d "attached_assets/eol_batch2" ]; then
    EOL_COUNT=$(ls attached_assets/eol_batch2/*.jpg 2>/dev/null | wc -l)
    EOL_SIZE=$(du -sh attached_assets/eol_batch2 2>/dev/null | cut -f1)
    echo "4️⃣  EOL Batch 2: $EOL_COUNT images ($EOL_SIZE)"
fi

echo ""
echo "======================================"
echo "📋 Recent log activity:"
echo ""
tail -5 logs/gbif.log 2>/dev/null | head -2
tail -5 logs/idigbio.log 2>/dev/null | head -2
tail -5 logs/tropicos.log 2>/dev/null | head -2
tail -5 logs/eol_batch2.log 2>/dev/null | head -2
