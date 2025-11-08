#!/usr/bin/env python3
"""
Robust Parallel Enrichment System
Runs all data sources concurrently with error isolation and recovery
"""
import subprocess
import time
import os
from datetime import datetime
from pathlib import Path

class RobustParallelEnricher:
    def __init__(self):
        self.sources = [
            {
                'name': 'GBIF',
                'command': 'python batch_gbif_eol_enrichment.py --full --no-ai-vision --gbif-only',
                'log': 'logs/gbif_enrichment.log',
                'pid': None,
                'status': 'pending',
                'required': True  # Must have
            },
            {
                'name': 'POWO (Kew Gardens)',
                'command': 'python batch_powo_enrichment.py --full',
                'log': 'logs/powo_enrichment.log',
                'pid': None,
                'status': 'pending',
                'required': True  # Must have
            },
            {
                'name': 'Tropicos (Missouri)',
                'command': 'python batch_tropicos_enrichment.py --full',
                'log': 'logs/tropicos_enrichment.log',
                'pid': None,
                'status': 'pending',
                'required': False,  # Optional - skip if no API key
                'check_env': 'TROPICOS_API_KEY'
            },
            {
                'name': 'EOL (TraitBank)',
                'command': 'python batch_gbif_eol_enrichment.py --full --eol-only --no-ai-vision',
                'log': 'logs/eol_enrichment.log',
                'pid': None,
                'status': 'pending',
                'required': False  # Optional - EOL has SSL issues sometimes
            }
        ]
        
        # Create logs directory
        Path('logs').mkdir(exist_ok=True)
    
    def check_source_ready(self, source):
        """Check if a source is ready to run"""
        if source.get('check_env'):
            if not os.environ.get(source['check_env']):
                return False, f"Missing {source['check_env']}"
        return True, "Ready"
    
    def start_source(self, source):
        """Start enrichment source with error handling"""
        ready, reason = self.check_source_ready(source)
        
        if not ready:
            source['status'] = 'skipped'
            print(f"   ⏭️  {source['name']}: SKIPPED ({reason})")
            return None
        
        try:
            print(f"   🚀 {source['name']}: Starting...")
            
            # Open log file
            log_file = open(source['log'], 'w')
            
            # Start process with error isolation
            process = subprocess.Popen(
                source['command'].split(),
                stdout=log_file,
                stderr=log_file,
                stdin=subprocess.DEVNULL,
                start_new_session=True  # Isolate from parent
            )
            
            source['pid'] = process.pid
            source['status'] = 'running'
            source['log_file'] = log_file
            source['process'] = process
            
            print(f"      ✅ PID: {process.pid}")
            return process
            
        except Exception as e:
            source['status'] = 'failed'
            print(f"      ❌ Failed to start: {e}")
            return None
    
    def monitor_sources(self):
        """Monitor all sources and report status"""
        running_count = sum(1 for s in self.sources if s['status'] == 'running')
        
        print(f"\n📊 STATUS CHECK:")
        for source in self.sources:
            status_icon = {
                'running': '⏳',
                'completed': '✅',
                'failed': '❌',
                'skipped': '⏭️',
                'pending': '⏸️'
            }.get(source['status'], '❓')
            
            print(f"   {status_icon} {source['name']}: {source['status'].upper()}")
            
            # Show recent activity for running sources
            if source['status'] == 'running' and os.path.exists(source['log']):
                try:
                    result = subprocess.run(
                        ['tail', '-2', source['log']],
                        capture_output=True,
                        text=True,
                        timeout=2
                    )
                    if result.stdout:
                        for line in result.stdout.strip().split('\n')[-1:]:
                            if line.strip():
                                print(f"      {line[:80]}")
                except:
                    pass
        
        return running_count
    
    def check_completion(self):
        """Check if sources have completed"""
        for source in self.sources:
            if source['status'] == 'running' and source.get('process'):
                poll = source['process'].poll()
                if poll is not None:
                    # Process finished
                    if poll == 0:
                        source['status'] = 'completed'
                        print(f"   ✅ {source['name']} completed successfully")
                    else:
                        source['status'] = 'failed'
                        print(f"   ❌ {source['name']} failed (exit code: {poll})")
                    
                    # Close log file
                    if source.get('log_file'):
                        source['log_file'].close()
    
    def run(self):
        """Run all sources in parallel"""
        print("="*80)
        print("🚀 ROBUST PARALLEL ENRICHMENT SYSTEM")
        print("="*80)
        print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Sources configured: {len(self.sources)}")
        print("")
        
        # Start all sources
        print("🔧 STARTING ENRICHMENT SOURCES:")
        for source in self.sources:
            self.start_source(source)
            time.sleep(2)  # Stagger starts
        
        print("\n" + "="*80)
        
        # Count what's running
        running = [s for s in self.sources if s['status'] == 'running']
        skipped = [s for s in self.sources if s['status'] == 'skipped']
        
        print(f"✅ PARALLEL ENRICHMENT ACTIVE!")
        print(f"   Running: {len(running)} sources")
        print(f"   Skipped: {len(skipped)} sources")
        print("="*80)
        
        if running:
            print("\n🔍 Monitor individual logs:")
            for source in running:
                print(f"   tail -f {source['log']}")
            
            print("\n⏱️  Estimated completion: 2-3 hours")
            print("   (All sources run in parallel - same total time!)")
            
            # Monitor every 5 minutes
            print("\n📊 Will check status every 5 minutes...\n")
            
            try:
                while True:
                    time.sleep(300)  # 5 minutes
                    
                    self.check_completion()
                    running_count = self.monitor_sources()
                    
                    if running_count == 0:
                        print("\n🎉 ALL SOURCES COMPLETE!")
                        break
                        
            except KeyboardInterrupt:
                print("\n\n⏸️  Monitoring stopped (processes continue in background)")
                print("   Running sources:")
                for source in self.sources:
                    if source['status'] == 'running':
                        print(f"     • {source['name']} (PID: {source['pid']})")
        else:
            print("\n❌ No sources started successfully")
        
        # Final summary
        print("\n" + "="*80)
        print("📊 FINAL STATUS:")
        print("="*80)
        
        for source in self.sources:
            status_icon = {
                'completed': '✅',
                'running': '⏳',
                'failed': '❌',
                'skipped': '⏭️'
            }.get(source['status'], '❓')
            
            print(f"{status_icon} {source['name']}: {source['status'].upper()}")
        
        completed = sum(1 for s in self.sources if s['status'] == 'completed')
        total_attempted = sum(1 for s in self.sources if s['status'] != 'skipped')
        
        if total_attempted > 0:
            print(f"\nSuccess rate: {completed}/{total_attempted} sources completed")

if __name__ == "__main__":
    enricher = RobustParallelEnricher()
    enricher.run()
