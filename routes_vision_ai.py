"""
Vision AI Analysis Routes
Admin dashboard to analyze orchid images and view results
"""

from flask import render_template, jsonify, request
from app import app
import logging
from vision_ai_analyzer import VisionAIAnalyzer, start_vision_analysis
import threading

logger = logging.getLogger(__name__)

# Global analysis thread
analysis_thread = None
analysis_status = {
    'running': False,
    'stats': {}
}

@app.route('/admin/vision-ai')
def vision_ai_dashboard():
    """Admin dashboard for Vision AI analysis"""
    return render_template('admin/vision_ai_dashboard.html')

@app.route('/api/admin/vision-ai/status')
def get_vision_status():
    """Get current Vision AI progress"""
    try:
        analyzer = VisionAIAnalyzer()
        progress = analyzer.get_analysis_progress()
        
        return jsonify({
            'success': True,
            'progress': progress,
            'is_running': analysis_status['running'],
            'stats': analysis_status['stats']
        })
    except Exception as e:
        logger.error(f"Error getting vision status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/vision-ai/start', methods=['POST'])
def start_vision_analysis_api():
    """Start Vision AI analysis"""
    global analysis_thread, analysis_status
    
    if analysis_status['running']:
        return jsonify({
            'success': False,
            'error': 'Analysis already in progress'
        }), 400
    
    try:
        data = request.json or {}
        limit = data.get('limit', 100)  # Default 100 for testing
        batch_size = data.get('batch_size', 50)
        
        def run_analysis():
            global analysis_status
            analysis_status['running'] = True
            
            try:
                stats = start_vision_analysis(
                    batch_size=batch_size,
                    limit=limit
                )
                analysis_status['stats'] = stats
            except Exception as e:
                logger.error(f"Analysis error: {e}")
                analysis_status['stats'] = {'error': str(e)}
            finally:
                analysis_status['running'] = False
        
        analysis_thread = threading.Thread(target=run_analysis)
        analysis_thread.start()
        
        return jsonify({
            'success': True,
            'message': f'Started analyzing {limit} images',
            'limit': limit,
            'batch_size': batch_size
        })
        
    except Exception as e:
        logger.error(f"Error starting analysis: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/vision-ai/results')
def get_vision_results():
    """Get Vision AI analysis results"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        analyzer = VisionAIAnalyzer()
        
        with analyzer.engine.connect() as conn:
            from sqlalchemy import text
            
            # Get total count
            count_result = conn.execute(text("""
                SELECT COUNT(*) FROM vision_ai_results
            """))
            total = count_result.scalar()
            
            # Get results with pagination
            query = text("""
                SELECT 
                    var.id,
                    var.orchid_image_id,
                    var.image_url,
                    var.identified_genus,
                    var.identified_species,
                    var.confidence_score,
                    var.ai_description,
                    var.flower_color,
                    var.growth_habit,
                    var.distinctive_features,
                    var.matches_database_taxonomy,
                    var.database_genus,
                    var.database_species,
                    var.taxonomy_confidence,
                    var.image_quality,
                    var.specimen_completeness,
                    var.identification_difficulty,
                    var.analysis_cost,
                    var.created_at
                FROM vision_ai_results var
                ORDER BY var.created_at DESC
                LIMIT :per_page OFFSET :offset
            """)
            
            result = conn.execute(query, {
                'per_page': per_page,
                'offset': (page - 1) * per_page
            })
            
            results = []
            for row in result:
                results.append({
                    'id': row[0],
                    'orchid_image_id': row[1],
                    'image_url': row[2],
                    'identified_genus': row[3],
                    'identified_species': row[4],
                    'confidence_score': float(row[5]) if row[5] else 0.0,
                    'ai_description': row[6],
                    'flower_color': row[7],
                    'growth_habit': row[8],
                    'distinctive_features': row[9],
                    'matches_database_taxonomy': row[10],
                    'database_genus': row[11],
                    'database_species': row[12],
                    'taxonomy_confidence': row[13],
                    'image_quality': row[14],
                    'specimen_completeness': row[15],
                    'identification_difficulty': row[16],
                    'analysis_cost': float(row[17]) if row[17] else 0.0,
                    'created_at': row[18].isoformat() if row[18] else None
                })
            
            return jsonify({
                'success': True,
                'results': results,
                'total': total,
                'page': page,
                'per_page': per_page,
                'pages': (total + per_page - 1) // per_page
            })
            
    except Exception as e:
        logger.error(f"Error getting results: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/vision-ai/export-csv')
def export_vision_results_csv():
    """Export Vision AI results to CSV"""
    try:
        import csv
        from io import StringIO
        from flask import make_response
        
        analyzer = VisionAIAnalyzer()
        
        with analyzer.engine.connect() as conn:
            from sqlalchemy import text
            
            query = text("""
                SELECT 
                    var.id,
                    var.orchid_image_id,
                    var.image_url,
                    var.identified_genus,
                    var.identified_species,
                    var.confidence_score,
                    var.ai_description,
                    var.flower_color,
                    var.flower_structure,
                    var.leaf_characteristics,
                    var.growth_habit,
                    var.distinctive_features,
                    var.matches_database_taxonomy,
                    var.database_genus,
                    var.database_species,
                    var.taxonomy_confidence,
                    var.image_quality,
                    var.specimen_completeness,
                    var.identification_difficulty,
                    var.analysis_cost,
                    var.created_at
                FROM vision_ai_results var
                ORDER BY var.id
            """)
            
            result = conn.execute(query)
            
            # Create CSV
            si = StringIO()
            writer = csv.writer(si)
            
            # Write header
            writer.writerow([
                'ID', 'Image ID', 'Image URL', 'AI Genus', 'AI Species', 
                'Confidence', 'Description', 'Flower Color', 'Flower Structure',
                'Leaf Characteristics', 'Growth Habit', 'Distinctive Features',
                'Matches Database', 'DB Genus', 'DB Species', 'Taxonomy Confidence',
                'Image Quality', 'Specimen Completeness', 'ID Difficulty',
                'Cost', 'Analysis Date'
            ])
            
            # Write data
            for row in result:
                writer.writerow(row)
            
            output = make_response(si.getvalue())
            output.headers["Content-Disposition"] = "attachment; filename=vision_ai_results.csv"
            output.headers["Content-type"] = "text/csv"
            
            return output
            
    except Exception as e:
        logger.error(f"Error exporting CSV: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
