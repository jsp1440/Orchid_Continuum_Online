#!/usr/bin/env python3
"""
Vision AI Autonomous Agent
---------------------------
Analyzes existing orchid images in parallel using AI vision.
Works independently from Julius and enrichment agent.
"""

import os
import time
import json
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import base64
import requests

DATABASE_URL = os.environ.get("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

class VisionAIAgent:
    def __init__(self):
        self.session = Session()
        self.agent_name = "vision_ai"
        self.batch_size = 10  # Process 10 images at a time
        self.openai_api_key = os.environ.get("OPENAI_API_KEY")
        
    def log(self, message):
        """Print with timestamp"""
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [VISION AI] {message}")
        
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
            self.log(f"Posted to dashboard: {subject}")
        except Exception as e:
            self.log(f"Error posting to dashboard: {e}")
            self.session.rollback()
            
    def log_action(self, action_type, orchid_ids=None, notes=None):
        """Log enrichment action"""
        try:
            query = text("""
                INSERT INTO enrichment_actions_log (
                    performed_by, action_type, orchid_ids, notes
                ) VALUES (:by, :type, :ids, :notes)
            """)
            self.session.execute(query, {
                'by': self.agent_name,
                'type': action_type,
                'ids': orchid_ids,
                'notes': notes
            })
            self.session.commit()
        except Exception as e:
            self.log(f"Error logging action: {e}")
            self.session.rollback()
    
    def get_orchids_needing_vision_analysis(self, limit=100):
        """Get orchids with images but missing AI analysis"""
        query = text("""
            SELECT id, genus, species, scientific_name, image_url
            FROM orchid_record
            WHERE image_url IS NOT NULL
              AND (ai_description IS NULL OR ai_description = '')
            ORDER BY id
            LIMIT :limit
        """)
        result = self.session.execute(query, {'limit': limit})
        return [{'id': r.id, 'genus': r.genus, 'species': r.species, 
                 'scientific_name': r.scientific_name, 'image_url': r.image_url} 
                for r in result]
    
    def analyze_image_with_vision(self, image_url, scientific_name):
        """Analyze orchid image using OpenAI Vision API"""
        if not self.openai_api_key:
            return None, "No OpenAI API key available"
        
        try:
            # Construct full URL if relative path
            if image_url.startswith('/static'):
                image_url = f"https://{os.environ.get('REPL_SLUG')}.{os.environ.get('REPL_OWNER')}.repl.co{image_url}"
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.openai_api_key}"
            }
            
            payload = {
                "model": "gpt-4o",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"Analyze this orchid ({scientific_name}). Describe: flower color, shape, size, labellum characteristics, number of flowers, growth habit, and any unique features. Be specific and detailed for botanical identification."
                            },
                            {
                                "type": "image_url",
                                "image_url": {"url": image_url}
                            }
                        ]
                    }
                ],
                "max_tokens": 300
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                description = result['choices'][0]['message']['content']
                return description, None
            else:
                return None, f"API error: {response.status_code}"
                
        except Exception as e:
            return None, str(e)
    
    def process_batch(self, orchids):
        """Process a batch of orchids with vision analysis"""
        processed = 0
        errors = 0
        
        for orchid in orchids:
            self.log(f"Analyzing: {orchid['scientific_name']} (ID: {orchid['id']})")
            
            description, error = self.analyze_image_with_vision(
                orchid['image_url'],
                orchid['scientific_name']
            )
            
            if description:
                # Get old value for change tracking
                old_value_query = text("SELECT ai_description FROM orchid_record WHERE id = :id")
                old_result = self.session.execute(old_value_query, {'id': orchid['id']}).fetchone()
                old_value = old_result.ai_description if old_result else None
                
                # Update database with AI description
                update_query = text("""
                    UPDATE orchid_record
                    SET ai_description = :description,
                        ai_last_synced_at = CURRENT_TIMESTAMP
                    WHERE id = :orchid_id
                """)
                self.session.execute(update_query, {
                    'description': description,
                    'orchid_id': orchid['id']
                })
                self.session.commit()
                
                # Log database change
                change_log_query = text("""
                    INSERT INTO database_changes_log (
                        performed_by, operation_type, table_name, record_id,
                        field_name, old_value, new_value, orchid_scientific_name
                    ) VALUES (:by, :op, :table, :id, :field, :old, :new, :name)
                """)
                self.session.execute(change_log_query, {
                    'by': self.agent_name,
                    'op': 'UPDATE',
                    'table': 'orchid_record',
                    'id': orchid['id'],
                    'field': 'ai_description',
                    'old': old_value,
                    'new': description,
                    'name': orchid['scientific_name']
                })
                self.session.commit()
                
                # Log file operation (image analysis)
                file_log_query = text("""
                    INSERT INTO file_operations_log (
                        performed_by, operation_type, file_url, orchid_id, status
                    ) VALUES (:by, :op, :url, :id, :status)
                """)
                self.session.execute(file_log_query, {
                    'by': self.agent_name,
                    'op': 'image_analysis',
                    'url': orchid['image_url'],
                    'id': orchid['id'],
                    'status': 'success'
                })
                self.session.commit()
                
                # Log action
                self.log_action(
                    'vision_analysis',
                    orchid_ids=[orchid['id']],
                    notes=f"Vision AI analyzed {orchid['scientific_name']}: {description[:100]}..."
                )
                
                processed += 1
                self.log(f"✅ Analyzed successfully")
            else:
                errors += 1
                self.log(f"❌ Error: {error}")
            
            time.sleep(1)  # Rate limiting
        
        return processed, errors
    
    def run_vision_analysis(self, total_limit=100):
        """Run vision analysis on orchids"""
        self.post_to_dashboard(
            'status_update',
            'Vision AI Agent Started',
            f'Starting vision analysis on up to {total_limit} orchid images. Working in parallel with other agents.',
            {'agent': 'vision_ai', 'target_orchids': total_limit, 'batch_size': self.batch_size}
        )
        
        total_processed = 0
        total_errors = 0
        
        while total_processed < total_limit:
            # Get batch
            orchids = self.get_orchids_needing_vision_analysis(self.batch_size)
            
            if not orchids:
                self.log("No more orchids needing vision analysis")
                break
            
            # Process batch
            self.log(f"Processing batch of {len(orchids)} orchids...")
            processed, errors = self.process_batch(orchids)
            
            total_processed += processed
            total_errors += errors
            
            # Post progress update
            self.post_to_dashboard(
                'status_update',
                f'Vision AI Progress: {total_processed} analyzed',
                f'Completed {total_processed} orchids. {total_errors} errors. Continuing...',
                {
                    'processed': total_processed,
                    'errors': total_errors,
                    'remaining': total_limit - total_processed
                }
            )
            
            if total_processed >= total_limit:
                break
        
        # Final summary
        self.post_to_dashboard(
            'result',
            'Vision AI Analysis Complete',
            f'Vision AI completed analysis of {total_processed} orchids. {total_errors} errors encountered. AI descriptions added to database.',
            {
                'total_analyzed': total_processed,
                'total_errors': total_errors,
                'completion_status': 'success' if total_processed > 0 else 'failed'
            }
        )
        
        self.log(f"Vision analysis complete! Processed: {total_processed}, Errors: {total_errors}")
        self.session.close()

if __name__ == "__main__":
    agent = VisionAIAgent()
    agent.run_vision_analysis(total_limit=100)
