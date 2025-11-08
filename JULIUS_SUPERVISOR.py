#!/usr/bin/env python3
"""
UNIFIED SUPERVISOR - Makes the system truly autonomous
======================================================
This script manages BOTH the job seeder and the workers.
Run this once, it handles everything until all species complete.

WHAT IT DOES:
- Ensures job seeder is always running
- Ensures 32 workers are always running  
- Monitors queue health
- Auto-restarts anything that dies
- Runs until ALL 35,327 species have 30+ images

USER REQUIREMENT: "No babysitting needed"
This script delivers on that promise.
"""
import os
import sys
import time
import psycopg2
import subprocess
from datetime import datetime

# Configuration
TARGET_WORKERS = 32
CHECK_INTERVAL = 60  # Check every minute
LAUNCHER_SCRIPT = "launcher.sh"
SEEDER_SCRIPT = "continuous_job_seeder.py"
MIN_QUEUE_DEPTH = 1000  # If queue drops below this, force seeder restart

class Supervisor:
    def __init__(self):
        self.db_url = os.environ['DATABASE_URL']
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
            
            # Active workers
            cur.execute("""
                SELECT COUNT(DISTINCT lease_owner)
                FROM harvest_jobs
                WHERE status='leased' AND leased_at > NOW() - INTERVAL '5 minutes'
            """)
            active_workers = cur.fetchone()[0]
            
            # Species completion
            cur.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE img_count >= 30) as complete,
                    COUNT(*) FILTER (WHERE img_count > 0 AND img_count < 30) as in_progress,
                    COUNT(*) FILTER (WHERE img_count = 0) as not_started
                FROM (
                    SELECT t.id, COUNT(i.id) as img_count
                    FROM orchid_taxonomy t
                    LEFT JOIN orchid_images i ON t.id = i.taxonomy_id
                    GROUP BY t.id
                ) s
            """)
            total, complete, in_progress, not_started = cur.fetchone()
            
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
                'active_workers': active_workers,
                'total_species': total,
                'complete_species': complete,
                'in_progress': in_progress,
                'not_started': not_started,
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
        """Count running workers"""
        try:
            result = subprocess.run(
                "ps aux | grep julius_multi_source_worker | grep -v grep | wc -l",
                shell=True,
                capture_output=True,
                text=True
            )
            return int(result.stdout.strip())
        except:
            return 0
    
    def start_seeder(self):
        """Start the job seeder"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔄 Starting job seeder...")
        try:
            subprocess.Popen(
                ["nohup", "python3", SEEDER_SCRIPT],
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
        """Start worker processes"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔄 Starting {count} workers...")
        try:
            for i in range(count):
                subprocess.Popen(
                    ["bash", LAUNCHER_SCRIPT],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
                time.sleep(0.5)  # Stagger starts
            
            time.sleep(3)
            actual_count = self.count_workers()
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Started {actual_count} workers")
            return actual_count
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Error starting workers: {e}")
            return 0
    
    def kill_all_workers(self):
        """Kill all existing workers"""
        try:
            subprocess.run(
                "pkill -f julius_multi_source_worker",
                shell=True,
                capture_output=True
            )
            time.sleep(2)
        except:
            pass
    
    def supervise_cycle(self, stats):
        """One supervision cycle"""
        issues_fixed = []
        
        # Check 1: Job seeder running?
        if not self.is_process_running(SEEDER_SCRIPT):
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️  Job seeder not running")
            if self.start_seeder():
                issues_fixed.append("Started job seeder")
        
        # Check 2: Queue too low but work incomplete?
        if stats['pending'] < MIN_QUEUE_DEPTH and stats['complete_species'] < stats['total_species']:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️  Queue low ({stats['pending']}) but work incomplete")
            # Force seeder restart
            subprocess.run("pkill -f continuous_job_seeder", shell=True, capture_output=True)
            time.sleep(2)
            if self.start_seeder():
                issues_fixed.append("Restarted job seeder (queue low)")
        
        # Check 3: Workers running?
        worker_count = self.count_workers()
        if worker_count < TARGET_WORKERS:
            needed = TARGET_WORKERS - worker_count
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️  Only {worker_count}/{TARGET_WORKERS} workers running")
            started = self.start_workers(needed)
            if started > 0:
                issues_fixed.append(f"Started {started} workers")
        
        # Check 4: Workers stalled? (DB shows fewer active than process count)
        if stats['active_workers'] < worker_count - 5:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️  Workers stalled ({stats['active_workers']} active in DB, {worker_count} processes)")
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔄 Restarting all workers...")
            self.kill_all_workers()
            started = self.start_workers(TARGET_WORKERS)
            if started > 0:
                issues_fixed.append(f"Restarted all workers (stalled)")
        
        return issues_fixed
    
    def run(self):
        """Main supervisor loop"""
        print("=" * 80)
        print("🌺 ORCHID HARVESTER SUPERVISOR")
        print("=" * 80)
        print(f"Time: {datetime.now().strftime('%I:%M:%S %p')}")
        print(f"Target: ALL 35,327 species with 30+ images")
        print(f"Configuration:")
        print(f"  - Target workers: {TARGET_WORKERS}")
        print(f"  - Check interval: {CHECK_INTERVAL} seconds")
        print(f"  - Min queue depth: {MIN_QUEUE_DEPTH:,}")
        print("=" * 80)
        print()
        
        # Initial startup
        print("🚀 INITIAL STARTUP:")
        
        # Start seeder
        if not self.is_process_running(SEEDER_SCRIPT):
            self.start_seeder()
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Job seeder already running")
        
        # Start workers
        current_workers = self.count_workers()
        if current_workers < TARGET_WORKERS:
            needed = TARGET_WORKERS - current_workers
            self.start_workers(needed)
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ {current_workers} workers already running")
        
        print()
        print("🔍 MONITORING STARTED - Press Ctrl+C to stop")
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
                print(f"   Workers: {stats['active_workers']}/{TARGET_WORKERS} active")
                print(f"   Progress: {stats['total_images']:,} images ({(stats['total_images']/1059810)*100:.2f}%)")
                print(f"   Species: {stats['complete_species']:,} complete, {stats['in_progress']:,} in progress, {stats['not_started']:,} not started")
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
    supervisor = Supervisor()
    supervisor.run()
