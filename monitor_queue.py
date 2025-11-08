#!/usr/bin/env python3
"""
HARVEST QUEUE MONITOR
Real-time dashboard for queue-based harvesting system
"""
import os
import psycopg2
from datetime import datetime, timedelta

DATABASE_URL = os.environ.get('DATABASE_URL')

def clear_screen():
    """Clear terminal (works on Unix)"""
    print("\033[2J\033[H", end="")

def show_dashboard():
    """Display monitoring dashboard"""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    clear_screen()
    print("=" * 90)
    print("🌺 HARVEST QUEUE MONITOR".center(90))
    print("=" * 90)
    print(f"Time: {datetime.now().strftime('%I:%M:%S %p')}\n")
    
    # Job Status Summary
    print("📊 JOB QUEUE STATUS:")
    cur.execute("""
        SELECT 
            status,
            COUNT(*) as count,
            ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) as pct
        FROM harvest_jobs
        GROUP BY status
        ORDER BY 
            CASE status
                WHEN 'pending' THEN 1
                WHEN 'leased' THEN 2
                WHEN 'completed' THEN 3
                WHEN 'failed' THEN 4
            END
    """)
    
    for status, count, pct in cur.fetchall():
        emoji = {'pending': '⏳', 'leased': '🔄', 'completed': '✅', 'failed': '❌'}.get(status, '•')
        print(f"   {emoji} {status.upper():12} {count:6,} jobs ({pct:5.1f}%)")
    
    # Active Workers
    print(f"\n👷 ACTIVE WORKERS:")
    cur.execute("""
        SELECT 
            lease_owner,
            COUNT(*) as jobs_leased,
            MIN(leased_at) as first_lease
        FROM harvest_jobs
        WHERE status = 'leased'
        GROUP BY lease_owner
        ORDER BY jobs_leased DESC
    """)
    
    workers = cur.fetchall()
    if workers:
        for worker, jobs, first_lease in workers:
            age = (datetime.now() - first_lease).total_seconds() / 60 if first_lease else 0
            print(f"   {worker}: {jobs} jobs (active {age:.1f} min)")
    else:
        print("   No active workers")
    
    # Recent Activity (last 15 min)
    print(f"\n⚡ RECENT ACTIVITY:")
    for mins in [1, 5, 15]:
        cur.execute("""
            SELECT COUNT(*)
            FROM harvest_jobs
            WHERE completed_at >= NOW() - INTERVAL '%s minutes'
        """, (mins,))
        completed = cur.fetchone()[0]
        rate = completed / mins if mins > 0 else 0
        print(f"   Last {mins:2d} min: {completed:4d} jobs completed ({rate:.1f}/min)")
    
    # Images Added
    print(f"\n📸 IMAGES HARVESTED:")
    for mins in [1, 5, 15, 60]:
        cur.execute("""
            SELECT COUNT(*)
            FROM orchid_images
            WHERE created_at >= NOW() - INTERVAL '%s minutes'
        """, (mins,))
        count = cur.fetchone()[0]
        rate = count / mins if mins > 0 else 0
        print(f"   Last {mins:2d} min: {count:5d} images ({rate:.1f}/min)")
    
    # Overall Progress
    print(f"\n🎯 OVERALL PROGRESS:")
    cur.execute("""
        SELECT 
            COUNT(*) as total_jobs,
            COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
            COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed,
            MIN(created_at) as started,
            SUM(current_image_count) as total_images
        FROM harvest_jobs
    """)
    
    total, completed, failed, started, images = cur.fetchone()
    pct_done = (completed / total * 100) if total > 0 else 0
    
    if started:
        elapsed = (datetime.now() - started).total_seconds() / 3600  # hours
        if elapsed > 0:
            jobs_per_hour = completed / elapsed
            eta_hours = (total - completed) / jobs_per_hour if jobs_per_hour > 0 else 0
            print(f"   Completed: {completed:,} / {total:,} jobs ({pct_done:.1f}%)")
            print(f"   Failed: {failed:,}")
            print(f"   Total images: {images:,}")
            print(f"   Running: {elapsed:.1f} hours")
            print(f"   Rate: {jobs_per_hour:.1f} jobs/hour")
            if eta_hours < 100:
                print(f"   ETA: {eta_hours:.1f} hours to complete")
    
    # Top Species Being Processed
    print(f"\n🔬 CURRENTLY PROCESSING:")
    cur.execute("""
        SELECT scientific_name, lease_owner, leased_at
        FROM harvest_jobs
        WHERE status = 'leased'
        ORDER BY leased_at DESC
        LIMIT 5
    """)
    
    for sci_name, worker, leased_at in cur.fetchall():
        age = (datetime.now() - leased_at).total_seconds() / 60 if leased_at else 0
        print(f"   [{worker}] {sci_name[:55]} ({age:.1f}m ago)")
    
    conn.close()
    print("=" * 90)
    print("Press Ctrl+C to exit | Refreshing in 10 seconds...")

if __name__ == "__main__":
    import time
    try:
        while True:
            show_dashboard()
            time.sleep(10)
    except KeyboardInterrupt:
        print("\n\n👋 Monitor stopped.")
