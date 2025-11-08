#!/usr/bin/env python3
"""
GBIF Image Download Agent
Downloads real orchid images from GBIF occurrence data
"""

import os
import time
import json
import requests
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

class GBIFImageDownloadAgent:
    def __init__(self):
        self.session = Session()
        self.agent_name = "gbif_image_downloader"
        
    def log(self, message):
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [GBIF IMAGE] {message}")
        
    def post_to_dashboard(self, message_type, subject, message, data=None):
        """Post message to shared dashboard"""
        try:
            if data:
                query = text("""
                    INSERT INTO julius_communication (message_from, message_type, subject, message, data)
                    VALUES (:from, :type, :subject, :message, :data::jsonb)
                """)
                self.session.execute(query, {
                    'from': self.agent_name,
                    'type': message_type,
                    'subject': subject,
                    'message': message,
                    'data': json.dumps(data)
                })
            else:
                query = text("""
                    INSERT INTO julius_communication (message_from, message_type, subject, message)
                    VALUES (:from, :type, :subject, :message)
                """)
                self.session.execute(query, {
                    'from': self.agent_name,
                    'type': message_type,
                    'subject': subject,
                    'message': message
                })
            self.session.commit()
            self.log(f"Posted: {subject}")
        except Exception as e:
            self.log(f"Dashboard post error: {e}")
            self.session.rollback()
    
    def get_orchids_needing_images(self, limit=50):
        """Get orchids without images that might have GBIF data"""
        query = text("""
            SELECT id, genus, species, scientific_name
            FROM orchid_record
            WHERE image_url IS NULL
              AND species IS NOT NULL 
              AND species != ''
              AND species NOT LIKE '%×%'
              AND scientific_name NOT LIKE '%×%'
            ORDER BY id
            LIMIT :limit
        """)
        result = self.session.execute(query, {'limit': limit})
        return [{'id': r.id, 'genus': r.genus, 'species': r.species, 
                 'scientific_name': r.scientific_name} for r in result]
    
    def search_gbif_image(self, scientific_name):
        """Search GBIF for images of this species"""
        try:
            # Search for occurrences with images
            url = "https://api.gbif.org/v1/occurrence/search"
            params = {
                'scientificName': scientific_name,
                'mediaType': 'StillImage',
                'limit': 5
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code != 200:
                return None, f"GBIF API error: {response.status_code}"
            
            data = response.json()
            
            if data.get('count', 0) == 0:
                return None, "No GBIF occurrences with images"
            
            # Get first occurrence with media
            for result in data.get('results', []):
                if 'media' in result and len(result['media']) > 0:
                    for media in result['media']:
                        if media.get('type') == 'StillImage':
                            image_url = media.get('identifier')
                            if image_url:
                                return {
                                    'url': image_url,
                                    'gbif_key': result.get('key'),
                                    'country': result.get('country'),
                                    'lat': result.get('decimalLatitude'),
                                    'lon': result.get('decimalLongitude')
                                }, None
            
            return None, "No images in GBIF results"
            
        except Exception as e:
            return None, str(e)
    
    def download_and_save_image(self, orchid, image_data):
        """Download image and update database"""
        try:
            # Update database with GBIF image URL
            update_query = text("""
                UPDATE orchid_record
                SET image_url = :url,
                    image_source = :source,
                    image_attribution = :attribution
                WHERE id = :id
            """)
            
            attribution = f"GBIF Occurrence {image_data['gbif_key']}"
            if image_data.get('country'):
                attribution += f" ({image_data['country']})"
            
            self.session.execute(update_query, {
                'url': image_data['url'],
                'source': 'GBIF',
                'attribution': attribution,
                'id': orchid['id']
            })
            self.session.commit()
            
            # Log file operation
            file_log = text("""
                INSERT INTO file_operations_log (
                    performed_by, operation_type, file_url, orchid_id, status
                ) VALUES (:by, :op, :url, :id, :status)
            """)
            self.session.execute(file_log, {
                'by': self.agent_name,
                'op': 'image_download',
                'url': image_data['url'],
                'id': orchid['id'],
                'status': 'success'
            })
            self.session.commit()
            
            # Log database change
            db_change = text("""
                INSERT INTO database_changes_log (
                    performed_by, operation_type, table_name, record_id,
                    field_name, old_value, new_value, orchid_scientific_name
                ) VALUES (:by, :op, :table, :id, :field, :old, :new, :name)
            """)
            self.session.execute(db_change, {
                'by': self.agent_name,
                'op': 'UPDATE',
                'table': 'orchid_record',
                'id': orchid['id'],
                'field': 'image_url',
                'old': None,
                'new': image_data['url'],
                'name': orchid['scientific_name']
            })
            self.session.commit()
            
            return True
            
        except Exception as e:
            self.log(f"Error saving image: {e}")
            self.session.rollback()
            return False
    
    def run(self, limit=50):
        """Main execution"""
        self.post_to_dashboard(
            'status_update',
            '🖼️ GBIF Image Downloader Started',
            f'Starting to download images from GBIF for up to {limit} orchids without images.'
        )
        
        orchids = self.get_orchids_needing_images(limit)
        self.log(f"Found {len(orchids)} orchids needing images")
        
        if not orchids:
            self.post_to_dashboard(
                'result',
                'No Orchids Need Images',
                'All orchids already have images or are hybrids without GBIF data.'
            )
            return
        
        downloaded = 0
        not_found = 0
        errors = 0
        
        for orchid in orchids:
            self.log(f"Searching GBIF for: {orchid['scientific_name']}")
            
            image_data, error = self.search_gbif_image(orchid['scientific_name'])
            
            if image_data:
                if self.download_and_save_image(orchid, image_data):
                    downloaded += 1
                    self.post_to_dashboard(
                        'result',
                        f"✅ Image Downloaded: {orchid['scientific_name']}",
                        f"Found and saved GBIF image. Country: {image_data.get('country', 'Unknown')}",
                        {'orchid_id': orchid['id'], 'gbif_key': image_data['gbif_key']}
                    )
                else:
                    errors += 1
            else:
                not_found += 1
                self.log(f"No image found: {error}")
            
            time.sleep(0.5)  # Rate limiting
        
        self.post_to_dashboard(
            'result',
            f'GBIF Image Download Complete: {downloaded} Images',
            f'Downloaded {downloaded} images from GBIF. {not_found} not found, {errors} errors.',
            {'downloaded': downloaded, 'not_found': not_found, 'errors': errors}
        )
        
        self.log(f"Complete! Downloaded: {downloaded}, Not found: {not_found}, Errors: {errors}")
        self.session.close()

if __name__ == "__main__":
    agent = GBIFImageDownloadAgent()
    agent.run(limit=50)
