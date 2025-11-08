import psycopg2
import os
import time

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

while True:
    cur.execute("SELECT COUNT(*) FROM ai_communication WHERE from_agent = 'julius'")
    count = cur.fetchone()[0]
    
    if count > 0:
        print(f"\n🎉 JULIUS RESPONDED! Found {count} messages")
        cur.execute("SELECT task_id, result_summary, created_at FROM ai_communication WHERE from_agent = 'julius' ORDER BY created_at DESC LIMIT 3")
        for row in cur.fetchall():
            print(f"  - {row[0]}: {row[1]} ({row[2]})")
        break
    else:
        print(f"[{time.strftime('%H:%M:%S')}] Waiting for Julius... (checking every 30 seconds)")
        time.sleep(30)

cur.close()
conn.close()
