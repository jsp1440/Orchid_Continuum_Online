#!/usr/bin/env python3
"""
Continuous Julius AI Monitor
Automatically processes Julius insights as they arrive
"""

import time
import subprocess
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def monitor_and_process():
    """Monitor julius_communication and auto-process insights"""
    
    logger.info("🤖 AUTOMATED JULIUS AI MONITOR STARTED")
    logger.info("=" * 60)
    logger.info("📊 Checking for new insights every 30 seconds")
    logger.info("🔄 Processing happens automatically")
    logger.info("🛑 Press Ctrl+C to stop")
    logger.info("=" * 60)
    logger.info("")
    
    insights_processed = 0
    last_check = datetime.now()
    
    try:
        while True:
            current_time = datetime.now().strftime("%H:%M:%S")
            
            # Run the insight processor
            result = subprocess.run(
                ['python', 'julius_insight_processor.py'],
                capture_output=True,
                text=True
            )
            
            # Check for new insights
            if 'Found' in result.stdout and 'unprocessed' in result.stdout:
                # Extract number of insights
                if 'Found 0' in result.stdout:
                    # No new insights
                    logger.info(f"[{current_time}] ⏸️  No new insights. Waiting...")
                else:
                    # New insights detected!
                    insights_processed += 1
                    logger.info(f"[{current_time}] 📥 NEW INSIGHTS DETECTED! Processing...")
                    logger.info("")
                    print(result.stdout)
                    logger.info("")
                    logger.info(f"✅ Total insights processed this session: {insights_processed}")
                    logger.info("")
            
            # Wait 30 seconds before next check
            time.sleep(30)
            
    except KeyboardInterrupt:
        logger.info("")
        logger.info("=" * 60)
        logger.info("🛑 Monitor stopped by user")
        logger.info(f"📊 Total insights processed: {insights_processed}")
        logger.info("=" * 60)

if __name__ == "__main__":
    monitor_and_process()
