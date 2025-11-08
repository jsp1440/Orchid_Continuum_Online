#!/usr/bin/env python3
"""Quick status check for orchid harvester"""
import os
import psycopg2
from datetime import datetime, timedelta

DATABASE_URL = os.environ.get('DATABASE_URL')

print("=" * 80)
print("🌺 ORCHID HARVESTER STATUS CHECK")
print("=" * 80)
print(f"Time: {datetime.now().strftime('%I:%M:%S %p')}\n")

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# Total counts
cur.execute("""
    SELECT 
        COUNT(*) as total_images,
        COUNT(DISTINCT taxonomy_id) as species_count,
        COUNT(DISTINCT country) as countries,
        MAX(created_at) as most_recent
    FROM orchid_images
""")
total_images, species_count, countries, most_recent = cur.fetchone()

print(f"📊 TOTALS:")
print(f"   Images: {total_images:,}")
print(f"   Species: {species_count:,}")
print(f"   Countries: {countries}")
print(f"   Most recent: {most_recent}\n")

# Recent activity
for mins in [1, 5, 15, 60]:
    cur.execute(f"""
        SELECT COUNT(*) 
        FROM orchid_images 
        WHERE created_at >= NOW() - INTERVAL '{mins} minutes'
    """)
    count = cur.fetchone()[0]
    rate = count / mins if mins > 0 else 0
    print(f"   Last {mins:2d} min: {count:4d} images ({rate:.1f}/min)")

# Species progress
cur.execute("""
    SELECT 
        COUNT(CASE WHEN img_count >= 30 THEN 1 END) as at_goal,
        COUNT(CASE WHEN img_count BETWEEN 10 AND 29 THEN 1 END) as progress,
        COUNT(CASE WHEN img_count BETWEEN 1 AND 9 THEN 1 END) as started
    FROM (
        SELECT taxonomy_id, COUNT(*) as img_count
        FROM orchid_images
        GROUP BY taxonomy_id
    ) counts
""")
at_goal, progress, started = cur.fetchone()

print(f"\n🎯 SPECIES PROGRESS:")
print(f"   ✅ At goal (30+): {at_goal}")
print(f"   🔄 In progress (10-29): {progress}")
print(f"   🌱 Started (1-9): {started}")

cur.execute("SELECT COUNT(*) FROM orchid_taxonomy")
total_species = cur.fetchone()[0]
remaining = total_species - (at_goal + progress + started)
print(f"   ⏳ Not started: {remaining:,}")

conn.close()

print("=" * 80)
