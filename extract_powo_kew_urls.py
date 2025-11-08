#!/usr/bin/env python3
"""
POWO/Kew Royal Botanic Gardens Image URL Extractor
Uses pykew library to get orchid taxonomy and image URLs
"""
import time
from pykew import powo
from pykew.powo_terms import Filters
from app import app, db
from models import OrchidTaxonomy, OrchidImages

print("🌸 POWO/KEW IMAGE URL EXTRACTOR")
print("=" * 80)

def search_orchid_genus(genus_name, limit=500):
    """Search POWO for a genus and get all species with images"""
    print(f"\n🔍 Searching for {genus_name}...")
    
    try:
        # Search for accepted species in this genus
        results = powo.search(
            genus_name,
            filters=[Filters.accepted, Filters.species]
        )
        
        species_count = 0
        images_added = 0
        
        for result in results:
            if species_count >= limit:
                break
            
            # Get full record with images
            fqid = result.get('fqId')
            if not fqid:
                continue
            
            try:
                # Lookup full record
                full_record = powo.lookup(fqid, include=['images'])
                
                scientific_name = full_record.get('name')
                images = full_record.get('images', [])
                
                if images and scientific_name:
                    # Try to match to our taxonomy
                    species_match = OrchidTaxonomy.query.filter_by(
                        scientific_name=scientific_name
                    ).first()
                    
                    if not species_match:
                        # Create new taxonomy entry
                        genus = full_record.get('genus')
                        species = scientific_name.replace(genus, '').strip()
                        
                        species_match = OrchidTaxonomy(
                            scientific_name=scientific_name,
                            genus=genus,
                            species=species,
                            family='Orchidaceae'
                        )
                        db.session.add(species_match)
                        db.session.flush()
                    
                    # Add images
                    for img in images:
                        image_url = img.get('contentUrl')
                        if image_url:
                            # Check if exists
                            existing = OrchidImages.query.filter_by(
                                image_url=image_url
                            ).first()
                            
                            if not existing:
                                new_image = OrchidImages(
                                    taxonomy_id=species_match.id,
                                    image_url=image_url,
                                    image_type='herbarium_sheet',
                                    source='powo_kew',
                                    photographer='Royal Botanic Gardens, Kew',
                                    license='CC-BY'
                                )
                                db.session.add(new_image)
                                images_added += 1
                
                species_count += 1
                
                # Commit every 50 records
                if species_count % 50 == 0:
                    db.session.commit()
                    print(f"   Progress: {species_count} species, {images_added} images", end='\r')
                
                # Rate limiting
                time.sleep(0.2)
                
            except Exception as e:
                print(f"   ⚠️  Error fetching {fqid}: {e}")
                continue
        
        db.session.commit()
        print(f"\n   ✅ {genus_name}: {species_count} species, {images_added} new images")
        return images_added
        
    except Exception as e:
        print(f"   ❌ Error searching {genus_name}: {e}")
        return 0


def main():
    """Extract images for major orchid genera"""
    # Top orchid genera by species count
    MAJOR_GENERA = [
        'Bulbophyllum',  # ~2,000 species
        'Epidendrum',    # ~1,500 species
        'Dendrobium',    # ~1,200 species
        'Pleurothallis', # ~1,100 species
        'Stelis',        # ~950 species
        'Lepanthes',     # ~800 species
        'Habenaria',     # ~800 species
        'Maxillaria',    # ~650 species
        'Masdevallia',   # ~600 species
        'Oncidium',      # ~600 species
        'Cattleya',      # ~500 species
        'Phalaenopsis',  # ~70 species
        'Vanda',         # ~80 species
        'Paphiopedilum', # ~100 species
        'Cypripedium'    # ~50 species
    ]
    
    with app.app_context():
        total_images = 0
        
        for genus in MAJOR_GENERA:
            images_added = search_orchid_genus(genus, limit=500)
            total_images += images_added
            time.sleep(1)  # Be nice to Kew's API
        
        print("\n" + "=" * 80)
        print("✅ POWO/KEW URL EXTRACTION COMPLETE!")
        print(f"   Total images added: {total_images:,}")


if __name__ == '__main__':
    main()
