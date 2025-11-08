#!/usr/bin/env python3
"""
Import Full 34,000+ Orchid Taxonomy Database
Restores the complete species list for image collection
"""

import csv
import logging
from app import app, db
from models import OrchidTaxonomy
from datetime import datetime
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_genus_species(name: str, taxon_type: str):
    """Extract genus and species from scientific name"""
    if not name:
        return None, None
    
    # Split name into parts
    parts = name.split()
    
    if taxon_type in ['G', 'SG']:  # Genus or Subgenus
        return parts[0] if parts else None, None
    elif taxon_type == 'S':  # Species
        genus = parts[0] if len(parts) > 0 else None
        species = parts[1] if len(parts) > 1 else None
        return genus, species
    else:
        # For families, subfamilies, etc. just return first part
        return parts[0] if parts else None, None

def import_taxonomy_database(csv_path: str = '/tmp/full_taxonomy.csv'):
    """Import the full taxonomy database"""
    try:
        with app.app_context():
            logger.info("🌺 Starting taxonomy import...")
            
            # Read CSV
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                imported = 0
                skipped = 0
                errors = 0
                
                for row in reader:
                    try:
                        taxon_type = row.get('Taxon', '').strip()
                        name = row.get('Name', '').strip()
                        
                        # Skip non-species entries or empty names
                        if not name or taxon_type not in ['S', 'G', 'SG']:
                            skipped += 1
                            continue
                        
                        # Parse genus and species
                        genus, species = parse_genus_species(name, taxon_type)
                        
                        if not genus:
                            skipped += 1
                            continue
                        
                        # Check if already exists
                        existing = OrchidTaxonomy.query.filter_by(
                            scientific_name=name
                        ).first()
                        
                        if existing:
                            skipped += 1
                            continue
                        
                        # Create new taxonomy record
                        taxonomy = OrchidTaxonomy(
                            scientific_name=name,
                            genus=genus,
                            species=species or '',
                            author=row.get('Author', '').strip(),
                            synonyms=row.get('Synonyms', '').strip(),
                            common_names=row.get('TrivialName', '').strip(),
                            created_at=datetime.now(),
                            updated_at=datetime.now()
                        )
                        
                        db.session.add(taxonomy)
                        imported += 1
                        
                        # Commit in batches
                        if imported % 1000 == 0:
                            db.session.commit()
                            logger.info(f"✅ Imported {imported} records...")
                        
                    except Exception as e:
                        logger.error(f"Error importing row {row.get('Name')}: {e}")
                        errors += 1
                        continue
                
                # Final commit
                db.session.commit()
                
                logger.info(f"""
🎉 TAXONOMY IMPORT COMPLETE!
   ✅ Imported: {imported:,} new records
   ⏭️  Skipped: {skipped:,} (duplicates or non-species)
   ❌ Errors: {errors}
   📊 Total in database: {OrchidTaxonomy.query.count():,}
                """)
                
                return {
                    'imported': imported,
                    'skipped': skipped,
                    'errors': errors,
                    'total': OrchidTaxonomy.query.count()
                }
                
    except Exception as e:
        logger.error(f"Fatal error importing taxonomy: {e}")
        db.session.rollback()
        return {'error': str(e)}

if __name__ == '__main__':
    result = import_taxonomy_database()
    print(f"\n✅ Import complete: {result}")
