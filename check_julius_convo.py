#!/usr/bin/env python3
"""Quick Julius conversation checker"""
import os
import psycopg2
from datetime import datetime

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

print("\n🤖 REPLIT ↔ JULIUS CONVERSATION\n" + "="*60)

cur.execute("""
    SELECT 
        id,
        CASE 
            WHEN from_agent = 'julius' THEN '🧠 Julius → Replit'
            ELSE '🤖 Replit → Julius'
        END as direction,
        status,
        created_at,
        LEFT(prompt_text, 120) as preview
    FROM ai_communication
    WHERE (from_agent = 'julius' OR to_agent = 'julius')
    ORDER BY created_at DESC
    LIMIT 15
""")

for row in cur.fetchall():
    msg_id, direction, status, created, preview = row
    time_ago = (datetime.now() - created).total_seconds() / 3600
    print(f"\n#{msg_id} | {direction}")
    print(f"Status: {status} | {time_ago:.1f}h ago")
    print(f"Preview: {preview}...")

cur.close()
conn.close()
print("\n" + "="*60 + "\n")
