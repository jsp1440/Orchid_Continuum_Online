#!/usr/bin/env python3
"""
Culture Sheet Routes - Flask Blueprint
Handles all culture sheet related endpoints including data sources/citations
"""
import os
from flask import Blueprint, render_template, jsonify
from culture_sheet_generator import CultureSheetGenerator
from microclimate_analyzer import MicroclimateAnalyzer
import psycopg2

DATABASE_URL = os.environ.get('DATABASE_URL')

culture_sheets_bp = Blueprint('culture_sheets', __name__, url_prefix='/culture-sheets')

@culture_sheets_bp.route('/<int:taxonomy_id>/sources')
def culture_sheet_sources(taxonomy_id):
    """
    Data Sources & Citations page for microclimate analysis
    Shows which APIs contributed images, sample sizes, metadata completeness
    
    Example: /culture-sheets/1962/sources
    """
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    try:
        # Get species information
        cur.execute("""
            SELECT scientific_name, genus, species, common_name
            FROM orchid_taxonomy
            WHERE id = %s
        """, (taxonomy_id,))
        
        species_row = cur.fetchone()
        if not species_row:
            return render_template('culture_sheets/sources.html',
                error="Species not found",
                taxonomy_id=taxonomy_id
            )
        
        scientific_name, genus, species, common_name = species_row
        
        # Get microclimate analysis with source breakdown
        analyzer = MicroclimateAnalyzer(connection=conn)
        microclimate_data = analyzer.analyze_species_images(taxonomy_id)
        
        source_breakdown = microclimate_data.get('source_breakdown', {})
        
        # Get total image count for this species
        cur.execute("""
            SELECT COUNT(*) FROM orchid_images
            WHERE taxonomy_id = %s AND wild_specimen = true
        """, (taxonomy_id,))
        total_images = cur.fetchone()[0]
        
        # Build context for template
        context = {
            'taxonomy_id': taxonomy_id,
            'scientific_name': scientific_name,
            'genus': genus,
            'species': species,
            'common_name': common_name,
            'total_images': total_images,
            'source_breakdown': source_breakdown,
            'microclimate_status': microclimate_data.get('status'),
            'data_quality_score': microclimate_data.get('data_quality_score'),
            'analysis_date': microclimate_data.get('analysis_date'),
            'has_data': source_breakdown and source_breakdown.get('sources'),
            'culture_sheet_url': f'/culture-sheets/{taxonomy_id}'  # Link back to main culture sheet
        }
        
        return render_template('culture_sheets/sources.html', **context)
    
    finally:
        cur.close()
        conn.close()


@culture_sheets_bp.route('/<int:taxonomy_id>')
def culture_sheet_main(taxonomy_id):
    """
    Main culture sheet view (placeholder for future implementation)
    Currently redirects to print version
    
    Example: /culture-sheets/1962
    """
    from flask import redirect
    return redirect(f'/print/culture-sheet/{taxonomy_id}')
