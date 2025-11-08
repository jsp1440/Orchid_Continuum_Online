#!/bin/bash
echo "========================================="
echo "ORCHID CONTINUUM - PROGRESS CHECK"
echo "========================================="
echo ""

echo "📊 Database Status:"
psql $DATABASE_URL -c "
SELECT 
    (SELECT COUNT(*) FROM orchid_taxonomy) as total_species,
    (SELECT COUNT(*) FROM orchid_images WHERE image_source LIKE '%EOL%') as eol_images,
    (SELECT COUNT(DISTINCT taxonomy_id) FROM orchid_images WHERE image_source LIKE '%EOL%') as species_with_eol_images;
" 2>&1

echo ""
echo "🔄 EOL Enrichment Status:"
if ps aux | grep "enrich_eol_from_zenodo" | grep -v grep > /dev/null; then
    echo "✅ Running (PID: $(ps aux | grep enrich_eol_from_zenodo | grep -v grep | awk '{print $2}'))"
    echo ""
    echo "Recent log output:"
    tail -10 validation/eol_enrichment.log
else
    echo "❌ Not running"
fi

echo ""
echo "💬 Julius AI Status:"
psql $DATABASE_URL -c "SELECT COUNT(*) as messages_from_julius FROM ai_communication WHERE from_agent = 'julius';" 2>&1

echo ""
echo "========================================="
