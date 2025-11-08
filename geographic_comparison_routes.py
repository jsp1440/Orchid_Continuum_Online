"""
Routes for Geographic Trait Comparison System
Provides API endpoints and web interface for comparing orchid traits across locations
"""

import logging
from flask import Blueprint, render_template, jsonify, request
from geographic_trait_comparison import geographic_comparison

logger = logging.getLogger(__name__)

# Create blueprint
geographic_bp = Blueprint('geographic_comparison', __name__)

@geographic_bp.route('/compare/geographic/<scientific_name>')
def geographic_comparison_view(scientific_name):
    """
    Web interface for geographic trait comparison
    """
    try:
        logger.info(f"🌍 Viewing geographic comparison for {scientific_name}")
        
        # Get comparison data
        comparison = geographic_comparison.compare_trait_variations(scientific_name)
        
        return render_template(
            'geographic_comparison.html',
            scientific_name=scientific_name,
            comparison=comparison
        )
        
    except Exception as e:
        logger.error(f"Error in geographic comparison view: {e}")
        return render_template(
            'error.html',
            error_message=f"Failed to load geographic comparison: {str(e)}"
        ), 500


@geographic_bp.route('/api/geographic-variants/<scientific_name>')
def api_geographic_variants(scientific_name):
    """
    API endpoint: Get geographic variants of a species
    
    Returns:
        JSON with all locations where species is found and their traits
    """
    try:
        variants = geographic_comparison.get_geographic_variants(scientific_name)
        return jsonify(variants)
        
    except Exception as e:
        logger.error(f"API error getting geographic variants: {e}")
        return jsonify({'error': str(e)}), 500


@geographic_bp.route('/api/trait-comparison/<scientific_name>')
def api_trait_comparison(scientific_name):
    """
    API endpoint: Compare trait variations across geographic locations
    
    Query parameters:
        - include_ai: Include AI analysis (default: true)
    
    Returns:
        JSON with comprehensive trait comparison including:
        - Observed traits per location
        - Climate correlations
        - AI analysis (with disclaimers)
        - Academic citations
    """
    try:
        include_ai = request.args.get('include_ai', 'true').lower() == 'true'
        
        comparison = geographic_comparison.compare_trait_variations(scientific_name)
        
        # Remove AI analysis if requested
        if not include_ai and 'ai_trait_analysis' in comparison:
            del comparison['ai_trait_analysis']
        
        return jsonify(comparison)
        
    except Exception as e:
        logger.error(f"API error in trait comparison: {e}")
        return jsonify({'error': str(e)}), 500


@geographic_bp.route('/api/climate-correlations/<scientific_name>')
def api_climate_correlations(scientific_name):
    """
    API endpoint: Get climate correlations for a species
    
    Returns:
        JSON with climate data and statistical correlations
    """
    try:
        comparison = geographic_comparison.compare_trait_variations(scientific_name)
        
        if 'error' in comparison:
            return jsonify(comparison), 400
        
        return jsonify({
            'scientific_name': scientific_name,
            'climate_correlations': comparison.get('climate_correlations'),
            'locations_analyzed': comparison.get('total_locations_analyzed'),
            'data_citations': comparison.get('data_citations')
        })
        
    except Exception as e:
        logger.error(f"API error getting climate correlations: {e}")
        return jsonify({'error': str(e)}), 500


logger.info("🌍 Geographic Comparison routes registered successfully")
