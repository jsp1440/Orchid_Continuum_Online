#!/usr/bin/env python3
"""
Interactive Medicinal Orchid Map Widget
Visualizes medicinal orchids by region and genus with research data
"""

from flask import Blueprint, render_template, jsonify, request
from app import db
from models import GenusKnowledgeCard, ResearchDocument, OrchidRecord
from sqlalchemy import func
import folium
from folium import plugins
import logging
import json

medicinal_map_bp = Blueprint('medicinal_map', __name__)
logger = logging.getLogger(__name__)

@medicinal_map_bp.route('/widgets/medicinal-orchid-map')
def medicinal_orchid_map():
    """Display interactive map of medicinal orchids by region and genus"""
    
    try:
        # Get all genera with medicinal knowledge
        medicinal_genera = db.session.query(
            GenusKnowledgeCard.genus,
            func.count(GenusKnowledgeCard.id).label('card_count')
        ).group_by(GenusKnowledgeCard.genus).all()
        
        genera_list = [g[0] for g in medicinal_genera]
        
        # Get statistics
        total_genera = len(genera_list)
        total_cards = sum([g[1] for g in medicinal_genera])
        total_documents = ResearchDocument.query.count()
        
        return render_template(
            'medicinal_orchid_map.html',
            genera_list=genera_list,
            total_genera=total_genera,
            total_cards=total_cards,
            total_documents=total_documents
        )
        
    except Exception as e:
        logger.error(f"Error loading medicinal orchid map: {e}")
        return render_template('error.html', error=str(e)), 500

@medicinal_map_bp.route('/api/medicinal-orchid-map-data')
def get_medicinal_map_data():
    """API endpoint to get medicinal orchid location data for map"""
    
    try:
        genus_filter = request.args.get('genus', '').strip()
        
        # Get all genus knowledge cards
        query = GenusKnowledgeCard.query
        
        if genus_filter:
            query = query.filter(
                func.lower(GenusKnowledgeCard.genus) == func.lower(genus_filter)
            )
        
        knowledge_cards = query.all()
        
        # Build location data
        locations = []
        genus_stats = {}
        
        for card in knowledge_cards:
            # Get orchids of this genus with location data
            orchids = OrchidRecord.query.filter(
                func.lower(OrchidRecord.genus) == func.lower(card.genus),
                OrchidRecord.latitude.isnot(None),
                OrchidRecord.longitude.isnot(None)
            ).limit(50).all()  # Limit to avoid overwhelming map
            
            # Get research document for citation
            document = ResearchDocument.query.get(card.document_id)
            
            # Track genus stats
            if card.genus not in genus_stats:
                genus_stats[card.genus] = {
                    'count': 0,
                    'uses': set(),
                    'regions': set()
                }
            
            # Add uses and regions
            if card.traditional_uses:
                for use in card.traditional_uses:
                    if use:
                        genus_stats[card.genus]['uses'].add(use)
            
            if card.cultural_areas:
                for area in card.cultural_areas:
                    if area:
                        genus_stats[card.genus]['regions'].add(area)
            
            # Create location markers for each orchid
            for orchid in orchids:
                genus_stats[card.genus]['count'] += 1
                
                # Build popup content
                popup_content = {
                    'orchid_id': orchid.id,
                    'genus': card.genus,
                    'species': orchid.species or 'sp.',
                    'display_name': orchid.display_name,
                    'location': orchid.region or orchid.native_habitat or 'Unknown',
                    'traditional_uses': card.traditional_uses[:3] if card.traditional_uses else [],
                    'medicinal_uses': card.medicinal_uses[:3] if card.medicinal_uses else [],
                    'active_compounds': card.active_compounds[:3] if card.active_compounds else [],
                    'cultural_areas': list(card.cultural_areas) if card.cultural_areas else [],
                    'source': f"{document.title} ({document.year})" if document else "Research Library",
                    'page_refs': card.page_references if card.page_references else []
                }
                
                locations.append({
                    'lat': float(orchid.latitude),
                    'lng': float(orchid.longitude),
                    'genus': card.genus,
                    'data': popup_content
                })
        
        # Convert genus_stats sets to lists for JSON
        for genus in genus_stats:
            genus_stats[genus]['uses'] = list(genus_stats[genus]['uses'])
            genus_stats[genus]['regions'] = list(genus_stats[genus]['regions'])
        
        return jsonify({
            'success': True,
            'locations': locations,
            'genus_stats': genus_stats,
            'total_locations': len(locations)
        })
        
    except Exception as e:
        logger.error(f"Error getting medicinal map data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@medicinal_map_bp.route('/api/medicinal-genera-list')
def get_medicinal_genera_list():
    """API endpoint to get list of genera with medicinal knowledge"""
    
    try:
        genera = db.session.query(
            GenusKnowledgeCard.genus,
            func.count(GenusKnowledgeCard.id).label('card_count')
        ).group_by(GenusKnowledgeCard.genus).order_by(GenusKnowledgeCard.genus).all()
        
        genera_list = [
            {
                'genus': g[0],
                'card_count': g[1]
            }
            for g in genera
        ]
        
        return jsonify({
            'success': True,
            'genera': genera_list,
            'total': len(genera_list)
        })
        
    except Exception as e:
        logger.error(f"Error getting medicinal genera list: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

logger.info("🗺️ Medicinal Orchid Map routes initialized")
