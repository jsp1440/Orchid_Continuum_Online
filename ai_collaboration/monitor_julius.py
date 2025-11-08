#!/usr/bin/env python3
"""
Real-time Julius AI Activity Monitor
Run this to watch Julius work in real-time
"""

import os
import time
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

def get_db_connection():
    """Connect to database"""
    return psycopg2.connect(os.environ.get('DATABASE_URL'))

def check_julius_activity():
    """Check if Julius has been active"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("\n" + "="*70)
    print(f"🔍 JULIUS AI ACTIVITY CHECK - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # Check for Julius messages
    cur.execute("""
        SELECT COUNT(*) as count, MAX(created_at) as last_activity
        FROM ai_communication 
        WHERE from_agent = 'julius_ai'
    """)
    julius_messages = cur.fetchone()
    
    if julius_messages['count'] > 0:
        print(f"\n✅ JULIUS IS ACTIVE!")
        print(f"   Total messages from Julius: {julius_messages['count']}")
        print(f"   Last activity: {julius_messages['last_activity']}")
    else:
        print(f"\n❌ JULIUS NOT ACTIVE YET")
        print(f"   No messages from Julius detected")
    
    # Check pending tasks
    cur.execute("""
        SELECT task_id, status, created_at
        FROM ai_communication 
        WHERE to_agent = 'julius_ai' 
        ORDER BY created_at DESC 
        LIMIT 5
    """)
    pending = cur.fetchall()
    
    if pending:
        print(f"\n📋 TASKS FOR JULIUS:")
        for task in pending:
            status_icon = "⚙️" if task['status'] == 'in_progress' else "⏳" if task['status'] == 'pending' else "✅"
            print(f"   {status_icon} {task['task_id']}: {task['status'].upper()}")
    
    # Check research insights
    cur.execute("""
        SELECT COUNT(*) as count, MAX(created_at) as last_insight
        FROM research_insights 
        WHERE julius_generated = TRUE
    """)
    insights = cur.fetchone()
    
    if insights['count'] > 0:
        print(f"\n💡 RESEARCH INSIGHTS:")
        print(f"   Julius has generated {insights['count']} insights!")
        print(f"   Latest: {insights['last_insight']}")
        
        # Show latest insights
        cur.execute("""
            SELECT insight_type, research_area, insight_text, created_at
            FROM research_insights 
            WHERE julius_generated = TRUE
            ORDER BY created_at DESC 
            LIMIT 3
        """)
        recent = cur.fetchall()
        
        print(f"\n   📝 Recent discoveries:")
        for i, insight in enumerate(recent, 1):
            print(f"   {i}. [{insight['insight_type']}] {insight['insight_text'][:60]}...")
    else:
        print(f"\n💡 RESEARCH INSIGHTS: None yet")
    
    # Check output files
    output_dir = "ai_collaboration/julius_to_replit"
    if os.path.exists(output_dir):
        files = []
        for root, dirs, filenames in os.walk(output_dir):
            files.extend([os.path.join(root, f) for f in filenames])
        
        if files:
            print(f"\n📁 OUTPUT FILES: {len(files)} files created")
            for f in files[:5]:
                print(f"   - {f}")
        else:
            print(f"\n📁 OUTPUT FILES: None yet")
    
    print("\n" + "="*70)
    
    cur.close()
    conn.close()
    
    return julius_messages['count'] > 0

def monitor_continuously():
    """Monitor Julius activity every 30 seconds"""
    print("\n🚀 Starting continuous Julius monitoring...")
    print("Press Ctrl+C to stop\n")
    
    try:
        while True:
            is_active = check_julius_activity()
            
            if is_active:
                print("\n✅ Julius is working! Check again in 30 seconds...")
            else:
                print("\n⏳ Waiting for Julius to activate...")
                print("\nTo activate Julius:")
                print("1. Copy: ai_collaboration/COMPLETE_JULIUS_PROMPT_WITH_VISION.txt")
                print("2. Paste into Julius AI")
                print("3. Wait for Julius to confirm activation")
            
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("\n\n👋 Monitoring stopped")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--continuous":
        monitor_continuously()
    else:
        check_julius_activity()
        print("\nTip: Run with --continuous flag to monitor in real-time")
        print("     python3 ai_collaboration/monitor_julius.py --continuous")
