#!/bin/bash
# Launcher for Reserved VM workers
# Creates unique worker ID with 'rv' prefix

WORKER_NUM=$((RANDOM % 10000))
WORKER_ID="rv-${WORKER_NUM}"

echo "Starting Reserved VM worker: $WORKER_ID"
python3 julius_multi_source_worker.py "$WORKER_ID"
