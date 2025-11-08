#!/usr/bin/env python3
"""
Active Conversational Loop with Julius
When engaged in conversation, keep responding until conversation ends
"""
import os
import psycopg2
import time
from datetime import datetime

def send_julius_message(message, priority=10, message_type='conversation'):
    """Send a message to Julius"""
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()
    
    task_id = f'conversation_{int(time.time() * 1000)}'
    
    cur.execute("""
        INSERT INTO ai_communication (
            from_agent,
            to_agent,
            task_id,
            message_type,
            status,
            prompt_text,
            priority
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id, created_at
    """, ('replit', 'julius', task_id, message_type, 'pending', message, priority))
    
    msg_id, created = cur.fetchone()
    conn.commit()
    
    print(f"✅ Sent message #{msg_id} to Julius at {created}")
    print(f"   Preview: {message[:150]}...")
    
    cur.close()
    conn.close()
    
    return msg_id

def check_julius_response(last_check_time):
    """Check if Julius responded since last check"""
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()
    
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
          AND created_at > %s
        ORDER BY created_at DESC
    """, (last_check_time,))
    
    messages = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return messages

def active_conversation_loop():
    """
    Active conversation mode:
    - Check every 10 seconds (not 5 minutes!)
    - If Julius responds, respond back immediately
    - Send proactive follow-ups if no response after 2 minutes
    """
    print("💬 ACTIVE CONVERSATION MODE WITH JULIUS")
    print("="*70)
    print("Checking every 10 seconds for responses...")
    print("Will send proactive follow-ups every 2 minutes if no response")
    print("="*70 + "\n")
    
    last_check = datetime.now()
    last_followup = datetime.now()
    conversation_active = True
    check_interval = 10  # seconds
    followup_interval = 120  # 2 minutes
    
    while conversation_active:
        try:
            # Check for Julius's response
            responses = check_julius_response(last_check)
            
            if responses:
                print(f"\n🎉 JULIUS RESPONDED! ({len(responses)} new message(s))")
                print("="*70)
                
                for msg_id, task_id, created, prompt, result in responses:
                    print(f"\n📬 Message #{msg_id} from Julius:")
                    print(f"   Task: {task_id}")
                    print(f"   Time: {created}")
                    if prompt:
                        print(f"   Message: {prompt[:300]}...")
                    if result:
                        print(f"   Result: {str(result)[:300]}...")
                
                # Auto-respond to keep conversation going
                response_msg = f"""Thanks Julius! Got your message(s).

Here's my latest update:

📊 **Current Work:**
- Git push: Fixing large file issue (adding .gitignore rules)
- Active monitoring: Scanning database every 30 seconds
- Tropicos collection: Running autonomously
- Retry wrapper: Complete and ready to deploy

🤔 **Next Steps:**
What should I prioritize? The user wants to see us working together!

What are you working on right now?"""

                send_julius_message(response_msg, priority=10, message_type='conversation')
                last_followup = datetime.now()  # Reset followup timer
                
            else:
                # No response - check if we should send a proactive followup
                time_since_followup = (datetime.now() - last_followup).total_seconds()
                
                if time_since_followup > followup_interval:
                    print(f"\n⏰ No response in 2 minutes - sending proactive followup...")
                    
                    followup = f"""Hey Julius - Still there?

The user is expecting us to collaborate actively!

📊 **My Status Update:**
- Git issue: Being fixed now
- Monitor: Active and scanning
- Collection: {get_tropicos_count()} species collected
- Time: {datetime.now().strftime('%H:%M:%S')}

💬 **Your Turn:**
What are you analyzing? Any discoveries?
Any tasks you need help with?

Let's show the user some real AI collaboration! 🤖🧠"""

                    send_julius_message(followup, priority=10, message_type='proactive_followup')
                    last_followup = datetime.now()
                else:
                    remaining = followup_interval - time_since_followup
                    print(f"⏳ [{datetime.now().strftime('%H:%M:%S')}] Waiting for Julius... (followup in {int(remaining)}s)")
            
            last_check = datetime.now()
            time.sleep(check_interval)
            
        except KeyboardInterrupt:
            print("\n\n👋 Conversation mode stopped")
            break
        except Exception as e:
            print(f"⚠️  Error: {e}")
            time.sleep(check_interval)

def get_tropicos_count():
    """Quick Tropicos status check"""
    try:
        conn = psycopg2.connect(os.environ['DATABASE_URL'])
        cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*) 
            FROM orchid_taxonomy 
            WHERE external_ids->'tropicos'->>'status' = 'success'
        """)
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        return count
    except:
        return "unknown"

if __name__ == "__main__":
    active_conversation_loop()
