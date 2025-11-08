"""
Digital Botanist Vision AI Routes
Admin dashboard for botanical identification with knowledge base
"""

from flask import render_template, jsonify, request
from app import app
import logging
from vision_ai_botanist import BotanistVisionAI
from botanist_db_setup import get_botanist_stats, ensure_botanist_table_exists
import threading

logger = logging.getLogger(__name__)

# Global analysis thread
botanist_thread = None
botanist_status = {
    'running': False,
    'stats': {}
}

@app.route('/admin/botanist-vision')
def botanist_dashboard():
    """Admin dashboard for Digital Botanist Vision AI"""
    # Ensure table exists before loading dashboard
    ensure_botanist_table_exists()
    return render_template('admin/botanist_dashboard.html')

@app.route('/api/admin/botanist/status')
def get_botanist_status():
    """Get current Digital Botanist progress (lightweight - no heavy initialization)"""
    try:
        # Use lightweight function that doesn't initialize OpenAI or load 1,763 terms
        progress = get_botanist_stats()
        
        if progress is None:
            return jsonify({
                'success': False,
                'error': 'Database error - unable to retrieve stats'
            }), 500
        
        return jsonify({
            'success': True,
            'progress': progress,
            'is_running': botanist_status['running'],
            'stats': botanist_status['stats']
        })
    except Exception as e:
        logger.error(f"Error getting botanist status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/botanist/start', methods=['POST'])
def start_botanist_analysis_api():
    """Start Digital Botanist blind identification"""
    global botanist_thread, botanist_status
    
    if botanist_status['running']:
        return jsonify({
            'success': False,
            'error': 'Botanical analysis already in progress'
        }), 400
    
    try:
        data = request.json or {}
        limit = data.get('limit', 100)
        batch_size = data.get('batch_size', 50)
        
        def run_analysis():
            global botanist_status
            botanist_status['running'] = True
            
            try:
                # Initialize BotanistVisionAI and run analysis
                botanist = BotanistVisionAI()
                stats = botanist.batch_analyze_specimens(
                    batch_size=batch_size,
                    limit=limit
                )
                botanist_status['stats'] = stats
            except Exception as e:
                logger.error(f"Botanist analysis error: {e}")
                botanist_status['stats'] = {'error': str(e)}
            finally:
                botanist_status['running'] = False
        
        botanist_thread = threading.Thread(target=run_analysis)
        botanist_thread.start()
        
        return jsonify({
            'success': True,
            'message': f'Started blind identification of {limit} specimens',
            'limit': limit,
            'batch_size': batch_size,
            'note': 'AI will identify specimens WITHOUT knowing the answer first, then validate accuracy'
        })
        
    except Exception as e:
        logger.error(f"Error starting botanist analysis: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/botanist/results')
def get_botanist_results():
    """Get Digital Botanist analysis results (lightweight query)"""
    try:
        import os
        from sqlalchemy import create_engine
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        accuracy_filter = request.args.get('accuracy')  # perfect, genus_only, incorrect
        
        # Ensure table exists
        ensure_botanist_table_exists()
        
        # Use lightweight database connection
        database_url = os.environ.get("DATABASE_URL")
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            from sqlalchemy import text
            
            # Build query with optional filter
            where_clause = ""
            if accuracy_filter:
                where_clause = f"WHERE identification_accuracy = :accuracy"
            
            # Get total count
            count_query = f"SELECT COUNT(*) FROM botanist_vision_results {where_clause}"
            if accuracy_filter:
                count_result = conn.execute(text(count_query), {'accuracy': accuracy_filter})
            else:
                count_result = conn.execute(text(count_query))
            total = count_result.scalar()
            
            # Get results with pagination
            query = text(f"""
                SELECT 
                    bvr.id,
                    bvr.orchid_image_id,
                    bvr.image_url,
                    bvr.ai_genus,
                    bvr.ai_species,
                    bvr.ai_confidence,
                    bvr.database_genus,
                    bvr.database_species,
                    bvr.identification_accuracy,
                    bvr.identification_method,
                    bvr.botanical_description,
                    bvr.diagnostic_characters,
                    bvr.botanical_terms_used,
                    bvr.image_quality,
                    bvr.specimen_completeness,
                    bvr.analysis_cost,
                    bvr.created_at
                FROM botanist_vision_results bvr
                {where_clause}
                ORDER BY bvr.created_at DESC
                LIMIT :per_page OFFSET :offset
            """)
            
            params = {
                'per_page': per_page,
                'offset': (page - 1) * per_page
            }
            if accuracy_filter:
                params['accuracy'] = accuracy_filter
            
            result = conn.execute(query, params)
            
            results = []
            for row in result:
                results.append({
                    'id': row[0],
                    'orchid_image_id': row[1],
                    'image_url': row[2],
                    'ai_genus': row[3],
                    'ai_species': row[4],
                    'ai_confidence': float(row[5]) if row[5] else 0.0,
                    'actual_genus': row[6],
                    'actual_species': row[7],
                    'accuracy': row[8],
                    'method': row[9],
                    'description': row[10],
                    'diagnostic_characters': row[11],
                    'botanical_terms': row[12],
                    'image_quality': row[13],
                    'specimen_completeness': row[14],
                    'cost': float(row[15]) if row[15] else 0.0,
                    'created_at': row[16].isoformat() if row[16] else None
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
        logger.error(f"Error getting botanist results: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/botanist/accuracy-report')
def get_accuracy_report():
    """Get detailed accuracy analysis report (lightweight query)"""
    try:
        import os
        from sqlalchemy import create_engine
        
        # Ensure table exists
        ensure_botanist_table_exists()
        
        # Use lightweight database connection
        database_url = os.environ.get("DATABASE_URL")
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            from sqlalchemy import text
            
            # Overall accuracy
            overall = conn.execute(text("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN identification_accuracy = 'perfect' THEN 1 END) as perfect,
                    COUNT(CASE WHEN identification_accuracy = 'genus_only' THEN 1 END) as genus_only,
                    COUNT(CASE WHEN identification_accuracy = 'incorrect' THEN 1 END) as incorrect,
                    AVG(ai_confidence) as avg_confidence
                FROM botanist_vision_results
            """)).fetchone()
            
            # Accuracy by genus
            by_genus = conn.execute(text("""
                SELECT 
                    database_genus,
                    COUNT(*) as total,
                    COUNT(CASE WHEN identification_accuracy = 'perfect' THEN 1 END) as perfect,
                    COUNT(CASE WHEN identification_accuracy = 'genus_only' THEN 1 END) as genus_correct,
                    AVG(ai_confidence) as avg_confidence
                FROM botanist_vision_results
                WHERE database_genus IS NOT NULL
                GROUP BY database_genus
                ORDER BY total DESC
                LIMIT 20
            """)).fetchall()
            
            total = overall[0] or 0
            perfect = overall[1] or 0
            genus_only = overall[2] or 0
            incorrect = overall[3] or 0
            
            report = {
                'overall': {
                    'total_analyzed': total,
                    'perfect_identifications': perfect,
                    'genus_only': genus_only,
                    'incorrect': incorrect,
                    'perfect_rate': round((perfect / total * 100), 1) if total > 0 else 0,
                    'genus_accuracy': round(((perfect + genus_only) / total * 100), 1) if total > 0 else 0,
                    'avg_confidence': round(overall[4] or 0.0, 2)
                },
                'by_genus': [
                    {
                        'genus': row[0],
                        'total': row[1],
                        'perfect': row[2],
                        'genus_correct': row[3],
                        'perfect_rate': round((row[2] / row[1] * 100), 1) if row[1] > 0 else 0,
                        'genus_accuracy': round((row[3] / row[1] * 100), 1) if row[1] > 0 else 0,
                        'avg_confidence': round(row[4] or 0.0, 2)
                    }
                    for row in by_genus
                ]
            }
            
            return jsonify({
                'success': True,
                'report': report
            })
            
    except Exception as e:
        logger.error(f"Error getting accuracy report: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/botanist/export-csv')
def export_botanist_csv():
    """Export Digital Botanist results to CSV for Julius analysis"""
    try:
        import csv
        from io import StringIO
        from flask import make_response
        import os
        from sqlalchemy import create_engine
        
        # Ensure table exists before export
        if not ensure_botanist_table_exists():
            return jsonify({'success': False, 'error': 'Database setup failed'}), 500
        
        # Use lightweight database connection
        database_url = os.environ.get("DATABASE_URL")
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            from sqlalchemy import text
            
            query = text("""
                SELECT 
                    bvr.id,
                    bvr.orchid_image_id,
                    bvr.ai_genus,
                    bvr.ai_species,
                    bvr.ai_confidence,
                    bvr.database_genus,
                    bvr.database_species,
                    bvr.identification_accuracy,
                    bvr.sepal_count,
                    bvr.sepal_color,
                    bvr.petal_count,
                    bvr.petal_color,
                    bvr.labellum_shape,
                    bvr.labellum_color,
                    bvr.column_visible,
                    bvr.spur_present,
                    bvr.inflorescence_type,
                    bvr.growth_habit,
                    bvr.diagnostic_characters,
                    bvr.botanical_terms_used,
                    bvr.identification_reasoning,
                    bvr.image_quality,
                    bvr.specimen_completeness,
                    bvr.analysis_cost,
                    bvr.created_at
                FROM botanist_vision_results bvr
                ORDER BY bvr.id
            """)
            
            result = conn.execute(query)
            
            # Create CSV
            si = StringIO()
            writer = csv.writer(si)
            
            # Write header
            writer.writerow([
                'ID', 'Image ID', 'AI Genus', 'AI Species', 'Confidence',
                'Actual Genus', 'Actual Species', 'Accuracy',
                'Sepal Count', 'Sepal Color', 'Petal Count', 'Petal Color',
                'Labellum Shape', 'Labellum Color', 'Column Visible', 'Spur Present',
                'Inflorescence', 'Growth Habit', 'Diagnostic Characters',
                'Botanical Terms', 'Reasoning', 'Image Quality', 'Specimen Completeness',
                'Cost', 'Analysis Date'
            ])
            
            # Write data
            for row in result:
                writer.writerow(row)
            
            output = make_response(si.getvalue())
            output.headers["Content-Disposition"] = "attachment; filename=botanist_analysis_results.csv"
            output.headers["Content-type"] = "text/csv"
            
            return output
            
    except Exception as e:
        logger.error(f"Error exporting CSV: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
