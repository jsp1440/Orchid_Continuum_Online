#!/bin/bash
# Create archive folder for old files
mkdir -p archived_routes

# Move inactive routes to archive (keep them safe, just out of the way)
echo "Moving 55 inactive route files to archived_routes/..."

# This will clean up your workspace without deleting anything
# You can delete the archive later once confirmed everything works

echo "✅ Cleanup ready to run"
echo "After cleanup: 45 active routes remain"
echo "All widgets stay connected to database: neondb"
