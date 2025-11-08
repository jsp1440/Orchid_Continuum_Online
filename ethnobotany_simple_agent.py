#!/usr/bin/env python3
"""Simple Ethnobotany Enrichment - Working Version"""
import os
import json
import psycopg2
from datetime import datetime

DATABASE_URL = os.environ.get("DATABASE_URL")

# Ethnobotany knowledge base
ETHNOBOTANY = {
    'Vanilla': {'traditional_uses': ['Food flavoring', 'Medicine'], 'cultural': 'Sacred to Totonac people'},
    'Dendrobium': {'traditional_uses': ['TCM herb', 'Tea'], 'cultural': '2000+ years in Chinese medicine'},
    'Cymbidium': {'traditional_uses': ['Medicine', 'Perfume'], 'cultural': 'Symbol of nobility in China'},
    'Bletilla': {'traditional_uses': ['Wound healing', 'TCM'], 'cultural': 'Hemostatic herb'},
    'Angraecum': {'traditional_uses': ['Madagascar medicine'], 'cultural': 'Sacred in Madagascar'},
}

def main():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Post start message
    cur.execute("""
        INSERT INTO julius_communication (message_from, message_type, subject, message)
        VALUES ('ethnobotany_agent', 'status_update', '🌿 Ethnobotany Enrichment Started', 
                'Adding traditional uses and cultural significance to orchids...')
    """)
    conn.commit()
    
    enriched = 0
    for genus in ETHNOBOTANY.keys():
        data_json = json.dumps(ETHNOBOTANY[genus])
        
        # Update orchids of this genus
        cur.execute("""
            UPDATE orchid_record
            SET ethnobotany_data = %s::jsonb,
                ethnobotany_last_updated = CURRENT_TIMESTAMP
            WHERE genus = %s
              AND (ethnobotany_data IS NULL OR ethnobotany_data::text = '{}')
        """, (data_json, genus))
        
        enriched += cur.rowcount
        conn.commit()
        
        if cur.rowcount > 0:
            # Log to dashboard
            cur.execute("""
                INSERT INTO julius_communication (message_from, message_type, subject, message)
                VALUES ('ethnobotany_agent', 'result', %s, %s)
            """, (
                f'✅ Enriched {cur.rowcount} {genus} orchids',
                f'Added ethnobotany data: {ETHNOBOTANY[genus]["cultural"][:50]}...'
            ))
            conn.commit()
            print(f"Enriched {cur.rowcount} {genus} orchids")
    
    # Final message
    cur.execute("""
        INSERT INTO julius_communication (message_from, message_type, subject, message)
        VALUES ('ethnobotany_agent', 'result', %s, %s)
    """, (
        f'✅ Ethnobotany Complete: {enriched} Orchids Enriched',
        f'Added traditional uses and cultural significance to {enriched} orchids across {len(ETHNOBOTANY)} genera.'
    ))
    conn.commit()
    
    print(f"DONE! Enriched {enriched} orchids")
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
