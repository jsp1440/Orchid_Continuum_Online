#!/bin/bash
#
# Launch Multi-Database Enrichment System
# ========================================
# Uses GBIF + iNaturalist (EOL is down)
#

echo "=========================================="
echo "  MULTI-DATABASE ENRICHMENT SYSTEM"
echo "=========================================="
echo ""
echo "Data Sources:"
echo "  ✅ GBIF - Occurrence, elevation, distribution"
echo "  ✅ iNaturalist - Observations, images, phenology"
echo "  ❌ EOL - Currently down (connection issues)"
echo ""
echo "This will enrich ALL 5,915 orchids with:"
echo "  - Taxonomic verification"
echo "  - Occurrence counts and distribution"
echo "  - Community observation data"
echo "  - Conservation status"
echo "  - Additional images"
echo ""
echo "Features:"
echo "  ✅ Progress tracking (resume if interrupted)"
echo "  ✅ Rate-limited (respectful to APIs)"
echo "  ✅ Real-time status updates"
echo ""
echo "Starting in 3 seconds..."
sleep 3

python automated_multi_database_enrichment.py
