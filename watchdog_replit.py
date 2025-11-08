#!/usr/bin/env python3
"""
Watchdog: ensures 4 Replit workers + job seeder keep running and reclaims stale leases
"""
import os, sys, time, subprocess

# Ensure optimized params are present in env
os.environ.setdefault('MSW_BATCH_SIZE','8')
os.environ.setdefault('MSW_THREADS','12')
os.environ.setdefault('MSW_RECLAIM_MIN','7')

expected_workers = ['replit-r' + str(i) for i in range(1, 5)]
db_url = os.environ.get('DATABASE_URL')

def start_worker(wid):
    """Start a Replit worker"""
    logf = wid + '.log'
    try:
        lf = open(logf, 'a')
        subprocess.Popen([sys.executable, '-u', 'julius_multi_source_worker.py', wid], 
                        stdout=lf, stderr=lf)
        print(f"[{time.strftime('%H:%M:%S')}] Started {wid}")
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] Error starting {wid}: {e}")

def start_job_seeder():
    """Start continuous job seeder"""
    try:
        lf = open('job_seeder.log', 'a')
        subprocess.Popen([sys.executable, '-u', 'continuous_job_seeder.py'], 
                        stdout=lf, stderr=lf)
        print(f"[{time.strftime('%H:%M:%S')}] Started job seeder")
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] Error starting job seeder: {e}")

def is_running(pattern):
    """Check if a process is running"""
    try:
        cmd = f'ps aux | grep "{pattern}" | grep -v grep | wc -l'
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
        cnt = int(out.decode().strip() or '0')
        return cnt > 0
    except:
        return False

print("=" * 80)
print("🔄 REPLIT WATCHDOG STARTED")
print("=" * 80)
print(f"Time: {time.strftime('%I:%M:%S %p')}")
print(f"Monitoring: 4 workers + job seeder")
print("=" * 80)

while True:
    try:
        # Ensure each worker is running
        for wid in expected_workers:
            if not is_running(f'julius_multi_source_worker.py {wid}'):
                start_worker(wid)
        
        # Ensure job seeder is running
        if not is_running('continuous_job_seeder.py'):
            start_job_seeder()
        
        # Reclaim stale leases every cycle
        if db_url:
            try:
                import psycopg2
                conn = psycopg2.connect(db_url)
                cur = conn.cursor()
                cur.execute("""
                    UPDATE harvest_jobs
                    SET status = 'pending', lease_owner = NULL
                    WHERE status = 'leased'
                      AND leased_at < NOW() - INTERVAL '10 minutes'
                """)
                if cur.rowcount > 0:
                    print(f"[{time.strftime('%H:%M:%S')}] Reclaimed {cur.rowcount} stale leases")
                conn.commit()
                conn.close()
            except:
                pass
        
        # Status check every 5 minutes
        if int(time.time()) % 300 < 30:
            try:
                import psycopg2
                conn = psycopg2.connect(db_url)
                cur = conn.cursor()
                
                cur.execute("SELECT COUNT(*) FROM harvest_jobs WHERE status='pending'")
                pending = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(*) FROM harvest_jobs WHERE status='leased' AND lease_owner LIKE 'replit-%'")
                active = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(*) FROM orchid_images WHERE created_at > NOW() - INTERVAL '10 minutes'")
                recent = cur.fetchone()[0]
                
                print(f"[{time.strftime('%H:%M:%S')}] Replit: {active} active, {pending:,} pending, {recent} imgs/10min ({recent*6}/hr)")
                
                conn.close()
            except:
                pass
        
        time.sleep(30)
        
    except KeyboardInterrupt:
        print("\n\nWatchdog stopped by user")
        break
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] Watchdog error: {e}")
        time.sleep(30)
