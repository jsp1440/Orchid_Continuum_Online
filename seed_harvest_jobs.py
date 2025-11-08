#!/usr/bin/env python3
"""
Seed harvest_jobs table with species needing images
Prioritizes: Australia, PNG, SE Asia regions
"""
import os
import psycopg2
from datetime import datetime

DATABASE_URL = os.environ.get('DATABASE_URL')

print("=" * 80)
print("🌺 SEEDING HARVEST JOBS QUEUE")
print("=" * 80)

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# Get all species with their current image counts
print("\n📊 Analyzing species and image counts...")
cur.execute("""
    SELECT 
        ot.id,
        ot.scientific_name,
        COUNT(oi.id) as current_count
    FROM orchid_taxonomy ot
    LEFT JOIN orchid_images oi ON ot.id = oi.taxonomy_id
    GROUP BY ot.id, ot.scientific_name
    HAVING COUNT(oi.id) < 30
    ORDER BY COUNT(oi.id) ASC
""")

species_to_seed = cur.fetchall()
print(f"Found {len(species_to_seed):,} species needing images\n")

# Define priority regions (higher priority = harvested first)
PRIORITY_REGIONS = {
    'AU': 100,  # Australia
    'PG': 95,   # Papua New Guinea
    'ID': 90,   # Indonesia
    'MY': 85,   # Malaysia
    'PH': 85,   # Philippines
    'TH': 80,   # Thailand
    'VN': 80,   # Vietnam
    'CR': 75,   # Costa Rica
    'PA': 75,   # Panama
    'KE': 70,   # Kenya
    'TZ': 70,   # Tanzania
    'MG': 70,   # Madagascar
    'ZA': 70,   # South Africa
}

print("🎯 Assigning priorities based on geographic distribution...")
seeded = 0
skipped = 0

for tax_id, sci_name, current_count in species_to_seed:
    # Check if job already exists
    cur.execute("SELECT id FROM harvest_jobs WHERE taxonomy_id = %s", (tax_id,))
    if cur.fetchone():
        skipped += 1
        continue
    
    # Determine priority based on where this species has been found
    cur.execute("""
        SELECT DISTINCT country_code
        FROM orchid_images
        WHERE taxonomy_id = %s AND country_code IS NOT NULL
        LIMIT 5
    """, (tax_id,))
    
    country_codes = [row[0] for row in cur.fetchall()]
    
    # Calculate priority (higher = more important)
    priority = 0
    for code in country_codes:
        if code in PRIORITY_REGIONS:
            priority = max(priority, PRIORITY_REGIONS[code])
    
    # If no priority regions found, use default based on current count
    if priority == 0:
        if current_count == 0:
            priority = 50  # Medium priority for species with no images
        else:
            priority = 30  # Lower priority for species with some images
    
    # Insert job
    cur.execute("""
        INSERT INTO harvest_jobs (
            taxonomy_id, scientific_name, status, priority,
            current_image_count, target_image_count,
            created_at, updated_at
        ) VALUES (
            %s, %s, 'pending', %s, %s, 30, NOW(), NOW()
        )
    """, (tax_id, sci_name, priority, current_count))
    
    seeded += 1
    
    if seeded % 1000 == 0:
        conn.commit()
        print(f"  Seeded {seeded:,} jobs...")

conn.commit()

# Show summary
print(f"\n✅ SEEDING COMPLETE!")
print(f"   Total seeded: {seeded:,}")
print(f"   Skipped (already exist): {skipped:,}")

# Show priority breakdown
print(f"\n📊 PRIORITY BREAKDOWN:")
cur.execute("""
    SELECT 
        CASE 
            WHEN priority >= 90 THEN 'High (90+)'
            WHEN priority >= 70 THEN 'Medium-High (70-89)'
            WHEN priority >= 50 THEN 'Medium (50-69)'
            ELSE 'Low (<50)'
        END as priority_tier,
        COUNT(*) as count
    FROM harvest_jobs
    WHERE status = 'pending'
    GROUP BY priority_tier
    ORDER BY MIN(priority) DESC
""")

for tier, count in cur.fetchall():
    print(f"   {tier}: {count:,} species")

conn.close()
print("\n" + "=" * 80)
