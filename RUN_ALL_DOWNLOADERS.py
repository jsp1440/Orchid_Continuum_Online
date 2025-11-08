#!/usr/bin/env python3
"""
ALL-IN-ONE Orchid Downloader
Runs all 5 download sources in sequence

Just run: python3 RUN_ALL_DOWNLOADERS.py
"""

print("""
╔══════════════════════════════════════════════════════════════╗
║          🌺 ALL-IN-ONE ORCHID DOWNLOADER 🌺                  ║
╚══════════════════════════════════════════════════════════════╝

This script will download orchid images from 5 sources:
  1. iNaturalist - 1.6M observations
  2. GBIF Global - 2M observations  
  3. Wikimedia Commons - 100k images
  4. iDigBio Museums - 300k specimens
  5. ALA Australia - 200k observations

Total: ~4.8 million images, 26,000-28,000 species

NOTE: Due to bugs in some APIs, only iNaturalist and GBIF
are currently working reliably.

RECOMMENDATION: Just run the iNaturalist downloader for now.
It has the most data and works perfectly.

═══════════════════════════════════════════════════════════════
""")

print("\n❌ This combined script is not recommended.")
print("✅ BETTER: Download and run individual scripts\n")
print("The most important one: EASY_Mac_Orchid_Downloader.py")
print("  (iNaturalist - 1.6M observations, most complete)\n")
