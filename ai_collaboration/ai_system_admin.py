#!/usr/bin/env python3
"""
AI System Admin Controls
Provides monitoring and control for Julius AI autonomous sessions
"""

import os
import psycopg2
from datetime import datetime, timedelta
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.environ.get("DATABASE_URL")

class AISystemAdmin:
    def __init__(self):
        self.conn = psycopg2.connect(DATABASE_URL)
        self.conn.autocommit = True
    
    def create_session(self, agent_name='julius_ai', max_iterations=10, 
                      time_budget_min=60, cost_budget_usd=20.00, notes=''):
        """Create a new AI work session with safety limits"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            expires_at = datetime.now() + timedelta(minutes=time_budget_min)
            cur.execute("""
                INSERT INTO ai_sessions 
                (agent_name, max_iterations, time_budget_min, expires_at, 
                 cost_budget_usd, created_by, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id, started_at
            """, (agent_name, max_iterations, time_budget_min, expires_at,
                  cost_budget_usd, 'admin', notes))
            result = cur.fetchone()
            if result:
                print(f"✅ Created session {result['id']}")
                print(f"   Started: {result['started_at']}")
                print(f"   Expires: {expires_at}")
                print(f"   Max iterations: {max_iterations}")
                print(f"   Budget: ${cost_budget_usd}")
                return result['id']
            return None
    
    def get_active_session(self, agent_name='julius_ai'):
        """Get current active session"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM ai_sessions 
                WHERE agent_name = %s AND status = 'active'
                ORDER BY started_at DESC LIMIT 1
            """, (agent_name,))
            return cur.fetchone()
    
    def pause_agent(self, agent_name='julius_ai', reason='Manual pause'):
        """KILL SWITCH: Pause agent execution"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                INSERT INTO ai_killswitch (agent_name, is_paused, killed_at, killed_by, reason)
                VALUES (%s, TRUE, NOW(), 'admin', %s)
                ON CONFLICT (agent_name) 
                DO UPDATE SET is_paused = TRUE, killed_at = NOW(), 
                              killed_by = 'admin', reason = EXCLUDED.reason
            """, (agent_name, reason))
            print(f"🛑 KILL SWITCH ACTIVATED: {agent_name} paused")
            print(f"   Reason: {reason}")
    
    def resume_agent(self, agent_name='julius_ai'):
        """Resume agent execution"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                UPDATE ai_killswitch 
                SET is_paused = FALSE, updated_at = NOW()
                WHERE agent_name = %s
            """, (agent_name,))
            print(f"✅ Agent resumed: {agent_name}")
    
    def get_session_status(self, session_id=None):
        """Get detailed session status"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            if session_id:
                cur.execute("SELECT * FROM ai_sessions WHERE id = %s", (session_id,))
            else:
                cur.execute("""
                    SELECT * FROM ai_sessions 
                    WHERE status = 'active'
                    ORDER BY started_at DESC LIMIT 1
                """)
            session = cur.fetchone()
            
            if not session:
                print("❌ No active session found")
                return None
            
            # Get task metrics
            cur.execute("""
                SELECT COUNT(*) as total_tasks,
                       SUM(CASE WHEN outcome = 'completed' THEN 1 ELSE 0 END) as completed,
                       SUM(CASE WHEN outcome = 'error' THEN 1 ELSE 0 END) as errors,
                       SUM(cost_usd) as total_cost
                FROM ai_task_metrics
                WHERE session_id = %s
            """, (session['id'],))
            metrics = cur.fetchone()
            
            print(f"\n📊 SESSION STATUS: {session['id']}")
            print(f"   Agent: {session['agent_name']}")
            print(f"   Status: {session['status']}")
            print(f"   Started: {session['started_at']}")
            print(f"   Iterations: {session['iteration_count']}/{session['max_iterations']}")
            print(f"   Cost: ${session['cost_used_usd']:.2f}/${session['cost_budget_usd']:.2f}")
            if metrics:
                print(f"   Tasks completed: {metrics['completed'] or 0}")
                print(f"   Tasks errored: {metrics['errors'] or 0}")
            else:
                print(f"   Tasks completed: 0")
                print(f"   Tasks errored: 0")
            
            # Budget warnings
            cost_pct = (float(session['cost_used_usd']) / float(session['cost_budget_usd'])) * 100
            if cost_pct > 80:
                print(f"   ⚠️  WARNING: {cost_pct:.1f}% of budget used!")
            
            iteration_pct = (session['iteration_count'] / session['max_iterations']) * 100
            if iteration_pct > 80:
                print(f"   ⚠️  WARNING: {iteration_pct:.1f}% of iterations used!")
            
            return session
    
    def get_recent_tasks(self, limit=10):
        """Show recent AI tasks"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT task_id, from_agent, to_agent, status, 
                       created_at, completed_at, result_summary
                FROM ai_communication
                ORDER BY created_at DESC
                LIMIT %s
            """, (limit,))
            tasks = cur.fetchall()
            
            print(f"\n📋 RECENT TASKS (last {limit}):")
            for task in tasks:
                status_icon = {
                    'pending': '⏳',
                    'in_progress': '🔄',
                    'completed': '✅',
                    'failed': '❌'
                }.get(task['status'], '❓')
                
                print(f"{status_icon} {task['task_id']} ({task['from_agent']} → {task['to_agent']})")
                print(f"   Status: {task['status']}")
                print(f"   Created: {task['created_at']}")
                if task['result_summary']:
                    print(f"   Result: {task['result_summary'][:80]}...")
                print()
    
    def end_session(self, session_id=None, status='completed'):
        """Manually end a session"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            if session_id:
                cur.execute("UPDATE ai_sessions SET status = %s WHERE id = %s", 
                           (status, session_id))
            else:
                cur.execute("""
                    UPDATE ai_sessions SET status = %s 
                    WHERE status = 'active' AND agent_name = 'julius_ai'
                """, (status,))
            print(f"✅ Session ended with status: {status}")

def main():
    """Interactive admin console"""
    admin = AISystemAdmin()
    
    print("\n" + "="*60)
    print("  AI SYSTEM ADMIN CONSOLE")
    print("="*60)
    
    while True:
        print("\nCommands:")
        print("  1. Create new session")
        print("  2. Get session status")
        print("  3. Pause agent (KILL SWITCH)")
        print("  4. Resume agent")
        print("  5. View recent tasks")
        print("  6. End current session")
        print("  q. Quit")
        
        choice = input("\nEnter command: ").strip()
        
        if choice == '1':
            max_iter = input("Max iterations (default 10): ").strip() or "10"
            budget = input("Cost budget USD (default 20.00): ").strip() or "20.00"
            notes = input("Notes: ").strip()
            admin.create_session(max_iterations=int(max_iter), 
                               cost_budget_usd=float(budget), notes=notes)
        
        elif choice == '2':
            admin.get_session_status()
        
        elif choice == '3':
            reason = input("Pause reason: ").strip() or "Manual pause"
            admin.pause_agent(reason=reason)
        
        elif choice == '4':
            admin.resume_agent()
        
        elif choice == '5':
            limit = input("How many tasks (default 10): ").strip() or "10"
            admin.get_recent_tasks(int(limit))
        
        elif choice == '6':
            admin.end_session()
        
        elif choice == 'q':
            print("Goodbye!")
            break
        
        else:
            print("Invalid command")

if __name__ == '__main__':
    main()
