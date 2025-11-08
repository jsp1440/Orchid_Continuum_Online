"""Import BloomBuilder species data from CSV"""
import csv
from app import app, db
from models import BloomBuilderSpecies

def import_species():
    """Import species from BloomBuilder_Species_Index.csv"""
    csv_path = 'attached_assets/bloombuilder/BloomBuilder_Species_Index.csv'
    
    with app.app_context():
        print("Importing BloomBuilder species data...")
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            count = 0
            
            for row in reader:
                # Check if species already exists
                existing = BloomBuilderSpecies.query.filter_by(species=row['species']).first()
                if existing:
                    print(f"  Skipping {row['species']} (already exists)")
                    continue
                
                # Create new species
                species = BloomBuilderSpecies(
                    species=row['species'],
                    genus=row['genus'],
                    family=row['family'],
                    herbarium_url=row['herbarium_url'] or None,
                    photo_url=row['photo_url'] or None,
                    diagram_url=row['diagram_url'] or None,
                    source_reference=row['source_reference'] or None,
                    profile_type=row['profile_type'],
                    habitat=row['habitat'] or None,
                    distribution=row['distribution'] or None,
                    pollinators=row['pollinators'] or None,
                    ecological_notes=row['ecological_notes'] or None,
                    conservation_status=row['conservation_status'] or None,
                    evolutionary_notes=row['evolutionary_notes'] or None,
                    external_links=row['external_links'] or None,
                    notes=row['notes'] or None
                )
                db.session.add(species)
                count += 1
                print(f"  Added: {row['species']}")
            
            db.session.commit()
            print(f"\n✅ Imported {count} species successfully!")

if __name__ == '__main__':
    import_species()
