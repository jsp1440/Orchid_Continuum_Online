#!/usr/bin/env python3
"""Find all inactive route files to archive"""
import re
from pathlib import Path

# Read app.py to see what's imported
with open('app.py', 'r') as f:
    app_content = f.read()

# Find all route/widget files
all_route_files = []
for pattern in ['**/routes*.py', '**/*widget*.py', '**/*_routes.py']:
    all_route_files.extend(Path('.').glob(pattern))

# Remove duplicates
all_route_files = list(set(all_route_files))

# Check which are imported
inactive = []
for rf in all_route_files:
    # Skip if in subdirectories we want to keep
    if any(x in str(rf) for x in ['migration_package', 'simple_migration', 'verify', 'archived', '__pycache__']):
        continue
    
    module_name = rf.stem
    if module_name not in app_content and str(rf.name) not in app_content:
        inactive.append(rf)

print(f"Found {len(inactive)} inactive route files:")
for f in sorted(inactive):
    print(f"  {f}")

# Save list
with open('inactive_files.txt', 'w') as f:
    for fi in sorted(inactive):
        f.write(str(fi) + '\n')

print(f"\n✅ List saved to inactive_files.txt")
