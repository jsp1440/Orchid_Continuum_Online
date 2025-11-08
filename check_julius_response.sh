#!/bin/bash
echo "🔍 Checking for Julius responses..."
echo ""
echo "Database messages from Julius:"
psql $DATABASE_URL -c "SELECT task_id, created_at, result_summary FROM ai_communication WHERE from_agent = 'julius' ORDER BY created_at DESC LIMIT 5;"
echo ""
echo "Files from Julius:"
ls -lah ai_collaboration/julius_to_replit/ 2>&1
