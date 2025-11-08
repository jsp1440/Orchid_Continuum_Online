#!/bin/bash
set -e

# Find libstdc++ library
LIBSTDCPP_DIR=$(find /nix/store -type f -name 'libstdc++.so.6' -print -quit 2>/dev/null | xargs dirname)

if [ -z "$LIBSTDCPP_DIR" ]; then
    echo "Error: Could not find libstdc++.so.6"
    exit 1
fi

export LD_LIBRARY_PATH="$LIBSTDCPP_DIR:${LD_LIBRARY_PATH:-}"
echo "✅ Using libstdc++.so.6 from: $LIBSTDCPP_DIR"

# Start Flask
echo "🌸 Starting Flask application..."
cd /home/runner/workspace
exec gunicorn --workers 1 --bind 0.0.0.0:5000 --timeout 120 --access-logfile - --error-logfile - main:app
