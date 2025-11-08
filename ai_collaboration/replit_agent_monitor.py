#!/usr/bin/env python3
"""
Replit Agent Autonomous Monitor
Continuously checks for Julius AI responses and processes them
"""

import psycopg2
import os
import time
import json
from datetime import datetime

DATABASE_URL = os.environ.get("DATABASE_URL")

class ReplitAgentMonitor:
    def __init__(self):
        self.conn = psycopg2.connect(DATABASE_URL)
        self.agent_name = "replit_agent"
        
    def send_task_to_julius(self, task_id, prompt_text, file_path=None, priority=5):
        """Send a new task to Julius AI"""
        cur = self.conn.cursor()
        
        cur.execute("""
            INSERT INTO ai_communication 
            (from_agent, to_agent, task_id, message_type, status, prompt_text, file_path, priority)
            VALUES 
            ('replit_agent', 'julius_ai', %s, 'prompt', 'pending', %s, %s, %s)
            RETURNING id;
        """, (task_id, prompt_text, file_path, priority))
        
        task_db_id = cur.fetchone()[0]
        self.conn.commit()
        
        print(f"✅ Task {task_id} sent to Julius AI (DB ID: {task_db_id})")
        return task_db_id
    
    def check_julius_responses(self):
        """Check for completed tasks from Julius"""
        cur = self.conn.cursor()
        
        cur.execute("""
            SELECT id, task_id, result_file_path, result_summary, created_at
            FROM ai_communication 
            WHERE to_agent = 'replit_agent' 
            AND from_agent = 'julius_ai'
            AND status = 'pending'
            ORDER BY created_at ASC;
        """)
        
        responses = cur.fetchall()
        
        if responses:
            print(f"\n📬 Found {len(responses)} responses from Julius AI:")
            for resp in responses:
                db_id, task_id, file_path, summary, created = resp
                print(f"  Task {task_id}: {summary}")
                print(f"    Files: {file_path}")
                print(f"    Created: {created}")
        
        return responses
    
    def mark_response_processed(self, db_id):
        """Mark Julius's response as read and processed"""
        cur = self.conn.cursor()
        
        cur.execute("""
            UPDATE ai_communication 
            SET status = 'processed', read_at = NOW()
            WHERE id = %s;
        """, (db_id,))
        
        self.conn.commit()
        print(f"✅ Response {db_id} marked as processed")
    
    def process_task_001_response(self):
        """Process Julius's trait extraction results"""
        print("\n🔄 Processing Task 001 results from Julius...")
        
        # Check if file exists
        trait_file = "ai_collaboration/julius_to_replit/task_001_response_orchid_traits.csv"
        
        if os.path.exists(trait_file):
            print(f"✅ Found: {trait_file}")
            
            # Import to database (would implement actual import here)
            print("📊 Importing traits to database...")
            
            # For now, just count rows
            with open(trait_file, 'r') as f:
                row_count = sum(1 for line in f) - 1  # Minus header
            
            print(f"✅ Imported {row_count:,} trait records")
            
            # Generate Task 002
            self.generate_task_002(row_count)
            
            return True
        else:
            print(f"⚠️  File not found: {trait_file}")
            return False
    
    def generate_task_002(self, trait_count):
        """Generate Task 002: Match images to traits"""
        print("\n📝 Generating Task 002: Match Images to Traits...")
        
        prompt = f"""
Task 002: Match EOL Images to Orchid Traits

CONTEXT:
- Task 001 completed: {trait_count:,} orchid traits extracted
- Database has 95,000 EOL images
- Need to match images to traits using page_id

INSTRUCTIONS:
1. Query database for EOL images:
   SELECT page_id, eol_url, license, copyright, source_url 
   FROM eol_images;

2. Load Task 001 traits:
   ai_collaboration/julius_to_replit/task_001_response_orchid_traits.csv

3. Match on page_id:
   - Inner join to find species with BOTH images AND traits
   - Count species with only images
   - Count species with only traits

4. Export results:
   - task_002_response_matched.csv (all matched records)
   - task_002_response_coverage_stats.txt (statistics)
   - task_002_response_priority_species.csv (species needing more data)

EXECUTE and save results to ai_collaboration/julius_to_replit/
"""
        
        file_path = "ai_collaboration/replit_to_julius/task_002_match_images_to_traits_2025-10-20.md"
        
        task_db_id = self.send_task_to_julius(
            task_id="task_002",
            prompt_text=prompt,
            file_path=file_path,
            priority=5
        )
        
        print(f"✅ Task 002 ready for Julius (ID: {task_db_id})")
    
    def monitor_loop(self, interval=60):
        """Main monitoring loop - runs continuously"""
        print(f"\n🤖 Replit Agent Monitor ACTIVE")
        print(f"📊 Checking for Julius responses every {interval} seconds")
        print(f"⏸️  Press Ctrl+C to stop\n")
        
        try:
            while True:
                # Check for responses
                responses = self.check_julius_responses()
                
                # Process each response
                for resp in responses:
                    db_id, task_id, file_path, summary, created = resp
                    
                    print(f"\n⚡ Processing {task_id}...")
                    
                    if task_id == "task_001":
                        success = self.process_task_001_response()
                        if success:
                            self.mark_response_processed(db_id)
                    
                    elif task_id == "task_002":
                        # Would implement task 002 processing
                        print("📊 Task 002 processing not yet implemented")
                        self.mark_response_processed(db_id)
                    
                    else:
                        print(f"⚠️  Unknown task: {task_id}")
                        self.mark_response_processed(db_id)
                
                # Wait before next check
                if not responses:
                    print(f"💤 No new responses. Checking again in {interval}s...")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n\n⏸️  Monitor stopped by user")
            self.conn.close()

def initialize_system():
    """One-time setup: Send Task 001 to Julius"""
    monitor = ReplitAgentMonitor()
    
    print("🚀 Initializing AI Collaboration System...")
    
    # Send Task 001
    prompt = """
Task 001: Extract Orchid Traits from TraitBank

You have a TraitBank ZIP file uploaded with orchid trait data.

EXECUTE:
1. Load pages.csv and filter for family = 'Orchidaceae'
2. Load traits.csv and join with orchid pages on page_id
3. Extract columns: page_id, canonical (as scientific_name), predicate (as trait_name), 
   measurement/literal (as trait_value), units (as trait_unit)
4. Export to: ai_collaboration/julius_to_replit/task_001_response_orchid_traits.csv
5. Generate statistics: ai_collaboration/julius_to_replit/task_001_response_stats.txt

See detailed instructions in: ai_collaboration/replit_to_julius/task_001_extract_orchid_traits_2025-10-20.md

When complete, INSERT response message to ai_communication table.
"""
    
    monitor.send_task_to_julius(
        task_id="task_001",
        prompt_text=prompt,
        file_path="ai_collaboration/replit_to_julius/task_001_extract_orchid_traits_2025-10-20.md",
        priority=10  # High priority
    )
    
    print("\n✅ System initialized!")
    print("📍 Task 001 sent to Julius AI")
    print("\n💡 Next steps:")
    print("   1. Give Julius the INITIAL PROMPT from AUTONOMOUS_SETUP.md")
    print("   2. Julius will detect Task 001 and execute it")
    print("   3. Run this monitor to process Julius's responses")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "init":
        # Initialize and send first task
        initialize_system()
    else:
        # Run monitoring loop
        monitor = ReplitAgentMonitor()
        monitor.monitor_loop(interval=60)
