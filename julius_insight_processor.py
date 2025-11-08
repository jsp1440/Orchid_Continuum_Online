"""
Julius AI Insight Processor
Automatically converts Julius AI analysis into database enhancement actions
"""

import psycopg2
import os
import re
import json
from datetime import datetime
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class JuliusInsightProcessor:
    """
    Processes Julius AI insights and converts them into actionable database tasks
    """
    
    def __init__(self):
        self.db_url = os.environ.get('DATABASE_URL')
        self.conn = None
        
    def connect_db(self):
        """Connect to database"""
        self.conn = psycopg2.connect(self.db_url)
        logger.info("✅ Connected to database")
    
    def fetch_unprocessed_insights(self) -> List[Dict]:
        """Fetch Julius communications that haven't been processed"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT id, message, created_at
            FROM julius_communication
            WHERE processed_by_agent = FALSE
            AND message_from = 'Julius AI'
            ORDER BY created_at DESC
        """)
        
        insights = []
        for row in cursor.fetchall():
            insights.append({
                'id': row[0],
                'message': row[1],
                'created_at': row[2]
            })
        
        cursor.close()
        logger.info(f"📥 Found {len(insights)} unprocessed insights from Julius")
        return insights
    
    def parse_genus_priorities(self, message: str) -> List[Dict]:
        """
        Parse genus enrichment priorities from Julius message
        
        Looks for patterns like:
        - "Paphiopedilum has 45 species but only 12 images"
        - "Genus: Dendrobium, Gap Score: 78"
        - "Phalaenopsis - Missing 34 images"
        """
        priorities = []
        
        # Pattern 1: "Genus has X species but only Y images"
        pattern1 = re.finditer(r'(\w+)\s+has\s+(\d+)\s+species\s+but\s+only\s+(\d+)\s+images?', message, re.IGNORECASE)
        for match in pattern1:
            genus = match.group(1)
            species_count = int(match.group(2))
            image_count = int(match.group(3))
            gap_score = species_count - image_count
            
            priorities.append({
                'genus': genus,
                'priority_type': 'image_gap',
                'gap_score': gap_score,
                'details': f"{species_count} species, {image_count} images"
            })
        
        # Pattern 2: Table format "Genus | Species Count | Image Count | Gap Score"
        pattern2 = re.finditer(r'(\w+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)', message)
        for match in pattern2:
            genus = match.group(1)
            gap_score = int(match.group(4))
            
            priorities.append({
                'genus': genus,
                'priority_type': 'image_gap',
                'gap_score': gap_score,
                'details': f"Gap score: {gap_score}"
            })
        
        # Pattern 3: "Missing bloom data" or "Low enrichment"
        if 'bloom' in message.lower() and ('missing' in message.lower() or 'low' in message.lower()):
            bloom_genera = re.findall(r'\b([A-Z][a-z]+)\b', message)
            for genus in set(bloom_genera):
                priorities.append({
                    'genus': genus,
                    'priority_type': 'bloom_data',
                    'gap_score': 50,
                    'details': 'Missing phenological data'
                })
        
        # Pattern 4: Geographic gaps
        if 'geographic' in message.lower() or 'location' in message.lower():
            geo_genera = re.findall(r'\b([A-Z][a-z]+)\b.*?(\d+)%?\s*missing', message, re.IGNORECASE)
            for genus, percentage in geo_genera:
                priorities.append({
                    'genus': genus,
                    'priority_type': 'geographic_gap',
                    'gap_score': int(percentage),
                    'details': f"{percentage}% missing location data"
                })
        
        return priorities
    
    def create_scraper_priorities(self, priorities: List[Dict]):
        """Create priority tasks for the autonomous scraper"""
        cursor = self.conn.cursor()
        
        for priority in priorities:
            # Update scraper configuration to prioritize this genus
            cursor.execute("""
                INSERT INTO scraper_priorities (
                    genus, priority_type, priority_score, 
                    source, target_count, status, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (genus, priority_type) 
                DO UPDATE SET 
                    priority_score = EXCLUDED.priority_score,
                    updated_at = NOW()
            """, (
                priority['genus'],
                priority['priority_type'],
                priority['gap_score'],
                'julius_ai_insight',
                priority.get('target_count', 20),
                'queued'
            ))
            
            logger.info(f"  ✅ Created priority: {priority['genus']} ({priority['priority_type']}, score: {priority['gap_score']})")
        
        self.conn.commit()
        cursor.close()
    
    def create_enrichment_tasks(self, priorities: List[Dict]):
        """Create enrichment tasks based on Julius insights"""
        cursor = self.conn.cursor()
        
        for priority in priorities:
            if priority['priority_type'] in ['bloom_data', 'geographic_gap']:
                # Create enrichment task
                cursor.execute("""
                    INSERT INTO enrichment_queue (
                        genus, enrichment_type, priority, 
                        source, metadata, status, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, NOW())
                """, (
                    priority['genus'],
                    priority['priority_type'],
                    priority['gap_score'],
                    'julius_ai',
                    json.dumps({'details': priority['details']}),
                    'pending'
                ))
                
                logger.info(f"  ✅ Created enrichment: {priority['genus']} ({priority['priority_type']})")
        
        self.conn.commit()
        cursor.close()
    
    def mark_as_processed(self, insight_id: int, actions_taken: str):
        """Mark Julius insight as processed and log actions"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            UPDATE julius_communication
            SET 
                processed_by_agent = TRUE,
                agent_actions_taken = %s,
                processed_at = NOW()
            WHERE id = %s
        """, (actions_taken, insight_id))
        
        self.conn.commit()
        cursor.close()
        logger.info(f"  ✅ Marked insight {insight_id} as processed")
    
    def send_response_to_julius(self, insight_id: int, response: str):
        """Send agent's response back to Julius (via julius_communication)"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO julius_communication (
                message_from, message_type, subject, message, related_to_insight_id, created_at
            ) VALUES (%s, %s, %s, %s, %s, NOW())
        """, ('Autonomous Agent', 'response', 'Task Completion Report', response, insight_id))
        
        self.conn.commit()
        cursor.close()
    
    def process_insights(self):
        """Main processing loop"""
        logger.info("🤖 Julius Insight Processor starting...")
        
        self.connect_db()
        
        insights = self.fetch_unprocessed_insights()
        
        if not insights:
            logger.info("ℹ️  No new insights to process")
            return
        
        for insight in insights:
            logger.info(f"\n📊 Processing insight {insight['id']}...")
            logger.info(f"   Message preview: {insight['message'][:100]}...")
            
            # Parse for genus priorities
            priorities = self.parse_genus_priorities(insight['message'])
            
            if priorities:
                logger.info(f"   Found {len(priorities)} priorities:")
                
                # Create scraper priorities
                scraper_priorities = [p for p in priorities if p['priority_type'] == 'image_gap']
                if scraper_priorities:
                    self.create_scraper_priorities(scraper_priorities)
                
                # Create enrichment tasks
                enrichment_priorities = [p for p in priorities if p['priority_type'] != 'image_gap']
                if enrichment_priorities:
                    self.create_enrichment_tasks(enrichment_priorities)
                
                # Generate response
                actions_summary = f"Created {len(scraper_priorities)} scraper priorities, {len(enrichment_priorities)} enrichment tasks"
                
                response = f"""✅ Processed your analysis successfully!

Actions taken:
- {len(scraper_priorities)} genera prioritized for image collection
- {len(enrichment_priorities)} genera queued for data enrichment

Top priorities identified:
{chr(10).join([f"- {p['genus']}: {p['details']}" for p in priorities[:5]])}

The autonomous workers will now focus on these areas.
Estimated completion: 24-48 hours.

Will report back with results!"""
                
                # Mark as processed
                self.mark_as_processed(insight['id'], actions_summary)
                
                # Send response
                self.send_response_to_julius(insight['id'], response)
                
                logger.info(f"✅ Insight {insight['id']} processed successfully!")
            
            else:
                logger.info(f"⚠️  No actionable priorities found in insight {insight['id']}")
                self.mark_as_processed(insight['id'], "No actionable items detected")
        
        self.conn.close()
        logger.info("\n🎉 Processing complete!")

def create_required_tables():
    """Create tables needed for Julius insight processing"""
    conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
    cursor = conn.cursor()
    
    # Scraper priorities table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scraper_priorities (
            id SERIAL PRIMARY KEY,
            genus VARCHAR(100),
            priority_type VARCHAR(50),
            priority_score INTEGER,
            source VARCHAR(100),
            target_count INTEGER DEFAULT 20,
            status VARCHAR(50) DEFAULT 'queued',
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(genus, priority_type)
        );
    """)
    
    # Enrichment queue table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS enrichment_queue (
            id SERIAL PRIMARY KEY,
            genus VARCHAR(100),
            enrichment_type VARCHAR(50),
            priority INTEGER,
            source VARCHAR(100),
            metadata JSONB,
            status VARCHAR(50) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT NOW(),
            completed_at TIMESTAMP
        );
    """)
    
    # Update julius_communication table
    cursor.execute("""
        ALTER TABLE julius_communication 
        ADD COLUMN IF NOT EXISTS processed_by_agent BOOLEAN DEFAULT FALSE,
        ADD COLUMN IF NOT EXISTS agent_actions_taken TEXT,
        ADD COLUMN IF NOT EXISTS processed_at TIMESTAMP,
        ADD COLUMN IF NOT EXISTS related_to_insight_id INTEGER;
    """)
    
    conn.commit()
    cursor.close()
    conn.close()
    
    logger.info("✅ Required tables created/updated")

if __name__ == "__main__":
    # Create tables if needed
    create_required_tables()
    
    # Process insights
    processor = JuliusInsightProcessor()
    processor.process_insights()
