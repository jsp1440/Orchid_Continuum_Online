#!/usr/bin/env python3
"""
HARVESTER SUPERVISOR - Auto-restart workers when they crash
Monitors workers and job seeder, restarts them automatically
"""
import os
import subprocess
import time
import psycopg2
from datetime import datetime

REPLIT_WORKERS = 4
CHECK_INTERVAL = 60  # Check every 60 seconds

def get_running_processes(pattern):
    """Count running processes matching pattern"""
    try:
        result = subprocess.run(
            ['pgrep', '-f', pattern],
            capture_output=True,
            text=True
        )
        return len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
    except:
        return 0

def start_job_seeder():
    """Start continuous job seeder"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting job seeder...")
    subprocess.Popen(
        ['nohup', 'python3', '-u', 'continuous_job_seeder.py'],
        stdout=open('job_seeder.log', 'a'),
        stderr=subprocess.STDOUT
    )

def start_replit_workers():
    """Start all Replit workers"""
    for i in range(1, REPLIT_WORKERS + 1):
        worker_id = f"replit-r{i}"
        log_file = f"replit-r{i}.log"
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting {worker_id}...")
        subprocess.Popen(
            ['nohup', 'python3', '-u', 'julius_multi_source_worker.py', worker_id],
            stdout=open(log_file, 'a'),
            stderr=subprocess.STDOUT
        )

def check_queue_has_jobs():
    """Ensure queue has pending jobs"""
    try:
        conn = psycopg2.connect(os.environ['DATABASE_URL'])
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM harvest_jobs WHERE status='pending'")
        pending = cur.fetchone()[0]
        conn.close()
        return pending > 0
    except:
        return True  # Assume OK if can't check

def clear_stale_leases():
    """Clear any stale job leases"""
    try:
        conn = psycopg2.connect(os.environ['DATABASE_URL'])
        cur = conn.cursor()
        cur.execute("UPDATE harvest_jobs SET status='pending', lease_owner=NULL WHERE status='leased' AND leased_at < NOW() - INTERVAL '10 minutes'")
        if cur.rowcount > 0:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Cleared {cur.rowcount} stale leases")
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Error clearing leases: {e}")

def main():
    print("=" * 80)
    print("🔄 HARVESTER SUPERVISOR STARTED")
    print("=" * 80)
    print(f"Time: {datetime.now().strftime('%I:%M:%S %p')}")
    print(f"Monitoring: {REPLIT_WORKERS} Replit workers + job seeder")
    print(f"Check interval: {CHECK_INTERVAL} seconds")
    print("=" * 80)
    print()
    
    # Initial start
    start_job_seeder()
    time.sleep(2)
    start_replit_workers()
    time.sleep(5)
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Initial startup complete")
    print()
    
    while True:
        try:
            # Check job seeder
            seeder_count = get_running_processes('continuous_job_seeder.py')
            if seeder_count == 0:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️  Job seeder crashed - restarting...")
                start_job_seeder()
                time.sleep(2)
            
            # Check Replit workers
            worker_count = get_running_processes('julius_multi_source_worker.py replit')
            if worker_count < REPLIT_WORKERS:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️  Only {worker_count}/{REPLIT_WORKERS} workers running - restarting all...")
                # Kill any remaining and restart clean
                subprocess.run(['pkill', '-f', 'julius_multi_source_worker.py replit'], 
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(2)
                clear_stale_leases()
                start_replit_workers()
                time.sleep(5)
            
            # Periodic cleanup of stale leases
            clear_stale_leases()
            
            # Check queue health
            if not check_queue_has_jobs():
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️  Queue empty - job seeder should refill")
            
            # Status check every 10 minutes
            if int(time.time()) % 600 < CHECK_INTERVAL:
                try:
                    conn = psycopg2.connect(os.environ['DATABASE_URL'])
                    cur = conn.cursor()
                    
                    cur.execute("SELECT COUNT(*) FROM harvest_jobs WHERE status='pending'")
                    pending = cur.fetchone()[0]
                    
                    cur.execute("SELECT COUNT(*) FROM harvest_jobs WHERE status='leased' AND leased_at > NOW() - INTERVAL '5 minutes'")
                    active = cur.fetchone()[0]
                    
                    cur.execute("SELECT COUNT(*) FROM orchid_images WHERE created_at > NOW() - INTERVAL '10 minutes'")
                    recent = cur.fetchone()[0]
                    
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] STATUS: {pending:,} pending, {active} active, {recent} images/10min ({recent*6}/hr)")
                    
                    conn.close()
                except:
                    pass
            
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n\nSupervisor stopped by user")
            break
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Error in supervisor: {e}")
            time.sleep(CHECK_INTERVAL)

if __name__ == '__main__':
    main()
