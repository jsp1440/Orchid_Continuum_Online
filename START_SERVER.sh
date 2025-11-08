#!/bin/bash
# Simple server starter for The Orchid Continuum
# Run this script to start the server and keep it alive

echo "============================================================"
echo "🌺 Starting The Orchid Continuum Server"
echo "============================================================"
echo ""
echo "Your server will be available at:"
echo "  - https://workspace.fcospresident.repl.co/health"
echo "  - https://workspace.fcospresident.repl.co/bloombuilder"
echo "  - https://workspace.fcospresident.repl.co/julius/status"
echo ""
echo "Press Ctrl+C to stop the server"
echo "============================================================"
echo ""

cd /home/runner/workspace
exec python3 main.py
