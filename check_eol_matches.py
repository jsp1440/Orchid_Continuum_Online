"""
Check how many of the 13,429 EOL page IDs can be matched to existing taxonomy
"""
from app import app, db
from models import OrchidTaxonomy

with app.app_context():
    # Read the EOL page IDs
    with open('orchid_eol_page_ids.txt', 'r') as f:
        eol_page_ids = [line.strip() for line in f if line.strip()]
    
    print(f"Total EOL page IDs to match: {len(eol_page_ids)}")
    
    # Check how many already exist in taxonomy
    existing = OrchidTaxonomy.query.filter(
        OrchidTaxonomy.eol_page_id.in_(eol_page_ids)
    ).count()
    
    print(f"Already in taxonomy table: {existing}")
    print(f"Missing from taxonomy: {len(eol_page_ids) - existing}")
    
    # Sample a few that are missing
    existing_ids = [row.eol_page_id for row in OrchidTaxonomy.query.filter(
        OrchidTaxonomy.eol_page_id.in_(eol_page_ids)
    ).limit(10).all()]
    
    print(f"\nSample existing EOL IDs in taxonomy: {existing_ids[:5]}")
    
    missing_ids = [pid for pid in eol_page_ids[:20] if pid not in existing_ids]
    print(f"Sample missing EOL IDs: {missing_ids[:5]}")
