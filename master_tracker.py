"""
MASTER PROJECT TRACKER
Shows all active tasks, who's working on what, and status of everything
"""

from flask import Blueprint, render_template, jsonify
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

tracker_bp = Blueprint('tracker', __name__)


# Project status tracking
PROJECT_STATUS = {
    'multi_ai_integration': {
        'name': 'Multi-AI Integration System',
        'status': 'complete',
        'owner': 'Replit Agent',
        'features': [
            {'name': 'Google Gemini Vision AI', 'status': 'working', 'cost': 'FREE'},
            {'name': 'Together AI Image Generation', 'status': 'working', 'cost': 'FREE'},
            {'name': 'Hugging Face Backup', 'status': 'available', 'cost': 'FREE'},
            {'name': 'OpenAI Fallback', 'status': 'quota_issue', 'cost': 'PAID'}
        ],
        'notes': 'Saves $90-180/month using free alternatives'
    },
    'live_ai_widget': {
        'name': 'Live AI Generation Widget',
        'status': 'testing',
        'owner': 'Replit Agent',
        'features': [
            {'name': 'Real-time visualization', 'status': 'complete'},
            {'name': 'Step-by-step progress', 'status': 'complete'},
            {'name': 'Database integration', 'status': 'complete'},
            {'name': 'Cost tracking', 'status': 'complete'}
        ],
        'url': '/widgets/live-ai-generation',
        'notes': 'Users can watch AI analyze and generate in real-time'
    },
    'monitoring_dashboard': {
        'name': 'System Monitoring Dashboard',
        'status': 'complete',
        'owner': 'Replit Agent',
        'features': [
            {'name': 'Database statistics', 'status': 'working'},
            {'name': 'AI provider tracking', 'status': 'working'},
            {'name': 'Recent activity feed', 'status': 'working'},
            {'name': 'Auto-refresh (5s)', 'status': 'working'}
        ],
        'url': '/monitor',
        'notes': 'Real-time system health and AI processing status'
    },
    'culture_sheets': {
        'name': 'AOS Culture Sheets',
        'status': 'pending',
        'owner': 'Unassigned',
        'notes': 'Interrupted - needs completion'
    },
    'database_enrichment': {
        'name': 'Background Database Enrichment',
        'status': 'unknown',
        'owner': 'Julius AI / Replit Agent',
        'notes': 'Status unclear - needs investigation'
    },
    'botanist_vision_system': {
        'name': 'Digital Botanist Vision AI',
        'status': 'in_progress',
        'owner': 'Replit Agent',
        'features': [
            {'name': '4-Mode Illustration System', 'status': 'designed'},
            {'name': 'Vision AI Integration', 'status': 'complete'},
            {'name': 'Multi-provider support', 'status': 'complete'}
        ],
        'notes': '2-phase learning with 1,648 herbarium specimens'
    },
    'eol_taxonomy_extraction': {
        'name': 'EOL Taxonomy Extraction - 13,429 Species',
        'status': 'in_progress',
        'owner': 'Julius AI',
        'priority': 'CRITICAL',
        'features': [
            {'name': 'Read orchid_eol_page_ids.txt (13,429 IDs)', 'status': 'in_progress'},
            {'name': 'Scrape scientific names from EOL pages', 'status': 'in_progress'},
            {'name': 'Create julius_taxonomy_results.csv', 'status': 'pending'},
            {'name': 'Upload CSV to Replit', 'status': 'pending'},
            {'name': 'Mark task complete in tracker', 'status': 'pending'}
        ],
        'instructions_file': 'JULIUS_READ_THIS_NOW.md',
        'input_file': 'orchid_eol_page_ids.txt',
        'output_file': 'julius_taxonomy_results.csv',
        'images_unlocked': 95321,
        'coverage_increase': '1.3% → 40%',
        'notes': 'HIGHEST PRIORITY - Unlocks 95,321 images and 40% species coverage',
        'started_at': datetime.now().isoformat()
    },
    'gbif_url_extraction': {
        'name': 'GBIF Image URL Extraction - 8,390 Species',
        'status': 'pending',
        'owner': 'Julius AI',
        'priority': 'HIGH',
        'features': [
            {'name': 'Query 8,390 species with GBIF keys', 'status': 'pending'},
            {'name': 'Call GBIF API for each species', 'status': 'pending'},
            {'name': 'Extract ~144,000 image URLs', 'status': 'pending'},
            {'name': 'Insert URLs to orchid_images table', 'status': 'pending'}
        ],
        'instructions_file': 'JULIUS_GBIF_EXTRACTION.md',
        'estimated_images': 144000,
        'estimated_time': '1-2 hours',
        'notes': 'Extract image URLs from GBIF using API - no downloading'
    },
    'tropicos_url_extraction': {
        'name': 'Tropicos Herbarium URL Extraction - 685K Images',
        'status': 'pending',
        'owner': 'Julius AI',
        'priority': 'HIGH',
        'features': [
            {'name': 'Download Darwin Core Archive (~150MB)', 'status': 'pending'},
            {'name': 'Parse occurrence.txt for Orchidaceae', 'status': 'pending'},
            {'name': 'Extract image URLs from multimedia.txt', 'status': 'pending'},
            {'name': 'Insert ~685,000 URLs to database', 'status': 'pending'}
        ],
        'instructions_file': 'JULIUS_TROPICOS_EXTRACTION.md',
        'estimated_images': 685000,
        'estimated_time': '1.5-2 hours',
        'notes': 'LARGEST extraction - MBG herbarium specimens'
    },
    'powo_kew_extraction': {
        'name': 'POWO/Kew Taxonomy & Image Extraction - 30K Species',
        'status': 'pending',
        'owner': 'Julius AI',
        'priority': 'MEDIUM',
        'features': [
            {'name': 'Extract 15 major orchid genera', 'status': 'pending'},
            {'name': 'Get taxonomy + images via pykew', 'status': 'pending'},
            {'name': 'Add ~30,000 species with images', 'status': 'pending'},
            {'name': 'Insert to taxonomy + images tables', 'status': 'pending'}
        ],
        'instructions_file': 'JULIUS_POWO_EXTRACTION.md',
        'estimated_images': 30000,
        'estimated_time': '7-8 hours',
        'notes': 'Authoritative Kew taxonomy + herbarium images'
    }
}


@tracker_bp.route('/tracker')
def master_tracker():
    """Master project tracker page"""
    return render_template('master_tracker.html')


@tracker_bp.route('/api/tracker/status')
def get_project_status():
    """Get current project status"""
    return jsonify({
        'success': True,
        'timestamp': datetime.now().isoformat(),
        'projects': PROJECT_STATUS,
        'summary': {
            'total_projects': len(PROJECT_STATUS),
            'complete': sum(1 for p in PROJECT_STATUS.values() if p['status'] == 'complete'),
            'in_progress': sum(1 for p in PROJECT_STATUS.values() if p['status'] in ['testing', 'in_progress']),
            'pending': sum(1 for p in PROJECT_STATUS.values() if p['status'] in ['pending', 'unknown'])
        }
    })


@tracker_bp.route('/api/tracker/update', methods=['POST'])
def update_project_status():
    """Update project status - Julius can call this to mark tasks complete"""
    from flask import request
    data = request.json
    
    project_key = data.get('project_key')
    new_status = data.get('status')
    notes = data.get('notes', '')
    completed_by = data.get('completed_by', 'Unknown')
    
    if project_key in PROJECT_STATUS:
        PROJECT_STATUS[project_key]['status'] = new_status
        if notes:
            PROJECT_STATUS[project_key]['notes'] = notes
        if new_status == 'complete':
            PROJECT_STATUS[project_key]['completed_at'] = datetime.now().isoformat()
            PROJECT_STATUS[project_key]['completed_by'] = completed_by
        
        return jsonify({
            'success': True, 
            'message': f'Project {project_key} updated to {new_status}',
            'project': PROJECT_STATUS[project_key]
        })
    else:
        return jsonify({
            'success': False,
            'error': f'Project {project_key} not found'
        }), 404
