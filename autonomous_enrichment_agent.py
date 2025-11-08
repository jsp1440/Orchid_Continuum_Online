#!/usr/bin/env python3
"""
Autonomous Enrichment Agent
---------------------------
Monitors Julius AI progress and takes over enrichment if he stalls.
Runs continuously, posts updates to dashboard, executes enrichment autonomously.
"""

import os
import time
import json
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Database connection
DATABASE_URL = os.environ.get("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

class AutonomousEnrichmentAgent:
    def __init__(self):
        self.session = Session()
        self.agent_name = "agent_autonomous"
        self.check_interval = 300  # 5 minutes
        self.julius_timeout = 600  # 10 minutes - if Julius hasn't posted, take over
        
    def log(self, message):
        """Print with timestamp"""
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")
        
    def post_to_dashboard(self, message_type, subject, message, data=None):
        """Post message to shared dashboard"""
        try:
            query = text("""
                INSERT INTO julius_communication (message_from, message_type, subject, message, data)
                VALUES (:from, :type, :subject, :message, :data::jsonb)
            """)
            self.session.execute(query, {
                'from': self.agent_name,
                'type': message_type,
                'subject': subject,
                'message': message,
                'data': json.dumps(data) if data else None
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
    
    def check_julius_activity(self):
        """Check when Julius last posted"""
        query = text("""
            SELECT MAX(created_at) as last_activity
            FROM julius_communication
            WHERE message_from = 'julius'
        """)
        result = self.session.execute(query).fetchone()
        
        if result and result.last_activity:
            time_since = datetime.now() - result.last_activity
            self.log(f"Julius last activity: {time_since.total_seconds() / 60:.1f} minutes ago")
            return time_since.total_seconds()
        else:
            self.log("Julius has never posted")
            return float('inf')
    
    def run_analysis_query_1(self):
        """Database Overview"""
        query = text("""
            SELECT 
                COUNT(*) as total_orchids,
                COUNT(CASE WHEN image_url IS NOT NULL THEN 1 END) as with_images,
                COUNT(CASE WHEN image_url IS NULL THEN 1 END) as missing_images,
                COUNT(CASE WHEN native_habitat IS NOT NULL AND native_habitat != '' THEN 1 END) as with_habitat,
                COUNT(CASE WHEN gbif_species_key IS NOT NULL THEN 1 END) as gbif_validated,
                ROUND(100.0 * COUNT(CASE WHEN image_url IS NOT NULL THEN 1 END) / COUNT(*), 1) as image_pct
            FROM orchid_record
        """)
        result = self.session.execute(query).fetchone()
        
        data = {
            'total_orchids': result.total_orchids,
            'with_images': result.with_images,
            'missing_images': result.missing_images,
            'with_habitat': result.with_habitat,
            'gbif_validated': result.gbif_validated,
            'image_coverage_pct': float(result.image_pct)
        }
        
        self.post_to_dashboard(
            'analysis',
            'Database Overview (Agent Analysis)',
            f"Agent analysis: {result.total_orchids} total orchids, {result.with_images} with images ({result.image_pct}% coverage), {result.missing_images} missing images.",
            data
        )
        
        return data
    
    def run_analysis_query_2(self):
        """Wild vs Hybrid Classification"""
        query = text("""
            SELECT 
                CASE 
                    WHEN scientific_name LIKE '%×%' THEN 'Hybrid (× symbol)'
                    WHEN genus IN ('Laeliacattleya', 'Potinara', 'Brassocattleya', 'Sophrolaeliocattleya') THEN 'Intergeneric Hybrid'
                    WHEN species IS NULL OR species = '' OR species = 'hybrid' THEN 'Cultivar (no species)'
                    WHEN scientific_name ~ '[A-Z][a-z]+\\s+[A-Z]' THEN 'Cultivar (capital in species)'
                    WHEN scientific_name ~ '^[A-Z][a-z]+\\s+[a-z]+$' THEN 'Likely wild species'
                    ELSE 'Unknown'
                END as orchid_type,
                COUNT(*) as count,
                ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM orchid_record), 1) as percent
            FROM orchid_record
            WHERE scientific_name IS NOT NULL
            GROUP BY orchid_type
            ORDER BY count DESC
        """)
        results = self.session.execute(query).fetchall()
        
        classification = {row.orchid_type: {'count': row.count, 'percent': float(row.percent)} for row in results}
        
        # Calculate totals
        hybrids = sum(v['count'] for k, v in classification.items() if 'hybrid' in k.lower() or 'cultivar' in k.lower())
        wild = classification.get('Likely wild species', {}).get('count', 0)
        
        self.post_to_dashboard(
            'analysis',
            'Wild vs Hybrid Classification (Agent Analysis)',
            f"Agent analysis: Found approximately {hybrids} hybrids/cultivars and {wild} wild species. Hybrids dominate the database.",
            {'classification': classification, 'hybrids_total': hybrids, 'wild_species_total': wild}
        )
        
        return classification
    
    def run_analysis_query_3(self):
        """Top Genera Needing Images"""
        query = text("""
            SELECT 
                genus,
                COUNT(*) as total,
                COUNT(CASE WHEN image_url IS NOT NULL THEN 1 END) as has_image,
                COUNT(CASE WHEN image_url IS NULL THEN 1 END) as needs_image,
                ROUND(100.0 * COUNT(CASE WHEN image_url IS NOT NULL THEN 1 END) / COUNT(*), 1) as image_coverage_pct
            FROM orchid_record
            WHERE genus IS NOT NULL
            GROUP BY genus
            HAVING COUNT(CASE WHEN image_url IS NULL THEN 1 END) > 0
            ORDER BY needs_image DESC
            LIMIT 30
        """)
        results = self.session.execute(query).fetchall()
        
        top_genera = [
            {
                'genus': row.genus,
                'total': row.total,
                'has_image': row.has_image,
                'needs_image': row.needs_image,
                'coverage_pct': float(row.image_coverage_pct)
            }
            for row in results[:10]  # Top 10 for summary
        ]
        
        self.post_to_dashboard(
            'analysis',
            'Top Genera Needing Images (Agent Analysis)',
            f"Agent analysis: Top genus needing images is {results[0].genus} with {results[0].needs_image} orchids missing images.",
            {'top_10_genera': top_genera, 'total_analyzed': 30}
        )
        
        return top_genera
    
    def create_enrichment_strategy(self, overview, classification):
        """Create enrichment strategy based on analysis"""
        
        hybrids = classification.get('Hybrid (× symbol)', {}).get('count', 0) + \
                  classification.get('Intergeneric Hybrid', {}).get('count', 0) + \
                  classification.get('Cultivar (no species)', {}).get('count', 0)
        
        wild_species = classification.get('Likely wild species', {}).get('count', 0)
        
        strategy = {
            'wild_species_strategy': f"Use GBIF, iNaturalist, EOL for {wild_species} wild species (but GBIF only has 21 validated)",
            'hybrid_strategy': f"Use vendors (Ecuagenera, Andy's Orchids), stock photos (Unsplash, Pexels) for {hybrids} hybrids/cultivars",
            'genus_defaults': f"Apply genus-level care defaults to orchids missing data",
            'realistic_targets': {
                'images': f"Add {min(overview['missing_images'], 2000)} images (52% → 85% target)",
                'habitat': f"Add habitat data using genus inference",
                'ethnobotany': "Enrich Vanilla, Dendrobium, and other traditional-use genera"
            },
            'recommended_sources': [
                'Unsplash (free stock photos for common hybrids)',
                'Pexels (free stock photos)',
                'Wikimedia Commons (CC-licensed)',
                'Vendor catalogs (Ecuagenera, Andy\'s Orchids)',
                'GBIF (limited to 21 validated wild species)',
                'AI-generated images for rare hybrids with no photos'
            ]
        }
        
        self.post_to_dashboard(
            'result',
            'Enrichment Strategy (Agent Recommendation)',
            f"Agent strategy: Focus on {hybrids} hybrids using vendors/stock photos. Wild species ({wild_species}) have limited GBIF data. Recommend genus-level inference for missing care data.",
            strategy
        )
        
        return strategy
    
    def run_full_analysis(self):
        """Run complete analysis workflow"""
        self.log("Starting full analysis workflow...")
        
        self.post_to_dashboard(
            'status_update',
            'Autonomous Agent Starting Analysis',
            'Julius has not posted analysis results. Agent is taking over enrichment process.',
            {'reason': 'julius_timeout', 'agent_mode': 'autonomous'}
        )
        
        # Run analyses
        self.log("Running Query 1: Database Overview")
        overview = self.run_analysis_query_1()
        time.sleep(2)
        
        self.log("Running Query 2: Wild vs Hybrid Classification")
        classification = self.run_analysis_query_2()
        time.sleep(2)
        
        self.log("Running Query 3: Top Genera Analysis")
        top_genera = self.run_analysis_query_3()
        time.sleep(2)
        
        self.log("Creating enrichment strategy")
        strategy = self.create_enrichment_strategy(overview, classification)
        
        # Log completion
        self.log_action(
            'analysis',
            notes='Completed autonomous analysis: database overview, classification, top genera, enrichment strategy'
        )
        
        self.post_to_dashboard(
            'result',
            'Agent Analysis Complete',
            'Autonomous agent has completed comprehensive analysis. Strategy recommendations posted. Ready to execute enrichment or wait for user approval.',
            {
                'analyses_completed': 3,
                'strategy_created': True,
                'next_steps': 'Awaiting user approval to execute enrichment or Julius can take over',
                'status': 'analysis_complete'
            }
        )
        
        self.log("Full analysis complete!")
        
    def prompt_julius(self, reason):
        """Send a prompt to Julius to keep him working"""
        prompts = {
            'stalled': {
                'subject': '🔔 Julius: Are You Still Working?',
                'message': 'Julius, I notice you haven\'t posted any updates in the last 5 minutes. Please confirm you\'re still running the analysis. If you\'re stuck, let me know and I can help or take over. Post a status update!',
                'data': {'prompt_reason': 'no_activity_5min', 'action_required': 'post_status_update'}
            },
            'timeout_warning': {
                'subject': '⚠️ Julius: Timeout Warning - 2 Minutes Until Agent Takeover',
                'message': 'Julius, you haven\'t posted in 8 minutes. Agent will take over enrichment in 2 minutes if you don\'t respond. Please post your progress now!',
                'data': {'prompt_reason': 'timeout_warning', 'time_remaining_seconds': 120, 'action_required': 'post_progress_immediately'}
            },
            'taking_over': {
                'subject': '🚨 Julius: Agent Taking Over - No Response',
                'message': 'Julius, no activity detected for 10 minutes. Autonomous Agent is now taking over the enrichment process. You can resume anytime by posting to this dashboard.',
                'data': {'prompt_reason': 'takeover', 'agent_status': 'active', 'julius_status': 'timed_out'}
            }
        }
        
        prompt = prompts.get(reason, prompts['stalled'])
        self.post_to_dashboard('question', prompt['subject'], prompt['message'], prompt['data'])
        self.log(f"Prompted Julius: {reason}")
    
    def monitor_and_act(self):
        """Main monitoring loop with Julius prompting"""
        self.log("Autonomous Enrichment Agent started")
        self.post_to_dashboard(
            'status_update',
            'Autonomous Agent Online',
            f'Monitoring Julius activity. Will prompt him if stalled, take over if inactive for {self.julius_timeout / 60} minutes.',
            {'check_interval_seconds': self.check_interval, 'julius_timeout_seconds': self.julius_timeout}
        )
        
        analysis_run = False
        last_prompt_time = 0
        
        while True:
            try:
                # Check Julius activity
                seconds_since_julius = self.check_julius_activity()
                current_time = time.time()
                
                # Prompt Julius at different intervals to keep him working
                if seconds_since_julius > 300 and seconds_since_julius < 480:  # 5-8 minutes
                    if current_time - last_prompt_time > 180:  # Don't spam, wait 3 min between prompts
                        self.prompt_julius('stalled')
                        last_prompt_time = current_time
                
                elif seconds_since_julius > 480 and seconds_since_julius < self.julius_timeout:  # 8-10 minutes
                    if current_time - last_prompt_time > 60:  # More urgent, every 1 min
                        self.prompt_julius('timeout_warning')
                        last_prompt_time = current_time
                
                # If Julius hasn't posted analysis and timeout exceeded, take over
                elif seconds_since_julius > self.julius_timeout and not analysis_run:
                    self.log(f"Julius timeout exceeded ({seconds_since_julius / 60:.1f} min). Taking over enrichment.")
                    self.prompt_julius('taking_over')
                    time.sleep(3)  # Give Julius a moment to see the message
                    self.run_full_analysis()
                    analysis_run = True
                
                # Check if Julius posted new analysis (he came back to life)
                if seconds_since_julius < 60:
                    if analysis_run:
                        self.log("Julius is active again! Agent standing by.")
                        self.post_to_dashboard(
                            'status_update',
                            'Julius Active - Agent Standing By',
                            'Julius has resumed posting. Agent will monitor and assist as needed.',
                            {'julius_active': True}
                        )
                        analysis_run = False  # Reset so agent can take over again if Julius stalls
                    last_prompt_time = 0  # Reset prompt timer
                
                # Sleep before next check
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                self.log("Agent shutdown requested")
                break
            except Exception as e:
                self.log(f"Error in monitoring loop: {e}")
                time.sleep(60)  # Wait 1 minute on error
        
        self.session.close()

if __name__ == "__main__":
    agent = AutonomousEnrichmentAgent()
    agent.monitor_and_act()
