"""
Standalone Image Acquisition Worker
NO Flask dependencies - pure PostgreSQL + image downloading
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

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class StandaloneImageWorker:
    """Standalone worker - no Flask dependencies"""
    
    def __init__(self, worker_type: str = 'standalone'):
        self.worker_type = worker_type
        self.worker_id = f"{worker_type}_worker_{int(time.time())}"
        self.db_url = os.environ.get('DATABASE_URL')
        self.conn = None  # For LISTEN
        self.work_conn = None  # For transactions
        self.running = True
        
        # Image storage
        self.image_dir = Path(f'static/acquired_images')
        self.image_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"✅ Standalone worker {self.worker_id} initialized (NO Flask overhead!)")
    
    def connect_db(self):
        """Establish dual database connections"""
        # Connection 1: For LISTEN (needs autocommit)
        self.conn = psycopg2.connect(self.db_url)
        self.conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        
        # Connection 2: For work (needs transactions for FOR UPDATE)
        self.work_conn = psycopg2.connect(self.db_url)
        
        logger.info(f"✅ Database connections established")
    
    def send_heartbeat(self):
        """Update worker heartbeat"""
        try:
            cursor = self.work_conn.cursor()
            cursor.execute("""
                INSERT INTO worker_heartbeats (worker_id, worker_type, status, last_heartbeat)
                VALUES (%s, %s, %s, NOW())
                ON CONFLICT (worker_id) 
                DO UPDATE SET 
                    status = EXCLUDED.status,
                    last_heartbeat = NOW(),
                    tasks_processed = worker_heartbeats.tasks_processed + 1
            """, (self.worker_id, 'standalone_image', 'running'))
            self.work_conn.commit()
        except Exception as e:
            logger.error(f"Heartbeat failed: {e}")
            self.work_conn.rollback()
    
    def fetch_next_task(self) -> Optional[Dict]:
        """Fetch next task using FOR UPDATE SKIP LOCKED"""
        try:
            cursor = self.work_conn.cursor()
            
            cursor.execute("""
                SELECT 
                    pt.id, pt.scientific_name, pt.source_event_id,
                    je.image_urls, je.source_url, je.metadata
                FROM pipeline_tasks pt
                JOIN julius_ingest_events je ON pt.source_event_id = je.id
                WHERE pt.status = 'queued'
                AND je.image_urls IS NOT NULL
                ORDER BY pt.priority DESC, pt.created_at
                LIMIT 1
                FOR UPDATE OF pt SKIP LOCKED
            """)
            
            row = cursor.fetchone()
            if not row:
                return None
            
            task = {
                'task_id': row[0],
                'scientific_name': row[1],
                'event_id': row[2],
                'image_urls': row[3],
                'source_url': row[4],
                'metadata': row[5]
            }
            
            # Mark as running
            cursor.execute("""
                UPDATE pipeline_tasks 
                SET status = 'running', started_at = NOW() 
                WHERE id = %s
            """, (task['task_id'],))
            
            self.work_conn.commit()
            logger.info(f"📋 Fetched task {task['task_id']}: {task['scientific_name']}")
            return task
            
        except Exception as e:
            logger.error(f"Error fetching task: {e}")
            self.work_conn.rollback()
            return None
    
    def download_image(self, url: str, scientific_name: str) -> Optional[str]:
        """Download image and return local path"""
        try:
            response = requests.get(url, timeout=15, stream=True)
            if response.status_code != 200:
                return None
            
            # Generate filename
            url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
            safe_name = scientific_name.replace(' ', '_').replace('.', '')[:50]
            ext = url.split('.')[-1].split('?')[0][:5]
            filename = f"{safe_name}_{url_hash}.{ext}"
            filepath = self.image_dir / filename
            
            # Save image
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"  ✅ Downloaded: {filename}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"  ❌ Download failed: {e}")
            return None
    
    def save_to_database(self, task: Dict, local_path: str, original_url: str):
        """Save image record to database"""
        try:
            cursor = self.work_conn.cursor()
            
            # Parse scientific name
            parts = task['scientific_name'].split()
            genus = parts[0] if parts else ''
            species = parts[1] if len(parts) > 1 else ''
            
            cursor.execute("""
                INSERT INTO image_assets (
                    scientific_name, genus, species, local_path, original_url,
                    source, source_url, pipeline, metadata, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """, (
                task['scientific_name'],
                genus,
                species,
                local_path,
                original_url,
                'autonomous_pipeline',
                task.get('source_url', ''),
                'standalone',
                Json(task.get('metadata', {}))
            ))
            
            self.work_conn.commit()
            logger.info(f"  💾 Saved to database: {task['scientific_name']}")
            
        except Exception as e:
            logger.error(f"  ❌ Database save failed: {e}")
            self.work_conn.rollback()
    
    def process_task(self, task: Dict):
        """Process a single task - download images"""
        images_downloaded = 0
        
        logger.info(f"🔄 Processing task {task['task_id']}: {task['scientific_name']}")
        
        image_urls = task.get('image_urls', [])
        if not image_urls:
            logger.warning(f"  ⚠️ No image URLs for task {task['task_id']}")
        
        for url in image_urls[:5]:  # Limit to 5 images per task
            local_path = self.download_image(url, task['scientific_name'])
            if local_path:
                self.save_to_database(task, local_path, url)
                images_downloaded += 1
        
        # Mark task as completed
        try:
            cursor = self.work_conn.cursor()
            cursor.execute("""
                UPDATE pipeline_tasks 
                SET status = 'completed', completed_at = NOW() 
                WHERE id = %s
            """, (task['task_id'],))
            self.work_conn.commit()
            logger.info(f"✅ Task {task['task_id']} completed: {images_downloaded} images acquired")
        except Exception as e:
            logger.error(f"Failed to mark task complete: {e}")
            self.work_conn.rollback()
    
    def listen_for_notifications(self):
        """Listen for PostgreSQL NOTIFY events"""
        cursor = self.conn.cursor()
        cursor.execute("LISTEN new_pipeline_task;")
        logger.info("👂 Listening for new_pipeline_task notifications...")
    
    def run_continuous(self):
        """Main worker loop"""
        logger.info(f"🚀 Standalone worker {self.worker_id} starting...")
        
        self.connect_db()
        self.listen_for_notifications()
        
        last_heartbeat = time.time()
        
        try:
            while self.running:
                # Check for NOTIFY events
                if select.select([self.conn], [], [], 1) == ([self.conn], [], []):
                    self.conn.poll()
                    while self.conn.notifies:
                        notify = self.conn.notifies.pop(0)
                        logger.info(f"🔔 Received: {notify.payload}")
                
                # Try to fetch and process a task
                task = self.fetch_next_task()
                if task:
                    self.process_task(task)
                else:
                    time.sleep(2)  # Short wait if no tasks
                
                # Periodic heartbeat
                if time.time() - last_heartbeat > 30:
                    self.send_heartbeat()
                    last_heartbeat = time.time()
        
        finally:
            logger.info(f"🛑 Worker {self.worker_id} shutting down")
            if self.conn:
                self.conn.close()
            if self.work_conn:
                self.work_conn.close()

if __name__ == "__main__":
    worker = StandaloneImageWorker()
    try:
        worker.run_continuous()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
        worker.running = False
