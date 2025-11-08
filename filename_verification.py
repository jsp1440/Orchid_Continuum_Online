"""
FILENAME-BASED VERIFICATION
Uses image filenames to verify orchid scientific names
Many filenames contain the actual orchid name - use this for validation
"""

from app import app, db
from models import OrchidRecord
import re
import os
from urllib.parse import urlparse, unquote
import logging

logger = logging.getLogger(__name__)

def extract_name_from_filename(filename_or_url):
    """Extract scientific name from filename"""
    if not filename_or_url:
        return None
    
    # If it's a URL, extract the filename
    if filename_or_url.startswith('http'):
        parsed = urlparse(filename_or_url)
        filename = os.path.basename(parsed.path)
        filename = unquote(filename)
    else:
        filename = filename_or_url
    
    # Remove file extension
    name = os.path.splitext(filename)[0]
    
    # Remove common prefixes/suffixes
    name = re.sub(r'(IMG_|DSC_|DSCN_|P\d+_|\d{8}_|\d{6}_)', '', name, flags=re.IGNORECASE)
    
    # Replace underscores and hyphens with spaces
    name = name.replace('_', ' ').replace('-', ' ')
    
    # Remove extra whitespace
    name = ' '.join(name.split())
    
    # Try to extract genus + species pattern
    # Look for capitalized word followed by lowercase word(s)
    match = re.search(r'\b([A-Z][a-z]+)\s+([a-z]+(?:\s+[a-z]+)?)\b', name)
    if match:
        genus = match.group(1)
        species = match.group(2)
        return f"{genus} {species}".strip()
    
    return None

def verify_orchid_by_filename(orchid):
    """Verify if orchid name matches filename"""
    filename = None
    
    # Try to get filename from various sources
    if orchid.image_url:
        filename = orchid.image_url
    elif orchid.google_drive_id:
        # Can't extract name from Drive ID
        return {'verified': None, 'filename_name': None, 'current_name': orchid.scientific_name}
    
    if not filename:
        return {'verified': None, 'filename_name': None, 'current_name': orchid.scientific_name}
    
    filename_name = extract_name_from_filename(filename)
    
    if not filename_name:
        return {'verified': None, 'filename_name': None, 'current_name': orchid.scientific_name}
    
    # Check if names match (case-insensitive)
    current_name = orchid.scientific_name or ''
    verified = filename_name.lower() == current_name.lower()
    
    return {
        'verified': verified,
        'filename_name': filename_name,
        'current_name': current_name,
        'confidence': 'high' if verified else 'mismatch'
    }

def run_filename_verification():
    """Run filename verification on all orchids"""
    with app.app_context():
        orchids = OrchidRecord.query.filter(
            db.or_(OrchidRecord.image_url.isnot(None), OrchidRecord.google_drive_id.isnot(None))
        ).all()
        
        results = {
            'verified': [],
            'mismatches': [],
            'no_filename_name': [],
            'total': len(orchids)
        }
        
        for orchid in orchids:
            result = verify_orchid_by_filename(orchid)
            
            if result['verified'] is True:
                results['verified'].append({
                    'id': orchid.id,
                    'name': orchid.scientific_name,
                    'filename_name': result['filename_name']
                })
            elif result['verified'] is False:
                results['mismatches'].append({
                    'id': orchid.id,
                    'current_name': result['current_name'],
                    'filename_name': result['filename_name'],
                    'filename': orchid.image_url or f"Drive:{orchid.google_drive_id}"
                })
            else:
                results['no_filename_name'].append(orchid.id)
        
        print(f"\n📊 FILENAME VERIFICATION RESULTS:")
        print(f"Total orchids checked: {results['total']}")
        print(f"✅ Verified by filename: {len(results['verified'])}")
        print(f"⚠️ Mismatches found: {len(results['mismatches'])}")
        print(f"❓ No name in filename: {len(results['no_filename_name'])}")
        
        if results['mismatches']:
            print(f"\n🚨 MISMATCHES (showing first 20):")
            for i, mismatch in enumerate(results['mismatches'][:20]):
                print(f"{i+1}. ID {mismatch['id']}:")
                print(f"   Current: {mismatch['current_name']}")
                print(f"   Filename: {mismatch['filename_name']}")
                print(f"   File: {mismatch['filename'][:80]}...")
        
        return results

if __name__ == '__main__':
    results = run_filename_verification()
    
    # Export mismatches to CSV
    if results['mismatches']:
        import csv
        with open('filename_mismatches.csv', 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['id', 'current_name', 'filename_name', 'filename'])
            writer.writeheader()
            writer.writerows(results['mismatches'])
        print(f"\n📄 Exported mismatches to: filename_mismatches.csv")
