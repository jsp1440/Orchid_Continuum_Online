#!/usr/bin/env python3
"""
Master Automated Collection Script
Runs full collection cycle from all partner photographers and breeding databases
"""

from automated_scraper_controller import automated_controller
import json
from datetime import datetime

print("=" * 80)
print("🌺 ORCHID CONTINUUM - AUTOMATED PARTNER COLLECTION SYSTEM")
print("=" * 80)
print()
print("Partner Photographers & Data Sources:")
print("  🌿 Gary Yong Gee (orchids.yonggee.name)")
print("  🌺 Roberta Fox (orchidcentral.org - 19 galleries)")
print("  📸 Ron Parsons (flowershots.net + ronsorchids.weebly.com)")
print("  🌅 Sunset Valley Orchids - Species (Sarcochilus, Catasetum, Zygopetalum, Cattleya)")
print("  🧬 Sunset Valley Orchids - Hybrids (Breeding data)")
print()
print(f"Collection started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)
print()

# Run full collection cycle
results = automated_controller.run_full_collection_cycle()

# Display summary
print()
print("=" * 80)
print("📊 FINAL COLLECTION SUMMARY")
print("=" * 80)
print()
print(f"Total orchids collected: {results['summary']['total_collected']}")
print(f"Duration: {results['summary']['cycle_duration']/60:.1f} minutes")
print(f"Sources processed: {results['summary']['sources_processed']}")
print()
print("Individual Source Results:")
print("-" * 80)

for source_name, source_result in results['sources'].items():
    status = "✅" if source_result.get('success', False) else "❌"
    collected = source_result.get('collected', 0)
    duration = source_result.get('duration', 0)
    
    print(f"{status} {source_name:20s}: {collected:5d} items in {duration:6.1f}s")

print()
print("=" * 80)
print("🎉 AUTOMATED COLLECTION COMPLETE!")
print("=" * 80)

# Save results to JSON
with open('collection_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print()
print("📄 Detailed results saved to: collection_results.json")
print()
