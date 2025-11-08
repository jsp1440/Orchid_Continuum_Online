#!/usr/bin/env python3
"""
Process Julius AI insights and create enrichment priorities
"""
import psycopg2
import os
from datetime import datetime

DATABASE_URL = os.environ.get('DATABASE_URL')

# Julius's findings
PRIORITY_GENERA = [
    {'genus': 'Cattleya', 'needs_images': 544, 'coverage_pct': 35.3, 'priority': 100},
    {'genus': 'Potinara', 'needs_images': 253, 'coverage_pct': 12.2, 'priority': 95},
    {'genus': 'Dendrobium', 'needs_images': 145, 'coverage_pct': 50.5, 'priority': 90},
    {'genus': 'Cymbidium', 'needs_images': 116, 'coverage_pct': 37.0, 'priority': 85},
    {'genus': 'Epidendrum', 'needs_images': 87, 'coverage_pct': 27.5, 'priority': 80},
]

def process_julius_insights():
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    print(f"🧠 Processing Julius AI insights at {datetime.now().strftime('%H:%M:%S')}")
    
    for genus_data in PRIORITY_GENERA:
        genus = genus_data['genus']
        needs = genus_data['needs_images']
        priority = genus_data['priority']
        
        # Create enrichment priority
        cursor.execute("""
            INSERT INTO enrichment_queue (
                genus, enrichment_type, priority, source, metadata, status, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT DO NOTHING
        """, (
            genus,
            'image_collection',
            priority,
            'julius_ai_analysis',
            f'{{"needs_images": {needs}, "target_sources": ["gbif", "inaturalist"]}}',
            'pending'
        ))
        
        print(f"✅ Priority created: {genus} (needs {needs} images, priority {priority})")
    
    conn.commit()
    
    # Post confirmation back to Julius
    cursor.execute("""
        INSERT INTO julius_communication (
            message_from, message_type, subject, message, created_at
        ) VALUES (
            'Autonomous Agent',
            'response',
            'Priorities Created - Image Collection Started',
            'Processed your analysis! Created high-priority enrichment tasks for: Cattleya (P:100), Potinara (P:95), Dendrobium (P:90), Cymbidium (P:85), Epidendrum (P:80). Workers now prioritizing these genera for GBIF/iNaturalist image collection.',
            NOW()
        )
    """)
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"🎯 All priorities created! Workers will now focus on these genera")

if __name__ == "__main__":
    process_julius_insights()
