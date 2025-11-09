"""
Flask API Routes for Culture Sheet Widget
Handles culture sheet generation with usage tracking and Neon One integration
"""
import logging
from flask import Blueprint, request, jsonify
from datetime import datetime
from app import db
from neon_one_integration import neon_one_service
from usage_tracking import usage_tracker

logger = logging.getLogger(__name__)

# Create blueprint for widget API
widget_api = Blueprint('widget_api', __name__, url_prefix='/api/widget')


def get_client_ip():
    """Get client IP address from request, handling proxies"""
    # Check for X-Forwarded-For header (from proxies/load balancers)
    if request.headers.get('X-Forwarded-For'):
        ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
    else:
        ip = request.remote_addr
    return ip


@widget_api.route('/check-access', methods=['POST'])
def check_access():
    """
    Check if user has access to generate culture sheets
    
    Request body:
    {
        "neon_one_account_id": "12345",  // Optional
        "email": "user@example.com",      // Optional (will lookup account)
        "with_ai_artwork": true           // Whether they want AI artwork
    }
    
    Response:
    {
        "allowed": true,
        "membership_tier": "member",
        "remaining_credits": 95,
        "limit": 100,
        "ai_artwork_allowed": true,
        "message": "You have 95 of 100 sheets remaining this year",
        "upgrade_prompt": false
    }
    """
    try:
        data = request.get_json() or {}
        
        neon_one_account_id = data.get('neon_one_account_id')
        email = data.get('email')
        with_ai_artwork = data.get('with_ai_artwork', False)
        ip_address = get_client_ip()
        
        # Determine membership tier
        membership_tier = 'visitor'
        
        if neon_one_account_id or email:
            # Check Neon One for membership status
            member_info = neon_one_service.verify_member_access(
                account_id=neon_one_account_id,
                email=email
            )
            
            if member_info.get('has_access'):
                membership_tier = member_info['tier']
                neon_one_account_id = member_info['account_id']
            else:
                # Account exists but no active membership
                logger.info(f"No active membership for {email or neon_one_account_id}")
        
        # Check usage limits
        usage_check = usage_tracker.check_usage_limit(
            neon_one_account_id=neon_one_account_id if membership_tier != 'visitor' else None,
            ip_address=ip_address if membership_tier == 'visitor' else None,
            membership_tier=membership_tier,
            with_ai_artwork=with_ai_artwork
        )
        
        return jsonify({
            'allowed': usage_check['allowed'],
            'membership_tier': usage_check['tier'],
            'remaining_credits': usage_check['remaining'],
            'limit': usage_check['limit'],
            'ai_artwork_allowed': usage_check['ai_artwork_allowed'],
            'message': usage_check['message'],
            'upgrade_prompt': usage_check['upgrade_prompt'],
            'usage_record_id': usage_check.get('usage_record_id')
        })
        
    except Exception as e:
        logger.error(f"Error in check_access: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@widget_api.route('/species/search', methods=['GET'])
def search_species():
    """
    Search for orchid species
    
    Query params:
    - query: Search term (genus or species name)
    - limit: Max results (default 10)
    
    Response:
    [
        {
            "taxonomy_id": 7905,
            "scientific_name": "Cattleya mossiae",
            "genus": "Cattleya",
            "common_name": "Easter Orchid",
            "region": "South America"
        }
    ]
    """
    try:
        query = request.args.get('query', '').strip()
        limit = int(request.args.get('limit', 10))
        
        if not query or len(query) < 2:
            return jsonify([])
        
        # Import here to avoid circular dependency
        from models import OrchidTaxonomy
        
        # Search by scientific name or genus
        results = OrchidTaxonomy.query.filter(
            db.or_(
                OrchidTaxonomy.species_name.ilike(f'%{query}%'),
                OrchidTaxonomy.genus.ilike(f'%{query}%')
            )
        ).limit(limit).all()
        
        return jsonify([{
            'taxonomy_id': r.id,
            'scientific_name': r.species_name,
            'genus': r.genus,
            'common_name': getattr(r, 'common_name', None),
            'region': getattr(r, 'native_region', 'Unknown')
        } for r in results])
        
    except Exception as e:
        logger.error(f"Error searching species: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@widget_api.route('/culture-sheet/generate', methods=['POST'])
def generate_culture_sheet():
    """
    Generate a personalized culture sheet
    
    Request body:
    {
        "taxonomy_id": 7905,
        "latitude": 34.0522,
        "longitude": -118.2437,
        "city": "Los Angeles",
        "country": "USA",
        "sections": ["temperature", "light", "water", "humidity", "potting", 
                     "fertilizer", "pollinators", "companions", "maps"],
        "artwork_style": "artistic",
        "interface_theme": "scientific-lab",
        "sheet_theme": "scientific-publication",
        "with_ai_artwork": true,
        "usage_record_id": 123,  // From check_access call
        "neon_one_account_id": "12345"  // Optional
    }
    
    Response:
    {
        "sheet_id": "uuid",
        "species": {...},
        "sections": {...},
        "artwork_url": "https://...",
        "generated_at": "2024-11-09T12:00:00Z"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        taxonomy_id = data.get('taxonomy_id')
        usage_record_id = data.get('usage_record_id')
        with_ai_artwork = data.get('with_ai_artwork', False)
        
        if not taxonomy_id:
            return jsonify({'error': 'taxonomy_id required'}), 400
        
        if not usage_record_id:
            return jsonify({'error': 'usage_record_id required - call /check-access first'}), 400
        
        # Record the generation
        recorded = usage_tracker.record_generation(
            usage_record_id=usage_record_id,
            with_ai_artwork=with_ai_artwork
        )
        
        if not recorded:
            return jsonify({'error': 'Failed to record usage'}), 500
        
        # Import models
        from models import OrchidTaxonomy
        
        # Get species data
        species = OrchidTaxonomy.query.get(taxonomy_id)
        if not species:
            return jsonify({'error': 'Species not found'}), 404
        
        # Build culture sheet data
        # TODO: Integrate with existing culture sheet generation system
        culture_data = {
            'sheet_id': f"cs_{taxonomy_id}_{datetime.utcnow().timestamp()}",
            'species': {
                'taxonomy_id': species.id,
                'scientific_name': species.species_name,
                'genus': species.genus,
                'common_name': getattr(species, 'common_name', None),
                'region': getattr(species, 'native_region', 'Unknown')
            },
            'sections': {
                'temperature': {
                    'day': '70-85°F (21-29°C)',
                    'night': '60-70°F (15-21°C)'
                } if 'temperature' in data.get('sections', []) else None,
                'light': {
                    'level': 'High',
                    'foot_candles': '2000-3000'
                } if 'light' in data.get('sections', []) else None,
                'water': {
                    'frequency': 'Water when media approaches dryness',
                    'method': 'Thorough soaking'
                } if 'water' in data.get('sections', []) else None,
                # Add other sections as needed
            },
            'artwork_url': None,  # TODO: Generate AI artwork if requested
            'generated_at': datetime.utcnow().isoformat()
        }
        
        return jsonify(culture_data)
        
    except Exception as e:
        logger.error(f"Error generating culture sheet: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@widget_api.route('/usage-stats', methods=['GET'])
def get_usage_stats():
    """
    Get usage statistics for current user
    
    Query params:
    - neon_one_account_id: Account ID (for members)
    OR uses IP address for visitors
    
    Response:
    {
        "tier": "member",
        "sheets_generated": 5,
        "sheets_with_ai": 3,
        "limit": 100,
        "remaining": 95,
        "last_generation": "2024-11-09T12:00:00Z",
        "last_reset": "2024-01-01"
    }
    """
    try:
        neon_one_account_id = request.args.get('neon_one_account_id')
        ip_address = get_client_ip() if not neon_one_account_id else None
        
        stats = usage_tracker.get_usage_stats(
            neon_one_account_id=neon_one_account_id,
            ip_address=ip_address
        )
        
        if 'error' in stats:
            return jsonify(stats), 404
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error getting usage stats: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@widget_api.route('/membership/verify', methods='POST'])
def verify_membership():
    """
    Verify membership status via Neon One
    
    Request body:
    {
        "email": "user@example.com"
        OR
        "account_id": "12345"
    }
    
    Response:
    {
        "has_access": true,
        "tier": "life_member",
        "status": "active",
        "expiration_date": null,
        "account_id": "12345"
    }
    """
    try:
        data = request.get_json()
        email = data.get('email')
        account_id = data.get('account_id')
        
        if not email and not account_id:
            return jsonify({'error': 'Email or account_id required'}), 400
        
        member_info = neon_one_service.verify_member_access(
            account_id=account_id,
            email=email
        )
        
        return jsonify(member_info)
        
    except Exception as e:
        logger.error(f"Error verifying membership: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@widget_api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({
        'status': 'healthy',
        'service': 'culture-sheet-widget-api',
        'timestamp': datetime.utcnow().isoformat()
    })
