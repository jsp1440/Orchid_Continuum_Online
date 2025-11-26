#!/bin/bash
# Simplified harvester startup - minimal dependencies
python3 workers/gbif_expanded_worker.py gbif-1 &
python3 workers/gbif_expanded_worker.py gbif-2 &
python3 workers/gbif_expanded_worker.py gbif-3 &
python3 workers/gbif_expanded_worker.py gbif-4 &
python3 workers/gbif_expanded_worker.py gbif-5 &
python3 workers/api_fallback_coordinator.py &
wait
