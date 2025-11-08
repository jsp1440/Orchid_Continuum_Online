#!/usr/bin/env python3
"""
GBIF Image URL Extractor
Extracts image URLs from GBIF for all orchid species we have GBIF keys for
NO DOWNLOADING - just stores URLs in database
"""
import os
import requests
import time
from datetime import datetime
from app import app, db
from models import OrchidTaxonomy, OrchidImages

print("🌍 GBIF IMAGE URL EXTRACTOR")
print("=" * 80)

# GBIF API configuration
GBIF_API = "https://api.gbif.org/v1"
BATCH_SIZE = 50  # Process in batches
MAX_IMAGES_PER_SPECIES = 100  # Limit per species to avoid overwhelming database

def get_gbif_occurrences_with_media(taxon_key, limit=100):
    """
    Get GBIF occurrence records that have media (images) for a taxon
    Returns list of {occurrence_id, media_urls[], scientific_name, location, etc}
    """
    url = f"{GBIF_API}/occurrence/search"
    params = {
        'taxonKey': taxon_key,
        'mediaType': 'StillImage',  # Only records with images
        'limit': limit
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for record in data.get('results', []):
            # Extract media URLs
            media_urls = []
            for media in record.get('media', []):
                if media.get('type') == 'StillImage':
                    media_urls.append(media.get('identifier'))
            
            if media_urls:
                results.append({
                    'gbif_occurrence_id': record.get('key'),
                    'media_urls': media_urls,
                    'scientific_name': record.get('scientificName'),
                    'latitude': record.get('decimalLatitude'),
                    'longitude': record.get('decimalLongitude'),
                    'country': record.get('country'),
                    'year': record.get('year'),
                    'basis_of_record': record.get('basisOfRecord'),
                    'institution': record.get('institutionCode'),
                    'license': record.get('license', 'CC-BY-4.0')
                })
        
        return results
        
    except Exception as e:
        print(f"   ⚠️  Error fetching GBIF data for taxon {taxon_key}: {e}")
        return []


def main():
    with app.app_context():
        # Get all species with GBIF taxon keys
        species_with_gbif = OrchidTaxonomy.query.filter(
            OrchidTaxonomy.gbif_taxon_key.isnot(None)
        ).all()
        
        print(f"\n📊 Found {len(species_with_gbif):,} species with GBIF taxon keys")
        print(f"⏱️  Processing in batches of {BATCH_SIZE}...")
        print()
        
        total_images_added = 0
        total_urls_extracted = 0
        species_processed = 0
        species_with_images = 0
        
        for i, species in enumerate(species_with_gbif, 1):
            try:
                # Get occurrences with media
                occurrences = get_gbif_occurrences_with_media(
                    species.gbif_taxon_key, 
                    limit=MAX_IMAGES_PER_SPECIES
                )
                
                if occurrences:
                    species_with_images += 1
                    
                    # Add each image URL to database
                    for occ in occurrences:
                        for media_url in occ['media_urls']:
                            # Check if URL already exists
                            existing = OrchidImages.query.filter_by(
                                image_url=media_url
                            ).first()
                            
                            if not existing:
                                # Create new image record
                                new_image = OrchidImages(
                                    taxonomy_id=species.id,
                                    image_url=media_url,
                                    image_type='living_photo',
                                    source='gbif',
                                    photographer=occ.get('institution', 'GBIF Contributor'),
                                    license=occ.get('license', 'CC-BY-4.0'),
                                    latitude=occ.get('latitude'),
                                    longitude=occ.get('longitude'),
                                    country=occ.get('country'),
                                    collection_year=occ.get('year'),
                                    gbif_occurrence_id=str(occ.get('gbif_occurrence_id')),
                                    basis_of_record=occ.get('basis_of_record')
                                )
                                db.session.add(new_image)
                                total_images_added += 1
                            
                            total_urls_extracted += 1
                    
                    # Commit every batch
                    if i % BATCH_SIZE == 0:
                        db.session.commit()
                        print(f"   ✅ Batch {i}/{len(species_with_gbif)}: "
                              f"+{total_images_added:,} new images | "
                              f"{total_urls_extracted:,} URLs extracted | "
                              f"{species_with_images} species with images")
                
                species_processed += 1
                
                # Rate limiting - GBIF is generous but let's be polite
                time.sleep(0.1)
                
            except Exception as e:
                print(f"   ⚠️  Error processing {species.scientific_name}: {e}")
                db.session.rollback()
                continue
        
        # Final commit
        db.session.commit()
        
        # Final report
        print()
        print("=" * 80)
        print("✅ GBIF URL EXTRACTION COMPLETE!")
        print()
        print(f"📊 Statistics:")
        print(f"   Species processed: {species_processed:,}")
        print(f"   Species with images: {species_with_images:,}")
        print(f"   Total URLs extracted: {total_urls_extracted:,}")
        print(f"   New image records added: {total_images_added:,}")
        print()
        
        # Database totals
        total_images = OrchidImages.query.count()
        total_species = OrchidTaxonomy.query.count()
        coverage_pct = (species_with_images / 33494) * 100  # ~33,494 total orchid species
        
        print(f"🌺 Updated Database Totals:")
        print(f"   Total images in database: {total_images:,}")
        print(f"   Total species in taxonomy: {total_species:,}")
        print(f"   Coverage: {coverage_pct:.2f}% of all known orchid species")
        print()


if __name__ == '__main__':
    main()
