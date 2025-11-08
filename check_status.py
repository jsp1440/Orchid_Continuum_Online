#!/usr/bin/env python3
"""Quick status checker for image uploads"""

import psycopg2
import os
from datetime import datetime, timedelta

DATABASE_URL = os.environ.get('DATABASE_URL')

try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Total counts
    cur.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE google_drive_url IS NOT NULL AND google_drive_url != '') as uploaded,
            COUNT(*) FILTER (WHERE google_drive_url IS NULL OR google_drive_url = '') as remaining
        FROM orchid_images
    """)
    total, uploaded, remaining = cur.fetchone()
    
    # Recent uploads (last hour)
    cur.execute("""
        SELECT COUNT(*) 
        FROM orchid_images 
        WHERE updated_at > NOW() - INTERVAL '1 hour'
        AND google_drive_url IS NOT NULL
    """)
    last_hour = cur.fetchone()[0]
    
    # Recent uploads (last 10 minutes)
    cur.execute("""
        SELECT COUNT(*) 
        FROM orchid_images 
        WHERE updated_at > NOW() - INTERVAL '10 minutes'
        AND google_drive_url IS NOT NULL
    """)
    last_10_min = cur.fetchone()[0]
    
    cur.close()
    conn.close()
    
    print("="*60)
    print("📊 UPLOAD STATUS CHECK")
    print("="*60)
    print(f"Total Images:     {total:,}")
    print(f"✅ Uploaded:      {uploaded:,}")
    print(f"⏳ Remaining:     {remaining:,}")
    print(f"📈 Progress:      {(uploaded/total*100):.2f}%")
    print()
    print(f"🕐 Last hour:     {last_hour:,} images")
    print(f"⚡ Last 10 min:   {last_10_min:,} images")
    print()
    
    if last_10_min > 0:
        rate = last_10_min * 6  # per hour
        eta_hours = remaining / rate if rate > 0 else 0
        eta_days = eta_hours / 24
        print(f"⚡ Current Speed:  ~{rate:,} images/hour")
        print(f"⏱️  ETA:           ~{eta_days:.1f} days")
        print()
        print("✅ UPLOAD IS WORKING!")
    else:
        print("⚠️  No recent uploads detected")
        print("   Either Colab hasn't started yet, or there's an issue")
    
    print("="*60)

except Exception as e:
    print(f"❌ Error: {e}")
