"""
Image Collection Routes
Admin routes for collecting images from EOL and GBIF for all orchid species
"""

import logging
from flask import Blueprint, render_template, jsonify, request
from complete_species_collector import species_collector

logger = logging.getLogger(__name__)

# Create blueprint
image_collection_bp = Blueprint('image_collection', __name__)

@image_collection_bp.route('/admin/image-collection')
def image_collection_dashboard():
    """Admin dashboard for image collection progress"""
    try:
        progress = species_collector.get_collection_progress()
        
        return render_template(
            'admin/image_collection_dashboard.html',
            progress=progress
        )
        
    except Exception as e:
        logger.error(f"Error loading image collection dashboard: {e}")
        return f"Error: {str(e)}", 500


@image_collection_bp.route('/api/start-image-collection', methods=['POST'])
def start_image_collection():
    """
    API endpoint to start collecting images
    
    Query parameters:
        - batch_size: Number of species to process (default: 50, max: 500)
    """
    try:
        batch_size = request.args.get('batch_size', 50, type=int)
        
        # Limit batch size to prevent overload
        batch_size = min(batch_size, 500)
        
        logger.info(f"🚀 Starting image collection for {batch_size} species")
        
        # Run batch collection
        stats = species_collector.batch_collect_images(batch_size=batch_size)
        
        return jsonify({
            'success': True,
            'stats': stats,
            'message': f'Collection complete: {stats.get("images_stored", 0)} images collected'
        })
        
    except Exception as e:
        logger.error(f"Error in image collection: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@image_collection_bp.route('/api/collection-progress')
def api_collection_progress():
    """Get current collection progress"""
    try:
        progress = species_collector.get_collection_progress()
        return jsonify(progress)
        
    except Exception as e:
        logger.error(f"Error getting collection progress: {e}")
        return jsonify({'error': str(e)}), 500


logger.info("🖼️ Image Collection routes registered successfully")
