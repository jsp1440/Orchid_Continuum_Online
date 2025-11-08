#!/usr/bin/env python3
"""
Active Julius Communication Monitor
Scans database every 30 seconds for new messages from Julius
Alerts immediately when new messages arrive
"""
import os
import psycopg2
import time
from datetime import datetime

def check_for_new_julius_messages():
    """Check for unread messages from Julius"""
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()
    
    # Find messages from Julius that are pending (not completed/read)
    cur.execute("""
        SELECT 
            id,
            task_id,
            created_at,
            prompt_text,
            result_summary
        FROM ai_communication
        WHERE from_agent = 'julius'
          AND to_agent = 'replit'
          AND status IN ('pending', 'in_progress')
          AND created_at > NOW() - INTERVAL '24 hours'
        ORDER BY created_at DESC
    """)
    
    messages = cur.fetchall()
    
    if messages:
        print("\n" + "="*70)
        print(f"🚨 ALERT: {len(messages)} UNREAD MESSAGE(S) FROM JULIUS!")
        print("="*70)
        
        for msg_id, task_id, created, prompt, result in messages:
            time_ago = (datetime.now() - created).total_seconds() / 3600
            print(f"\n📬 Message #{msg_id} | Task: {task_id}")
            print(f"   ⏰ Sent {time_ago:.1f} hours ago")
            print(f"   📝 Preview: {(prompt or '')[:200]}...")
            if result:
                print(f"   📊 Result: {str(result)[:200]}...")
        
        print("\n" + "="*70)
        print("⚡ ACTION REQUIRED: Respond to Julius's messages!")
        print("="*70 + "\n")
    else:
        print(f"✅ [{datetime.now().strftime('%H:%M:%S')}] No new messages from Julius")
    
    cur.close()
    conn.close()
    
    return len(messages)

def scan_all_agent_activity():
    """Scan for ANY database activity that might need attention"""
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()
    
    checks = []
    
    # Check 1: New Julius messages
    cur.execute("""
        SELECT COUNT(*) FROM ai_communication
        WHERE from_agent = 'julius'
          AND status = 'pending'
          AND created_at > NOW() - INTERVAL '1 hour'
    """)
    julius_msgs = cur.fetchone()[0]
    if julius_msgs > 0:
        checks.append(f"🧠 {julius_msgs} pending Julius message(s)")
    
    # Check 2: Failed tasks
    cur.execute("""
        SELECT COUNT(*) FROM ai_communication
        WHERE status = 'failed'
          AND created_at > NOW() - INTERVAL '1 hour'
    """)
    failed = cur.fetchone()[0]
    if failed > 0:
        checks.append(f"❌ {failed} failed task(s)")
    
    # Check 3: Long-running tasks (>1 hour)
    cur.execute("""
        SELECT COUNT(*) FROM ai_communication
        WHERE status = 'in_progress'
          AND created_at < NOW() - INTERVAL '1 hour'
    """)
    stuck = cur.fetchone()[0]
    if stuck > 0:
        checks.append(f"⏰ {stuck} stuck task(s) (>1hr)")
    
    # Check 4: Recent Tropicos progress
    cur.execute("""
        SELECT COUNT(*) FILTER (WHERE external_ids->'tropicos'->>'status' = 'success')
        FROM orchid_taxonomy
    """)
    tropicos_count = cur.fetchone()[0]
    checks.append(f"🌿 Tropicos: {tropicos_count} species collected")
    
    if checks:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] " + " | ".join(checks))
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    print("🔍 Starting Active Julius Monitor...")
    print("Scanning database every 30 seconds for new activity\n")
    
    while True:
        try:
            # Primary check: Julius messages
            new_count = check_for_new_julius_messages()
            
            # Secondary check: Overall system health
            if new_count == 0:
                scan_all_agent_activity()
            
            time.sleep(30)  # Check every 30 seconds
            
        except KeyboardInterrupt:
            print("\n\n👋 Monitor stopped by user")
            break
        except Exception as e:
            print(f"⚠️  Error during scan: {e}")
            time.sleep(30)
