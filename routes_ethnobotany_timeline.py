from flask import Blueprint, render_template, jsonify
from app import db
from models import GenusKnowledgeCard, OrchidRecord, ResearchDocument
from sqlalchemy import func, or_
import logging

logger = logging.getLogger(__name__)

ethnobotany_timeline_bp = Blueprint('ethnobotany_timeline', __name__)

@ethnobotany_timeline_bp.route('/ethnobotany-timeline')
def ethnobotany_timeline():
    """Display interactive ethnobotany timeline"""
    try:
        # Get all knowledge cards with cultural/historical data
        knowledge_cards = db.session.query(GenusKnowledgeCard).filter(
            or_(
                GenusKnowledgeCard.traditional_uses.isnot(None),
                GenusKnowledgeCard.medicinal_uses.isnot(None),
                GenusKnowledgeCard.cultural_areas.isnot(None)
            )
        ).all()
        
        # Get research documents for context
        documents = db.session.query(ResearchDocument).all()
        
        # Build timeline data
        timeline_data = build_timeline_data(knowledge_cards)
        
        # Get statistics
        total_genera = len(set([card.genus for card in knowledge_cards]))
        total_cultural_areas = len(set([area for card in knowledge_cards if card.cultural_areas for area in card.cultural_areas]))
        total_uses = sum([len(card.traditional_uses or []) + len(card.medicinal_uses or []) for card in knowledge_cards])
        
        logger.info(f"📅 Ethnobotany Timeline loaded: {total_genera} genera, {total_cultural_areas} cultural areas")
        
        return render_template('ethnobotany_timeline.html',
                             timeline_data=timeline_data,
                             total_genera=total_genera,
                             total_cultural_areas=total_cultural_areas,
                             total_uses=total_uses,
                             documents=documents)
    
    except Exception as e:
        logger.error(f"Error loading ethnobotany timeline: {e}")
        return f"Error loading timeline: {e}", 500


@ethnobotany_timeline_bp.route('/api/ethnobotany-timeline-data')
def get_timeline_data():
    """API endpoint for timeline data"""
    try:
        knowledge_cards = db.session.query(GenusKnowledgeCard).filter(
            or_(
                GenusKnowledgeCard.traditional_uses.isnot(None),
                GenusKnowledgeCard.medicinal_uses.isnot(None),
                GenusKnowledgeCard.cultural_areas.isnot(None)
            )
        ).all()
        
        timeline_data = build_timeline_data(knowledge_cards)
        
        return jsonify({
            'success': True,
            'timeline': timeline_data
        })
    
    except Exception as e:
        logger.error(f"Error getting timeline data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def build_timeline_data(knowledge_cards):
    """Build timeline data from knowledge cards"""
    # Define historical periods for traditional medicine
    periods = {
        'Ancient': {
            'range': 'Pre-500 CE',
            'description': 'Ancient traditional medicine systems',
            'icon': '🏺',
            'genera': []
        },
        'Classical': {
            'range': '500-1500 CE',
            'description': 'Classical herbalism and traditional healing',
            'icon': '📜',
            'genera': []
        },
        'Early Modern': {
            'range': '1500-1800',
            'description': 'Colonial era and plant exploration',
            'icon': '🌍',
            'genera': []
        },
        'Modern': {
            'range': '1800-1950',
            'description': 'Scientific documentation of traditional knowledge',
            'icon': '🔬',
            'genera': []
        },
        'Contemporary': {
            'range': '1950-Present',
            'description': 'Current ethnobotanical research and conservation',
            'icon': '🌿',
            'genera': []
        }
    }
    
    # Categorize genera by cultural areas (proxy for historical periods)
    for card in knowledge_cards:
        if not card.cultural_areas:
            continue
        
        genus_data = {
            'genus': card.genus,
            'traditional_uses': card.traditional_uses or [],
            'medicinal_uses': card.medicinal_uses or [],
            'cultural_areas': card.cultural_areas or [],
            'indigenous_names': card.indigenous_names or [],
            'source': card.source or 'Research Library',
            'page_reference': card.page_reference
        }
        
        # Assign to periods based on cultural context
        # Ancient: Traditional Chinese Medicine, Ayurveda
        if any(area in str(card.cultural_areas).lower() for area in ['china', 'chinese', 'ayurveda', 'india', 'indian']):
            periods['Ancient']['genera'].append(genus_data)
        
        # Classical: Southeast Asian traditional medicine
        if any(area in str(card.cultural_areas).lower() for area in ['southeast asia', 'thailand', 'vietnam', 'burma', 'myanmar']):
            periods['Classical']['genera'].append(genus_data)
        
        # Early Modern: Pacific and Indigenous knowledge
        if any(area in str(card.cultural_areas).lower() for area in ['pacific', 'polynesia', 'australia', 'new zealand', 'philippines']):
            periods['Early Modern']['genera'].append(genus_data)
        
        # Modern: All documented traditional uses
        if card.traditional_uses or card.medicinal_uses:
            periods['Modern']['genera'].append(genus_data)
        
        # Contemporary: All current research
        periods['Contemporary']['genera'].append(genus_data)
    
    # Remove duplicates and build final timeline
    timeline = []
    for period_name, period_data in periods.items():
        # Remove duplicate genera within each period
        unique_genera = {}
        for genus in period_data['genera']:
            if genus['genus'] not in unique_genera:
                unique_genera[genus['genus']] = genus
        
        if unique_genera:  # Only add periods with data
            timeline.append({
                'period': period_name,
                'range': period_data['range'],
                'description': period_data['description'],
                'icon': period_data['icon'],
                'genera': list(unique_genera.values()),
                'count': len(unique_genera)
            })
    
    return timeline


logger.info("📅 Ethnobotany Timeline routes initialized")
