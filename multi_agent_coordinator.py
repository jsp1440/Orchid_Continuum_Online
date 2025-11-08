#!/usr/bin/env python3
"""
Multi-Agent Coordinator
-----------------------
Coordinates Julius AI, Enrichment Agent, and Vision AI Agent.
Manages knowledge sharing, prevents conflicts, ensures progress.
"""

import os
import time
import json
import subprocess
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

class MultiAgentCoordinator:
    def __init__(self):
        self.session = Session()
        self.coordinator_name = "coordinator"
        self.agents = {
            'julius': {'status': 'unknown', 'last_activity': None, 'task': 'data_enrichment'},
            'enrichment_agent': {'status': 'unknown', 'last_activity': None, 'task': 'database_analysis'},
            'vision_ai': {'status': 'unknown', 'last_activity': None, 'task': 'image_analysis'}
        }
        self.check_interval = 300  # 5 minutes
        
    def log(self, message):
        """Print with timestamp"""
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [COORDINATOR] {message}")
        
    def post_to_dashboard(self, message_type, subject, message, data=None):
        """Post message to shared dashboard"""
        try:
            query = text("""
                INSERT INTO julius_communication (message_from, message_type, subject, message, data)
                VALUES (:from, :type, :subject, :message, :data::jsonb)
            """)
            self.session.execute(query, {
                'from': self.coordinator_name,
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
    
    def check_agent_activity(self, agent_name):
        """Check when agent last posted"""
        query = text("""
            SELECT MAX(created_at) as last_activity
            FROM julius_communication
            WHERE message_from = :agent
        """)
        result = self.session.execute(query, {'agent': agent_name}).fetchone()
        
        if result and result.last_activity:
            return result.last_activity
        return None
    
    def get_recent_discoveries(self, agent_name, hours=1):
        """Get recent discoveries from an agent"""
        query = text("""
            SELECT subject, message, data
            FROM julius_communication
            WHERE message_from = :agent
              AND message_type IN ('result', 'analysis')
              AND created_at > NOW() - INTERVAL ':hours hours'
            ORDER BY created_at DESC
            LIMIT 5
        """)
        result = self.session.execute(query, {'agent': agent_name, 'hours': hours})
        return [{'subject': r.subject, 'message': r.message, 'data': r.data} for r in result]
    
    def share_knowledge(self, from_agent, to_agent, discovery):
        """Share knowledge between agents"""
        self.post_to_dashboard(
            'status_update',
            f'Knowledge Share: {from_agent} → {to_agent}',
            f'Coordinator sharing discovery from {from_agent} with {to_agent}: {discovery["subject"]}',
            {
                'from_agent': from_agent,
                'to_agent': to_agent,
                'discovery': discovery,
                'action': 'knowledge_transfer'
            }
        )
        self.log(f"Shared knowledge: {from_agent} → {to_agent}")
    
    def coordinate_agents(self):
        """Main coordination loop"""
        self.log("Multi-Agent Coordinator started")
        self.post_to_dashboard(
            'status_update',
            'Multi-Agent Coordinator Online',
            'Coordinating Julius AI, Enrichment Agent, and Vision AI. Ensuring parallel progress and knowledge sharing.',
            {
                'agents_monitored': list(self.agents.keys()),
                'coordination_mode': 'active'
            }
        )
        
        while True:
            try:
                self.log("Checking agent status...")
                
                # Check each agent's activity
                for agent_name in self.agents:
                    last_activity = self.check_agent_activity(agent_name)
                    
                    if last_activity:
                        time_since = datetime.now() - last_activity
                        self.agents[agent_name]['last_activity'] = last_activity
                        
                        if time_since.total_seconds() < 300:  # Active in last 5 min
                            self.agents[agent_name]['status'] = 'active'
                            self.log(f"{agent_name}: ACTIVE ({time_since.total_seconds() / 60:.1f} min ago)")
                        else:
                            self.agents[agent_name]['status'] = 'stalled'
                            self.log(f"{agent_name}: STALLED ({time_since.total_seconds() / 60:.1f} min ago)")
                    else:
                        self.agents[agent_name]['status'] = 'never_active'
                        self.log(f"{agent_name}: NEVER ACTIVE")
                
                # Knowledge sharing: If one agent found something useful, share with others
                for agent_name in self.agents:
                    if self.agents[agent_name]['status'] == 'active':
                        discoveries = self.get_recent_discoveries(agent_name, hours=1)
                        
                        if discoveries:
                            # Share with other agents
                            for other_agent in self.agents:
                                if other_agent != agent_name:
                                    for discovery in discoveries:
                                        if 'image' in discovery['subject'].lower() or 'source' in discovery['subject'].lower():
                                            self.share_knowledge(agent_name, other_agent, discovery)
                
                # Check if ANY agent is making progress
                any_active = any(a['status'] == 'active' for a in self.agents.values())
                
                if not any_active:
                    self.post_to_dashboard(
                        'question',
                        '🚨 ALL AGENTS STALLED - Intervention Needed',
                        'No agents are currently active. All have stalled. Coordinator recommends: 1) Trigger autonomous agent analysis, 2) Check Julius connection, 3) Start Vision AI manually.',
                        {
                            'agents_stalled': [k for k, v in self.agents.items() if v['status'] in ['stalled', 'never_active']],
                            'recommendation': 'manual_intervention'
                        }
                    )
                    self.log("⚠️ ALL AGENTS STALLED - Posted alert")
                
                # Post status summary
                active_count = sum(1 for a in self.agents.values() if a['status'] == 'active')
                self.post_to_dashboard(
                    'status_update',
                    f'Coordinator Status: {active_count}/3 Agents Active',
                    f'Active agents: {active_count}/3. ' + ', '.join([f"{k}: {v['status']}" for k, v in self.agents.items()]),
                    {
                        'agents_status': self.agents,
                        'active_count': active_count,
                        'timestamp': datetime.now().isoformat()
                    }
                )
                
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                self.log("Coordinator shutdown requested")
                break
            except Exception as e:
                self.log(f"Error in coordination loop: {e}")
                time.sleep(60)
        
        self.session.close()

if __name__ == "__main__":
    coordinator = MultiAgentCoordinator()
    coordinator.coordinate_agents()
