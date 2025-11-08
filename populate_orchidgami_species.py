#!/usr/bin/env python3
"""Populate BloomBuilder with NAOCC Orchid-Gami species"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app import app, db
from models import BloomBuilderSpecies

ORCHIDGAMI_SPECIES = [
    {
        'genus': 'Dendrophylax',
        'species': 'lindenii',
        'common_name': 'Ghost Orchid',
        'profile_type': 'spurred_orchid',
        'habitat': 'Epiphytic in swamps',
        'distribution': 'Florida, Cuba',
        'pollinators': 'Giant sphinx moth',
        'conservation_status': 'Endangered'
    },
    {
        'genus': 'Cypripedium',
        'species': 'acaule',
        'common_name': 'Pink Lady\'s Slipper',
        'profile_type': 'pouch_orchid',
        'habitat': 'Acidic forest floors',
        'distribution': 'Eastern North America',
        'pollinators': 'Bumblebees',
        'conservation_status': 'Threatened'
    },
    {
        'genus': 'Calypso',
        'species': 'bulbosa',
        'common_name': 'Fairy Slipper',
        'profile_type': 'pouch_orchid',
        'habitat': 'Coniferous forests',
        'distribution': 'Northern hemisphere',
        'pollinators': 'Bumblebees',
        'conservation_status': 'Vulnerable'
    },
    {
        'genus': 'Platanthera',
        'species': 'ciliaris',
        'common_name': 'Orange Fringed Orchid',
        'profile_type': 'spurred_orchid',
        'habitat': 'Wet meadows, bogs',
        'distribution': 'Eastern US',
        'pollinators': 'Butterflies',
        'conservation_status': 'Threatened'
    },
    {
        'genus': 'Spiranthes',
        'species': 'cernua',
        'common_name': 'Nodding Ladies\' Tresses',
        'profile_type': 'default_orchid',
        'habitat': 'Moist meadows',
        'distribution': 'North America',
        'pollinators': 'Bumblebees',
        'conservation_status': 'Secure'
    },
    {
        'genus': 'Cypripedium',
        'species': 'arietinum',
        'common_name': 'Ram\'s Head Lady\'s Slipper',
        'profile_type': 'pouch_orchid',
        'habitat': 'Cedar swamps',
        'distribution': 'Northeastern US',
        'pollinators': 'Small bees',
        'conservation_status': 'Endangered'
    },
    {
        'genus': 'Goodyera',
        'species': 'pubescens',
        'common_name': 'Downy Rattlesnake Plantain',
        'profile_type': 'default_orchid',
        'habitat': 'Dry forests',
        'distribution': 'Eastern North America',
        'pollinators': 'Bumblebees',
        'conservation_status': 'Secure'
    },
    {
        'genus': 'Encyclia',
        'species': 'tampensis',
        'common_name': 'Butterfly Orchid',
        'profile_type': 'default_orchid',
        'habitat': 'Epiphytic in hammocks',
        'distribution': 'Florida',
        'pollinators': 'Butterflies',
        'conservation_status': 'Threatened'
    },
    {
        'genus': 'Habenaria',
        'species': 'repens',
        'common_name': 'Water Spider Orchid',
        'profile_type': 'spurred_orchid',
        'habitat': 'Wet prairies',
        'distribution': 'Southeastern US',
        'pollinators': 'Moths',
        'conservation_status': 'Secure'
    },
    {
        'genus': 'Platanthera',
        'species': 'leucophaea',
        'common_name': 'Prairie White Fringed Orchid',
        'profile_type': 'spurred_orchid',
        'habitat': 'Tallgrass prairies',
        'distribution': 'Central US',
        'pollinators': 'Sphinx moths',
        'conservation_status': 'Threatened'
    }
]

print("🌸 Populating BloomBuilder with NAOCC Orchid-Gami species...")

with app.app_context():
    for species_data in ORCHIDGAMI_SPECIES:
        existing = BloomBuilderSpecies.query.filter_by(
            genus=species_data['genus'],
            species=species_data['species']
        ).first()
        
        if not existing:
            species = BloomBuilderSpecies(**species_data)
            db.session.add(species)
            print(f"  ✅ Added: {species_data['genus']} {species_data['species']} ({species_data['common_name']})")
        else:
            print(f"  ⏭️  Exists: {species_data['genus']} {species_data['species']}")
    
    db.session.commit()
    
    count = BloomBuilderSpecies.query.count()
    print(f"\n✅ Complete! {count} Orchid-Gami species ready in BloomBuilder")

