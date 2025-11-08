"""
Master Download Manager - Runs all downloads in parallel
- GBIF living photos (9,774 from CSV)
- iDigBio herbarium specimens (10,000 target)
- Tropicos herbarium specimens (5,000 target)
"""
import os
import subprocess
import sys
import time
from datetime import datetime

print("=" * 80)
print("🌺 ORCHID CONTINUUM - MASTER DOWNLOAD MANAGER")
print("=" * 80)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("\nStarting 3 parallel download processes...\n")

# Start GBIF import
print("1️⃣  Starting GBIF living photos (9,774 images)...")
gbif_log = open('/tmp/gbif_import.log', 'w')
gbif_process = subprocess.Popen(
    ['python', 'import_gbif_52_columns.py'],
    stdout=gbif_log,
    stderr=subprocess.STDOUT
)
print(f"   ✅ GBIF download started (PID: {gbif_process.pid})")

time.sleep(2)

# Start Tropicos herbarium download
print("\n2️⃣  Starting Tropicos herbarium sheets (5,000 target)...")
tropicos_log = open('/tmp/tropicos_herbarium.log', 'w')
tropicos_process = subprocess.Popen(
    ['python', 'download_tropicos_herbarium.py'],
    stdout=tropicos_log,
    stderr=subprocess.STDOUT
)
print(f"   ✅ Tropicos download started (PID: {tropicos_process.pid})")

time.sleep(2)

# Start iDigBio herbarium download
print("\n3️⃣  Starting iDigBio herbarium sheets (10,000 target)...")
idigbio_log = open('/tmp/idigbio_herbarium.log', 'w')
idigbio_process = subprocess.Popen(
    ['python', 'download_idigbio_herbarium.py'],
    stdout=idigbio_log,
    stderr=subprocess.STDOUT
)
print(f"   ✅ iDigBio download started (PID: {idigbio_process.pid})")

time.sleep(2)

# Start EOL Batch 2 download
print("\n4️⃣  Starting EOL Batch 2 living photos (95,000 target)...")
eol_log = open('/tmp/eol_batch2.log', 'w')
eol_process = subprocess.Popen(
    ['python', 'download_eol_batch2.py'],
    stdout=eol_log,
    stderr=subprocess.STDOUT
)
print(f"   ✅ EOL Batch 2 download started (PID: {eol_process.pid})")

print("\n" + "=" * 80)
print("📊 ALL 4 DOWNLOADS RUNNING IN BACKGROUND")
print("=" * 80)
print(f"📁 Log files:")
print(f"   - GBIF: /tmp/gbif_import.log (9,774 images)")
print(f"   - Tropicos: /tmp/tropicos_herbarium.log (5,000 herbarium)")
print(f"   - iDigBio: /tmp/idigbio_herbarium.log (10,000 herbarium)")
print(f"   - EOL Batch 2: /tmp/eol_batch2.log (95,000 photos)")
print("\n💡 These will run for 12-24 hours. Check progress anytime!")
print("=" * 80)

# Keep script running
try:
    while True:
        time.sleep(3600)  # Check every hour
        
        # Check if processes are still running
        gbif_running = gbif_process.poll() is None
        tropicos_running = tropicos_process.poll() is None
        idigbio_running = idigbio_process.poll() is None
        eol_running = eol_process.poll() is None
        
        if not (gbif_running or tropicos_running or idigbio_running or eol_running):
            print("\n✅ All downloads completed!")
            break
            
except KeyboardInterrupt:
    print("\n⏸️  Download manager stopped (downloads continue in background)")
    sys.exit(0)
