#!/bin/bash
# Continuous import runner
cd /home/runner/workspace
while true; do
    echo "Starting import at $(date)"
    python import_gbif_52_columns.py
    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 0 ]; then
        echo "Import completed successfully!"
        break
    else
        echo "Import exited with code $EXIT_CODE, restarting in 5 seconds..."
        sleep 5
    fi
done
