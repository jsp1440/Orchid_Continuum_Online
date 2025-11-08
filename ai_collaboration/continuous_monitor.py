#!/usr/bin/env python3
"""
CONTINUOUS MONITORING: Check Julius AI progress every 5 minutes
Runs autonomously and responds to Julius's updates
"""
import psycopg2
import os
import time
import json
from datetime import datetime

DATABASE_URL = os.environ.get("DATABASE_URL")
CHECK_INTERVAL = 300  # 5 minutes in seconds

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)

def check_julius_progress():
    """Check if Julius has completed or updated any tasks"""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Check for completed tasks from Julius
    cur.execute("""
        SELECT task_id, status, result_summary, result_path, completed_at
        FROM ai_communication
        WHERE to_agent = 'julius'
          AND status IN ('completed', 'in_progress')
          AND task_id IN ('validation_quiz_20251021_023350', 'eol_page_id_mapping_20251021_030000')
    """)
    
    tasks = cur.fetchall()
    
    if tasks:
        log(f"📊 Julius status update:")
        for task in tasks:
            task_id, status, summary, path, completed_at = task
            log(f"  - {task_id}: {status}")
            if summary:
                log(f"    Summary: {summary[:100]}")
            if path:
                log(f"    Output: {path}")
    else:
        log("⏳ Waiting for Julius to start working...")
    
    cur.close()
    conn.close()
    return tasks

def check_julius_questions():
    """Check if Julius has asked any questions"""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    cur.execute("""
        SELECT task_id, prompt_text, created_at
        FROM ai_communication
        WHERE from_agent = 'julius'
          AND to_agent = 'replit_agent'
          AND status = 'pending'
        ORDER BY created_at DESC
        LIMIT 5
    """)
    
    questions = cur.fetchall()
    
    if questions:
        log(f"❓ Julius has {len(questions)} pending questions:")
        for q in questions:
            task_id, text, created = q
            log(f"  - {task_id}: {text[:100]}...")
    
    cur.close()
    conn.close()
    return questions

def send_encouragement():
    """Send periodic encouragement to Julius"""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Check how long Julius has been working
    cur.execute("""
        SELECT COUNT(*) FROM ai_communication
        WHERE to_agent = 'julius'
          AND status = 'in_progress'
    """)
    
    in_progress = cur.fetchone()[0]
    
    if in_progress > 0:
        log(f"💪 Julius is actively working on {in_progress} task(s). Keep going!")
    
    cur.close()
    conn.close()

def main():
    log("🚀 CONTINUOUS MONITORING SYSTEM STARTED")
    log(f"   Checking Julius AI progress every {CHECK_INTERVAL} seconds (5 minutes)")
    log(f"   Database: Connected to PostgreSQL")
    log(f"   Monitoring tasks: validation_quiz, eol_page_id_mapping")
    log("")
    
    cycle = 0
    
    while True:
        try:
            cycle += 1
            log(f"🔄 Check cycle #{cycle}")
            
            # Check Julius's progress
            tasks = check_julius_progress()
            
            # Check if Julius has questions
            questions = check_julius_questions()
            
            # Send encouragement every 3rd cycle (15 minutes)
            if cycle % 3 == 0:
                send_encouragement()
            
            log(f"   Next check in {CHECK_INTERVAL} seconds...")
            log("")
            
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            log("🛑 Monitoring stopped by user")
            break
        except Exception as e:
            log(f"❌ Error: {e}")
            log(f"   Retrying in 60 seconds...")
            time.sleep(60)

if __name__ == "__main__":
    main()
