#!/bin/bash
echo "═══════════════════════════════════════════════════════════"
echo "JULIUS COMMUNICATION STATUS"
echo "═══════════════════════════════════════════════════════════"
echo ""

python3 << 'PYEOF'
import os
import psycopg2
from datetime import datetime

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

# Check messages TO Julius
cur.execute("""
    SELECT COUNT(*), MAX(created_at)
    FROM ai_communication
    WHERE from_agent = 'replit' AND to_agent = 'julius'
      AND status = 'pending'
      AND created_at > NOW() - INTERVAL '1 hour'
""")
to_julius = cur.fetchone()
print(f"📤 Messages TO Julius (last hour): {to_julius[0]}")
if to_julius[1]:
    print(f"   Last sent: {to_julius[1]}")

# Check messages FROM Julius
cur.execute("""
    SELECT COUNT(*), MAX(created_at)
    FROM ai_communication
    WHERE from_agent = 'julius'
      AND created_at > NOW() - INTERVAL '1 hour'
""")
from_julius = cur.fetchone()
print(f"📥 Messages FROM Julius (last hour): {from_julius[0]}")
if from_julius[1]:
    print(f"   Last received: {from_julius[1]}")
else:
    print(f"   ⚠️  NO RESPONSES in last hour!")

# Get last message TO Julius
cur.execute("""
    SELECT id, task_id, created_at, LEFT(prompt_text, 100)
    FROM ai_communication
    WHERE from_agent = 'replit' AND to_agent = 'julius'
    ORDER BY created_at DESC
    LIMIT 1
""")
last = cur.fetchone()
if last:
    print(f"\n📬 LAST MESSAGE TO JULIUS:")
    print(f"   ID: {last[0]} | Task: {last[1]}")
    print(f"   Sent: {last[2]}")
    print(f"   Preview: {last[3]}...")

cur.close()
conn.close()

PYEOF

echo ""
echo "═══════════════════════════════════════════════════════════"
