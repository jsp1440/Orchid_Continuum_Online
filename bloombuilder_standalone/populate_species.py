#!/usr/bin/env python3
"""Populate BloomBuilder with all 25 NAOCC Orchid-Gami species"""
from app import app, db
from models import BloomBuilderSpecies

ORCHIDGAMI_SPECIES = [
    {'genus': 'Dendrophylax', 'species': 'lindenii', 'common_name': 'Ghost Orchid', 'profile_type': 'spurred_orchid', 'habitat': 'Epiphytic in swamps', 'distribution': 'Florida, Cuba', 'pollinators': 'Giant sphinx moth', 'conservation_status': 'Endangered'},
    {'genus': 'Cypripedium', 'species': 'acaule', 'common_name': 'Pink Lady\'s Slipper', 'profile_type': 'pouch_orchid', 'habitat': 'Acidic forest floors', 'distribution': 'Eastern North America', 'pollinators': 'Bumblebees', 'conservation_status': 'Threatened'},
    {'genus': 'Calypso', 'species': 'bulbosa', 'common_name': 'Fairy Slipper', 'profile_type': 'pouch_orchid', 'habitat': 'Coniferous forests', 'distribution': 'Northern hemisphere', 'pollinators': 'Bumblebees', 'conservation_status': 'Vulnerable'},
    {'genus': 'Platanthera', 'species': 'ciliaris', 'common_name': 'Orange Fringed Orchid', 'profile_type': 'spurred_orchid', 'habitat': 'Wet meadows, bogs', 'distribution': 'Eastern US', 'pollinators': 'Butterflies', 'conservation_status': 'Threatened'},
    {'genus': 'Spiranthes', 'species': 'cernua', 'common_name': 'Nodding Ladies\' Tresses', 'profile_type': 'default_orchid', 'habitat': 'Moist meadows', 'distribution': 'North America', 'pollinators': 'Bumblebees', 'conservation_status': 'Secure'},
    {'genus': 'Cypripedium', 'species': 'arietinum', 'common_name': 'Ram\'s Head Lady\'s Slipper', 'profile_type': 'pouch_orchid', 'habitat': 'Cedar swamps', 'distribution': 'Northeastern US', 'pollinators': 'Small bees', 'conservation_status': 'Endangered'},
    {'genus': 'Goodyera', 'species': 'pubescens', 'common_name': 'Downy Rattlesnake Plantain', 'profile_type': 'default_orchid', 'habitat': 'Dry forests', 'distribution': 'Eastern North America', 'pollinators': 'Bumblebees', 'conservation_status': 'Secure'},
    {'genus': 'Encyclia', 'species': 'tampensis', 'common_name': 'Butterfly Orchid', 'profile_type': 'default_orchid', 'habitat': 'Epiphytic in hammocks', 'distribution': 'Florida', 'pollinators': 'Butterflies', 'conservation_status': 'Threatened'},
    {'genus': 'Habenaria', 'species': 'repens', 'common_name': 'Water Spider Orchid', 'profile_type': 'spurred_orchid', 'habitat': 'Wet prairies', 'distribution': 'Southeastern US', 'pollinators': 'Moths', 'conservation_status': 'Secure'},
    {'genus': 'Platanthera', 'species': 'leucophaea', 'common_name': 'Prairie White Fringed Orchid', 'profile_type': 'spurred_orchid', 'habitat': 'Tallgrass prairies', 'distribution': 'Central US', 'pollinators': 'Sphinx moths', 'conservation_status': 'Threatened'},
    {'genus': 'Arethusa', 'species': 'bulbosa', 'common_name': 'Dragon\'s Mouth', 'profile_type': 'default_orchid', 'habitat': 'Sphagnum bogs', 'distribution': 'Northern US/Canada', 'pollinators': 'Bumblebees', 'conservation_status': 'Vulnerable'},
    {'genus': 'Cypripedium', 'species': 'reginae', 'common_name': 'Showy Lady\'s Slipper', 'profile_type': 'pouch_orchid', 'habitat': 'Swamps, fens', 'distribution': 'Northern US/Canada', 'pollinators': 'Bees', 'conservation_status': 'Threatened'},
    {'genus': 'Calopogon', 'species': 'tuberosus', 'common_name': 'Grass Pink', 'profile_type': 'default_orchid', 'habitat': 'Wet meadows, bogs', 'distribution': 'Eastern North America', 'pollinators': 'Bees', 'conservation_status': 'Secure'},
    {'genus': 'Platanthera', 'species': 'blephariglottis', 'common_name': 'White Fringed Orchid', 'profile_type': 'spurred_orchid', 'habitat': 'Wet meadows', 'distribution': 'Eastern US', 'pollinators': 'Moths', 'conservation_status': 'Secure'},
    {'genus': 'Cypripedium', 'species': 'parviflorum', 'common_name': 'Yellow Lady\'s Slipper', 'profile_type': 'pouch_orchid', 'habitat': 'Forests, fens', 'distribution': 'North America', 'pollinators': 'Bees', 'conservation_status': 'Secure'},
    {'genus': 'Platanthera', 'species': 'psycodes', 'common_name': 'Small Purple Fringed Orchid', 'profile_type': 'spurred_orchid', 'habitat': 'Wet meadows', 'distribution': 'Eastern North America', 'pollinators': 'Moths, butterflies', 'conservation_status': 'Secure'},
    {'genus': 'Pogonia', 'species': 'ophioglossoides', 'common_name': 'Rose Pogonia', 'profile_type': 'default_orchid', 'habitat': 'Bogs, fens', 'distribution': 'Eastern North America', 'pollinators': 'Bees', 'conservation_status': 'Secure'},
    {'genus': 'Platanthera', 'species': 'grandiflora', 'common_name': 'Large Purple Fringed Orchid', 'profile_type': 'spurred_orchid', 'habitat': 'Mountain meadows', 'distribution': 'Appalachian mountains', 'pollinators': 'Moths', 'conservation_status': 'Vulnerable'},
    {'genus': 'Tipularia', 'species': 'discolor', 'common_name': 'Crane-fly Orchid', 'profile_type': 'default_orchid', 'habitat': 'Deciduous forests', 'distribution': 'Eastern US', 'pollinators': 'Crane flies', 'conservation_status': 'Secure'},
    {'genus': 'Platanthera', 'species': 'cristata', 'common_name': 'Crested Yellow Orchid', 'profile_type': 'spurred_orchid', 'habitat': 'Wet meadows', 'distribution': 'Southeastern US', 'pollinators': 'Butterflies', 'conservation_status': 'Secure'},
    {'genus': 'Cleistes', 'species': 'divaricata', 'common_name': 'Spreading Pogonia', 'profile_type': 'default_orchid', 'habitat': 'Pine flatwoods', 'distribution': 'Southeastern US', 'pollinators': 'Bees', 'conservation_status': 'Vulnerable'},
    {'genus': 'Isotria', 'species': 'verticillata', 'common_name': 'Large Whorled Pogonia', 'profile_type': 'default_orchid', 'habitat': 'Mesic forests', 'distribution': 'Eastern US', 'pollinators': 'Small bees', 'conservation_status': 'Threatened'},
    {'genus': 'Triphora', 'species': 'trianthophoros', 'common_name': 'Three Birds Orchid', 'profile_type': 'default_orchid', 'habitat': 'Rich forests', 'distribution': 'Eastern US', 'pollinators': 'Bumblebees', 'conservation_status': 'Vulnerable'},
    {'genus': 'Platanthera', 'species': 'clavellata', 'common_name': 'Club-spur Orchid', 'profile_type': 'spurred_orchid', 'habitat': 'Bogs, swamps', 'distribution': 'Eastern North America', 'pollinators': 'Mosquitoes', 'conservation_status': 'Secure'},
    {'genus': 'Liparis', 'species': 'liliifolia', 'common_name': 'Lily-leaved Twayblade', 'profile_type': 'default_orchid', 'habitat': 'Rich forests', 'distribution': 'Eastern North America', 'pollinators': 'Small bees', 'conservation_status': 'Secure'}
]

print("🌸 Populating BloomBuilder with 25 NAOCC Orchid-Gami species...\n")

with app.app_context():
    added = 0
    for species_data in ORCHIDGAMI_SPECIES:
        existing = BloomBuilderSpecies.query.filter_by(
            genus=species_data['genus'],
            species=species_data['species']
        ).first()
        
        if not existing:
            species = BloomBuilderSpecies(**species_data)
            db.session.add(species)
            print(f"  ✅ {species_data['genus']} {species_data['species']} ({species_data['common_name']})")
            added += 1
    
    db.session.commit()
    total = BloomBuilderSpecies.query.count()
    print(f"\n📊 Added {added} species | Total: {total} species")
    print(f"✅ BloomBuilder ready with complete NAOCC collection!")

