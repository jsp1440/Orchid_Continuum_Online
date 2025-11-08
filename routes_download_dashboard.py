"""
Real-Time Orchid Image Download Dashboard
Tracks progress across all 6 download sources + botanical plates
"""
import os
import glob
from flask import Blueprint, render_template, jsonify
from datetime import datetime
from app import db

dashboard_bp = Blueprint('download_dashboard', __name__)

DOWNLOAD_DIR = os.path.expanduser("~/orchid_downloads")

@dashboard_bp.route('/download-dashboard')
def download_dashboard():
    """Main dashboard page"""
    return render_template('download_dashboard.html')

@dashboard_bp.route('/api/download-stats')
def download_stats():
    """API endpoint returning real-time download statistics"""
    
    stats = {
        'sources': [],
        'total_images': 0,
        'total_size_mb': 0,
        'last_updated': datetime.now().isoformat()
    }
    
    # Define all download sources
    sources = [
        {'name': 'EOL Batch 1', 'folder': 'eol_batch1', 'target': 20000, 'color': '#3b82f6'},
        {'name': 'EOL Batch 2', 'folder': 'eol_batch2', 'target': 20000, 'color': '#10b981'},
        {'name': 'GBIF', 'folder': 'gbif_images', 'target': 50000, 'color': '#f59e0b'},
        {'name': 'iNaturalist', 'folder': 'inaturalist_images', 'target': 10000, 'color': '#8b5cf6'},
        {'name': 'iDigBio', 'folder': 'idigbio_images', 'target': 5000, 'color': '#ec4899'},
        {'name': 'Wikimedia Plates', 'folder': 'wikimedia_plates', 'target': 1000, 'color': '#06b6d4'},
        {'name': 'ALA Australia', 'folder': 'ala_australia', 'target': 15000, 'color': '#14b8a6'},
    ]
    
    for source in sources:
        folder_path = os.path.join(DOWNLOAD_DIR, source['folder'])
        
        # Count images
        image_count = 0
        total_size = 0
        
        if os.path.exists(folder_path):
            # Count JPG files
            jpg_files = glob.glob(os.path.join(folder_path, '*.jpg'))
            image_count = len(jpg_files)
            
            # Calculate total size
            for jpg_file in jpg_files:
                try:
                    total_size += os.path.getsize(jpg_file)
                except:
                    pass
        
        size_mb = total_size / (1024 * 1024)
        progress = (image_count / source['target'] * 100) if source['target'] > 0 else 0
        
        stats['sources'].append({
            'name': source['name'],
            'folder': source['folder'],
            'count': image_count,
            'target': source['target'],
            'size_mb': round(size_mb, 2),
            'progress': round(progress, 1),
            'color': source['color'],
            'status': 'complete' if progress >= 100 else ('active' if image_count > 0 else 'pending')
        })
        
        stats['total_images'] += image_count
        stats['total_size_mb'] += size_mb
    
    stats['total_size_mb'] = round(stats['total_size_mb'], 2)
    stats['total_size_gb'] = round(stats['total_size_mb'] / 1024, 2)
    
    # Calculate overall progress
    total_target = sum(s['target'] for s in sources)
    stats['overall_progress'] = round((stats['total_images'] / total_target * 100), 1) if total_target > 0 else 0
    
    return jsonify(stats)


@dashboard_bp.route('/api/comprehensive-stats')
def comprehensive_stats():
    """
    Comprehensive orchid image statistics for Julius AI monitoring
    Includes database counts + Replit server downloads + Mac downloads
    """
    stats = {
        'timestamp': datetime.now().isoformat(),
        'mission': 'Complete coverage of all orchid taxa',
        'target_species': 28000,
        'target_images': 2000000,
        'sources': {}
    }
    
    # Database images count
    try:
        db_count = db.session.execute(db.text("SELECT COUNT(*) as count FROM orchid_images")).scalar()
        stats['database_images'] = db_count or 0
    except:
        stats['database_images'] = 0
    
    # Replit server images (botanical illustrations + downloads)
    replit_dir = "attached_assets/orchid_images"
    replit_count = 0
    replit_size_mb = 0
    
    if os.path.exists(replit_dir):
        jpg_files = glob.glob(os.path.join(replit_dir, '*.jpg'))
        replit_count = len(jpg_files)
        replit_size_mb = sum(os.path.getsize(f) for f in jpg_files) / (1024 * 1024)
    
    stats['replit_server_images'] = replit_count
    stats['replit_server_size_mb'] = round(replit_size_mb, 2)
    
    # Mac downloads (from user's Mac)
    mac_dir = os.path.expanduser("~/orchid_downloads")
    mac_stats = {}
    mac_total = 0
    
    mac_sources = {
        'gbif_images': 'GBIF',
        'inaturalist_images': 'iNaturalist',
        'eol_batch1': 'EOL Batch 1',
        'eol_batch2': 'EOL Batch 2',
        'ala_australia': 'ALA Australia',
        'idigbio_images': 'iDigBio',
        'wikimedia_plates': 'Wikimedia Plates'
    }
    
    for folder, name in mac_sources.items():
        folder_path = os.path.join(mac_dir, folder)
        count = 0
        if os.path.exists(folder_path):
            count = len(glob.glob(os.path.join(folder_path, '*.jpg')))
        mac_stats[name] = count
        mac_total += count
    
    stats['mac_downloads'] = mac_stats
    stats['mac_total_images'] = mac_total
    
    # Overall totals
    stats['total_images'] = stats['database_images'] + replit_count + mac_total
    stats['coverage_percent'] = round((stats['total_images'] / stats['target_images']) * 100, 2)
    
    # Breakdown by type
    stats['by_type'] = {
        'database': stats['database_images'],
        'botanical_illustrations': replit_count,
        'mac_downloaded': mac_total
    }
    
    # Available sources (not yet downloaded)
    stats['available_sources'] = {
        'GBIF': '2,422,409 records with images',
        'ALA Australia': '297,891 records with images',
        'EOL': '~500,000 orchid images',
        'Wikimedia Commons': 'Thousands of botanical plates',
        'Internet Archive': '100+ orchid books with plates'
    }
    
    # Current progress toward Gary Yong Gee partnership
    stats['gary_yong_gee_partnership'] = {
        'target_images': 100000,
        'target_species': 3500,
        'current_images': stats['total_images'],
        'coverage_increase': f"1.5% → {round((stats['total_images'] / stats['target_species']) * 100 / 28000 * 100, 1)}%"
    }
    
    return jsonify(stats)
