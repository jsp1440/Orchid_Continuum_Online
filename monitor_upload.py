#!/usr/bin/env python3
"""
Simple Upload Monitor - Run from Shell
Usage: python3 monitor_upload.py
"""
import os
import sys
from datetime import datetime, timedelta
import time

def clear_screen():
    """Clear terminal screen"""
    os.system('clear' if os.name == 'posix' else 'cls')

def get_upload_stats():
    """Get upload statistics from database"""
    try:
        import psycopg2
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        cur = conn.cursor()
        
        # Get totals
        cur.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(google_drive_url) FILTER (WHERE google_drive_url IS NOT NULL AND google_drive_url != '') as uploaded,
                COUNT(*) FILTER (WHERE google_drive_url IS NULL OR google_drive_url = '') as remaining
            FROM orchid_images;
        """)
        total, uploaded, remaining = cur.fetchone()
        
        # Get recent uploads with species names
        cur.execute("""
            SELECT 
                COALESCE(ot.scientific_name, 'Unknown species') as species,
                oi.updated_at
            FROM orchid_images oi
            LEFT JOIN orchid_taxonomy ot ON oi.taxonomy_id = ot.id
            WHERE oi.google_drive_url IS NOT NULL AND oi.google_drive_url != ''
            ORDER BY oi.updated_at DESC
            LIMIT 5;
        """)
        recent = cur.fetchall()
        
        # Get upload speed (last hour)
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        cur.execute("""
            SELECT COUNT(*) as uploads_last_hour
            FROM orchid_images
            WHERE google_drive_url IS NOT NULL 
            AND updated_at >= %s;
        """, (one_hour_ago,))
        uploads_last_hour = cur.fetchone()[0]
        
        cur.close()
        conn.close()
        
        return {
            'total': total,
            'uploaded': uploaded,
            'remaining': remaining,
            'recent': recent,
            'last_hour': uploads_last_hour
        }
    except Exception as e:
        return {'error': str(e)}

def format_time_remaining(minutes):
    """Format minutes into readable time"""
    if minutes < 60:
        return f"{minutes:.0f} minutes"
    elif minutes < 1440:  # Less than a day
        hours = minutes / 60
        return f"{hours:.1f} hours"
    else:
        days = minutes / 1440
        hours = (minutes % 1440) / 60
        return f"{days:.1f} days ({hours:.0f}h)"

def display_dashboard(stats):
    """Display upload dashboard"""
    clear_screen()
    
    if 'error' in stats:
        print("❌ Error:", stats['error'])
        return
    
    total = stats['total']
    uploaded = stats['uploaded']
    remaining = stats['remaining']
    last_hour = stats['last_hour']
    
    percent = (uploaded / total * 100) if total > 0 else 0
    rate = last_hour / 60  # per minute
    
    # Calculate ETA
    if rate > 0:
        minutes_remaining = remaining / rate
        eta = datetime.utcnow() + timedelta(minutes=minutes_remaining)
    else:
        minutes_remaining = remaining / 13  # Fallback to 13/min
        eta = datetime.utcnow() + timedelta(minutes=minutes_remaining)
    
    print("=" * 70)
    print("🌺 ORCHID CONTINUUM - GOOGLE DRIVE UPLOAD MONITOR")
    print("=" * 70)
    print()
    
    # Progress bar
    bar_width = 50
    filled = int(bar_width * percent / 100)
    bar = "█" * filled + "░" * (bar_width - filled)
    print(f"Progress: [{bar}] {percent:.2f}%")
    print()
    
    # Stats
    print(f"📊 STATISTICS:")
    print(f"   Total Images:    {total:,}")
    print(f"   ✅ Uploaded:     {uploaded:,}")
    print(f"   ⏳ Remaining:    {remaining:,}")
    print()
    
    # Speed
    print(f"⚡ UPLOAD SPEED:")
    print(f"   Last Hour:       {last_hour} images")
    print(f"   Current Rate:    {rate:.1f} images/min")
    print()
    
    # Time estimates
    print(f"⏰ TIME REMAINING:")
    print(f"   Estimated:       {format_time_remaining(minutes_remaining)}")
    print(f"   ETA:             {eta.strftime('%Y-%m-%d %H:%M UTC')}")
    print()
    
    # Recent uploads
    print(f"🆕 RECENT UPLOADS:")
    if stats['recent']:
        for species, upload_time in stats['recent']:
            time_str = upload_time.strftime('%H:%M:%S') if upload_time else 'Unknown'
            species_name = species[:50] if species else 'Unknown'
            print(f"   • {time_str} - {species_name}")
    else:
        print("   No recent uploads")
    print()
    
    print("=" * 70)
    print(f"Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("Press Ctrl+C to exit | Refreshing every 30 seconds...")
    print("=" * 70)

def main():
    """Main monitoring loop"""
    print("🌺 Starting Upload Monitor...")
    print("Loading...\n")
    
    try:
        while True:
            stats = get_upload_stats()
            display_dashboard(stats)
            time.sleep(30)  # Refresh every 30 seconds
    except KeyboardInterrupt:
        print("\n\n✅ Monitor stopped. Upload continues in background.")
        sys.exit(0)

if __name__ == '__main__':
    main()
