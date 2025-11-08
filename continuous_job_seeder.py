#!/usr/bin/env python3
"""
CONTINUOUS JOB SEEDER - Keeps ALL species needing images in queue
Adds every species with <30 images to the queue
Automatically adds new species as they complete
Runs until ALL 35,327 species have 30+ images
"""
import os
import sys
import time
import psycopg2
from psycopg2 import pool
from datetime import datetime

CHECK_INTERVAL = 300  # Check every 5 minutes

# Connection pool for resilience
db_pool = None

def init_pool():
    """Initialize connection pool"""
    global db_pool
    try:
        db_pool = psycopg2.pool.SimpleConnectionPool(
            1, 3,
            os.environ['DATABASE_URL'],
            keepalives=1,
            keepalives_idle=30,
            keepalives_interval=10,
            keepalives_count=5
        )
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Database pool initialized")
        return True
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR: Failed to init pool: {e}")
        return False

def get_conn():
    """Get connection from pool with retry"""
    global db_pool
    for attempt in range(3):
        try:
            if db_pool is None:
                if not init_pool():
                    time.sleep(5)
                    continue
            return db_pool.getconn()
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Connection attempt {attempt+1} failed: {e}")
            db_pool = None
            time.sleep(5)
    return None

def put_conn(conn):
    """Return connection to pool"""
    global db_pool
    try:
        if db_pool and conn:
            db_pool.putconn(conn)
    except:
        pass

def add_all_needed_jobs():
    """Add ALL species that need more images to the queue"""
    conn = get_conn()
    if not conn:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR: Could not get connection")
        return 0
    
    try:
        cur = conn.cursor()
        
        # Add EVERY species with <30 images that's not already in queue
        cur.execute("""
            INSERT INTO harvest_jobs (taxonomy_id, scientific_name, status, priority, created_at)
            SELECT 
                t.id,
                t.scientific_name,
                'pending',
                CASE 
                    WHEN img_count = 0 THEN 100
                    WHEN img_count < 10 THEN 90
                    ELSE 80
                END,
                NOW()
            FROM (
                SELECT t.id, t.scientific_name, COUNT(i.id) as img_count
                FROM orchid_taxonomy t
                LEFT JOIN orchid_images i ON t.id = i.taxonomy_id
                WHERE t.id NOT IN (
                    SELECT taxonomy_id FROM harvest_jobs WHERE status IN ('pending', 'leased')
                )
                GROUP BY t.id, t.scientific_name
                HAVING COUNT(i.id) < 30
                ORDER BY COUNT(i.id) ASC
            ) t
            ON CONFLICT (taxonomy_id) DO NOTHING
        """)
        
        added = cur.rowcount
        conn.commit()
        cur.close()
        
        if added > 0:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Added {added:,} jobs to queue")
        
        return added
        
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR adding jobs: {e}")
        try:
            conn.rollback()
        except:
            pass
        return 0
    finally:
        put_conn(conn)

def cleanup_completed():
    """Clean up completed jobs"""
    conn = get_conn()
    if not conn:
        return
    
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM harvest_jobs WHERE status='completed'")
        if cur.rowcount > 0:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Cleaned {cur.rowcount:,} completed jobs")
        conn.commit()
        cur.close()
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR cleaning: {e}")
        try:
            conn.rollback()
        except:
            pass
    finally:
        put_conn(conn)

def get_stats():
    """Get current status"""
    conn = get_conn()
    if not conn:
        return None
    
    try:
        cur = conn.cursor()
        
        # Queue stats
        cur.execute("SELECT COUNT(*) FROM harvest_jobs WHERE status='pending'")
        pending = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM harvest_jobs WHERE status='completed'")
        completed = cur.fetchone()[0]
        
        # Species completion stats
        cur.execute("""
            SELECT 
                COUNT(*) as total_species,
                COUNT(*) FILTER (WHERE img_count >= 30) as complete_species,
                COUNT(*) FILTER (WHERE img_count > 0 AND img_count < 30) as in_progress,
                COUNT(*) FILTER (WHERE img_count = 0) as not_started
            FROM (
                SELECT t.id, COUNT(i.id) as img_count
                FROM orchid_taxonomy t
                LEFT JOIN orchid_images i ON t.id = i.taxonomy_id
                GROUP BY t.id
            ) stats
        """)
        total, complete, in_progress, not_started = cur.fetchone()
        
        cur.close()
        
        return {
            'pending': pending,
            'completed': completed,
            'total_species': total,
            'complete_species': complete,
            'in_progress': in_progress,
            'not_started': not_started
        }
        
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR getting stats: {e}")
        return None
    finally:
        put_conn(conn)

def main():
    """Main loop - runs until ALL species have 30+ images"""
    print("=" * 80)
    print("🌺 Continuous Job Seeder - Running Until ALL Species Complete")
    print("=" * 80)
    print(f"Time: {datetime.now().strftime('%I:%M:%S %p')}")
    print(f"Goal: ALL 35,327 species with 30+ images each")
    print(f"Check interval: {CHECK_INTERVAL} seconds ({CHECK_INTERVAL//60} minutes)")
    print("=" * 80)
    print()
    
    if not init_pool():
        print("FATAL: Could not initialize database pool")
        sys.exit(1)
    
    cycle = 0
    consecutive_errors = 0
    
    while True:
        try:
            cycle += 1
            
            # Get current stats
            stats = get_stats()
            
            if stats is None:
                consecutive_errors += 1
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Stats check failed ({consecutive_errors} consecutive)")
                
                if consecutive_errors >= 5:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Too many errors, reinitializing pool...")
                    global db_pool
                    db_pool = None
                    consecutive_errors = 0
                
                time.sleep(60)
                continue
            
            consecutive_errors = 0
            
            # Clean up completed jobs
            if stats['completed'] > 0:
                cleanup_completed()
            
            # Add all species that need work
            added = add_all_needed_jobs()
            
            # Status report
            print(f"[{datetime.now().strftime('%H:%M:%S')}] STATUS:")
            print(f"   Queue: {stats['pending']:,} pending jobs")
            print(f"   Species: {stats['complete_species']:,}/{stats['total_species']:,} complete (30+ images)")
            print(f"   In progress: {stats['in_progress']:,} species (1-29 images)")
            print(f"   Not started: {stats['not_started']:,} species")
            
            # Check if we're done
            if stats['complete_species'] >= stats['total_species']:
                print()
                print("=" * 80)
                print("🎉 ALL SPECIES COMPLETE!")
                print(f"   {stats['total_species']:,} species all have 30+ images")
                print("=" * 80)
                break
            
            # Calculate remaining work
            remaining = stats['total_species'] - stats['complete_species']
            print(f"   Remaining: {remaining:,} species need more work")
            print()
            
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n\nSeeder stopped by user")
            break
        except Exception as e:
            consecutive_errors += 1
            print(f"[{datetime.now().strftime('%H:%M:%S')}] UNEXPECTED ERROR: {e}")
            time.sleep(60)

if __name__ == '__main__':
    main()
