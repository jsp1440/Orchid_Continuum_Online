#!/usr/bin/env python
"""
Reclaim Stalled Harvester Jobs
This script resets jobs that are stuck in 'leased' state so workers can process them again.
Jobs are considered stalled if they've been leased for more than 10 minutes.
"""
import os
import psycopg2
from datetime import datetime, timedelta

DATABASE_URL = os.environ.get('DATABASE_URL')

def reclaim_stalled_jobs(timeout_minutes=10):
    """
    Reclaim jobs that have been leased for longer than timeout_minutes.
    
    Args:
        timeout_minutes: How long a job can be leased before being reclaimed
    """
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    try:
        # Calculate the cutoff time
        cutoff_time = datetime.now() - timedelta(minutes=timeout_minutes)
        
        # Find stalled jobs
        cur.execute("""
            SELECT COUNT(*) 
            FROM harvest_jobs 
            WHERE status = 'leased' 
              AND leased_at < %s
        """, (cutoff_time,))
        
        stalled_count = cur.fetchone()[0]
        
        if stalled_count == 0:
            print("✅ No stalled jobs found")
            return 0
        
        print(f"⚠️  Found {stalled_count:,} stalled jobs (leased > {timeout_minutes} minutes ago)")
        print("🔄 Reclaiming jobs...")
        
        # Reset stalled jobs back to pending
        cur.execute("""
            UPDATE harvest_jobs 
            SET status = 'pending',
                lease_owner = NULL,
                leased_at = NULL,
                attempts = attempts + 1,
                last_error = COALESCE(last_error, '') || ' [Reclaimed from stalled state at ' || NOW() || ']'
            WHERE status = 'leased' 
              AND leased_at < %s
            RETURNING id
        """, (cutoff_time,))
        
        reclaimed_ids = cur.fetchall()
        conn.commit()
        
        print(f"✅ Reclaimed {len(reclaimed_ids):,} jobs back to 'pending' status")
        
        # Show current status
        cur.execute("""
            SELECT status, COUNT(*) as count
            FROM harvest_jobs
            GROUP BY status
            ORDER BY status
        """)
        
        print("\n📊 Current Job Status:")
        for status, count in cur.fetchall():
            print(f"   {status}: {count:,}")
        
        return len(reclaimed_ids)
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        cur.close()
        conn.close()


def force_reclaim_all_leased():
    """
    Emergency function: Force reclaim ALL leased jobs regardless of time.
    Use this when workers have completely stopped.
    """
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    try:
        # Count leased jobs
        cur.execute("SELECT COUNT(*) FROM harvest_jobs WHERE status = 'leased'")
        leased_count = cur.fetchone()[0]
        
        if leased_count == 0:
            print("✅ No leased jobs to reclaim")
            return 0
        
        print(f"🚨 FORCE RECLAIMING {leased_count:,} jobs...")
        
        # Reset ALL leased jobs
        cur.execute("""
            UPDATE harvest_jobs 
            SET status = 'pending',
                lease_owner = NULL,
                leased_at = NULL,
                last_error = COALESCE(last_error, '') || ' [Force reclaimed at ' || NOW() || ']'
            WHERE status = 'leased'
            RETURNING id
        """)
        
        reclaimed = cur.fetchall()
        conn.commit()
        
        print(f"✅ Force reclaimed {len(reclaimed):,} jobs")
        
        # Show status
        cur.execute("""
            SELECT status, COUNT(*) as count
            FROM harvest_jobs
            GROUP BY status
            ORDER BY status
        """)
        
        print("\n📊 Current Job Status:")
        for status, count in cur.fetchall():
            print(f"   {status}: {count:,}")
        
        return len(reclaimed)
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == '__main__':
    print("="*60)
    print("🔧 Harvester Job Reclaim Tool")
    print("="*60)
    print()
    
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--force':
        print("🚨 FORCE MODE: Reclaiming ALL leased jobs")
        print()
        reclaimed = force_reclaim_all_leased()
    else:
        print("🕐 Standard mode: Reclaiming jobs leased > 10 minutes")
        print("   (Use --force to reclaim ALL leased jobs)")
        print()
        reclaimed = reclaim_stalled_jobs(timeout_minutes=10)
    
    print()
    print("="*60)
    print(f"✅ Done! Reclaimed {reclaimed:,} jobs")
    print("="*60)
