#!/bin/bash
# Simple server start without GBIF enrichment

export LD_LIBRARY_PATH="/nix/store/$(ls /nix/store | grep glibc | head -1)/lib:${LD_LIBRARY_PATH:-}"

echo "🌸 Starting Flask application..."
exec gunicorn --workers 2 --bind 0.0.0.0:5000 --timeout 120 --access-logfile - --error-logfile - main:app
