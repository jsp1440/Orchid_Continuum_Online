#!/usr/bin/env python3
"""Import botanical illustration plates into database"""
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app import app, db
from models import OrchidImage

PLATES_DIR = Path("attached_assets/botanical_illustrations")

print("🎨 Importing Lindenia botanical plates to database...")

with app.app_context():
    plates = list(PLATES_DIR.glob("Lindenia*.jpg"))
    
    for plate in plates:
        # Extract plate number from filename
        plate_num = int(plate.stem.split('_')[-1])
        
        # Check if already exists
        existing = OrchidImage.query.filter_by(
            image_source='Botanical Illustration',
            local_path=str(plate)
        ).first()
        
        if not existing:
            img = OrchidImage(
                image_url=f"/static/botanical_illustrations/{plate.name}",
                image_source='Botanical Illustration',
                local_path=str(plate),
                image_license='Public Domain',
                download_status='downloaded'
            )
            db.session.add(img)
            print(f"  ✅ Added: {plate.name}")
    
    db.session.commit()
    print(f"\n✅ Complete! {len(plates)} botanical plates imported")

