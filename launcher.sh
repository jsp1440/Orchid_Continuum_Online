#!/bin/bash
# Julius Multi-Source Worker Launcher
# Launches a single worker with a unique ID

WORKER_ID="julius-$(date +%s)-$$"
python3 -u julius_multi_source_worker.py "$WORKER_ID" >> worker_${WORKER_ID}.log 2>&1 &
disown
