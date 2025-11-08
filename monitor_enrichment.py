#!/usr/bin/env python3
"""
Enrichment Monitor - Checks progress every 10 minutes and restarts if needed
Forces completion of all 5,588 orchids
"""
import os
import time
import subprocess
import logging
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

DATABASE_URL = os.environ.get('DATABASE_URL')
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

ENRICHMENT_SCRIPT = "smart_gbif_enrichment.py"
CHECK_INTERVAL = 600  # 10 minutes
TARGET_TOTAL = 5588

def get_enrichment_stats():
    """Get current enrichment statistics"""
    session = Session()
    try:
        result = session.execute(text("""
            SELECT 
                COUNT(*) as total_orchids,
                COUNT(CASE WHEN image_source = 'GBIF' THEN 1 END) as gbif_images,
                COUNT(CASE WHEN native_habitat IS NOT NULL AND native_habitat != '' THEN 1 END) as with_habitat,
                COUNT(CASE WHEN region IS NOT NULL AND region != '' THEN 1 END) as with_region
            FROM orchid_record
        """))
        return dict(result.fetchone()._mapping)
    finally:
        session.close()

def is_enrichment_running():
    """Check if enrichment process is running"""
    try:
        result = subprocess.run(
            ['pgrep', '-f', ENRICHMENT_SCRIPT],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except:
        return False

def start_enrichment():
    """Start enrichment process"""
    logger.info("🚀 Starting enrichment process...")
    subprocess.Popen(
        ['python3', ENRICHMENT_SCRIPT],
        stdout=open('smart_enrichment.log', 'a'),
        stderr=subprocess.STDOUT,
        start_new_session=True
    )
    time.sleep(5)  # Give it time to start

def monitor():
    """Monitor enrichment progress and restart if needed"""
    logger.info("="*70)
    logger.info("🔍 ENRICHMENT MONITOR STARTED")
    logger.info(f"📊 Target: {TARGET_TOTAL} orchids with complete species names")
    logger.info(f"⏱️  Check interval: {CHECK_INTERVAL/60} minutes")
    logger.info("="*70)
    
    start_time = datetime.now()
    last_gbif_count = 0
    stalled_checks = 0
    
    while True:
        # Get current stats
        stats = get_enrichment_stats()
        gbif_images = stats['gbif_images']
        with_habitat = stats['with_habitat']
        with_region = stats['with_region']
        
        # Calculate progress
        progress_pct = (gbif_images / TARGET_TOTAL) * 100
        elapsed = (datetime.now() - start_time).total_seconds() / 60
        
        logger.info("")
        logger.info("="*70)
        logger.info(f"⏰ CHECK #{int(elapsed/10)+1} - {datetime.now().strftime('%H:%M:%S')}")
        logger.info("="*70)
        logger.info(f"📸 GBIF Images: {gbif_images}/{TARGET_TOTAL} ({progress_pct:.1f}%)")
        logger.info(f"🌍 Habitat data: {with_habitat}")
        logger.info(f"📍 Region data: {with_region}")
        logger.info(f"⏱️  Running time: {elapsed:.1f} minutes")
        
        # Check if process is running
        is_running = is_enrichment_running()
        logger.info(f"🔄 Process status: {'RUNNING ✅' if is_running else 'STOPPED ❌'}")
        
        # Check if stalled (no progress)
        if gbif_images == last_gbif_count:
            stalled_checks += 1
            logger.info(f"⚠️  No progress detected ({stalled_checks} checks)")
        else:
            stalled_checks = 0
            logger.info(f"✅ Progress detected (+{gbif_images - last_gbif_count} images)")
        
        last_gbif_count = gbif_images
        
        # Restart if stopped or stalled
        if not is_running or stalled_checks >= 2:
            logger.info("🔄 RESTARTING ENRICHMENT...")
            # Kill any zombie processes
            subprocess.run(['pkill', '-9', '-f', ENRICHMENT_SCRIPT], 
                         capture_output=True)
            time.sleep(2)
            start_enrichment()
            stalled_checks = 0
        
        # Check if complete
        if gbif_images >= TARGET_TOTAL * 0.95:  # 95% completion threshold
            logger.info("")
            logger.info("="*70)
            logger.info("🎉 ENRICHMENT NEAR COMPLETION!")
            logger.info(f"✅ {gbif_images} GBIF images downloaded")
            logger.info(f"⏱️  Total time: {elapsed:.1f} minutes")
            logger.info("="*70)
            break
        
        logger.info(f"⏳ Next check in {CHECK_INTERVAL/60} minutes...")
        logger.info("="*70)
        
        # Wait for next check
        time.sleep(CHECK_INTERVAL)
    
    logger.info("\n✅ Monitor completed successfully")

if __name__ == "__main__":
    # Ensure enrichment is running at start
    if not is_enrichment_running():
        start_enrichment()
    
    try:
        monitor()
    except KeyboardInterrupt:
        logger.info("\n⚠️  Monitor stopped by user")
    except Exception as e:
        logger.error(f"\n❌ Monitor error: {e}")
