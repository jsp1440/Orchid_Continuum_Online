#!/usr/bin/env python3
"""
Ethnobotany Enrichment Agent
Adds traditional uses, indigenous names, and cultural significance data
"""

import os
import time
import json
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# Ethnobotany knowledge base
ETHNOBOTANY_DATA = {
    'Vanilla': {
        'traditional_uses': ['Food flavoring', 'Perfume', 'Traditional medicine for fever'],
        'indigenous_names': {
            'Totonac': 'xanat',
            'Nahuatl': 'tlilxochitl',
            'Maya': 'sisbic'
        },
        'cultural_significance': 'Sacred to Totonac people of Mexico. Used in Aztec chocolate drinks and religious ceremonies.',
        'medicinal_uses': 'Traditional remedy for digestive issues, aphrodisiac properties',
        'regions': ['Mexico', 'Central America', 'Madagascar', 'Tahiti']
    },
    'Dendrobium': {
        'traditional_uses': ['Traditional Chinese Medicine (TCM)', 'Food additive', 'Herbal tea'],
        'indigenous_names': {
            'Chinese': 'shi hu (石斛)',
            'Japanese': 'sekkoku'
        },
        'cultural_significance': 'One of 50 fundamental herbs in TCM. Used for over 2000 years.',
        'medicinal_uses': 'Immune system support, anti-aging, kidney and stomach health',
        'regions': ['China', 'Japan', 'Southeast Asia', 'Australia']
    },
    'Gastrodia': {
        'traditional_uses': ['Traditional Chinese Medicine', 'Treatment for headaches and dizziness'],
        'indigenous_names': {
            'Chinese': 'tian ma (天麻)'
        },
        'cultural_significance': 'Highly valued in TCM, considered a tonic herb',
        'medicinal_uses': 'Headache relief, vertigo treatment, seizure control, neuroprotection',
        'regions': ['China', 'Japan', 'Korea']
    },
    'Phaius': {
        'traditional_uses': ['Ornamental', 'Traditional medicine in Southeast Asia'],
        'indigenous_names': {
            'Thai': 'กล้วยไม้พื้นดิน'
        },
        'cultural_significance': 'Used in traditional Thai and Vietnamese medicine',
        'medicinal_uses': 'Anti-inflammatory properties, wound healing',
        'regions': ['Southeast Asia', 'Pacific Islands']
    },
    'Cymbidium': {
        'traditional_uses': ['Traditional medicine', 'Cultural ceremonies', 'Perfume'],
        'indigenous_names': {
            'Chinese': 'lan hua (兰花)',
            'Japanese': 'ran'
        },
        'cultural_significance': 'Symbol of nobility and refinement in Chinese culture. One of the "Four Gentlemen" in Chinese art.',
        'medicinal_uses': 'Respiratory health, anti-inflammatory',
        'regions': ['China', 'Japan', 'India', 'Southeast Asia']
    },
    'Angraecum': {
        'traditional_uses': ['Traditional Madagascar medicine', 'Perfume'],
        'indigenous_names': {
            'Malagasy': 'faham'
        },
        'cultural_significance': 'Sacred in Madagascar traditional beliefs',
        'medicinal_uses': 'Digestive aid, respiratory health',
        'regions': ['Madagascar', 'Africa', 'Indian Ocean Islands']
    },
    'Bletilla': {
        'traditional_uses': ['Traditional Chinese Medicine', 'Wound healing paste'],
        'indigenous_names': {
            'Chinese': 'bai ji (白及)'
        },
        'cultural_significance': 'Important TCM herb for stopping bleeding',
        'medicinal_uses': 'Hemostatic (stops bleeding), wound healing, lung health',
        'regions': ['China', 'Japan', 'Korea']
    },
    'Spiranthes': {
        'traditional_uses': ['Native American medicine', 'Love charms'],
        'indigenous_names': {
            'Cherokee': 'Ladies tresses'
        },
        'cultural_significance': 'Used by Native Americans for various remedies',
        'medicinal_uses': 'Kidney health, urinary issues',
        'regions': ['North America', 'Europe', 'Asia']
    },
    'Orchis': {
        'traditional_uses': ['Salep (traditional drink)', 'Aphrodisiac', 'Nutritional supplement'],
        'indigenous_names': {
            'Turkish': 'salep',
            'Persian': 'sahlep'
        },
        'cultural_significance': 'Root tubers used to make salep drink in Middle East and Turkey',
        'medicinal_uses': 'Digestive health, energy boost, aphrodisiac',
        'regions': ['Mediterranean', 'Middle East', 'Turkey', 'Iran']
    },
    'Eulophia': {
        'traditional_uses': ['African traditional medicine', 'Food source (tubers)'],
        'indigenous_names': {
            'Swahili': 'kinanda'
        },
        'cultural_significance': 'Important in various African traditional healing practices',
        'medicinal_uses': 'Digestive issues, fertility, general health tonic',
        'regions': ['Sub-Saharan Africa', 'Madagascar', 'Asia']
    }
}

class EthnobotanyEnrichmentAgent:
    def __init__(self):
        self.session = Session()
        self.agent_name = "ethnobotany_agent"
        
    def log(self, message):
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ETHNOBOTANY] {message}")
        
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
    
    def get_orchids_for_ethnobotany(self):
        """Get orchids in genera with known ethnobotany data"""
        genera = list(ETHNOBOTANY_DATA.keys())
        placeholders = ','.join([f":genus{i}" for i in range(len(genera))])
        
        query = text(f"""
            SELECT id, genus, species, scientific_name
            FROM orchid_record
            WHERE genus IN ({placeholders})
              AND (ethnobotany_data IS NULL OR ethnobotany_data::text = '{{}}')
            ORDER BY genus, species
            LIMIT 200
        """)
        
        params = {f'genus{i}': genus for i, genus in enumerate(genera)}
        result = self.session.execute(query, params)
        return [{'id': r.id, 'genus': r.genus, 'species': r.species, 
                 'scientific_name': r.scientific_name} for r in result]
    
    def enrich_orchid(self, orchid):
        """Add ethnobotany data to orchid"""
        genus = orchid['genus']
        data = ETHNOBOTANY_DATA.get(genus)
        
        if not data:
            return False
        
        try:
            # Update with ethnobotany data
            update_query = text("""
                UPDATE orchid_record
                SET ethnobotany_data = :ethnobotany_data::jsonb,
                    ethnobotany_last_updated = CURRENT_TIMESTAMP
                WHERE id = :orchid_id
            """)
            
            self.session.execute(update_query, {
                'ethnobotany_data': json.dumps(data),
                'orchid_id': orchid['id']
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
                'field': 'ethnobotany_data',
                'old': None,
                'new': json.dumps(data)[:100] + '...',
                'name': orchid['scientific_name']
            })
            self.session.commit()
            
            return True
            
        except Exception as e:
            self.log(f"Error enriching {orchid['scientific_name']}: {e}")
            self.session.rollback()
            return False
    
    def run(self):
        """Main execution"""
        self.post_to_dashboard(
            'status_update',
            '🌿 Ethnobotany Agent Started',
            f'Adding traditional uses, indigenous names, and cultural significance for {len(ETHNOBOTANY_DATA)} genera.'
        )
        
        orchids = self.get_orchids_for_ethnobotany()
        self.log(f"Found {len(orchids)} orchids to enrich")
        
        if not orchids:
            self.post_to_dashboard(
                'result',
                'No Orchids Need Ethnobotany Data',
                'All relevant orchids already have ethnobotany data.'
            )
            return
        
        enriched_by_genus = {}
        total_enriched = 0
        
        for orchid in orchids:
            if self.enrich_orchid(orchid):
                genus = orchid['genus']
                enriched_by_genus[genus] = enriched_by_genus.get(genus, 0) + 1
                total_enriched += 1
                
                if total_enriched % 10 == 0:
                    self.post_to_dashboard(
                        'status_update',
                        f'Progress: {total_enriched} Orchids Enriched',
                        f'Added ethnobotany data to {total_enriched} orchids so far...'
                    )
        
        # Final summary
        summary_data = {
            'total_enriched': total_enriched,
            'by_genus': enriched_by_genus,
            'genera_covered': list(ETHNOBOTANY_DATA.keys())
        }
        
        self.post_to_dashboard(
            'result',
            f'✅ Ethnobotany Enrichment Complete: {total_enriched} Orchids',
            f'Added traditional uses, indigenous names, and cultural significance to {total_enriched} orchids across {len(enriched_by_genus)} genera.',
            summary_data
        )
        
        self.log(f"Complete! Enriched {total_enriched} orchids")
        self.session.close()

if __name__ == "__main__":
    agent = EthnobotanyEnrichmentAgent()
    agent.run()
