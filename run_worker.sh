#!/usr/bin/env bash
set -euo pipefail
: "${WORKER_ID:?missing}"
: "${DATABASE_URL:?missing}"
: "${TROPICOS_API_KEY:?missing}"
: "${BHL_API_KEY:?missing}"
while true; do
  python3 julius_multi_source_worker.py
  echo "$(date -Is) $WORKER_ID exited; restarting in 5s" >> logs/$WORKER_ID.log
  sleep 5
done
