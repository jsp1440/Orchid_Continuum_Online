#!/usr/bin/env python3
"""
Sequential Enrichment Queue
Auto-runs each data source when previous completes
"""
import subprocess
import time
import os
import sys
from datetime import datetime

ENRICHMENT_PHASES = [
    {
        'name': 'GBIF',
        'command': 'python batch_gbif_eol_enrichment.py --full --no-ai-vision --gbif-only',
        'log': 'gbif_final.log',
        'status': 'running'  # Already running
    },
    {
        'name': 'POWO (Kew Gardens)',
        'command': 'python batch_powo_enrichment.py --full',
        'log': 'powo_enrichment.log',
        'status': 'queued'
    },
    {
        'name': 'Tropicos (Missouri Botanical)',
        'command': 'python batch_tropicos_enrichment.py --full',
        'log': 'tropicos_enrichment.log',
        'status': 'queued',
        'skip_if_no_key': True
    }
]

def check_if_complete(log_file):
    """Check if enrichment phase is complete"""
    if not os.path.exists(log_file):
        return False
    
    try:
        result = subprocess.run(
            ['tail', '-50', log_file],
            capture_output=True,
            text=True
        )
        output = result.stdout
        return 'COMPLETE' in output or '✅ BATCH ENRICHMENT COMPLETE' in output
    except:
        return False

def check_if_running(process_name):
    """Check if process is running"""
    result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
    return process_name in result.stdout

def run_phase(phase):
    """Run an enrichment phase"""
    print(f"\n{'='*80}")
    print(f"🚀 Starting: {phase['name']}")
    print(f"   Command: {phase['command']}")
    print(f"   Log: {phase['log']}")
    print(f"{'='*80}\n")
    
    # Start process in background
    with open(phase['log'], 'w') as log:
        subprocess.Popen(
            phase['command'].split(),
            stdout=log,
            stderr=log
        )
    
    time.sleep(5)  # Give it time to start
    return True

def main():
    print("🎯 Sequential Enrichment Queue System")
    print("="*80)
    print("This will auto-run each phase when the previous completes")
    print("="*80)
    
    while True:
        all_complete = True
        
        for phase in ENRICHMENT_PHASES:
            if phase['status'] == 'running':
                # Check if still running
                if check_if_complete(phase['log']):
                    print(f"✅ {phase['name']}: COMPLETE")
                    phase['status'] = 'complete'
                else:
                    print(f"⏳ {phase['name']}: Running...")
                    all_complete = False
                    break  # Wait for this to finish
                    
            elif phase['status'] == 'queued':
                # Start this phase
                if phase.get('skip_if_no_key') and not os.environ.get('TROPICOS_API_KEY'):
                    print(f"⏭️  {phase['name']}: SKIPPED (no API key)")
                    phase['status'] = 'skipped'
                else:
                    run_phase(phase)
                    phase['status'] = 'running'
                    all_complete = False
                    break
                    
            elif phase['status'] == 'complete':
                all_complete = all_complete and True
            elif phase['status'] == 'skipped':
                pass  # Continue to next
        
        if all_complete:
            print("\n" + "="*80)
            print("🎉 ALL ENRICHMENT PHASES COMPLETE!")
            print("="*80)
            
            # Print summary
            for phase in ENRICHMENT_PHASES:
                status = '✅' if phase['status'] == 'complete' else '⏭️' if phase['status'] == 'skipped' else '❌'
                print(f"   {status} {phase['name']}: {phase['status'].upper()}")
            
            break
        
        time.sleep(300)  # Check every 5 minutes

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏸️  Queue stopped")
