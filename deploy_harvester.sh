#!/bin/bash
# Orchid Harvester Deployment Entry Point
# This runs on the Reserved VM and starts the entire system

echo "🌺 ORCHID HARVESTER - STARTING ON RESERVED VM"
echo "=============================================="

# Start the supervisor (which starts seeder + workers)
python3 JULIUS_SUPERVISOR.py
