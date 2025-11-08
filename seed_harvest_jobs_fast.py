#!/usr/bin/env python3
"""Fast job seeding - no geographic lookups"""
import os
import psycopg2

DATABASE_URL = os.environ.get('DATABASE_URL')

print("🌺 FAST SEEDING - Populating harvest jobs...")

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# Simple batch insert - priority based on current image count only
cur.execute("""
    INSERT INTO harvest_jobs (
        taxonomy_id, scientific_name, status, priority,
        current_image_count, target_image_count,
        created_at, updated_at
    )
    SELECT 
        ot.id,
        ot.scientific_name,
        'pending',
        CASE 
            WHEN COUNT(oi.id) = 0 THEN 100
            WHEN COUNT(oi.id) < 5 THEN 80
            WHEN COUNT(oi.id) < 10 THEN 60
            WHEN COUNT(oi.id) < 20 THEN 40
            ELSE 20
        END as priority,
        COUNT(oi.id),
        30,
        NOW(),
        NOW()
    FROM orchid_taxonomy ot
    LEFT JOIN orchid_images oi ON ot.id = oi.taxonomy_id
    WHERE NOT EXISTS (
        SELECT 1 FROM harvest_jobs hj WHERE hj.taxonomy_id = ot.id
    )
    GROUP BY ot.id, ot.scientific_name
    HAVING COUNT(oi.id) < 30
""")

seeded = cur.rowcount
conn.commit()

print(f"✅ Seeded {seeded:,} jobs!")

# Summary
cur.execute("""
    SELECT 
        CASE 
            WHEN priority >= 80 THEN 'High (80+): 0-4 images'
            WHEN priority >= 60 THEN 'Med-High (60-79): 5-9 images'
            WHEN priority >= 40 THEN 'Medium (40-59): 10-19 images'
            ELSE 'Low (20-39): 20-29 images'
        END as tier,
        COUNT(*)
    FROM harvest_jobs
    WHERE status = 'pending'
    GROUP BY tier
    ORDER BY MIN(priority) DESC
""")

print("\n📊 PRIORITY TIERS:")
for tier, count in cur.fetchall():
    print(f"   {tier}: {count:,}")

conn.close()
