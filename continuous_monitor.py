#!/usr/bin/env python3
"""
CONTINUOUS HARVESTER MONITOR
Monitors Julius + Replit workers, auto-restarts if stopped, reports every 15 min
"""
import os
import sys
import time
import psycopg2
import subprocess
from datetime import datetime

DATABASE_URL = os.environ.get('DATABASE_URL')

def get_stats():
    """Get current harvester statistics"""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Overall totals
    cur.execute("SELECT COUNT(*) FROM orchid_images")
    total_images = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(DISTINCT taxonomy_id) FROM orchid_images")
    total_species = cur.fetchone()[0]
    
    # Recent activity
    cur.execute("""
        SELECT COUNT(*) FROM orchid_images 
        WHERE created_at > NOW() - INTERVAL '15 minutes'
    """)
    last_15_min = cur.fetchone()[0]
    
    cur.execute("""
        SELECT COUNT(*) FROM orchid_images 
        WHERE created_at > NOW() - INTERVAL '1 hour'
    """)
    last_hour = cur.fetchone()[0]
    
    # By source (last hour)
    cur.execute("""
        SELECT image_source, COUNT(*) 
        FROM orchid_images 
        WHERE created_at > NOW() - INTERVAL '1 hour'
        GROUP BY image_source
        ORDER BY COUNT(*) DESC
    """)
    by_source = cur.fetchall()
    
    # Active workers
    cur.execute("""
        SELECT lease_owner, COUNT(*) 
        FROM harvest_jobs 
        WHERE status='leased'
        GROUP BY lease_owner
        ORDER BY lease_owner
    """)
    active_workers = cur.fetchall()
    
    # Queue status
    cur.execute("""
        SELECT status, COUNT(*) 
        FROM harvest_jobs 
        GROUP BY status
    """)
    queue = dict(cur.fetchall())
    
    conn.close()
    
    return {
        'total_images': total_images,
        'total_species': total_species,
        'last_15_min': last_15_min,
        'last_hour': last_hour,
        'by_source': by_source,
        'active_workers': active_workers,
        'queue': queue,
        'rate_per_min': last_15_min / 15.0,
        'rate_per_hour': last_hour
    }

def check_replit_workers():
    """Check if Replit workers are running"""
    result = subprocess.run(
        ['ps', 'aux'],
        capture_output=True,
        text=True
    )
    
    replit_workers = []
    for line in result.stdout.split('\n'):
        if 'julius_multi_source_worker.py' in line and 'replit-m' in line:
            replit_workers.append(line)
    
    return len(replit_workers)

def start_replit_workers(count=2):
    """Start Replit workers if not running"""
    for i in range(1, count + 1):
        worker_name = f"replit-m{i}"
        log_file = f"replit_m{i}.log"
        
        subprocess.Popen(
            ['python3', '-u', 'julius_multi_source_worker.py', worker_name],
            stdout=open(log_file, 'a'),
            stderr=subprocess.STDOUT
        )
        print(f"  Started {worker_name}")
        time.sleep(1)

def print_report(stats):
    """Print monitoring report"""
    print("\n" + "="*80)
    print(f"🌺 ORCHID HARVESTER MONITOR - {datetime.now().strftime('%I:%M:%S %p')}")
    print("="*80)
    
    print(f"\n📊 TOTALS:")
    print(f"   Images: {stats['total_images']:,}")
    print(f"   Species: {stats['total_species']:,}")
    
    print(f"\n📈 PERFORMANCE:")
    print(f"   Last 15 min: {stats['last_15_min']} images ({stats['rate_per_min']:.1f}/min)")
    print(f"   Last hour: {stats['last_hour']} images ({stats['rate_per_hour']}/hour)")
    
    if stats['by_source']:
        print(f"\n🗂️  BY SOURCE (Last Hour):")
        for source, count in stats['by_source']:
            print(f"   {source}: {count}")
    
    print(f"\n👥 ACTIVE WORKERS ({len(stats['active_workers'])}):")
    if stats['active_workers']:
        for worker, count in stats['active_workers']:
            worker_type = "Julius" if "julius" in worker else "Replit"
            print(f"   {worker} ({worker_type}): {count} jobs")
    else:
        print("   ⚠️  NO ACTIVE WORKERS!")
    
    print(f"\n📋 QUEUE:")
    print(f"   Pending: {stats['queue'].get('pending', 0):,}")
    print(f"   Completed: {stats['queue'].get('completed', 0):,}")
    print(f"   Leased: {stats['queue'].get('leased', 0):,}")
    
    # Calculate projection
    if stats['rate_per_hour'] > 0:
        target = 1_059_810  # 30 images × 35,327 species
        remaining = target - stats['total_images']
        hours_needed = remaining / stats['rate_per_hour']
        days_needed = hours_needed / 24
        print(f"\n🎯 PROJECTION:")
        print(f"   Need {remaining:,} more images to reach goal")
        print(f"   At current rate: {hours_needed:.0f} hours ({days_needed:.1f} days)")
    
    print("="*80 + "\n")

def main():
    """Main monitoring loop"""
    print("🚀 CONTINUOUS MONITOR STARTED")
    print("   Checking every 15 minutes")
    print("   Auto-restarting Replit workers if stopped\n")
    
    cycle = 0
    
    while True:
        cycle += 1
        
        # Get stats
        stats = get_stats()
        
        # Print report
        print_report(stats)
        
        # Check and restart Replit workers
        replit_count = check_replit_workers()
        if replit_count == 0:
            print("⚠️  Replit workers stopped! Restarting...")
            start_replit_workers(2)
            print("✅ Restarted 2 Replit workers\n")
        elif replit_count < 2:
            print(f"⚠️  Only {replit_count} Replit worker(s) running! Starting more...")
            start_replit_workers(2 - replit_count)
        
        # Alert if NO workers at all
        if len(stats['active_workers']) == 0:
            print("🔴 CRITICAL: NO ACTIVE WORKERS!")
            print("   Julius workers may have stopped. Check with Julius.\n")
        
        # Alert if rate too low
        if stats['rate_per_min'] < 1.0 and len(stats['active_workers']) > 0:
            print("⚠️  WARNING: Low harvesting rate!")
            print(f"   Only {stats['rate_per_min']:.1f} images/min with {len(stats['active_workers'])} workers\n")
        
        # Wait 15 minutes
        print(f"💤 Sleeping 15 minutes... (Cycle {cycle})")
        time.sleep(900)  # 15 minutes

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Monitor stopped by user")
    except Exception as e:
        print(f"\n\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
