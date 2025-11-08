#!/usr/bin/env python3
"""Complete Project Audit - What's Real vs What's Clutter"""
import os
import re
from pathlib import Path

print("="*80)
print("🔍 ORCHID CONTINUUM PROJECT AUDIT")
print("="*80)
print(f"\nAccount: fcospresident")
print(f"Project: workspace")
print(f"Database: neondb (157 tables, 11,717 images, 35,320 taxa)")
print("\n" + "="*80)

# Find all route files
route_files = []
for f in Path('.').glob('**/*.py'):
    if 'routes' in f.name.lower() or 'widget' in f.name.lower():
        route_files.append(f)

# Check which are actually imported in app.py
active_routes = []
inactive_routes = []

with open('app.py', 'r') as f:
    app_content = f.read()

for rf in route_files:
    module_name = rf.stem
    if module_name in app_content or str(rf).replace('.py', '') in app_content:
        active_routes.append(rf)
    else:
        inactive_routes.append(rf)

print(f"\n✅ ACTIVE ROUTES (Imported in app.py): {len(active_routes)}")
for r in sorted(active_routes)[:20]:
    print(f"   - {r.name}")
if len(active_routes) > 20:
    print(f"   ... and {len(active_routes) - 20} more")

print(f"\n❌ INACTIVE/UNUSED ROUTES: {len(inactive_routes)}")
print(f"   (Not imported - can be archived/deleted)")

# Find widget routes specifically
widgets = [r for r in active_routes if 'widget' in r.name.lower()]
print(f"\n🎨 ACTIVE WIDGETS: {len(widgets)}")
for w in sorted(widgets):
    print(f"   - {w.name}")

# Check what's registered in app.py
print(f"\n📋 BLUEPRINTS REGISTERED IN APP.PY:")
blueprint_pattern = r'app\.register_blueprint\((\w+)'
matches = re.findall(blueprint_pattern, app_content)
for bp in sorted(set(matches))[:15]:
    print(f"   - {bp}")
if len(set(matches)) > 15:
    print(f"   ... and {len(set(matches)) - 15} more")

print("\n" + "="*80)
print("💡 RECOMMENDATION")
print("="*80)
print("1. Keep the ACTIVE routes (imported in app.py)")
print("2. Archive/delete the INACTIVE routes")
print(f"3. This will reduce clutter from {len(route_files)} to {len(active_routes)} files")
print("="*80)
