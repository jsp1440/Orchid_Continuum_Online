#!/usr/bin/env python3
"""
Monitor Replit ↔ Julius AI Conversation
Run this to see real-time communication status
"""

import os
from sqlalchemy import create_engine, text
from datetime import datetime

def monitor_conversation():
    # Connect to database
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not set")
        return
    
    engine = create_engine(db_url)
    
    print("=" * 80)
    print("🤖 REPLIT ↔ JULIUS AI CONVERSATION MONITOR")
    print("=" * 80)
    print()
    
    with engine.connect() as conn:
        # Get recent conversation
        query = text("""
            SELECT 
                id,
                CASE 
                    WHEN from_agent = 'replit' THEN '🤖 → Julius'
                    WHEN from_agent = 'julius' THEN '🧠 Julius → Me'
                END as direction,
                task_id,
                message_type,
                LEFT(prompt_text, 80) as message_preview,
                status,
                priority,
                created_at,
                completed_at
            FROM ai_communication
            WHERE (from_agent = 'julius' AND to_agent = 'replit')
               OR (from_agent = 'replit' AND to_agent = 'julius')
            ORDER BY created_at DESC
            LIMIT 10
        """)
        
        result = conn.execute(query)
        rows = result.fetchall()
        
        if not rows:
            print("📭 No conversation found yet")
            return
        
        print(f"📊 Showing last {len(rows)} messages:\n")
        
        for row in rows:
            print(f"{'─' * 80}")
            print(f"Direction: {row[1]}")
            print(f"Task: {row[2]}")
            print(f"Type: {row[3]}")
            print(f"Status: {row[5]} (Priority: {row[6]})")
            print(f"Created: {row[7]}")
            if row[8]:
                print(f"Completed: {row[8]}")
            print(f"Message: {row[4]}...")
            print()
        
        # Check pending tasks for Julius
        pending_query = text("""
            SELECT COUNT(*) as count
            FROM ai_communication
            WHERE to_agent = 'julius'
            AND status = 'pending'
        """)
        
        pending_result = conn.execute(pending_query)
        pending_count = pending_result.fetchone()[0]
        
        print(f"{'=' * 80}")
        print(f"📬 Julius has {pending_count} pending task(s) to work on")
        print(f"{'=' * 80}")
        
        # Check Julius's latest response
        julius_query = text("""
            SELECT 
                task_id,
                result_summary,
                completed_at
            FROM ai_communication
            WHERE from_agent = 'julius'
            ORDER BY created_at DESC
            LIMIT 1
        """)
        
        julius_result = conn.execute(julius_query)
        julius_row = julius_result.fetchone()
        
        if julius_row:
            print(f"\n🧠 Julius's Latest Response:")
            print(f"Task: {julius_row[0]}")
            print(f"Time: {julius_row[2]}")
            print(f"Summary: {julius_row[1][:200] if julius_row[1] else 'No summary'}...")
        else:
            print(f"\n⏳ Julius hasn't responded yet - tasks are pending!")

if __name__ == "__main__":
    monitor_conversation()
