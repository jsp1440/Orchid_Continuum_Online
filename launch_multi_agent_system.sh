#!/bin/bash

# Multi-Agent AI System Launcher for Orchid Continuum
# Coordinates specialized AI agents for autonomous research tasks

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     ORCHID CONTINUUM - MULTI-AGENT AI SYSTEM                ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "Available Agents:"
echo "  🖼️  Image Acquisition Specialist - Finds optimal image sources"
echo "  📊 Data Enrichment Specialist - Identifies enrichment targets"
echo "  🌍 Geographic Analysis Specialist - Analyzes spatial patterns"
echo "  ✅ Quality Control Specialist - Validates data quality"
echo "  🎯 Research Coordinator - Synthesizes all findings"
echo ""
echo "Choose analysis type:"
echo "  1) Comprehensive (all agents + coordinator)"
echo "  2) Image Acquisition Analysis"
echo "  3) Data Enrichment Analysis (EOL, GBIF, iNaturalist)"
echo "  4) Geographic & Elevation Analysis"
echo "  5) Quality Control Check"
echo ""
read -p "Enter choice (1-5): " choice

case $choice in
  1) python multi_agent_orchestrator.py <<< "1" ;;
  2) python multi_agent_orchestrator.py <<< "2" ;;
  3) python multi_agent_orchestrator.py <<< "3" ;;
  4) python multi_agent_orchestrator.py <<< "4" ;;
  5) python multi_agent_orchestrator.py <<< "5" ;;
  *) echo "Invalid choice"; exit 1 ;;
esac

echo ""
echo "✅ Multi-agent analysis complete!"
echo ""
echo "📊 View results:"
echo "   SELECT * FROM agent_insights ORDER BY created_at DESC LIMIT 10;"
echo ""
echo "🔄 Process agent findings:"
echo "   python julius_insight_processor.py"
