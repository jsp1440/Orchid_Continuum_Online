#!/usr/bin/env python3
"""
Priority Harvester - Targets specific orchid species for intensive image collection
Designed for the 5 "Snow Orchids" collection
"""

import os
import sys
import time
import json
import requests
import hashlib
import logging
from datetime import datetime

import psycopg2
from psycopg2.extras import RealDictCursor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PRIORITY_SPECIES = [
    {"genus": "Calypso", "species": "bulbosa", "common_name": "Fairy Slipper Orchid", "taxonomy_id": 31581},
    {"genus": "Dactylorhiza", "species": "aristata", "common_name": "Glacier Orchid", "taxonomy_id": 11325},
    {"genus": "Habenaria", "species": "intermedia", "common_name": "Himalayan Spurred Orchid", "taxonomy_id": 2188},
    {"genus": "Cephalanthera", "species": "austiniae", "common_name": "Phantom Orchid", "taxonomy_id": 15257},
    {"genus": "Platanthera", "species": "elegans", "common_name": "Mount Rainier Orchid", "taxonomy_id": 4387},
]

class PriorityHarvester:
    def __init__(self):
        self.conn = psycopg2.connect(os.environ['DATABASE_URL'])
        self.stats = {s["genus"] + " " + s["species"]: 0 for s in PRIORITY_SPECIES}
        
    def get_current_counts(self):
        """Get current image counts for priority species"""
        cur = self.conn.cursor(cursor_factory=RealDictCursor)
        results = []
        for spec in PRIORITY_SPECIES:
            cur.execute("""
                SELECT COUNT(*) as count FROM orchid_images 
                WHERE taxonomy_id = %s
            """, (spec["taxonomy_id"],))
            row = cur.fetchone()
            count = row["count"] if row else 0
            results.append({
                **spec,
                "current_images": count
            })
        cur.close()
        return results
    
    def harvest_gbif(self, genus, species, taxonomy_id):
        """Harvest images from GBIF for a specific species"""
        logger.info(f"🌍 GBIF: Searching for {genus} {species}...")
        
        search_url = "https://api.gbif.org/v1/occurrence/search"
        params = {
            "scientificName": f"{genus} {species}",
            "mediaType": "StillImage",
            "limit": 300,
            "hasCoordinate": True
        }
        
        try:
            resp = requests.get(search_url, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            
            images_added = 0
            for record in data.get("results", []):
                if "media" not in record:
                    continue
                    
                for media in record.get("media", []):
                    if media.get("type") != "StillImage":
                        continue
                    
                    image_url = media.get("identifier")
                    if not image_url:
                        continue
                    
                    if self.save_image(
                        taxonomy_id=taxonomy_id,
                        image_url=image_url,
                        source="GBIF",
                        gbif_key=record.get("key"),
                        country=record.get("country"),
                        locality=record.get("locality"),
                        latitude=record.get("decimalLatitude"),
                        longitude=record.get("decimalLongitude"),
                        observer=record.get("recordedBy"),
                        license=media.get("license")
                    ):
                        images_added += 1
            
            logger.info(f"   ✅ GBIF: Added {images_added} images for {genus} {species}")
            return images_added
            
        except Exception as e:
            logger.error(f"   ❌ GBIF error: {e}")
            return 0
    
    def harvest_inaturalist(self, genus, species, taxonomy_id):
        """Harvest images from iNaturalist for a specific species"""
        logger.info(f"🦋 iNaturalist: Searching for {genus} {species}...")
        
        search_url = "https://api.inaturalist.org/v1/observations"
        params = {
            "taxon_name": f"{genus} {species}",
            "photos": True,
            "quality_grade": "research",
            "per_page": 200
        }
        
        try:
            resp = requests.get(search_url, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            
            images_added = 0
            for obs in data.get("results", []):
                for photo in obs.get("photos", []):
                    image_url = photo.get("url", "").replace("square", "original")
                    if not image_url:
                        continue
                    
                    if self.save_image(
                        taxonomy_id=taxonomy_id,
                        image_url=image_url,
                        source="iNaturalist",
                        country=obs.get("place_guess"),
                        locality=obs.get("place_guess"),
                        latitude=obs.get("geojson", {}).get("coordinates", [None, None])[1] if obs.get("geojson") else None,
                        longitude=obs.get("geojson", {}).get("coordinates", [None, None])[0] if obs.get("geojson") else None,
                        observer=obs.get("user", {}).get("login"),
                        license=photo.get("license_code")
                    ):
                        images_added += 1
            
            logger.info(f"   ✅ iNaturalist: Added {images_added} images for {genus} {species}")
            return images_added
            
        except Exception as e:
            logger.error(f"   ❌ iNaturalist error: {e}")
            return 0
    
    def harvest_flickr(self, genus, species, taxonomy_id):
        """Search Flickr for Creative Commons orchid images"""
        logger.info(f"📷 Flickr: Searching for {genus} {species}...")
        
        api_key = os.environ.get("FLICKR_API_KEY")
        if not api_key:
            logger.info("   ⏭️ No Flickr API key, skipping")
            return 0
            
        search_url = "https://api.flickr.com/services/rest/"
        params = {
            "method": "flickr.photos.search",
            "api_key": api_key,
            "text": f"{genus} {species} orchid",
            "license": "1,2,3,4,5,6",  # Creative Commons
            "content_type": 1,  # Photos only
            "media": "photos",
            "per_page": 100,
            "format": "json",
            "nojsoncallback": 1,
            "extras": "license,owner_name,geo,url_l,url_o"
        }
        
        try:
            resp = requests.get(search_url, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            
            images_added = 0
            for photo in data.get("photos", {}).get("photo", []):
                image_url = photo.get("url_o") or photo.get("url_l")
                if not image_url:
                    continue
                
                if self.save_image(
                    taxonomy_id=taxonomy_id,
                    image_url=image_url,
                    source="Flickr",
                    country=None,
                    locality=None,
                    latitude=photo.get("latitude") if photo.get("latitude") != 0 else None,
                    longitude=photo.get("longitude") if photo.get("longitude") != 0 else None,
                    observer=photo.get("ownername"),
                    license=f"CC-{photo.get('license')}"
                ):
                    images_added += 1
            
            logger.info(f"   ✅ Flickr: Added {images_added} images for {genus} {species}")
            return images_added
            
        except Exception as e:
            logger.error(f"   ❌ Flickr error: {e}")
            return 0
    
    def save_image(self, taxonomy_id, image_url, source, gbif_key=None, country=None, 
                   locality=None, latitude=None, longitude=None, observer=None, license=None):
        """Save an image to the database if it doesn't already exist"""
        try:
            cur = self.conn.cursor()
            
            # Check for duplicate
            url_hash = hashlib.md5(image_url.encode()).hexdigest()
            cur.execute("""
                SELECT id FROM orchid_images WHERE image_url = %s
            """, (image_url,))
            
            if cur.fetchone():
                cur.close()
                return False
            
            # Insert new image
            cur.execute("""
                INSERT INTO orchid_images (
                    taxonomy_id, image_url, image_source, gbif_occurrence_key,
                    country, locality, latitude, longitude, observer_name, image_license,
                    created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT DO NOTHING
            """, (taxonomy_id, image_url, source, gbif_key, country, locality, 
                  latitude, longitude, observer, license))
            
            self.conn.commit()
            cur.close()
            return True
            
        except Exception as e:
            self.conn.rollback()
            logger.debug(f"Save error: {e}")
            return False
    
    def run_priority_harvest(self):
        """Run intensive harvest for all priority species"""
        print("\n" + "="*60)
        print("🌺 PRIORITY ORCHID HARVESTER - Snow Orchids Collection")
        print("="*60)
        
        # Show current status
        print("\n📊 CURRENT STATUS:")
        counts = self.get_current_counts()
        for c in counts:
            status = "✅" if c["current_images"] >= 30 else "🔶" if c["current_images"] > 0 else "❌"
            print(f"   {status} {c['common_name']}: {c['current_images']} images")
        
        print("\n🔄 STARTING PRIORITY HARVEST...")
        
        total_added = 0
        for spec in PRIORITY_SPECIES:
            name = f"{spec['genus']} {spec['species']}"
            print(f"\n{'='*40}")
            print(f"🎯 TARGET: {spec['common_name']} ({name})")
            print(f"{'='*40}")
            
            # Harvest from all sources
            added = 0
            added += self.harvest_gbif(spec["genus"], spec["species"], spec["taxonomy_id"])
            time.sleep(1)  # Rate limiting
            
            added += self.harvest_inaturalist(spec["genus"], spec["species"], spec["taxonomy_id"])
            time.sleep(1)
            
            added += self.harvest_flickr(spec["genus"], spec["species"], spec["taxonomy_id"])
            time.sleep(1)
            
            self.stats[name] = added
            total_added += added
            print(f"   📈 Total added for {name}: {added}")
        
        # Final summary
        print("\n" + "="*60)
        print("🎉 PRIORITY HARVEST COMPLETE!")
        print("="*60)
        print(f"\n📊 FINAL STATUS:")
        counts = self.get_current_counts()
        for c in counts:
            added = self.stats.get(f"{c['genus']} {c['species']}", 0)
            status = "✅" if c["current_images"] >= 30 else "🔶" if c["current_images"] > 0 else "❌"
            print(f"   {status} {c['common_name']}: {c['current_images']} images (+{added} new)")
        
        print(f"\n🌺 TOTAL NEW IMAGES: {total_added}")
        
        self.conn.close()
        return total_added


if __name__ == "__main__":
    harvester = PriorityHarvester()
    harvester.run_priority_harvest()
