#!/usr/bin/env python3
"""
Quick test of AI Vision + GBIF/EOL batch enrichment
Tests on 3 orchids to verify the complete pipeline
"""

import sys
sys.path.insert(0, '.')

from app import app
from batch_gbif_eol_enrichment import BatchOrchidEnrichment

if __name__ == '__main__':
    print("🧪 Testing AI Vision Enrichment Pipeline")
    print("=" * 60)
    
    with app.app_context():
        # Initialize enrichment with AI vision enabled
        enricher = BatchOrchidEnrichment(enable_ai_vision=True)
        
        # Test on just 3 orchids
        enricher.run_batch_enrichment(limit=3)
        
        print("\n✅ Test complete!")
        print(f"📊 AI Vision Analyzed: {enricher.stats['ai_vision_analyzed']}")
