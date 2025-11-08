"""
Field Completion Dashboard Routes
Tracks enrichment progress across all 28 Phase 1+2+3 fields
"""

from flask import render_template, Blueprint
from models import OrchidRecord
from app import db
from sqlalchemy import func

field_completion_bp = Blueprint('field_completion', __name__)

# Define field groups
PHASE1_FIELDS = [
    ('flower_color', 'Flower Color'),
    ('bloom_stage', 'Bloom Stage'),
    ('inflorescence_type', 'Inflorescence Type'),
    ('inflorescence_position', 'Inflorescence Position'),
    ('bloombot_category', 'Bloombot Category'),
    ('widget_visibility', 'Widget Visibility'),
    ('is_hybrid', 'Is Hybrid'),
    ('image_caption', 'Image Caption')
]

PHASE2_FIELDS = [
    ('leaf_shape', 'Leaf Shape'),
    ('pseudobulb_presence', 'Pseudobulb Presence'),
    ('pseudobulb_form', 'Pseudobulb Form'),
    ('labellum_type', 'Labellum Type'),
    ('flower_resupination', 'Flower Resupination'),
    ('keiki_formation', 'Keiki Formation'),
    ('rhizome_spread_type', 'Rhizome Spread Type'),
    ('leaf_venation', 'Leaf Venation'),
    ('tissue_succulence', 'Tissue Succulence'),
    ('growth_rate', 'Growth Rate'),
    ('flower_longevity_days', 'Flower Longevity (Days)'),
    ('dormant_leaf_drop', 'Dormant Leaf Drop'),
    ('growth_eye_activation', 'Growth Eye Activation')
]

PHASE3_FIELDS = [
    ('taxonomic_status', 'Taxonomic Status'),
    ('taxonomic_authority', 'Taxonomic Authority'),
    ('continent', 'Native Continent'),
    ('country', 'Native Country'),
    ('fragrance', 'Fragrance'),
    ('fragrance_description', 'Fragrance Description'),
    ('parent_species_1', 'Parent Species 1'),
    ('parent_species_2', 'Parent Species 2')
]

@field_completion_bp.route('/admin/field-completion')
def field_completion_dashboard():
    """Display field completion statistics"""
    
    # Get total orchid count
    total_orchids = db.session.query(func.count(OrchidRecord.id)).scalar() or 0
    
    if total_orchids == 0:
        # Handle empty database
        return render_template('field_completion_dashboard.html',
            stats={'total_orchids': 0, 'overall_completion': 0, 'fields_analyzed': 28, 'enriched_count': 0},
            phase1_fields=[], phase2_fields=[], phase3_fields=[])
    
    # Calculate field statistics (simple: just count non-null values)
    def get_field_stats(fields):
        results = []
        for field_name, display_name in fields:
            # Count non-null values for this field (universal check for all types)
            count = db.session.query(func.count(OrchidRecord.id)).filter(
                getattr(OrchidRecord, field_name).isnot(None)
            ).scalar() or 0
            
            percentage = round((count / total_orchids * 100), 1) if total_orchids > 0 else 0
            results.append({
                'name': display_name,
                'field': field_name,
                'count': count,
                'percentage': percentage
            })
        return results
    
    phase1_stats = get_field_stats(PHASE1_FIELDS)
    phase2_stats = get_field_stats(PHASE2_FIELDS)
    phase3_stats = get_field_stats(PHASE3_FIELDS)
    
    # Calculate overall completion (average of all fields)
    all_percentages = [f['percentage'] for f in phase1_stats + phase2_stats + phase3_stats]
    overall_completion = round(sum(all_percentages) / len(all_percentages), 1) if all_percentages else 0
    
    # Count fully enriched orchids (all fields populated)
    all_field_names = [f[0] for f in PHASE1_FIELDS + PHASE2_FIELDS + PHASE3_FIELDS]
    
    # Build query to find orchids with all fields populated (just check NOT NULL for all types)
    query = db.session.query(func.count(OrchidRecord.id))
    for field_name in all_field_names:
        query = query.filter(
            getattr(OrchidRecord, field_name).isnot(None)
        )
    enriched_count = query.scalar() or 0
    
    stats = {
        'total_orchids': total_orchids,
        'overall_completion': overall_completion,
        'fields_analyzed': 28,
        'enriched_count': enriched_count
    }
    
    return render_template('field_completion_dashboard.html',
        stats=stats,
        phase1_fields=phase1_stats,
        phase2_fields=phase2_stats,
        phase3_fields=phase3_stats
    )
