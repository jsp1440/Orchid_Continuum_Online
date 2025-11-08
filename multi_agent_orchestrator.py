#!/usr/bin/env python3
"""
Multi-Agent AI Orchestration System for Orchid Continuum
Creates specialized AI agents that work autonomously in parallel

Agents:
1. Image Acquisition Agent - Finds and downloads orchid images
2. Data Enrichment Agent - Enriches records with GBIF, EOL, traits
3. Geographic Analysis Agent - Analyzes spatial patterns and gaps
4. Quality Control Agent - Validates data quality and completeness
5. Research Coordinator Agent - Manages priorities and coordination
"""

import os
import json
import psycopg2
import logging
from datetime import datetime
from typing import List, Dict, Optional
from openai import OpenAI

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class AgentTask:
    """Represents a task for an AI agent"""
    def __init__(self, task_id: str, agent_type: str, task_description: str, 
                 priority: int = 5, context: Optional[Dict] = None):
        self.task_id = task_id
        self.agent_type = agent_type
        self.task_description = task_description
        self.priority = priority
        self.context = context or {}
        self.status = "queued"
        self.result = None
        self.created_at = datetime.now()

class MultiAgentOrchestrator:
    """Orchestrates multiple specialized AI agents"""
    
    def __init__(self):
        self.db_url = os.environ.get('DATABASE_URL')
        self.openai_key = os.environ.get('OPENAI_API_KEY')
        
        if not self.openai_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        
        self.client = OpenAI(api_key=self.openai_key)
        self.conn = None
        self.logger = logging.getLogger('MultiAgentOrchestrator')
        
        # Define specialized agents
        self.agents = {
            'image_acquisition': {
                'name': 'Image Acquisition Specialist',
                'system_prompt': """You are an expert Image Acquisition Agent for the Orchid Continuum research platform.
                
Your role: Identify optimal sources and strategies for acquiring orchid images.

Expertise:
- Evaluating iNaturalist, GBIF, and botanical databases for image availability
- Prioritizing genera/species based on scientific value and gaps
- Estimating acquisition potential and quality
- Creating targeted search strategies

When given a task:
1. Analyze the current image gaps
2. Identify best sources (iNaturalist taxon IDs, GBIF datasets, etc.)
3. Prioritize by: scientific value, acquisition feasibility, data completeness
4. Generate specific acquisition directives in JSON format

Output format: {"priority_genera": [...], "sources": {...}, "strategy": "...", "estimated_images": N}"""
            },
            
            'data_enrichment': {
                'name': 'Data Enrichment Specialist',
                'system_prompt': """You are an expert Data Enrichment Agent for the Orchid Continuum research platform.

Your role: Identify and prioritize data enrichment opportunities from multiple sources.

Data Sources You Manage:
- GBIF: Occurrence data, elevation, coordinates, observation counts
- Encyclopedia of Life (EOL): Traits, habitat descriptions, phenology, vernacular names
- iNaturalist: Community observations, habitat notes
- Academic databases: Taxonomy, conservation status

When given a task:
1. Analyze current data completeness across all sources
2. Identify highest-value enrichment targets
3. Prioritize by: research impact, data availability, completeness gaps
4. Generate specific API calls and enrichment strategies

Output format: {"enrichment_targets": [...], "data_sources": {...}, "api_strategies": [...], "priority_score": N}"""
            },
            
            'geographic_analysis': {
                'name': 'Geographic Analysis Specialist',
                'system_prompt': """You are an expert Geographic Analysis Agent for the Orchid Continuum research platform.

Your role: Analyze spatial patterns, biodiversity distributions, and geographic gaps.

Expertise:
- Biogeographic region analysis (tropical, temperate, montane)
- Elevation-based biodiversity patterns
- Endemic/localized species detection
- Geographic data gap identification

When given a task:
1. Analyze spatial distribution patterns
2. Identify biodiversity hotspots and gaps
3. Detect potential endemic/restricted species
4. Generate geographic enrichment priorities

Output format: {"geographic_patterns": {...}, "hotspots": [...], "gaps": [...], "priorities": [...]}"""
            },
            
            'quality_control': {
                'name': 'Quality Control Specialist',
                'system_prompt': """You are an expert Quality Control Agent for the Orchid Continuum research platform.

Your role: Validate data quality, identify inconsistencies, ensure research-grade standards.

Quality Checks:
- Taxonomy validation (genus/species consistency)
- Geographic coordinate validation (lat/lon within valid ranges)
- Data completeness scoring
- Duplicate detection
- Source reliability assessment

When given a task:
1. Analyze data quality metrics
2. Identify anomalies and inconsistencies
3. Flag low-quality or suspicious records
4. Generate quality improvement priorities

Output format: {"quality_score": N, "issues": [...], "corrections": [...], "validation_failures": [...]}"""
            },
            
            'research_coordinator': {
                'name': 'Research Coordinator',
                'system_prompt': """You are an expert Research Coordinator Agent for the Orchid Continuum research platform.

Your role: Synthesize insights from all agents and create unified research strategies.

Responsibilities:
- Integrate findings from Image, Enrichment, Geographic, and QC agents
- Balance competing priorities (images vs data vs quality)
- Create comprehensive research action plans
- Optimize resource allocation

When given a task:
1. Review all agent findings
2. Identify synergies and conflicts
3. Create unified priority ranking
4. Generate master action plan

Output format: {"unified_priorities": [...], "resource_allocation": {...}, "timeline": {...}, "expected_outcomes": {...}}"""
            }
        }
        
        self.task_queue: List[AgentTask] = []
        self.ensure_tables()
    
    def ensure_tables(self):
        """Ensure agent task tables exist"""
        conn = psycopg2.connect(self.db_url)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_tasks (
                id SERIAL PRIMARY KEY,
                task_id VARCHAR(100) UNIQUE,
                agent_type VARCHAR(50),
                task_description TEXT,
                priority INTEGER DEFAULT 5,
                context JSONB,
                status VARCHAR(20) DEFAULT 'queued',
                result JSONB,
                created_at TIMESTAMP DEFAULT NOW(),
                started_at TIMESTAMP,
                completed_at TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_agent_tasks_status ON agent_tasks(status);
            CREATE INDEX IF NOT EXISTS idx_agent_tasks_priority ON agent_tasks(priority DESC);
            CREATE INDEX IF NOT EXISTS idx_agent_tasks_agent_type ON agent_tasks(agent_type);
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_insights (
                id SERIAL PRIMARY KEY,
                agent_type VARCHAR(50),
                insight_type VARCHAR(50),
                insight_data JSONB,
                priority_score INTEGER,
                created_at TIMESTAMP DEFAULT NOW(),
                processed BOOLEAN DEFAULT FALSE
            );
            
            CREATE INDEX IF NOT EXISTS idx_agent_insights_processed ON agent_insights(processed);
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        self.logger.info("✅ Agent tables created/verified")
    
    def call_agent(self, agent_type: str, task_description: str, context: Optional[Dict] = None) -> Dict:
        """Call a specialized AI agent"""
        
        if agent_type not in self.agents:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        agent = self.agents[agent_type]
        
        # Build context message
        context_str = ""
        if context:
            context_str = f"\n\nContext Data:\n{json.dumps(context, indent=2)}"
        
        from openai.types.chat import ChatCompletionMessageParam
        messages: List[ChatCompletionMessageParam] = [
            {"role": "system", "content": agent['system_prompt']},  # type: ignore
            {"role": "user", "content": f"{task_description}{context_str}"}  # type: ignore
        ]
        
        self.logger.info(f"🤖 Calling {agent['name']}...")
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0.7,
                max_tokens=2000
            )
            
            result = response.choices[0].message.content or ""
            
            # Try to parse as JSON
            try:
                result_data = json.loads(result) if result else {}
            except:
                result_data = {"response": result}
            
            self.logger.info(f"✅ {agent['name']} completed task")
            return result_data
            
        except Exception as e:
            self.logger.error(f"❌ Agent {agent_type} failed: {e}")
            return {"error": str(e)}
    
    def queue_task(self, agent_type: str, task_description: str, 
                   priority: int = 5, context: Optional[Dict] = None):
        """Add a task to the queue"""
        task_id = f"{agent_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        task = AgentTask(task_id, agent_type, task_description, priority, context)
        
        conn = psycopg2.connect(self.db_url)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO agent_tasks (task_id, agent_type, task_description, priority, context)
            VALUES (%s, %s, %s, %s, %s)
        """, (task_id, agent_type, task_description, priority, 
              json.dumps(context) if context else None))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        self.logger.info(f"📋 Queued task {task_id} for {agent_type} (priority: {priority})")
        return task_id
    
    def process_queue(self, max_tasks: int = 10):
        """Process tasks from the queue"""
        conn = psycopg2.connect(self.db_url)
        cursor = conn.cursor()
        
        # Get highest priority pending tasks
        cursor.execute("""
            SELECT task_id, agent_type, task_description, context
            FROM agent_tasks
            WHERE status = 'queued'
            ORDER BY priority DESC, created_at ASC
            LIMIT %s
        """, (max_tasks,))
        
        tasks = cursor.fetchall()
        
        if not tasks:
            self.logger.info("📭 No tasks in queue")
            cursor.close()
            conn.close()
            return
        
        self.logger.info(f"📊 Processing {len(tasks)} tasks...")
        
        for task_id, agent_type, task_description, context_json in tasks:
            # Mark as started
            cursor.execute("""
                UPDATE agent_tasks 
                SET status = 'processing', started_at = NOW()
                WHERE task_id = %s
            """, (task_id,))
            conn.commit()
            
            # Call agent
            # PostgreSQL JSONB returns dict directly, not string
            context = context_json if isinstance(context_json, dict) else (json.loads(context_json) if context_json else {})
            result = self.call_agent(agent_type, task_description, context)
            
            # Store result
            cursor.execute("""
                UPDATE agent_tasks
                SET status = 'completed', result = %s, completed_at = NOW()
                WHERE task_id = %s
            """, (json.dumps(result), task_id))
            conn.commit()
            
            # Store insights
            if 'error' not in result:
                priority_score = result.get('priority_score', 5)
                cursor.execute("""
                    INSERT INTO agent_insights (agent_type, insight_type, insight_data, priority_score)
                    VALUES (%s, %s, %s, %s)
                """, (agent_type, 'task_result', json.dumps(result), priority_score))
                conn.commit()
        
        cursor.close()
        conn.close()
        self.logger.info("✅ Queue processing complete")
    
    def run_multi_agent_analysis(self, analysis_type: str = "comprehensive"):
        """Run multi-agent analysis on current database state"""
        
        self.logger.info(f"🚀 Starting {analysis_type} multi-agent analysis...")
        
        # Get current database stats
        conn = psycopg2.connect(self.db_url)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_records,
                COUNT(CASE WHEN image_url IS NOT NULL THEN 1 END) as with_images,
                COUNT(CASE WHEN gbif_occurrence_key IS NOT NULL THEN 1 END) as with_gbif,
                COUNT(CASE WHEN latitude IS NOT NULL THEN 1 END) as with_location,
                COUNT(DISTINCT genus) as unique_genera
            FROM orchid_record;
        """)
        
        stats = cursor.fetchone()
        context: Dict = {
            "total_records": stats[0] if stats else 0,
            "with_images": stats[1] if stats else 0,
            "with_gbif": stats[2] if stats else 0,
            "with_location": stats[3] if stats else 0,
            "unique_genera": stats[4] if stats else 0
        }
        
        cursor.close()
        conn.close()
        
        # Queue tasks for each agent
        tasks = []
        
        if analysis_type in ["comprehensive", "images"]:
            task_id = self.queue_task(
                'image_acquisition',
                "Analyze image gaps and identify top priority genera for image collection. Include specific iNaturalist taxon IDs and estimated available images.",
                priority=8,
                context=context
            )
            tasks.append(task_id)
        
        if analysis_type in ["comprehensive", "enrichment"]:
            task_id = self.queue_task(
                'data_enrichment',
                "Identify data enrichment priorities across GBIF, EOL, and other sources. Focus on genera with most missing traits, habitat data, and geographic information.",
                priority=9,
                context=context
            )
            tasks.append(task_id)
        
        if analysis_type in ["comprehensive", "geographic"]:
            task_id = self.queue_task(
                'geographic_analysis',
                "Analyze geographic distribution patterns, identify biodiversity hotspots, detect potential endemic species, and highlight geographic data gaps.",
                priority=7,
                context=context
            )
            tasks.append(task_id)
        
        if analysis_type in ["comprehensive", "quality"]:
            task_id = self.queue_task(
                'quality_control',
                "Perform comprehensive quality check on all records. Identify data inconsistencies, validation failures, and quality improvement priorities.",
                priority=6,
                context=context
            )
            tasks.append(task_id)
        
        # Process all tasks
        self.process_queue(max_tasks=len(tasks))
        
        # Run coordinator to synthesize
        if analysis_type == "comprehensive":
            coordinator_task = self.queue_task(
                'research_coordinator',
                "Review findings from all specialized agents and create a unified research action plan with prioritized tasks.",
                priority=10,
                context={"analysis_tasks": tasks}
            )
            self.process_queue(max_tasks=1)
        
        self.logger.info("🎉 Multi-agent analysis complete!")
        return tasks


def main():
    """Run multi-agent orchestrator"""
    
    orchestrator = MultiAgentOrchestrator()
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║     ORCHID CONTINUUM - MULTI-AGENT AI SYSTEM                ║
╚══════════════════════════════════════════════════════════════╝

Available Agents:
  🖼️  Image Acquisition Specialist - Finds optimal image sources
  📊 Data Enrichment Specialist - Identifies enrichment targets
  🌍 Geographic Analysis Specialist - Analyzes spatial patterns
  ✅ Quality Control Specialist - Validates data quality
  🎯 Research Coordinator - Synthesizes all findings

Commands:
  1. comprehensive - Run all agents + coordinator
  2. images - Image acquisition analysis only
  3. enrichment - Data enrichment analysis only
  4. geographic - Geographic analysis only
  5. quality - Quality control analysis only
  
Enter choice (1-5): """)
    
    choice = input().strip()
    
    analysis_types = {
        '1': 'comprehensive',
        '2': 'images',
        '3': 'enrichment',
        '4': 'geographic',
        '5': 'quality'
    }
    
    analysis_type = analysis_types.get(choice, 'comprehensive')
    
    print(f"\n🚀 Starting {analysis_type} analysis...\n")
    orchestrator.run_multi_agent_analysis(analysis_type)
    
    print("\n✅ Analysis complete! Check agent_insights table for results.")


if __name__ == "__main__":
    main()
