"""
Routes for Image Downloader System
Admin dashboard to download and manage 105,000+ orchid images

FIX #3: Added authentication requirement to all routes
"""

from flask import render_template, jsonify, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import app
import logging
from image_downloader_system import ImageDownloaderSystem, start_download_process
import threading

logger = logging.getLogger(__name__)

# Global download thread
download_thread = None
download_status = {
    'running': False,
    'current_source': None,
    'stats': {}
}

def admin_required(f):
    """Decorator to require admin access"""
    @login_required
    def decorated_function(*args, **kwargs):
        # Check if user is admin (customize based on your user model)
        if not hasattr(current_user, 'is_admin') or not current_user.is_admin:
            flash('Admin access required', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/admin/image-downloader')
@admin_required  # FIX #3: Require admin authentication
def image_downloader_dashboard():
    """Admin dashboard for downloading GBIF & EOL images"""
    return render_template('admin/image_downloader_dashboard.html')

@app.route('/api/admin/image-downloader/status')
@admin_required  # FIX #3: Require admin authentication
def get_download_status():
    """Get current download progress"""
    try:
        downloader = ImageDownloaderSystem()
        progress = downloader.get_download_progress()
        
        return jsonify({
            'success': True,
            'progress': progress,
            'is_running': download_status['running'],
            'current_source': download_status['current_source'],
            'stats': download_status['stats']
        })
    except Exception as e:
        logger.error(f"Error getting download status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/image-downloader/start', methods=['POST'])
@admin_required  # FIX #3: Require admin authentication
def start_image_download():
    """Start downloading images"""
    global download_thread, download_status
    
    if download_status['running']:
        return jsonify({
            'success': False,
            'error': 'Download already in progress'
        }), 400
    
    try:
        data = request.json or {}
        source = data.get('source', 'gbif')  # 'gbif', 'eol', or 'both'
        batch_size = data.get('batch_size', 50)
        limit = data.get('limit', None)  # For testing with small batches
        
        def run_download():
            global download_status
            download_status['running'] = True
            download_status['current_source'] = source
            
            try:
                stats = start_download_process(
                    source=source,
                    batch_size=batch_size,
                    limit=limit
                )
                download_status['stats'] = stats
            except Exception as e:
                logger.error(f"Download error: {e}")
                download_status['stats'] = {'error': str(e)}
            finally:
                download_status['running'] = False
                download_status['current_source'] = None
        
        download_thread = threading.Thread(target=run_download)
        download_thread.start()
        
        return jsonify({
            'success': True,
            'message': f'Started downloading {source} images',
            'source': source,
            'batch_size': batch_size,
            'limit': limit
        })
        
    except Exception as e:
        logger.error(f"Error starting download: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/image-downloader/test', methods=['POST'])
@admin_required  # FIX #3: Require admin authentication
def test_image_download():
    """Test download with just 5 images"""
    global download_thread, download_status
    
    if download_status['running']:
        return jsonify({
            'success': False,
            'error': 'Download already in progress'
        }), 400
    
    try:
        def run_test():
            global download_status
            download_status['running'] = True
            download_status['current_source'] = 'test'
            
            try:
                stats = start_download_process(
                    source='gbif',
                    batch_size=5,
                    limit=5  # Just 5 images for testing
                )
                download_status['stats'] = stats
            except Exception as e:
                logger.error(f"Test download error: {e}")
                download_status['stats'] = {'error': str(e)}
            finally:
                download_status['running'] = False
                download_status['current_source'] = None
        
        download_thread = threading.Thread(target=run_test)
        download_thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Started test download (5 images)'
        })
        
    except Exception as e:
        logger.error(f"Error starting test: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
