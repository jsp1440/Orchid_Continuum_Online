"""
Digital Botanist Vision AI - Real-Time Monitoring Dashboard
Shows live progress, sample results, and statistics
Includes download routes for botanical drawings in multiple formats
"""
from flask import Blueprint, render_template, jsonify, send_file, Response
from botanist_db_setup import get_botanist_stats
import psycopg2
import os
import io
import base64
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

bp = Blueprint('botanist_monitor', __name__, url_prefix='/botanist')

@bp.route('/monitor')
def monitor_dashboard():
    """Real-time monitoring dashboard"""
    return render_template('botanist_monitor.html')

@bp.route('/api/stats')
def get_stats():
    """API endpoint for live stats"""
    stats = get_botanist_stats()
    if not stats:
        return jsonify({'error': 'No data yet'}), 404
    
    return jsonify(stats)

@bp.route('/api/recent_results')
def get_recent_results():
    """Get most recent 10 analysis results with images"""
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    cur = conn.cursor()
    
    cur.execute("""
        SELECT 
            bvr.id,
            bvr.image_url,
            bvr.ai_genus,
            bvr.ai_species,
            bvr.ai_confidence,
            bvr.identification_accuracy,
            bvr.database_genus,
            bvr.database_species,
            bvr.flower_count,
            bvr.labellum_color,
            bvr.inflorescence_type,
            bvr.botanical_description,
            bvr.analysis_cost,
            bvr.processing_time_seconds,
            bvr.created_at,
            bvr.botanical_drawing_url,
            bvr.labeled_drawing_url,
            bvr.artistic_illustration_url,
            bvr.coloring_page_url,
            bvr.drawing_labels
        FROM botanist_vision_results bvr
        ORDER BY bvr.created_at DESC
        LIMIT 10
    """)
    
    results = []
    for row in cur.fetchall():
        results.append({
            'id': row[0],
            'image_url': row[1],
            'ai_genus': row[2],
            'ai_species': row[3],
            'ai_confidence': float(row[4]) if row[4] else 0,
            'accuracy': row[5],
            'actual_genus': row[6],
            'actual_species': row[7],
            'flower_count': row[8],
            'labellum_color': row[9],
            'inflorescence_type': row[10],
            'description': row[11],
            'cost': float(row[12]) if row[12] else 0,
            'time': float(row[13]) if row[13] else 0,
            'timestamp': row[14].isoformat() if row[14] else None,
            'botanical_drawing_url': row[15],
            'labeled_drawing_url': row[16],
            'artistic_illustration_url': row[17],
            'coloring_page_url': row[18],
            'drawing_labels': row[19]
        })
    
    cur.close()
    conn.close()
    
    return jsonify(results)

@bp.route('/download/<int:result_id>/<drawing_type>/<format>')
def download_drawing(result_id, drawing_type, format):
    """
    Download botanical drawing in specified format.
    
    Args:
        result_id: Database ID of botanist_vision_results
        drawing_type: 'scientific', 'labeled', 'artistic', or 'coloring'
        format: 'png', 'jpeg', or 'pdf'
    """
    # Get drawing from database
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    cur = conn.cursor()
    
    # Map drawing type to column name
    column_map = {
        'scientific': 'botanical_drawing_url',
        'labeled': 'labeled_drawing_url',
        'artistic': 'artistic_illustration_url',
        'coloring': 'coloring_page_url'
    }
    
    column_name = column_map.get(drawing_type)
    if not column_name:
        return jsonify({'error': 'Invalid drawing type'}), 400
    
    cur.execute(f"""
        SELECT {column_name}, ai_genus, ai_species
        FROM botanist_vision_results
        WHERE id = %s
    """, (result_id,))
    
    row = cur.fetchone()
    cur.close()
    conn.close()
    
    if not row or not row[0]:
        return jsonify({'error': 'Drawing not found'}), 404
    
    drawing_data_url = row[0]
    genus = row[1] or "Orchid"
    species = row[2] or "species"
    
    # Create filename
    filename_base = f"{genus}_{species}_{drawing_type}"
    
    # Decode base64 image
    if drawing_data_url.startswith('data:image'):
        image_data = drawing_data_url.split(',')[1]
        image_bytes = base64.b64decode(image_data)
    else:
        return jsonify({'error': 'Invalid image format'}), 400
    
    # Convert to requested format
    if format == 'png':
        return Response(
            image_bytes,
            mimetype='image/png',
            headers={'Content-Disposition': f'attachment; filename={filename_base}.png'}
        )
    
    elif format == 'jpeg':
        # Convert to JPEG
        img = Image.open(io.BytesIO(image_bytes))
        if img.mode == 'RGBA':
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[3])
            img = rgb_img
        
        jpeg_buffer = io.BytesIO()
        img.save(jpeg_buffer, format='JPEG', quality=95)
        jpeg_buffer.seek(0)
        
        return Response(
            jpeg_buffer.getvalue(),
            mimetype='image/jpeg',
            headers={'Content-Disposition': f'attachment; filename={filename_base}.jpg'}
        )
    
    elif format == 'pdf':
        # Create PDF with image
        img = Image.open(io.BytesIO(image_bytes))
        
        # Calculate PDF size to fit image
        img_width, img_height = img.size
        aspect_ratio = img_width / img_height
        
        # Standard letter size with margins
        pdf_buffer = io.BytesIO()
        c = canvas.Canvas(pdf_buffer, pagesize=letter)
        page_width, page_height = letter
        
        # Fit image to page with margins
        margin = 50
        available_width = page_width - 2 * margin
        available_height = page_height - 2 * margin
        
        if aspect_ratio > (available_width / available_height):
            # Width is limiting factor
            draw_width = available_width
            draw_height = available_width / aspect_ratio
        else:
            # Height is limiting factor
            draw_height = available_height
            draw_width = available_height * aspect_ratio
        
        # Center image on page
        x = (page_width - draw_width) / 2
        y = (page_height - draw_height) / 2
        
        # Save image to temp buffer
        temp_img_buffer = io.BytesIO()
        if img.mode == 'RGBA':
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[3])
            img = rgb_img
        img.save(temp_img_buffer, format='JPEG', quality=95)
        temp_img_buffer.seek(0)
        
        # Draw image on PDF
        c.drawImage(temp_img_buffer, x, y, width=draw_width, height=draw_height)
        
        # Add title
        c.setFont("Helvetica-Bold", 14)
        c.drawString(margin, page_height - 30, f"{genus} {species} - {drawing_type.title()} Drawing")
        
        # Add footer
        c.setFont("Helvetica", 10)
        c.drawString(margin, 30, "The Orchid Continuum - Digital Botanist Vision AI")
        c.drawString(page_width - 200, 30, "Rights-free botanical illustration")
        
        c.save()
        pdf_buffer.seek(0)
        
        return Response(
            pdf_buffer.getvalue(),
            mimetype='application/pdf',
            headers={'Content-Disposition': f'attachment; filename={filename_base}.pdf'}
        )
    
    else:
        return jsonify({'error': 'Invalid format. Use png, jpeg, or pdf'}), 400
