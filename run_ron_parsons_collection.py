#!/usr/bin/env python3
"""
Quick script to run Ron Parsons collection
Finds thousands of public domain orchid photos from:
- flowershots.net
- ronsorchids.weebly.com
"""

from automated_scraper_controller import automated_controller
import json

print("=" * 70)
print("🚀 RON PARSONS PUBLIC DOMAIN ORCHID PHOTO COLLECTION")
print("=" * 70)
print()
print("Sources:")
print("  📸 flowershots.net - Main Orchid Photogallery")
print("  🏠 ronsorchids.weebly.com - Personal orchid collection")
print()
print("Starting collection...")
print("=" * 70)
print()

# Run Ron Parsons collection only
result = automated_controller.run_ron_parsons_collection()

print()
print("=" * 70)
print("COLLECTION RESULTS:")
print("=" * 70)
print(json.dumps(result, indent=2))
print()
print(f"✅ Total collected: {result.get('collected', 0)} orchid photos")
print(f"⏱️  Duration: {result.get('duration', 0):.1f} seconds")
print()
