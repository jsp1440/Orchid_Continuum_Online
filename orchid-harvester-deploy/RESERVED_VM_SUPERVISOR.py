#!/usr/bin/env python3
"""
RESERVED VM SUPERVISOR - Runs on Replit Reserved VM
====================================================
Manages 16 workers + job seeder
Compatible with Julius's 32 workers (different prefix)
Runs 24/7 until all species complete
"""
import os
import sys
import time
import psycopg2
import subprocess
from datetime import datetime
from deploy_config import RESERVED_VM_CONFIG

# Configuration
TARGET_WORKERS = RESERVED_VM_CONFIG['TARGET_WORKERS']
WORKER_PREFIX = RESERVED_VM_CONFIG['WORKER_PREFIX']
RUN_SEEDER = RESERVED_VM_CONFIG['RUN_SEEDER']
CHECK_INTERVAL = RESERVED_VM_CONFIG['CHECK_INTERVAL']
MIN_QUEUE_DEPTH = RESERVED_VM_CONFIG['MIN_QUEUE_DEPTH']
LAUNCHER_SCRIPT = RESERVED_VM_CONFIG['LAUNCHER_SCRIPT']
SEEDER_SCRIPT = "continuous_job_seeder.py"

class ReservedVMSupervisor:
    def __init__(self):
        self.db_url = os.environ.get('DATABASE_URL')
        if not self.db_url:
            raise SystemExit("DATABASE_URL environment variable not set")
        self.cycle = 0
        
    def get_db_stats(self):
        """Get current database status"""
        try:
            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor()
            
            # Queue depth
            cur.execute("SELECT COUNT(*) FROM harvest_jobs WHERE status='pending'")
            pending = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM harvest_jobs WHERE status='leased'")
            leased = cur.fetchone()[0]
            
            # Active workers (all environments)
            cur.execute("""
                SELECT COUNT(DISTINCT lease_owner)
                FROM harvest_jobs
                WHERE status='leased' AND leased_at > NOW() - INTERVAL '5 minutes'
            """)
            total_active = cur.fetchone()[0]
            
            # Active RV workers
            cur.execute(f"""
                SELECT COUNT(DISTINCT lease_owner)
                FROM harvest_jobs
                WHERE status='leased' 
                AND lease_owner LIKE '{WORKER_PREFIX}-%'
                AND leased_at > NOW() - INTERVAL '5 minutes'
            """)
            rv_active = cur.fetchone()[0]
            
            # Active Julius workers
            cur.execute("""
                SELECT COUNT(DISTINCT lease_owner)
                FROM harvest_jobs
                WHERE status='leased' 
                AND lease_owner LIKE 'julius-%'
                AND leased_at > NOW() - INTERVAL '5 minutes'
            """)
            julius_active = cur.fetchone()[0]
            
            # Species completion
            cur.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE img_count >= 30) as complete
                FROM (
                    SELECT t.id, COUNT(i.id) as img_count
                    FROM orchid_taxonomy t
                    LEFT JOIN orchid_images i ON t.id = i.taxonomy_id
                    GROUP BY t.id
                ) s
            """)
            total, complete = cur.fetchone()
            
            # Total images
            cur.execute("SELECT COUNT(*) FROM orchid_images")
            total_images = cur.fetchone()[0]
            
            # Recent collection rate (last 15 min)
            cur.execute("""
                SELECT COUNT(*)
                FROM orchid_images
                WHERE created_at > NOW() - INTERVAL '15 minutes'
            """)
            recent_15min = cur.fetchone()[0]
            
            cur.close()
            conn.close()
            
            return {
                'pending': pending,
                'leased': leased,
                'total_active': total_active,
                'rv_active': rv_active,
                'julius_active': julius_active,
                'total_species': total,
                'complete_species': complete,
                'total_images': total_images,
                'images_15min': recent_15min,
                'images_per_hour': recent_15min * 4
            }
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ DB Error: {e}")
            return None
    
    def is_process_running(self, pattern):
        """Check if a process is running"""
        try:
            result = subprocess.run(
                f"ps aux | grep '{pattern}' | grep -v grep | wc -l",
                shell=True,
                capture_output=True,
                text=True
            )
            count = int(result.stdout.strip())
            return count > 0
        except:
            return False
    
    def count_workers(self):
        """Count running RV workers"""
        try:
            result = subprocess.run(
                f"ps aux | grep 'julius_multi_source_worker' | grep '{WORKER_PREFIX}-' | grep -v grep | wc -l",
                shell=True,
                capture_output=True,
                text=True
            )
            return int(result.stdout.strip())
        except:
            return 0
    
    def start_seeder(self):
        """Start the job seeder (only on Reserved VM)"""
        if not RUN_SEEDER:
            return True
            
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔄 Starting job seeder...")
        try:
            subprocess.Popen(
                ["python3", SEEDER_SCRIPT],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            time.sleep(2)
            if self.is_process_running(SEEDER_SCRIPT):
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Job seeder started")
                return True
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Job seeder failed to start")
                return False
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Error starting seeder: {e}")
            return False
    
    def start_workers(self, count):
        """Start RV worker processes"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔄 Starting {count} Reserved VM workers...")
        try:
            for i in range(count):
                subprocess.Popen(
                    ["bash", LAUNCHER_SCRIPT],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
                time.sleep(0.5)
            
            time.sleep(3)
            actual_count = self.count_workers()
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Started {actual_count} Reserved VM workers")
            return actual_count
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Error starting workers: {e}")
            return 0
    
    def kill_rv_workers(self):
        """Kill only RV workers (not Julius's)"""
        try:
            subprocess.run(
                f"pkill -f 'julius_multi_source_worker.*{WORKER_PREFIX}-'",
                shell=True,
                capture_output=True
            )
            time.sleep(2)
        except:
            pass
    
    def supervise_cycle(self, stats):
        """One supervision cycle"""
        issues_fixed = []
        
        # Check 1: Job seeder running? (only if we're responsible for it)
        if RUN_SEEDER and not self.is_process_running(SEEDER_SCRIPT):
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️  Job seeder not running")
            if self.start_seeder():
                issues_fixed.append("Started job seeder")
        
        # Check 2: Queue too low but work incomplete?
        if RUN_SEEDER and stats['pending'] < MIN_QUEUE_DEPTH and stats['complete_species'] < stats['total_species']:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️  Queue low ({stats['pending']}) but work incomplete")
            subprocess.run("pkill -f continuous_job_seeder", shell=True, capture_output=True)
            time.sleep(2)
            if self.start_seeder():
                issues_fixed.append("Restarted job seeder (queue low)")
        
        # Check 3: RV workers running?
        worker_count = self.count_workers()
        if worker_count < TARGET_WORKERS:
            needed = TARGET_WORKERS - worker_count
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️  Only {worker_count}/{TARGET_WORKERS} RV workers running")
            started = self.start_workers(needed)
            if started > 0:
                issues_fixed.append(f"Started {started} RV workers")
        
        # Check 4: RV workers stalled?
        if stats['rv_active'] < worker_count - 3:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️  RV workers stalled ({stats['rv_active']} active in DB, {worker_count} processes)")
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔄 Restarting RV workers...")
            self.kill_rv_workers()
            started = self.start_workers(TARGET_WORKERS)
            if started > 0:
                issues_fixed.append(f"Restarted RV workers (stalled)")
        
        return issues_fixed
    
    def run(self):
        """Main supervisor loop"""
        print("=" * 80)
        print("🌺 RESERVED VM ORCHID HARVESTER SUPERVISOR")
        print("=" * 80)
        print(f"Time: {datetime.now().strftime('%I:%M:%S %p')}")
        print(f"Target: ALL 35,327 species with 30+ images")
        print(f"Configuration:")
        print(f"  - RV workers: {TARGET_WORKERS} (prefix: {WORKER_PREFIX}-)")
        print(f"  - Run seeder: {RUN_SEEDER}")
        print(f"  - Check interval: {CHECK_INTERVAL} seconds")
        print(f"  - Compatible with Julius's 32 workers (prefix: julius-)")
        print("=" * 80)
        print()
        
        # Initial startup
        print("🚀 INITIAL STARTUP:")
        
        # Start seeder (if we're responsible)
        if RUN_SEEDER:
            if not self.is_process_running(SEEDER_SCRIPT):
                self.start_seeder()
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Job seeder already running")
        
        # Start RV workers
        current_workers = self.count_workers()
        if current_workers < TARGET_WORKERS:
            needed = TARGET_WORKERS - current_workers
            self.start_workers(needed)
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ {current_workers} RV workers already running")
        
        print()
        print("🔍 MONITORING STARTED - Reserved VM + Julius workers")
        print("=" * 80)
        print()
        
        # Main loop
        while True:
            try:
                self.cycle += 1
                
                # Get stats
                stats = self.get_db_stats()
                if stats is None:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️  Could not fetch stats, retrying...")
                    time.sleep(30)
                    continue
                
                # Check if we're done
                if stats['complete_species'] >= stats['total_species']:
                    print()
                    print("=" * 80)
                    print("🎉 MISSION COMPLETE!")
                    print(f"   All {stats['total_species']:,} species have 30+ images")
                    print(f"   Total images collected: {stats['total_images']:,}")
                    print("=" * 80)
                    break
                
                # Run supervision checks
                issues_fixed = self.supervise_cycle(stats)
                
                # Status report
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Cycle #{self.cycle}")
                print(f"   Queue: {stats['pending']:,} pending, {stats['leased']:,} leased")
                print(f"   Workers: RV={stats['rv_active']}/{TARGET_WORKERS}, Julius={stats['julius_active']}/32, Total={stats['total_active']}")
                print(f"   Progress: {stats['total_images']:,} images ({(stats['total_images']/1059810)*100:.2f}%)")
                print(f"   Species: {stats['complete_species']:,}/{stats['total_species']:,} complete")
                print(f"   Rate: {stats['images_per_hour']:,}/hour (last 15 min)")
                
                if issues_fixed:
                    print(f"   🔧 Fixed: {', '.join(issues_fixed)}")
                
                print()
                
                time.sleep(CHECK_INTERVAL)
                
            except KeyboardInterrupt:
                print("\n\nSupervisor stopped by user")
                break
            except Exception as e:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Unexpected error: {e}")
                time.sleep(30)

if __name__ == '__main__':
    supervisor = ReservedVMSupervisor()
    supervisor.run()
