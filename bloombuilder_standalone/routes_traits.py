"""Trait Toggle System Routes - Backend for Julius AI Frontend"""
from flask import Blueprint, jsonify, request
from models import db, OrchidTrait, BloomBuilderSpecies, TraitVariation
from eol_traitbank_api import eol_client, ORCHIDGAMI_TRAIT_DATA

traits_bp = Blueprint('traits', __name__, url_prefix='/bloombuilder/api/traits')

@traits_bp.route('/species/<int:species_id>')
def get_species_traits(species_id):
    """
    Get all available traits for a species
    
    Returns trait categories and available values for toggling
    Example: {spur_length: [short, medium, long]}
    """
    species = BloomBuilderSpecies.query.get_or_404(species_id)
    scientific_name = f"{species.genus} {species.species}"
    
    # Get traits from database
    traits = OrchidTrait.query.filter_by(species_id=species_id).all()
    
    # Organize by category
    trait_categories = {}
    for trait in traits:
        if trait.trait_category not in trait_categories:
            trait_categories[trait.trait_category] = []
        
        trait_categories[trait.trait_category].append({
            'value': trait.trait_value,
            'description': trait.trait_description,
            'image_url': trait.image_url,
            'pollinator': trait.pollinator_association,
            'significance': trait.evolutionary_significance
        })
    
    return jsonify({
        'species': scientific_name,
        'trait_categories': trait_categories,
        'available_toggles': list(trait_categories.keys())
    })

@traits_bp.route('/toggle', methods=['POST'])
def toggle_trait():
    """
    Toggle a trait and get updated image/description
    
    POST body: {
        species_id: int,
        trait_category: str,
        trait_value: str
    }
    
    Returns: Updated image URL and description for that trait variant
    """
    data = request.get_json()
    
    trait = OrchidTrait.query.filter_by(
        species_id=data['species_id'],
        trait_category=data['trait_category'],
        trait_value=data['trait_value']
    ).first()
    
    if not trait:
        return jsonify({'error': 'Trait variant not found'}), 404
    
    return jsonify({
        'trait': trait.to_dict(),
        'image_url': trait.image_url,
        'description': trait.trait_description,
        'pollinator_effect': trait.pollinator_association,
        'evolution_note': trait.evolutionary_significance
    })

@traits_bp.route('/compare/<int:species_id>')
def compare_traits(species_id):
    """
    Get trait comparison data for educational display
    
    Shows how different trait values affect pollinator attraction
    """
    # Get all traits for this species
    traits = OrchidTrait.query.filter_by(species_id=species_id).all()
    
    # Get variations for each trait
    comparisons = []
    for trait in traits:
        variations = TraitVariation.query.filter_by(
            base_trait_id=trait.id
        ).all()
        
        for var in variations:
            comparisons.append({
                'trait_category': trait.trait_category,
                'variant_name': var.variant_name,
                'type': var.variant_type,
                'geographic_distribution': var.geographic_distribution,
                'selective_pressure': var.selective_pressure,
                'comparison_data': var.comparison_data
            })
    
    return jsonify({
        'species_id': species_id,
        'trait_variations': comparisons
    })

@traits_bp.route('/pollinator-correlation/<int:species_id>')
def pollinator_correlation(species_id):
    """
    Show how each trait correlates with specific pollinators
    
    Educational visualization data
    """
    traits = OrchidTrait.query.filter_by(species_id=species_id).all()
    
    correlations = {}
    for trait in traits:
        if trait.pollinator_association:
            if trait.pollinator_association not in correlations:
                correlations[trait.pollinator_association] = []
            
            correlations[trait.pollinator_association].append({
                'trait_category': trait.trait_category,
                'trait_value': trait.trait_value,
                'how_it_helps': trait.evolutionary_significance
            })
    
    return jsonify({
        'species_id': species_id,
        'pollinator_correlations': correlations
    })

