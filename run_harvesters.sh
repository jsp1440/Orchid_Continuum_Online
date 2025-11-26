#!/bin/bash
# Minimal harvester startup
nohup python3 workers/gbif_expanded_worker.py gbif-1 > logs/gbif-1.log 2>&1 &
nohup python3 workers/gbif_expanded_worker.py gbif-2 > logs/gbif-2.log 2>&1 &
nohup python3 workers/gbif_expanded_worker.py gbif-3 > logs/gbif-3.log 2>&1 &
nohup python3 workers/gbif_expanded_worker.py gbif-4 > logs/gbif-4.log 2>&1 &
nohup python3 workers/api_fallback_coordinator.py > logs/api_coordinator.log 2>&1 &
echo "🌺 Harvesters started (4 GBIF + API Coordinator)"
