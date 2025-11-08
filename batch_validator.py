#!/usr/bin/env python3
"""
Batched GBIF validator - processes 100 orchids at a time
"""
import os
import time
import logging
import requests
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

DATABASE_URL = os.environ.get('DATABASE_URL')
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

session_http = requests.Session()
session_http.headers.update({'User-Agent': 'Orchid Research Platform'})

def validate_and_mark(orchid_id, scientific_name, db_session):
    """Validate single orchid against GBIF"""
    try:
        response = session_http.get(
            "https://api.gbif.org/v1/species/match",
            params={'name': scientific_name},
            timeout=10
        )
        time.sleep(0.5)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('matchType') == 'EXACT' and data.get('status') == 'ACCEPTED':
                db_session.execute(
                    text("UPDATE orchid_record SET gbif_species_key = :key WHERE id = :id"),
                    {'id': orchid_id, 'key': data.get('usageKey')}
                )
                db_session.commit()
                return True
        return False
    except:
        return False

def process_batch():
    """Process one batch of 100 orchids"""
    db_session = Session()
    try:
        result = db_session.execute(text("""
            SELECT id, scientific_name
            FROM orchid_record
            WHERE scientific_name IS NOT NULL
              AND LENGTH(scientific_name) > 5
              AND gbif_species_key IS NULL
            ORDER BY id
            LIMIT 100
        """))
        
        orchids = result.fetchall()
        if not orchids:
            return 0
        
        valid = 0
        for orchid in orchids:
            if validate_and_mark(orchid.id, orchid.scientific_name, db_session):
                valid += 1
                logger.info(f"✅ {orchid.scientific_name}")
            else:
                logger.info(f"❌ {orchid.scientific_name}")
        
        return len(orchids)
    finally:
        db_session.close()

if __name__ == "__main__":
    batch_num = 0
    while True:
        batch_num += 1
        logger.info(f"\n{'='*70}")
        logger.info(f"BATCH {batch_num}")
        logger.info(f"{'='*70}")
        
        processed = process_batch()
        if processed == 0:
            logger.info("✅ ALL ORCHIDS VALIDATED")
            break
        
        logger.info(f"Processed: {processed}")
