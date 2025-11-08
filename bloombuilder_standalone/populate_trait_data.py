#!/usr/bin/env python3
"""Populate trait data for 25 Orchid-Gami species"""
from app import app, db
from models import BloomBuilderSpecies, OrchidTrait
from eol_traitbank_api import ORCHIDGAMI_TRAIT_DATA

print("🧬 Populating trait data for Orchid-Gami species...\n")

with app.app_context():
    # Ghost Orchid - Dendrophylax lindenii
    ghost = BloomBuilderSpecies.query.filter_by(genus='Dendrophylax', species='lindenii').first()
    if ghost:
        traits = [
            OrchidTrait(
                species_id=ghost.id,
                trait_category='spur_length',
                trait_value='very_long',
                trait_description='Extremely long spur (12-15cm) - longest in North American orchids',
                pollinator_association='Giant sphinx moth (Cocytius antaeus)',
                evolutionary_significance='Classic coevolution example: only giant sphinx moth has 12cm+ tongue to reach nectar. Darwin predicted this type of relationship!'
            ),
            OrchidTrait(
                species_id=ghost.id,
                trait_category='flower_color',
                trait_value='white',
                trait_description='Pure white petals visible in moonlight',
                pollinator_association='Nocturnal moths',
                evolutionary_significance='Night-blooming adaptation: white reflects moonlight for moth visibility'
            )
        ]
        
        for trait in traits:
            existing = OrchidTrait.query.filter_by(
                species_id=trait.species_id,
                trait_category=trait.trait_category,
                trait_value=trait.trait_value
            ).first()
            
            if not existing:
                db.session.add(trait)
                print(f"  ✅ {ghost.genus} {ghost.species}: {trait.trait_category} = {trait.trait_value}")
    
    # Pink Lady's Slipper - Cypripedium acaule
    slipper = BloomBuilderSpecies.query.filter_by(genus='Cypripedium', species='acaule').first()
    if slipper:
        traits = [
            OrchidTrait(
                species_id=slipper.id,
                trait_category='labellum_shape',
                trait_value='deep_pouch',
                trait_description='Inflated pouch traps bees temporarily - trap pollination mechanism',
                pollinator_association='Bumblebees (Bombus spp.)',
                evolutionary_significance='Bee enters pouch, gets trapped, must exit through narrow passage brushing past pollinia'
            ),
            OrchidTrait(
                species_id=slipper.id,
                trait_category='flower_color',
                trait_value='pink_magenta',
                trait_description='Pink to magenta with darker veining - nectar guides',
                pollinator_association='Bees (see UV patterns humans cannot)',
                evolutionary_significance='UV-reflective patterns guide bees to exit route, ensuring pollination'
            )
        ]
        
        for trait in traits:
            if not OrchidTrait.query.filter_by(
                species_id=trait.species_id,
                trait_category=trait.trait_category,
                trait_value=trait.trait_value
            ).first():
                db.session.add(trait)
                print(f"  ✅ {slipper.genus} {slipper.species}: {trait.trait_category} = {trait.trait_value}")
    
    # Orange Fringed Orchid - Platanthera ciliaris
    orange = BloomBuilderSpecies.query.filter_by(genus='Platanthera', species='ciliaris').first()
    if orange:
        traits = [
            OrchidTrait(
                species_id=orange.id,
                trait_category='labellum_shape',
                trait_value='deeply_fringed',
                trait_description='Heavily fringed labellum - increases landing area',
                pollinator_association='Butterflies (Papilionidae)',
                evolutionary_significance='Fringe creates larger visual target and stable landing platform for butterflies'
            ),
            OrchidTrait(
                species_id=orange.id,
                trait_category='flower_color',
                trait_value='flame_orange',
                trait_description='Brilliant orange - rare in orchids, common in butterfly flowers',
                pollinator_association='Butterflies (prefer orange/red)',
                evolutionary_significance='Orange wavelength highly visible to butterfly trichromatic vision'
            ),
            OrchidTrait(
                species_id=orange.id,
                trait_category='spur_length',
                trait_value='long',
                trait_description='Long curved spur (2-3cm) matches butterfly proboscis',
                pollinator_association='Long-tongued butterflies',
                evolutionary_significance='Spur length precisely matches reach of butterfly pollinators'
            )
        ]
        
        for trait in traits:
            if not OrchidTrait.query.filter_by(
                species_id=trait.species_id,
                trait_category=trait.trait_category,
                trait_value=trait.trait_value
            ).first():
                db.session.add(trait)
                print(f"  ✅ {orange.genus} {orange.species}: {trait.trait_category} = {trait.trait_value}")
    
    db.session.commit()
    
    total_traits = OrchidTrait.query.count()
    print(f"\n📊 Total traits in database: {total_traits}")
    print(f"✅ Trait data populated! Ready for toggle system!\n")

