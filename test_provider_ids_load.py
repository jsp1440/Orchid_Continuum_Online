#!/usr/bin/env python3
import gzip
import csv
import time

print("Testing provider_ids.csv.gz load speed...")
start = time.time()
count = 0

with gzip.open('external_databases/zenodo_data/provider_ids.csv.gz', 'rt') as f:
    reader = csv.DictReader(f)
    for row in reader:
        count += 1
        if count % 500000 == 0:
            elapsed = time.time() - start
            print(f"Loaded {count:,} rows in {elapsed:.1f}s ({count/elapsed:.0f} rows/sec)")
        if count >= 1000000:  # Just test first million
            break

elapsed = time.time() - start
print(f"\nTotal: {count:,} rows in {elapsed:.1f}s")
print(f"Estimated total time for full file: {(5600000/count)*elapsed/60:.1f} minutes")
