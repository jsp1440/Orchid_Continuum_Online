#!/usr/bin/env python3
"""
AI Vision Analysis Worker
Analyzes orchid images separately from enrichment process
"""

import os
import time
import psycopg2
from openai import OpenAI
import base64
import requests
from datetime import datetime

DATABASE_URL = os.environ.get('DATABASE_URL')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def analyze_orchid_image(image_url):
    """Analyze orchid image with GPT-4 Vision"""
    if not client:
        return None
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """Analyze this orchid image and provide:
1. Flower color and patterns
2. Flower shape and structure
3. Growth habit (if visible)
4. Unique identifying features
5. Condition/health assessment

Keep it concise, 2-3 sentences max."""
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": image_url}
                        }
                    ]
                }
            ],
            max_tokens=300
        )
        
        return response.choices[0].message.content
    except Exception as e:
        log(f"Vision API error: {e}")
        return None

def run_vision_analysis():
    """Main vision analysis loop"""
    log("🤖 AI Vision Worker Starting...")
    
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Get orchids needing vision analysis
    cursor.execute("""
        SELECT id, scientific_name, image_url 
        FROM orchid_record 
        WHERE validation_status = 'approved'
        AND image_url IS NOT NULL
        AND ai_description IS NULL
        LIMIT 50
    """)
    
    orchids = cursor.fetchall()
    log(f"Found {len(orchids)} orchids needing AI vision analysis")
    
    if not orchids:
        log("No orchids need analysis. Sleeping...")
        cursor.close()
        conn.close()
        return
    
    for orchid_id, name, image_url in orchids:
        log(f"Analyzing: {name}")
        
        description = analyze_orchid_image(image_url)
        
        if description:
            cursor.execute("""
                UPDATE orchid_record 
                SET ai_description = %s, updated_at = NOW()
                WHERE id = %s
            """, (description, orchid_id))
            conn.commit()
            log(f"✅ Analyzed: {name}")
        else:
            log(f"⚠️ Failed: {name}")
        
        time.sleep(2)  # Rate limiting
    
    cursor.close()
    conn.close()
    log(f"✅ Batch complete! Analyzed {len(orchids)} orchids")

if __name__ == "__main__":
    while True:
        try:
            run_vision_analysis()
            time.sleep(60)  # Wait 1 minute between batches
        except KeyboardInterrupt:
            log("Vision worker stopped")
            break
        except Exception as e:
            log(f"Error: {e}")
            time.sleep(30)
