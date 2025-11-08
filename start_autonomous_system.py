#!/usr/bin/env python3
"""
Autonomous Image Acquisition System Startup Script
Launches all workers and orchestrator in a coordinated manner
"""

import subprocess
import time
import logging
import signal
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AutonomousSystemStarter:
    def __init__(self):
        self.processes = []
    
    def start_process(self, script_name, args=None, delay=2):
        """Start a Python script as a subprocess"""
        cmd = ['python', script_name]
        if args:
            cmd.extend(args)
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            self.processes.append(process)
            logger.info(f"✅ Started: {script_name} (PID: {process.pid})")
            time.sleep(delay)
            return process
        except Exception as e:
            logger.error(f"❌ Failed to start {script_name}: {e}")
            return None
    
    def signal_handler(self, sig, frame):
        """Handle shutdown gracefully"""
        logger.info("\n🛑 Shutdown signal received, stopping all workers...")
        for process in self.processes:
            process.terminate()
        sys.exit(0)
    
    def start_system(self):
        """Start the complete autonomous system"""
        logger.info("=" * 60)
        logger.info("🚀 AUTONOMOUS IMAGE ACQUISITION SYSTEM")
        logger.info("=" * 60)
        logger.info("")
        logger.info("🎯 Goal: 100,000+ orchid images with full metadata")
        logger.info("🤖 Strategy: Triple pipeline approach with trigger-based automation")
        logger.info("")
        logger.info("Starting workers...")
        logger.info("")
        
        # Register signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # Start Julius AI Scraper (discovers data)
        logger.info("1️⃣ Starting Julius AI Scraper Worker...")
        self.start_process('julius_ai_scraper_worker.py')
        
        # Start Pipeline Workers (process data)
        logger.info("2️⃣ Starting EOL/GBIF Pipeline Worker...")
        self.start_process('autonomous_pipeline_worker.py', ['eol_gbif'])
        
        logger.info("3️⃣ Starting Institutional Pipeline Worker...")
        self.start_process('autonomous_pipeline_worker.py', ['institutional'])
        
        # Start Central Orchestrator (coordinates everything)
        logger.info("4️⃣ Starting Central Orchestrator...")
        orchestrator = self.start_process('central_orchestrator.py')
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("✅ AUTONOMOUS SYSTEM RUNNING")
        logger.info("=" * 60)
        logger.info("")
        logger.info("📊 Monitor progress at: http://localhost:5000/autonomous-dashboard")
        logger.info("🔍 View metrics in database: orchestration_status table")
        logger.info("")
        logger.info("The system will now run continuously:")
        logger.info("  • Julius AI scrapes new data every 5 minutes")
        logger.info("  • Database triggers auto-launch pipeline tasks")
        logger.info("  • Workers process images 24/7")
        logger.info("  • Orchestrator monitors and refills queues every 60 seconds")
        logger.info("")
        logger.info("Press Ctrl+C to stop all workers")
        logger.info("")
        
        # Keep running and monitor
        try:
            while True:
                time.sleep(10)
                # Check if orchestrator is still running
                if orchestrator and orchestrator.poll() is not None:
                    logger.error("❌ Orchestrator died, restarting...")
                    orchestrator = self.start_process('central_orchestrator.py')
        
        except KeyboardInterrupt:
            logger.info("\n🛑 Stopping autonomous system...")
            for process in self.processes:
                process.terminate()
            logger.info("✅ All workers stopped")

if __name__ == "__main__":
    starter = AutonomousSystemStarter()
    starter.start_system()
