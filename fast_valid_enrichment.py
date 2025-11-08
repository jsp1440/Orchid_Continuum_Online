#!/usr/bin/env python3
"""
FAST Enrichment - VALID ORCHIDS ONLY
=====================================
Only enriches orchids with proper scientific names
Skips all broken/invalid names - no time wasting!
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, Optional
import psycopg2
from psycopg2.extras import Json
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

progress_lock = threading.Lock()

class FastValidEnrichment:
    def __init__(self):
        self.db_url = os.environ.get('DATABASE_URL')
        self.gbif_base = "https://api.gbif.org/v1"
        self.inat_base = "https://api.inaturalist.org/v1"
        
    def get_valid_orchids(self):
        """Get ONLY orchids with valid scientific names"""
        conn = psycopg2.connect(self.db_url)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, scientific_name
            FROM orchid_record
            WHERE scientific_name IS NOT NULL
            AND scientific_name != ''
            AND scientific_name LIKE '% %'
            AND scientific_name NOT LIKE '%  %'
            AND LENGTH(TRIM(scientific_name)) > 10
            AND scientific_name NOT IN ('Trichocentrum ', 'Cattleya ', ' ', 'I ', 'It ')
            ORDER BY id ASC
        """)
        
        orchids = cursor.fetchall()
        cursor.close()
        conn.close()
        return orchids
    
    def enrich_one(self, orchid_id, scientific_name, stats):
        """Enrich one orchid - get NEW images from APIs"""
        try:
            # GBIF - quick fetch
            gbif_resp = requests.get(
                f"{self.gbif_base}/species/match",
                params={'name': scientific_name},
                timeout=5
            )
            
            # iNaturalist - quick fetch  
            inat_resp = requests.get(
                f"{self.inat_base}/taxa",
                params={'q': scientific_name, 'rank': 'species'},
                timeout=5
            )
            
            # Update if we got data
            updates = []
            params = []
            
            if gbif_resp.status_code == 200:
                gbif = gbif_resp.json()
                if gbif.get('usageKey'):
                    updates.append("gbif_species_key = %s")
                    params.append(gbif['usageKey'])
                    with progress_lock:
                        stats['gbif'] += 1
            
            if inat_resp.status_code == 200:
                inat = inat_resp.json().get('results', [])
                if inat:
                    taxon = inat[0]
                    # Get photos if available
                    photos = [{'url': p.get('photo', {}).get('medium_url')} 
                             for p in taxon.get('taxon_photos', [])[:5]]
                    
                    if photos:
                        updates.extend([
                            "inaturalist_observation_id = %s",
                            "external_images = %s"
                        ])
                        params.extend([
                            taxon.get('id'),
                            Json(photos)
                        ])
                        with progress_lock:
                            stats['inat'] += 1
                            stats['photos'] += len(photos)
            
            if updates:
                conn = psycopg2.connect(self.db_url)
                cursor = conn.cursor()
                params.append(orchid_id)
                query = f"UPDATE orchid_record SET {', '.join(updates)}, updated_at = NOW() WHERE id = %s"
                cursor.execute(query, params)
                conn.commit()
                cursor.close()
                conn.close()
                return True
            
            return False
            
        except Exception as e:
            with progress_lock:
                stats['errors'] += 1
            return False
    
    def run(self):
        print("=" * 60)
        print("🚀 FAST ENRICHMENT - VALID ORCHIDS ONLY")
        print("=" * 60)
        
        orchids = self.get_valid_orchids()
        print(f"📊 Found {len(orchids)} orchids with VALID names")
        print(f"⏭️  Skipping all broken/invalid names")
        print()
        
        stats = {'gbif': 0, 'inat': 0, 'photos': 0, 'errors': 0, 'processed': 0}
        start = time.time()
        
        # Process in parallel (10 workers)
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(self.enrich_one, oid, name, stats): (oid, name) 
                      for oid, name in orchids}
            
            for future in as_completed(futures):
                stats['processed'] += 1
                
                if stats['processed'] % 100 == 0:
                    elapsed = time.time() - start
                    rate = stats['processed'] / elapsed
                    eta = (len(orchids) - stats['processed']) / rate / 60 if rate > 0 else 0
                    print(f"📊 {stats['processed']}/{len(orchids)} | "
                          f"GBIF: {stats['gbif']} | iNat: {stats['inat']} | "
                          f"Photos: {stats['photos']} | ETA: {eta:.1f}m")
        
        elapsed = time.time() - start
        print()
        print("=" * 60)
        print("✅ COMPLETE!")
        print(f"⏱️  Time: {elapsed/60:.1f} minutes")
        print(f"✅ GBIF enriched: {stats['gbif']}")
        print(f"✅ iNat enriched: {stats['inat']}")
        print(f"📸 New photos added: {stats['photos']}")
        print(f"❌ Errors: {stats['errors']}")
        print("=" * 60)

if __name__ == "__main__":
    enrichment = FastValidEnrichment()
    enrichment.run()
