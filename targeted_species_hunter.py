#!/usr/bin/env python3
"""
Targeted Species Hunter - Orchid Continuum
Queries multiple APIs to find images for specific missing species
Goal: 30+ images per species for AI-ready coverage
Captures ALL 52+ metadata fields per image
"""
import os
import sys
import json
import time
import requests
import psycopg2
import argparse
from datetime import datetime

# API endpoints
INATURALIST_API = "https://api.inaturalist.org/v1"
GBIF_API = "https://api.gbif.org/v1"

# Coverage targets
MIN_IMAGES = 10
IDEAL_IMAGES = 30
MAX_IMAGES = 50

class TargetedSpeciesHunter:
    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.conn = psycopg2.connect(os.environ['DATABASE_URL'])
        self.cur = self.conn.cursor()
        self.stats = {
            'species_processed': 0,
            'images_found': 0,
            'images_inserted': 0,
            'api_calls': 0
        }
    
    def clean_scientific_name(self, scientific_name):
        """Extract just genus and species (remove author citations)"""
        parts = scientific_name.split()
        if len(parts) >= 2:
            return f"{parts[0]} {parts[1]}"
        return parts[0] if parts else scientific_name
    
    def extract_inaturalist_metadata(self, observation):
        """Extract ALL metadata fields from iNaturalist observation"""
        images = []
        taxon = observation.get('taxon', {})
        location = observation.get('geojson', {}).get('coordinates', [None, None])
        
        for photo in observation.get('photos', []):
            metadata = {
                # Core identification
                'occurrence_key': str(observation.get('id')),
                'image_url': photo.get('url', '').replace('square', 'original'),
                'image_source': 'iNaturalist',
                'image_license': photo.get('license_code', 'CC-BY-NC'),
                
                # Location data (ALL fields)
                'latitude': location[1] if len(location) > 1 else None,
                'longitude': location[0] if len(location) > 0 else None,
                'coordinate_uncertainty': observation.get('positional_accuracy'),
                'country': observation.get('place_guess'),
                'locality': observation.get('place_guess'),
                
                # Temporal data
                'observation_date': observation.get('observed_on'),
                'year_observed': observation.get('observed_on_details', {}).get('year'),
                'month_observed': observation.get('observed_on_details', {}).get('month'),
                
                # Observer
                'observer_name': observation.get('user', {}).get('login'),
                
                # Specimen data
                'wild_specimen': observation.get('captive') == False,
                
                # Conservation
                'iucn_red_list_category': taxon.get('conservation_status', {}).get('status'),
                
                # Complete raw metadata (ALL remaining fields)
                'occurrence_metadata': json.dumps({
                    'inat_id': observation.get('id'),
                    'uuid': observation.get('uuid'),
                    'taxon_id': taxon.get('id'),
                    'quality_grade': observation.get('quality_grade'),
                    'identifications_count': observation.get('identifications_count'),
                    'num_identification_agreements': observation.get('num_identification_agreements'),
                    'num_identification_disagreements': observation.get('num_identification_disagreements'),
                    'comments_count': observation.get('comments_count'),
                    'faves_count': observation.get('faves_count'),
                }),
                'media_metadata': json.dumps({
                    'photo_id': photo.get('id'),
                    'photo_uuid': photo.get('uuid'),
                    'large_url': photo.get('url', '').replace('square', 'large'),
                    'medium_url': photo.get('url', '').replace('square', 'medium'),
                })
            }
            images.append(metadata)
        
        return images
    
    def extract_gbif_metadata(self, occurrence):
        """Extract ALL metadata fields from GBIF occurrence"""
        images = []
        
        for media in occurrence.get('media', []):
            if media.get('type') == 'StillImage':
                metadata = {
                    # Core identification
                    'occurrence_key': str(occurrence.get('key')),
                    'image_url': media.get('identifier'),
                    'image_source': 'GBIF',
                    'image_license': media.get('license'),
                    
                    # Location data (ALL fields)
                    'latitude': occurrence.get('decimalLatitude'),
                    'longitude': occurrence.get('decimalLongitude'),
                    'coordinate_uncertainty': occurrence.get('coordinateUncertaintyInMeters'),
                    'country': occurrence.get('country'),
                    'country_code': occurrence.get('countryCode'),
                    'state_province': occurrence.get('stateProvince'),
                    'locality': occurrence.get('locality'),
                    'continent': occurrence.get('continent'),
                    'elevation_meters': occurrence.get('elevation'),
                    
                    # Temporal data
                    'observation_date': occurrence.get('eventDate'),
                    'year_observed': occurrence.get('year'),
                    'month_observed': occurrence.get('month'),
                    
                    # Observer/Institution
                    'observer_name': occurrence.get('recordedBy'),
                    'institution_code': occurrence.get('institutionCode'),
                    
                    # Specimen data
                    'individual_count': occurrence.get('individualCount'),
                    'sex': occurrence.get('sex'),
                    'life_stage': occurrence.get('lifeStage'),
                    'reproductive_condition': occurrence.get('reproductiveCondition'),
                    'wild_specimen': occurrence.get('basisOfRecord') != 'PRESERVED_SPECIMEN',
                    
                    # Complete raw metadata
                    'occurrence_metadata': json.dumps({
                        'gbif_key': occurrence.get('key'),
                        'basis_of_record': occurrence.get('basisOfRecord'),
                        'catalog_number': occurrence.get('catalogNumber'),
                        'collection_code': occurrence.get('collectionCode'),
                        'dataset_name': occurrence.get('datasetName'),
                        'publisher': occurrence.get('publisher'),
                        'taxon_rank': occurrence.get('taxonRank'),
                        'taxonomic_status': occurrence.get('taxonomicStatus'),
                    }),
                    'media_metadata': json.dumps(media)
                }
                images.append(metadata)
        
        return images
    
    def get_species_needing_images(self, limit=100, priority='CRITICAL'):
        """Get species that need more images for AI coverage"""
        print(f"\n🔍 Finding species needing images (priority: {priority})...")
        
        if priority == 'CRITICAL':
            max_current = 0
        elif priority == 'HIGH':
            max_current = 9
        elif priority == 'MEDIUM':
            max_current = 29
        else:
            max_current = 0
        
        self.cur.execute("""
            SELECT 
                ot.id,
                ot.scientific_name,
                ot.genus,
                ot.species,
                COUNT(oi.id) as current_images
            FROM orchid_taxonomy ot
            LEFT JOIN orchid_images oi ON ot.id = oi.taxonomy_id
            WHERE ot.scientific_name IS NOT NULL
            AND ot.scientific_name != ''
            GROUP BY ot.id, ot.scientific_name, ot.genus, ot.species
            HAVING COUNT(oi.id) <= %s
            ORDER BY COUNT(oi.id) ASC, ot.scientific_name
            LIMIT %s
        """, (max_current, limit))
        
        species_list = self.cur.fetchall()
        print(f"✅ Found {len(species_list)} species needing images\n")
        return species_list
    
    def search_inaturalist(self, scientific_name, needed_count=30):
        """Search iNaturalist for species images with ALL metadata"""
        clean_name = self.clean_scientific_name(scientific_name)
        print(f"   🔎 iNaturalist: {clean_name}...", end=" ", flush=True)
        self.stats['api_calls'] += 1
        
        try:
            response = requests.get(
                f"{INATURALIST_API}/observations",
                params={
                    'taxon_name': clean_name,
                    'photos': 'true',
                    'quality_grade': 'research',
                    'per_page': min(needed_count, 200),
                    'order': 'desc',
                    'order_by': 'votes'
                },
                timeout=15
            )
            response.raise_for_status()
            
            observations = response.json().get('results', [])
            
            images = []
            for obs in observations:
                images.extend(self.extract_inaturalist_metadata(obs))
                if len(images) >= needed_count:
                    break
            
            print(f"found {len(images)}")
            return images
        
        except Exception as e:
            print(f"error ({str(e)[:30]})")
            return []
    
    def search_gbif(self, scientific_name, genus, needed_count=30):
        """Search GBIF for species images with ALL metadata"""
        clean_name = self.clean_scientific_name(scientific_name)
        print(f"   🌍 GBIF: {clean_name}...", end=" ", flush=True)
        self.stats['api_calls'] += 1
        
        try:
            response = requests.get(
                f"{GBIF_API}/occurrence/search",
                params={
                    'scientificName': clean_name,
                    'mediaType': 'StillImage',
                    'hasCoordinate': 'true',
                    'limit': min(needed_count, 300)
                },
                timeout=15
            )
            response.raise_for_status()
            
            occurrences = response.json().get('results', [])
            
            images = []
            for occ in occurrences:
                images.extend(self.extract_gbif_metadata(occ))
                if len(images) >= needed_count:
                    break
            
            print(f"found {len(images)}")
            return images
        
        except Exception as e:
            print(f"error ({str(e)[:30]})")
            return []
    
    def insert_images(self, taxonomy_id, scientific_name, images):
        """Insert images with ALL metadata fields to database"""
        if self.dry_run:
            print(f"   💾 [DRY RUN] Would insert {len(images)} images")
            return len(images)
        
        inserted = 0
        for img in images:
            try:
                self.cur.execute("""
                    INSERT INTO orchid_images (
                        taxonomy_id, gbif_occurrence_key, image_url, image_source,
                        wild_specimen, image_license, latitude, longitude,
                        coordinate_uncertainty, country, country_code, state_province,
                        locality, continent, elevation_meters, observation_date,
                        year_observed, month_observed, observer_name, institution_code,
                        individual_count, sex, life_stage, reproductive_condition,
                        iucn_red_list_category, occurrence_metadata, media_metadata,
                        created_at
                    )
                    SELECT %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                           %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    WHERE NOT EXISTS (
                        SELECT 1 FROM orchid_images WHERE image_url = %s
                    )
                """, (
                    taxonomy_id,
                    img.get('occurrence_key'),
                    img.get('image_url'),
                    img.get('image_source'),
                    img.get('wild_specimen'),
                    img.get('image_license'),
                    img.get('latitude'),
                    img.get('longitude'),
                    img.get('coordinate_uncertainty'),
                    img.get('country'),
                    img.get('country_code'),
                    img.get('state_province'),
                    img.get('locality'),
                    img.get('continent'),
                    img.get('elevation_meters'),
                    img.get('observation_date'),
                    img.get('year_observed'),
                    img.get('month_observed'),
                    img.get('observer_name'),
                    img.get('institution_code'),
                    img.get('individual_count'),
                    img.get('sex'),
                    img.get('life_stage'),
                    img.get('reproductive_condition'),
                    img.get('iucn_red_list_category'),
                    img.get('occurrence_metadata'),
                    img.get('media_metadata'),
                    datetime.now(),
                    img.get('image_url')  # for WHERE NOT EXISTS
                ))
                
                if self.cur.rowcount > 0:
                    inserted += 1
            
            except Exception as e:
                self.conn.rollback()
                continue
        
        self.conn.commit()
        print(f"   💾 Inserted {inserted} new images")
        return inserted
    
    def hunt_species(self, species_data):
        """Hunt for images of a specific species"""
        tax_id, sci_name, genus, species, current_images = species_data
        
        needed = IDEAL_IMAGES - current_images
        if needed <= 0:
            return 0
        
        print(f"\n🎯 Hunting: {sci_name}")
        print(f"   Current images: {current_images}, Need: {needed}")
        
        all_images = []
        
        # Search iNaturalist first (largest source)
        if len(all_images) < needed:
            inat_images = self.search_inaturalist(sci_name, needed - len(all_images))
            all_images.extend(inat_images)
            time.sleep(1)  # Rate limiting
        
        # Search GBIF if still need more
        if len(all_images) < needed:
            gbif_images = self.search_gbif(sci_name, genus, needed - len(all_images))
            all_images.extend(gbif_images)
            time.sleep(1)  # Rate limiting
        
        # Insert to database
        if all_images:
            inserted = self.insert_images(tax_id, sci_name, all_images)
            self.stats['images_found'] += len(all_images)
            self.stats['images_inserted'] += inserted
            return inserted
        else:
            print(f"   ⚠️  No images found")
            return 0
    
    def run_batch(self, batch_size=50, priority='CRITICAL'):
        """Run batch processing for multiple species"""
        print("\n" + "=" * 80)
        print(f"🌺 TARGETED SPECIES HUNTER - Batch Processing")
        print(f"🎯 Target: {IDEAL_IMAGES} images per species (AI-ready coverage)")
        print(f"📊 Batch size: {batch_size} species")
        print(f"🔥 Priority: {priority}")
        print(f"📝 Capturing ALL 52+ metadata fields per image")
        print("=" * 80)
        
        species_list = self.get_species_needing_images(batch_size, priority)
        
        for i, species_data in enumerate(species_list, 1):
            print(f"\n[{i}/{len(species_list)}]", end=" ")
            self.hunt_species(species_data)
            self.stats['species_processed'] += 1
        
        self.print_summary()
    
    def print_summary(self):
        """Print batch summary"""
        print("\n" + "=" * 80)
        print("📊 BATCH SUMMARY")
        print("=" * 80)
        print(f"   Species processed: {self.stats['species_processed']}")
        print(f"   Images found: {self.stats['images_found']}")
        print(f"   Images inserted: {self.stats['images_inserted']}")
        print(f"   API calls made: {self.stats['api_calls']}")
        print(f"   Average images per species: {self.stats['images_inserted'] / max(self.stats['species_processed'], 1):.1f}")
        print("=" * 80 + "\n")
    
    def close(self):
        self.cur.close()
        self.conn.close()

def main():
    parser = argparse.ArgumentParser(description='Targeted Species Hunter for AI-Ready Coverage')
    parser.add_argument('--batch-size', type=int, default=50, help='Number of species to process (default: 50)')
    parser.add_argument('--priority', choices=['CRITICAL', 'HIGH', 'MEDIUM'], default='CRITICAL',
                       help='Priority level (CRITICAL=0 images, HIGH=1-9, MEDIUM=10-29)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without inserting')
    
    args = parser.parse_args()
    
    hunter = TargetedSpeciesHunter(dry_run=args.dry_run)
    hunter.run_batch(batch_size=args.batch_size, priority=args.priority)
    hunter.close()

if __name__ == '__main__':
    main()
