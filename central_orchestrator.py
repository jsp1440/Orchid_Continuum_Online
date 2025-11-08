"""
Central Orchestrator
Coordinates all autonomous workers, monitors progress, refills queues
Creates self-sustaining loop for continuous image acquisition
"""

import logging
import time
import os
import subprocess
import psycopg2
from psycopg2.extras import Json
from typing import Dict, List
import json

logger = logging.getLogger(__name__)

class CentralOrchestrator:
    """
    Master orchestrator that coordinates all workers and maintains continuous operation
    """
    
    def __init__(self):
        self.db_url = os.environ.get('DATABASE_URL')
        self.conn = None
        self.cursor = None
        self.running = True
        
        # Worker process handles
        self.workers = {}
        
        # Target metrics
        self.target_images = 100000
        self.batch_size = 100
    
    def connect_db(self):
        """Connect to database"""
        try:
            self.conn = psycopg2.connect(self.db_url)
            self.conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            self.cursor = self.conn.cursor()
            logger.info("✅ Central Orchestrator connected to database")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    def get_current_metrics(self) -> Dict:
        """Get current system metrics"""
        try:
            # Total images acquired
            self.cursor.execute("SELECT COUNT(*) FROM image_assets")
            total_images = self.cursor.fetchone()[0]
            
            # Total unique species with images
            self.cursor.execute("SELECT COUNT(DISTINCT scientific_name) FROM image_assets")
            species_with_images = self.cursor.fetchone()[0]
            
            # Total taxonomy entries
            self.cursor.execute("SELECT COUNT(*) FROM orchid_taxonomy")
            total_taxonomy = self.cursor.fetchone()[0]
            
            # Pending tasks
            self.cursor.execute("SELECT COUNT(*) FROM pipeline_tasks WHERE status = 'queued'")
            pending_tasks = self.cursor.fetchone()[0]
            
            # Running tasks
            self.cursor.execute("SELECT COUNT(*) FROM pipeline_tasks WHERE status = 'running'")
            running_tasks = self.cursor.fetchone()[0]
            
            # Julius events pending
            self.cursor.execute("SELECT COUNT(*) FROM julius_ingest_events WHERE status = 'pending'")
            julius_pending = self.cursor.fetchone()[0]
            
            # Worker status
            self.cursor.execute("""
                SELECT worker_type, COUNT(*), MAX(last_heartbeat)
                FROM worker_heartbeats
                WHERE status = 'running' AND last_heartbeat > NOW() - INTERVAL '2 minutes'
                GROUP BY worker_type
            """)
            active_workers = {row[0]: row[1] for row in self.cursor.fetchall()}
            
            coverage_pct = (species_with_images / total_taxonomy * 100) if total_taxonomy > 0 else 0
            
            return {
                'total_images': total_images,
                'species_with_images': species_with_images,
                'total_taxonomy': total_taxonomy,
                'coverage_percent': round(coverage_pct, 2),
                'pending_tasks': pending_tasks,
                'running_tasks': running_tasks,
                'julius_pending': julius_pending,
                'active_workers': active_workers,
                'progress_to_goal': round((total_images / self.target_images * 100), 2)
            }
        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return {}
    
    def check_worker_health(self) -> Dict[str, bool]:
        """Check if workers are alive and responding"""
        try:
            self.cursor.execute("""
                SELECT worker_id, worker_type, last_heartbeat, status
                FROM worker_heartbeats
                WHERE last_heartbeat > NOW() - INTERVAL '2 minutes'
            """)
            
            alive_workers = {}
            for row in self.cursor.fetchall():
                worker_id, worker_type, last_heartbeat, status = row
                alive_workers[worker_type] = True
            
            # Check required workers
            required_workers = ['julius_scraper', 'eol_gbif']
            health = {}
            
            for worker_type in required_workers:
                health[worker_type] = alive_workers.get(worker_type, False)
            
            return health
        except Exception as e:
            logger.error(f"Error checking worker health: {e}")
            return {}
    
    def refill_task_queue(self, batch_size: int = 100):
        """Refill pipeline task queue with high-priority species"""
        try:
            # Find species without images
            self.cursor.execute("""
                SELECT ot.scientific_name, ot.genus
                FROM orchid_taxonomy ot
                LEFT JOIN image_assets ia ON ot.scientific_name = ia.scientific_name
                WHERE ia.id IS NULL
                ORDER BY RANDOM()
                LIMIT %s
            """, (batch_size,))
            
            species_to_process = self.cursor.fetchall()
            
            if not species_to_process:
                logger.info("✅ All species have at least one image!")
                return 0
            
            # Create julius ingest events for these species (triggers will create tasks)
            created = 0
            for scientific_name, genus in species_to_process:
                try:
                    self.cursor.execute("""
                        INSERT INTO julius_ingest_events (
                            event_type, scientific_name, pipeline_assigned, priority, status
                        ) VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT DO NOTHING
                    """, ('image_discovered', scientific_name, 'eol_gbif', 8, 'pending'))
                    created += 1
                except Exception as e:
                    logger.error(f"Error creating event for {scientific_name}: {e}")
            
            logger.info(f"📋 Refilled queue with {created} high-priority species")
            return created
        except Exception as e:
            logger.error(f"Error refilling queue: {e}")
            return 0
    
    def start_worker(self, worker_script: str, worker_args: List[str] = None):
        """Start a worker process"""
        try:
            cmd = ['python', worker_script]
            if worker_args:
                cmd.extend(worker_args)
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            worker_id = f"{worker_script}_{process.pid}"
            self.workers[worker_id] = process
            logger.info(f"✅ Started worker: {worker_id}")
            return process
        except Exception as e:
            logger.error(f"Failed to start worker {worker_script}: {e}")
            return None
    
    def restart_dead_workers(self):
        """Restart any dead workers"""
        health = self.check_worker_health()
        
        # Restart Julius scraper if dead
        if not health.get('julius_scraper'):
            logger.warning("🔴 Julius scraper is dead, restarting...")
            self.start_worker('julius_ai_scraper_worker.py')
        
        # Restart pipeline workers if dead
        if not health.get('eol_gbif'):
            logger.warning("🔴 EOL/GBIF worker is dead, restarting...")
            self.start_worker('autonomous_pipeline_worker.py', ['eol_gbif'])
    
    def run_orchestration_cycle(self):
        """Run one orchestration cycle"""
        logger.info("🎯 Running orchestration cycle...")
        
        # Get current metrics
        metrics = self.get_current_metrics()
        logger.info(f"📊 Current metrics: {json.dumps(metrics, indent=2)}")
        
        # Check worker health and restart if needed
        self.restart_dead_workers()
        
        # If queue is low, refill it
        if metrics.get('pending_tasks', 0) < 10:
            logger.info("📋 Task queue low, refilling...")
            self.refill_task_queue(self.batch_size)
        
        # Update orchestration status in database
        try:
            self.cursor.execute("""
                INSERT INTO orchestration_status (metric_name, metric_value)
                VALUES (%s, %s)
                ON CONFLICT (metric_name) 
                DO UPDATE SET metric_value = EXCLUDED.metric_value, updated_at = NOW()
            """, ('current_metrics', Json(metrics)))
        except Exception as e:
            logger.error(f"Error updating metrics: {e}")
        
        # Log progress
        logger.info(f"🎯 Progress: {metrics.get('total_images', 0):,} / {self.target_images:,} images ({metrics.get('progress_to_goal', 0)}%)")
        logger.info(f"🌿 Species coverage: {metrics.get('species_with_images', 0)} / {metrics.get('total_taxonomy', 0)} ({metrics.get('coverage_percent', 0)}%)")
        logger.info(f"📋 Tasks: {metrics.get('pending_tasks', 0)} queued, {metrics.get('running_tasks', 0)} running")
        logger.info(f"👷 Workers: {json.dumps(metrics.get('active_workers', {}))}")
    
    def run_continuous(self, cycle_interval: int = 60):
        """
        Run continuously, monitoring and coordinating workers
        cycle_interval: seconds between orchestration cycles
        """
        logger.info("🚀 Central Orchestrator starting continuous operation")
        logger.info(f"🎯 Goal: {self.target_images:,} images")
        logger.info(f"📅 Running orchestration cycles every {cycle_interval} seconds")
        
        self.connect_db()
        
        # Start initial workers
        logger.info("🔧 Starting initial workers...")
        self.start_worker('julius_ai_scraper_worker.py')
        time.sleep(2)
        self.start_worker('autonomous_pipeline_worker.py', ['eol_gbif'])
        time.sleep(2)
        
        try:
            while self.running:
                self.run_orchestration_cycle()
                time.sleep(cycle_interval)
        
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        finally:
            logger.info("🛑 Central Orchestrator shutting down")
            
            # Stop all workers
            for worker_id, process in self.workers.items():
                logger.info(f"Stopping worker {worker_id}")
                process.terminate()
            
            if self.cursor:
                self.cursor.close()
            if self.conn:
                self.conn.close()
    
    def stop(self):
        """Stop the orchestrator"""
        self.running = False


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    orchestrator = CentralOrchestrator()
    try:
        orchestrator.run_continuous(cycle_interval=60)
    except KeyboardInterrupt:
        orchestrator.stop()
