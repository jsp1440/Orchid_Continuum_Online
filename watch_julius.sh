#!/bin/bash
# Quick Julius conversation monitor for the user

echo "🤖 JULIUS ↔ REPLIT CONVERSATION MONITOR"
echo "========================================"
echo ""

python3 << 'PYEOF'
import os
import psycopg2
from datetime import datetime

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

# Get last 10 messages
cur.execute("""
    SELECT 
        id,
        from_agent,
        to_agent,
        status,
        created_at,
        prompt_text
    FROM ai_communication
    WHERE (from_agent = 'julius' OR to_agent = 'julius')
    ORDER BY created_at DESC
    LIMIT 10
""")

for row in cur.fetchall():
    msg_id, from_a, to_a, status, created, text = row
    time_ago = (datetime.now() - created).total_seconds() / 3600
    
    direction = "🧠 JULIUS → Replit" if from_a == 'julius' else "🤖 Replit → Julius"
    preview = text[:120] if text else "(no text)"
    
    print(f"\n#{msg_id} | {direction} | {status.upper()}")
    print(f"   ⏰ {time_ago:.1f} hours ago")
    print(f"   💬 {preview}...")

print("\n" + "="*60)
print("Run this anytime: bash watch_julius.sh")
print("="*60 + "\n")

cur.close()
conn.close()
PYEOF
