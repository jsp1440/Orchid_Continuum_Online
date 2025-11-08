"""
Autonomous Pipeline Worker
Listens for PostgreSQL NOTIFY events, processes tasks automatically
Runs continuously without human intervention
"""

import logging
import time
import psycopg2
import select
import os
import requests
import hashlib
from pathlib import Path
from typing import Dict, Optional
from psycopg2.extras import Json
import json

logger = logging.getLogger(__name__)

class AutonomousPipelineWorker:
    """
    Autonomous worker that listens for database notifications and processes tasks
    """
    
    def __init__(self, worker_type: str = 'eol_gbif'):
        self.worker_type = worker_type  # 'eol_gbif', 'institutional', or 'ai_discovery'
        self.worker_id = f"{worker_type}_worker_{int(time.time())}"
        self.db_url = os.environ.get('DATABASE_URL')
        self.conn = None
        self.cursor = None
        self.running = True
        self.pipeline = None
        
        # Lazy load pipeline processor (avoid heavy imports at startup)
        if worker_type == 'eol_gbif':
            # Import only when needed to avoid Flask app initialization
            try:
                from image_acquisition_pipeline_1 import ImageAcquisitionPipeline1
                self.pipeline = ImageAcquisitionPipeline1()
                logger.info(f"✅ Pipeline loaded for {worker_type}")
            except Exception as e:
                logger.warning(f"⚠️ Pipeline not available: {e}. Will use direct image download only.")
        
        # Image storage
        self.image_dir = Path(f'static/{worker_type}_images')
        self.image_dir.mkdir(parents=True, exist_ok=True)
        
        self.tasks_processed = 0
        self.last_heartbeat = time.time()
    
    def connect_and_listen(self):
        """Connect to database and start listening for notifications"""
        try:
            # Connection for LISTEN (needs autocommit)
            self.conn = psycopg2.connect(self.db_url)
            self.conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            self.cursor = self.conn.cursor()
            
            # Separate connection for task processing (needs transactions for FOR UPDATE)
            self.work_conn = psycopg2.connect(self.db_url)
            self.work_cursor = self.work_conn.cursor()
            
            # Listen for task notifications
            self.cursor.execute("LISTEN pipeline_task_created;")
            self.cursor.execute("LISTEN image_acquired;")
            
            logger.info(f"✅ Worker {self.worker_id} connected and listening for tasks")
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            raise
    
    def update_heartbeat(self, status: str = 'running', task_info: Optional[Dict] = None):
        """Update worker heartbeat"""
        try:
            self.cursor.execute("""
                INSERT INTO worker_heartbeats (worker_id, worker_type, status, last_heartbeat, tasks_processed, current_task)
                VALUES (%s, %s, %s, NOW(), %s, %s)
                ON CONFLICT (worker_id) 
                DO UPDATE SET 
                    status = EXCLUDED.status,
                    last_heartbeat = NOW(),
                    tasks_processed = EXCLUDED.tasks_processed,
                    current_task = EXCLUDED.current_task
            """, (self.worker_id, self.worker_type, status, self.tasks_processed, Json(task_info or {})))
            self.last_heartbeat = time.time()
        except Exception as e:
            logger.error(f"Heartbeat update failed: {e}")
    
    def fetch_next_task(self) -> Optional[Dict]:
        """Fetch next queued task for this worker type"""
        try:
            # Start transaction
            self.work_cursor.execute("""
                SELECT id, task_type, scientific_name, task_data, source_event_id
                FROM pipeline_tasks
                WHERE task_type = %s AND status = 'queued'
                ORDER BY priority DESC, created_at ASC
                LIMIT 1
                FOR UPDATE SKIP LOCKED
            """, (self.worker_type,))
            
            result = self.work_cursor.fetchone()
            if result:
                task_id, task_type, scientific_name, task_data, source_event_id = result
                
                # Mark as running
                self.work_cursor.execute("""
                    UPDATE pipeline_tasks
                    SET status = 'running', started_at = NOW(), assigned_worker = %s
                    WHERE id = %s
                """, (self.worker_id, task_id))
                
                # Commit transaction
                self.work_conn.commit()
                
                return {
                    'id': task_id,
                    'type': task_type,
                    'scientific_name': scientific_name,
                    'data': task_data or {},
                    'source_event_id': source_event_id
                }
            else:
                # No task found, rollback empty transaction
                self.work_conn.rollback()
            return None
        except Exception as e:
            logger.error(f"Error fetching task: {e}")
            self.work_conn.rollback()
            return None
    
    def download_and_save_image(self, url: str, scientific_name: str, metadata: Dict) -> Optional[Dict]:
        """Download image and save to image_assets table"""
        try:
            response = requests.get(url, timeout=15)
            if response.status_code != 200:
                return None
            
            # Calculate perceptual hash for duplicate detection
            img_hash = hashlib.md5(response.content).hexdigest()
            
            # Check if already exists
            self.work_cursor.execute("""
                SELECT id FROM image_assets WHERE perceptual_hash = %s
            """, (img_hash,))
            
            if self.work_cursor.fetchone():
                logger.debug(f"⏭️ Duplicate image skipped for {scientific_name}")
                return None
            
            # Save image file
            safe_name = scientific_name.replace(' ', '_').replace('/', '_')
            timestamp = int(time.time())
            filename = f"{safe_name}_{timestamp}_{img_hash[:8]}.jpg"
            filepath = self.image_dir / filename
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            local_path = f"/static/{self.worker_type}_images/{filename}"
            
            # Extract genus/species
            parts = scientific_name.split()
            genus = parts[0] if len(parts) > 0 else ''
            species = parts[1] if len(parts) > 1 else ''
            
            # Insert into image_assets (triggers orchestration update)
            self.work_cursor.execute("""
                INSERT INTO image_assets (
                    scientific_name, genus, species, local_path, original_url,
                    perceptual_hash, source, license, attribution, pipeline, metadata
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                scientific_name, genus, species, local_path, url,
                img_hash, metadata.get('source', self.worker_type),
                metadata.get('license', 'Unknown'),
                metadata.get('attribution', 'Unknown'),
                self.worker_type, Json(metadata)
            ))
            
            asset_id = self.work_cursor.fetchone()[0]
            self.work_conn.commit()
            
            logger.info(f"✅ Saved image asset {asset_id} for {scientific_name}")
            
            return {
                'id': asset_id,
                'local_path': local_path,
                'hash': img_hash
            }
        
        except Exception as e:
            logger.error(f"Error downloading image from {url}: {e}")
            return None
    
    def process_task(self, task: Dict):
        """Process a task and acquire images"""
        scientific_name = task['scientific_name']
        logger.info(f"🔧 Processing task for {scientific_name}")
        
        try:
            images_acquired = 0
            
            # Get image URLs from task data
            task_data = task['data']
            if isinstance(task_data, str):
                task_data = json.loads(task_data)
            
            # Try to get images from julius event
            self.work_cursor.execute("""
                SELECT image_urls, metadata FROM julius_ingest_events
                WHERE id = %s
            """, (task['source_event_id'],))
            
            result = self.work_cursor.fetchone()
            if result and result[0]:
                image_urls = result[0] if isinstance(result[0], list) else json.loads(result[0])
                metadata = result[1] if isinstance(result[1], dict) else json.loads(result[1] or '{}')
                
                # Download each image
                for url in image_urls[:5]:  # Max 5 images per task
                    asset = self.download_and_save_image(url, scientific_name, metadata)
                    if asset:
                        images_acquired += 1
            
            # If no images from julius, use pipeline to find them
            if images_acquired == 0 and self.worker_type == 'eol_gbif':
                result = self.pipeline.process_queue_item({
                    'scientific_name': scientific_name,
                    'type': 'taxonomy_only'
                })
                images_acquired = len(result.get('images_collected', []))
            
            # Mark task as completed
            self.work_cursor.execute("""
                UPDATE pipeline_tasks
                SET status = 'completed', completed_at = NOW()
                WHERE id = %s
            """, (task['id'],))
            self.work_conn.commit()
            
            self.tasks_processed += 1
            logger.info(f"✅ Task completed: {scientific_name} ({images_acquired} images)")
            
            return True
        
        except Exception as e:
            logger.error(f"Task processing error: {e}")
            
            # Mark as failed
            self.work_cursor.execute("""
                UPDATE pipeline_tasks
                SET status = 'failed', error_message = %s
                WHERE id = %s
            """, (str(e), task['id']))
            self.work_conn.commit()
            
            return False
    
    def check_for_tasks_and_process(self):
        """Check for queued tasks and process them"""
        task = self.fetch_next_task()
        if task:
            self.update_heartbeat('processing', task)
            self.process_task(task)
            self.update_heartbeat('idle')
            return True
        return False
    
    def run_continuous(self):
        """Run continuously, listening for notifications and processing tasks"""
        logger.info(f"🚀 Autonomous Pipeline Worker {self.worker_id} starting")
        logger.info(f"📋 Worker type: {self.worker_type}")
        
        self.connect_and_listen()
        
        try:
            while self.running:
                # Check for any pending notifications
                if select.select([self.conn], [], [], 5) == ([], [], []):
                    # No notification, check for queued tasks anyway
                    if not self.check_for_tasks_and_process():
                        # Update heartbeat even when idle
                        if time.time() - self.last_heartbeat > 30:
                            self.update_heartbeat('idle')
                else:
                    # Process notifications
                    self.conn.poll()
                    while self.conn.notifies:
                        notify = self.conn.notifies.pop(0)
                        logger.info(f"📬 Received notification: {notify.payload}")
                        
                        # Check if this notification is for our worker type
                        if ':' in notify.payload:
                            pipeline_type, species = notify.payload.split(':', 1)
                            if pipeline_type == self.worker_type:
                                # Process the task
                                self.check_for_tasks_and_process()
                        else:
                            # Generic notification, check for tasks
                            self.check_for_tasks_and_process()
        
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        finally:
            logger.info(f"🛑 Worker {self.worker_id} shutting down")
            if self.cursor:
                self.cursor.close()
            if self.conn:
                self.conn.close()
            if hasattr(self, 'work_cursor') and self.work_cursor:
                self.work_cursor.close()
            if hasattr(self, 'work_conn') and self.work_conn:
                self.work_conn.close()
    
    def stop(self):
        """Stop the worker"""
        self.running = False


if __name__ == "__main__":
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    worker_type = sys.argv[1] if len(sys.argv) > 1 else 'eol_gbif'
    worker = AutonomousPipelineWorker(worker_type)
    
    try:
        worker.run_continuous()
    except KeyboardInterrupt:
        worker.stop()
