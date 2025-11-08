#!/usr/bin/env python3
"""
Parallel Enrichment Launcher
Runs GBIF and POWO enrichment concurrently for faster completion
"""
import subprocess
import time
import sys
from datetime import datetime

def run_enrichment(name, command, log_file):
    """Start enrichment process"""
    print(f"🚀 Starting {name} enrichment...")
    print(f"   Command: {command}")
    print(f"   Log: {log_file}")
    
    with open(log_file, 'w') as log:
        process = subprocess.Popen(
            command.split(),
            stdout=log,
            stderr=subprocess.STDOUT,
            bufsize=1
        )
    
    print(f"   PID: {process.pid}")
    return process

def main():
    print("="*80)
    print("🚀 PARALLEL ENRICHMENT LAUNCHER")
    print("="*80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")
    
    # Start GBIF
    gbif_process = run_enrichment(
        "GBIF",
        "python batch_gbif_eol_enrichment.py --full --no-ai-vision --gbif-only",
        "gbif_parallel.log"
    )
    
    time.sleep(2)
    
    # Start POWO
    powo_process = run_enrichment(
        "POWO",
        "python batch_powo_enrichment.py --full",
        "powo_parallel.log"
    )
    
    print("")
    print("="*80)
    print("✅ BOTH PROCESSES LAUNCHED IN PARALLEL!")
    print("="*80)
    print(f"GBIF PID: {gbif_process.pid}")
    print(f"POWO PID: {powo_process.pid}")
    print("")
    print("📊 Monitor with:")
    print("   tail -f gbif_parallel.log")
    print("   tail -f powo_parallel.log")
    print("")
    print("⏱️  Expected completion: 2-3 hours (50% faster than sequential)")
    print("="*80)
    
    # Keep parent process alive for monitoring
    print("\nMonitoring (Ctrl+C to stop monitoring, processes will continue)...")
    try:
        while True:
            # Check if processes are still running
            gbif_status = gbif_process.poll()
            powo_status = powo_process.poll()
            
            if gbif_status is not None and powo_status is not None:
                print("\n✅ Both processes completed!")
                print(f"GBIF exit code: {gbif_status}")
                print(f"POWO exit code: {powo_status}")
                break
            
            time.sleep(60)  # Check every minute
            
    except KeyboardInterrupt:
        print("\n\n⏸️  Monitoring stopped (processes continue in background)")
        print(f"GBIF PID: {gbif_process.pid}")
        print(f"POWO PID: {powo_process.pid}")

if __name__ == "__main__":
    main()
