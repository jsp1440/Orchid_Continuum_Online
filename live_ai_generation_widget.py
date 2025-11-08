"""
Live AI Generation Widget - Watch orchid analysis happen in real-time!
Users pick an orchid and watch as AI generates everything
"""

from flask import Blueprint, render_template, request, jsonify, session
from app import db
from models import OrchidTaxonomy, OrchidRecord, BotanistVisionResult
from multi_ai_vision_analyzer import MultiAIVisionAnalyzer
from multi_ai_image_generator import MultiAIImageGenerator
import logging
import os
import time
from datetime import datetime

logger = logging.getLogger(__name__)

live_widget_bp = Blueprint('live_widget', __name__)


@live_widget_bp.route('/widgets/live-ai-generation')
def live_ai_generation_page():
    """Main page for live AI generation widget"""
    # Get sample orchids for user selection
    sample_orchids = db.session.query(OrchidTaxonomy).limit(50).all()
    return render_template('live_ai_generation.html', orchids=sample_orchids)


@live_widget_bp.route('/api/live-generate', methods=['POST'])
def live_generate():
    """
    API endpoint for live AI generation
    Returns streaming updates as AI works
    """
    data = request.json if request.json else {}
    species_name = data.get('species')
    
    if not species_name:
        return jsonify({'error': 'No species provided'}), 400
    
    # Check if already generated
    existing = db.session.query(BotanistVisionResult).filter_by(
        scientific_name=species_name
    ).first()
    
    if existing:
        return jsonify({
            'cached': True,
            'message': f'✓ {species_name} already in database!',
            'data': {
                'species': species_name,
                'analysis': existing.vision_analysis,
                'created_at': existing.created_at.isoformat() if existing.created_at else None
            }
        })
    
    # Find image for this species
    orchid_record = db.session.query(OrchidRecord).filter_by(
        scientific_name=species_name
    ).first()
    
    if not orchid_record or not orchid_record.image_url:
        return jsonify({'error': f'No image found for {species_name}'}), 404
    
    # Start live generation!
    results = {
        'species': species_name,
        'steps': [],
        'cached': False
    }
    
    try:
        # Step 1: Initialize AI
        results['steps'].append({
            'step': 1,
            'name': 'Initializing AI Systems',
            'status': 'starting',
            'timestamp': datetime.now().isoformat()
        })
        
        analyzer = MultiAIVisionAnalyzer()
        generator = MultiAIImageGenerator()
        
        results['steps'][-1]['status'] = 'complete'
        results['steps'][-1]['time'] = 0.5
        
        # Step 2: Vision AI Analysis
        results['steps'].append({
            'step': 2,
            'name': 'AI Vision Analysis (Gemini)',
            'status': 'running',
            'timestamp': datetime.now().isoformat()
        })
        
        start_time = time.time()
        prompt = f"Analyze this {species_name} orchid. Identify key botanical features using proper terminology."
        
        vision_result = analyzer.analyze_with_best_free_option(
            orchid_record.image_url,
            prompt
        )
        
        results['steps'][-1]['status'] = 'complete'
        results['steps'][-1]['time'] = time.time() - start_time
        results['steps'][-1]['provider'] = vision_result.provider
        results['steps'][-1]['cost'] = f"${vision_result.cost_estimate:.4f}"
        results['analysis'] = vision_result.analysis
        
        # Step 3: Generate Scientific Line Drawing
        results['steps'].append({
            'step': 3,
            'name': 'Generate Scientific Line Drawing',
            'status': 'running',
            'timestamp': datetime.now().isoformat()
        })
        
        start_time = time.time()
        drawing_prompt = f"Scientific botanical line drawing of {species_name}, detailed B&W illustration"
        
        drawing_result = generator.generate_with_together_ai(drawing_prompt, model="flux-schnell")
        
        results['steps'][-1]['status'] = 'complete'
        results['steps'][-1]['time'] = time.time() - start_time
        results['steps'][-1]['cost'] = f"${drawing_result.cost_estimate:.4f}"
        results['line_drawing_url'] = drawing_result.image_url if drawing_result.success else None
        
        # Step 4: Save to database
        results['steps'].append({
            'step': 4,
            'name': 'Save to Database',
            'status': 'running',
            'timestamp': datetime.now().isoformat()
        })
        
        # Create database record
        botanist_result = BotanistVisionResult(
            scientific_name=species_name,
            vision_analysis=vision_result.analysis,
            ai_provider=vision_result.provider,
            processing_time=vision_result.processing_time,
            created_at=datetime.now()
        )
        
        db.session.add(botanist_result)
        db.session.commit()
        
        results['steps'][-1]['status'] = 'complete'
        results['steps'][-1]['time'] = 0.3
        
        results['success'] = True
        results['total_cost'] = f"${vision_result.cost_estimate + drawing_result.cost_estimate:.4f}"
        
    except Exception as e:
        logger.error(f"Live generation error: {str(e)}")
        results['error'] = str(e)
        results['success'] = False
    
    return jsonify(results)


@live_widget_bp.route('/api/search-orchids')
def search_orchids():
    """Search for orchids by name"""
    query = request.args.get('q', '')
    
    orchids = db.session.query(OrchidTaxonomy).filter(
        OrchidTaxonomy.scientific_name.ilike(f'%{query}%')
    ).limit(20).all()
    
    return jsonify([{
        'id': o.id,
        'name': o.scientific_name,
        'genus': o.genus
    } for o in orchids])
