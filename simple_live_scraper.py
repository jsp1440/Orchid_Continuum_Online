"""
SIMPLE LIVE ORCHID SCRAPER
Shows real-time data coming through - genus, species, metadata
No memory crashes - processes one at a time
"""

from flask import Blueprint, render_template, jsonify, Response
from admin_system import admin_required
import requests
import json
import time
from datetime import datetime
from app import db
from models import OrchidRecord

simple_scraper_bp = Blueprint('simple_scraper', __name__)

class SimpleLiveScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'OrchidContinuum/1.0'})
    
    def stream_gbif_orchids(self):
        """Stream GBIF orchids one by one with full metadata"""
        offset = 0
        
        while offset < 10000:  # Get 10,000 images
            try:
                response = self.session.get(
                    'https://api.gbif.org/v1/occurrence/search',
                    params={
                        'familyKey': 157167872,  # Orchidaceae
                        'mediaType': 'StillImage',
                        'hasCoordinate': 'true',
                        'limit': 20,
                        'offset': offset
                    },
                    timeout=15
                )
                
                if response.status_code != 200:
                    yield f"data: {json.dumps({'error': f'GBIF error: {response.status_code}'})}\n\n"
                    break
                
                data = response.json()
                results = data.get('results', [])
                
                if not results:
                    yield f"data: {json.dumps({'complete': True, 'total': offset})}\n\n"
                    break
                
                for occ in results:
                    if 'media' in occ and occ['media']:
                        # Extract data
                        genus = occ.get('genus', 'Unknown')
                        species = occ.get('species', 'Unknown')
                        scientific_name = occ.get('scientificName', f'{genus} {species}')
                        country = occ.get('country', 'Unknown')
                        lat = occ.get('decimalLatitude')
                        lon = occ.get('decimalLongitude')
                        image_url = occ['media'][0].get('identifier') if occ['media'] else None
                        
                        # Create/update record immediately
                        orchid = OrchidRecord.query.filter_by(scientific_name=scientific_name).first()
                        if not orchid:
                            orchid = OrchidRecord()
                            orchid.scientific_name = scientific_name
                            orchid.display_name = scientific_name
                            orchid.genus = genus
                            orchid.species = species
                            orchid.country = country
                            orchid.decimal_latitude = lat
                            orchid.decimal_longitude = lon
                            orchid.ingestion_source = 'GBIF_Live'
                            orchid.image_url = image_url
                            
                            db.session.add(orchid)
                            db.session.commit()
                            
                            # Stream to frontend
                            data_dict = {
                                'id': orchid.id,
                                'genus': genus,
                                'species': species,
                                'scientific_name': scientific_name,
                                'country': country,
                                'lat': lat,
                                'lon': lon,
                                'image_url': image_url,
                                'timestamp': datetime.now().isoformat(),
                                'total_processed': offset + len(results)
                            }
                            yield f"data: {json.dumps(data_dict)}\n\n"
                        
                        time.sleep(0.1)  # Small delay
                
                offset += 20
                
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                time.sleep(1)

@simple_scraper_bp.route('/admin/live-scraper')
@admin_required
def live_scraper_page():
    """Live scraper dashboard"""
    from models import OrchidRecord
    total = db.session.query(db.func.count(OrchidRecord.id)).scalar() or 0
    return render_template('live_scraper.html', total_orchids=total)

@simple_scraper_bp.route('/admin/stream-orchids')
@admin_required
def stream_orchids():
    """SSE endpoint for live orchid streaming"""
    scraper = SimpleLiveScraper()
    return Response(
        scraper.stream_gbif_orchids(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )

@simple_scraper_bp.route('/admin/api/current-count')
@admin_required
def current_count():
    """Get current orchid count"""
    total = db.session.query(db.func.count(OrchidRecord.id)).scalar() or 0
    return jsonify({'total': total})
