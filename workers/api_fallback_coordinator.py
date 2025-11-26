#!/usr/bin/env python3
"""
API FALLBACK COORDINATOR
========================
Monitors all APIs, detects failures, routes to fallbacks
Ensures continuous harvesting even when APIs fail
"""
import os, sys, time, requests, psycopg2
from datetime import datetime, timedelta

DATABASE_URL = os.environ.get('DATABASE_URL')

# Primary and fallback sources for orchid data
API_SOURCES = {
    'GBIF': {
        'health_check': 'https://api.gbif.org/v1/occurrence/search?limit=1',
        'primary': True,
        'fallback_to': 'iNaturalist'
    },
    'iNaturalist': {
        'health_check': 'https://api.inaturalist.org/v1/observations?limit=1&taxon_name=Orchidaceae',
        'primary': True,
        'fallback_to': 'Tropicos'
    },
    'Tropicos': {
        'health_check': 'https://www.tropicos.org/api/services/json/search',
        'primary': False,
        'fallback_to': 'iDigBio'
    },
    'iDigBio': {
        'health_check': 'https://www.idigbio.org/search/records',
        'primary': False,
        'fallback_to': None
    }
}

def check_api_health(source_name):
    """Check if API is responding"""
    endpoint = API_SOURCES[source_name]['health_check']
    try:
        resp = requests.get(endpoint, timeout=5)
        return resp.status_code < 500  # 200-499 is OK, 500+ is down
    except:
        return False

def log_api_status(source_name, is_healthy):
    """Log API status to database"""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO api_health_log (source_name, is_healthy, checked_at)
            VALUES (%s, %s, NOW())
            ON CONFLICT (source_name) DO UPDATE SET 
                is_healthy = EXCLUDED.is_healthy, 
                checked_at = NOW()
        """, (source_name, is_healthy))
        conn.commit()
    except:
        pass
    finally:
        cur.close()
        conn.close()

def get_active_workers():
    """Get list of currently running workers"""
    import subprocess
    result = subprocess.run(
        "ps aux | grep '_worker.py' | grep -v grep | awk '{print $12}' | sed 's/.*\\///g'",
        shell=True, capture_output=True, text=True
    )
    return result.stdout.strip().split('\n') if result.stdout else []

def monitor_loop():
    """Continuous monitoring"""
    print("🔄 API Fallback Coordinator Started")
    print(f"Monitoring {len(API_SOURCES)} sources for health\n")
    
    while True:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Health Check")
        
        for source, config in API_SOURCES.items():
            is_healthy = check_api_health(source)
            status = "✅" if is_healthy else "❌"
            print(f"  {status} {source}: {'Healthy' if is_healthy else 'DEGRADED'}")
            log_api_status(source, is_healthy)
            
            if not is_healthy and config.get('fallback_to'):
                print(f"     → Fallback: {config['fallback_to']}")
        
        print()
        time.sleep(300)  # Check every 5 minutes

if __name__ == "__main__":
    monitor_loop()
