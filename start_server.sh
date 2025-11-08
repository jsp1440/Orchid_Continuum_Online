#!/bin/bash
# Simple deployment startup - no background processes
set -e

echo "🌸 Starting Flask application..."
exec gunicorn --workers 1 --bind 0.0.0.0:5000 --timeout 120 --access-logfile - --error-logfile - wsgi:app
