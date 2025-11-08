"""
Ethnobotany Widget Package for Neon One CMS
============================================
Standalone embeddable widgets for medicinal orchid research visualization
"""

from flask import Blueprint, render_template, jsonify, request
from app import db
from models import GenusKnowledgeCard, OrchidRecord, ResearchDocument
from sqlalchemy import func, or_
import logging

logger = logging.getLogger(__name__)

ethnobotany_package_bp = Blueprint('ethnobotany_package', __name__, url_prefix='/widgets/ethnobotany')


@ethnobotany_package_bp.route('/medicinal-map-embed')
def medicinal_map_embed():
    """Embeddable medicinal orchid map widget"""
    try:
        # Get statistics for the widget
        total_cards = db.session.query(GenusKnowledgeCard).count()
        total_genera = db.session.query(func.count(func.distinct(GenusKnowledgeCard.genus))).scalar()
        total_documents = db.session.query(ResearchDocument).count()
        
        # Get list of genera for filtering
        genera_list = db.session.query(GenusKnowledgeCard.genus).distinct().order_by(GenusKnowledgeCard.genus).all()
        genera_list = [g[0] for g in genera_list]
        
        return render_template('widgets/medicinal_map_embed.html',
                             total_genera=total_genera,
                             total_cards=total_cards,
                             total_documents=total_documents,
                             genera_list=genera_list)
    
    except Exception as e:
        logger.error(f"Error loading medicinal map embed: {e}")
        return f"Error loading map: {e}", 500


@ethnobotany_package_bp.route('/timeline-embed')
def timeline_embed():
    """Embeddable ethnobotany timeline widget"""
    try:
        from routes_ethnobotany_timeline import build_timeline_data
        
        # Get all knowledge cards
        knowledge_cards = db.session.query(GenusKnowledgeCard).filter(
            or_(
                GenusKnowledgeCard.traditional_uses.isnot(None),
                GenusKnowledgeCard.medicinal_uses.isnot(None),
                GenusKnowledgeCard.cultural_areas.isnot(None)
            )
        ).all()
        
        # Build timeline data
        timeline_data = build_timeline_data(knowledge_cards)
        
        # Get statistics
        total_genera = len(set([card.genus for card in knowledge_cards]))
        total_cultural_areas = len(set([area for card in knowledge_cards if card.cultural_areas for area in card.cultural_areas]))
        total_uses = sum([len(card.traditional_uses or []) + len(card.medicinal_uses or []) for card in knowledge_cards])
        
        return render_template('widgets/timeline_embed.html',
                             timeline_data=timeline_data,
                             total_genera=total_genera,
                             total_cultural_areas=total_cultural_areas,
                             total_uses=total_uses)
    
    except Exception as e:
        logger.error(f"Error loading timeline embed: {e}")
        return f"Error loading timeline: {e}", 500


@ethnobotany_package_bp.route('/api/map-data')
def get_map_data():
    """API endpoint for medicinal orchid map data"""
    try:
        genus_filter = request.args.get('genus', '').strip()
        
        # Query knowledge cards
        query = db.session.query(GenusKnowledgeCard)
        
        if genus_filter:
            query = query.filter(func.lower(GenusKnowledgeCard.genus) == func.lower(genus_filter))
        
        knowledge_cards = query.all()
        
        # Build location data
        locations = []
        for card in knowledge_cards:
            # Get orchid records for this genus
            orchids = db.session.query(OrchidRecord).filter(
                func.lower(OrchidRecord.genus) == func.lower(card.genus)
            ).filter(
                or_(
                    OrchidRecord.latitude.isnot(None),
                    OrchidRecord.native_habitat.isnot(None)
                )
            ).limit(5).all()
            
            for orchid in orchids:
                # Use actual coordinates if available, otherwise estimate from habitat
                lat, lng = get_coordinates_for_orchid(orchid)
                
                if lat and lng:
                    locations.append({
                        'genus': card.genus,
                        'lat': lat,
                        'lng': lng,
                        'data': {
                            'genus': card.genus,
                            'species': orchid.species or 'sp.',
                            'location': orchid.native_habitat or 'Unknown',
                            'traditional_uses': card.traditional_uses or [],
                            'medicinal_uses': card.medicinal_uses or [],
                            'active_compounds': card.active_compounds or [],
                            'cultural_areas': card.cultural_areas or [],
                            'source': card.source or 'Research Library',
                            'orchid_id': orchid.id
                        }
                    })
        
        return jsonify({
            'success': True,
            'locations': locations,
            'count': len(locations)
        })
    
    except Exception as e:
        logger.error(f"Error getting map data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def get_coordinates_for_orchid(orchid):
    """Get coordinates for an orchid based on available data"""
    # If actual coordinates exist, use them
    if orchid.latitude and orchid.longitude:
        return float(orchid.latitude), float(orchid.longitude)
    
    # Otherwise, estimate based on habitat/native region
    habitat = (orchid.native_habitat or '').lower()
    
    # Region-based coordinate estimates
    region_coords = {
        'china': (30, 110),
        'india': (20, 78),
        'thailand': (15, 100),
        'myanmar': (21, 96),
        'burma': (21, 96),
        'vietnam': (16, 108),
        'philippines': (12, 122),
        'malaysia': (4, 102),
        'indonesia': (-2, 118),
        'australia': (-25, 133),
        'new zealand': (-41, 174),
        'madagascar': (-19, 46),
        'south africa': (-30, 25),
        'brazil': (-10, -55),
        'colombia': (4, -72),
        'ecuador': (-1, -78),
        'peru': (-9, -76),
        'mexico': (23, -102),
        'central america': (10, -85),
        'southeast asia': (10, 105),
        'pacific': (0, 160)
    }
    
    for region, coords in region_coords.items():
        if region in habitat:
            return coords
    
    # Default to Southeast Asia if no match
    return (10, 105)


@ethnobotany_package_bp.route('/widget-info')
def widget_info():
    """Widget package information and embedding instructions"""
    return render_template('widgets/ethnobotany_info.html')


logger.info("📦 Ethnobotany Widget Package initialized for Neon One deployment")
