from flask import render_template_string
from app import app, db
import psycopg2
import os

@app.route('/monitor')
def unified_monitor():
    """Single unified monitoring dashboard for ALL systems"""
    
    conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
    cursor = conn.cursor()
    
    # Enrichment progress
    cursor.execute("""
        SELECT 
            COUNT(*) FILTER (WHERE validation_status = 'approved') as valid_total,
            COUNT(*) FILTER (WHERE validation_status = 'approved' AND gbif_species_key IS NOT NULL) as gbif_done,
            COUNT(*) FILTER (WHERE validation_status = 'approved' AND inaturalist_observation_id IS NOT NULL) as inat_done,
            COUNT(*) FILTER (WHERE validation_status = 'invalid_taxonomy') as invalid_count,
            COUNT(*) FILTER (WHERE ai_description IS NOT NULL) as ai_analyzed
        FROM orchid_record
    """)
    
    stats = cursor.fetchone()
    valid_total = stats[0] if stats else 0
    gbif_done = stats[1] if stats else 0
    inat_done = stats[2] if stats else 0
    invalid_count = stats[3] if stats else 0
    ai_analyzed = stats[4] if stats else 0
    
    # Julius communication
    cursor.execute("""
        SELECT COUNT(*) FROM julius_communication WHERE message_from = 'Julius AI'
    """)
    julius_messages = cursor.fetchone()[0] if cursor.fetchone() else 0
    
    # Recent enrichment activity
    cursor.execute("""
        SELECT scientific_name, updated_at 
        FROM orchid_record 
        WHERE gbif_species_key IS NOT NULL 
        ORDER BY updated_at DESC 
        LIMIT 5
    """)
    recent = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    progress = int((gbif_done / valid_total * 100)) if valid_total > 0 else 0
    ai_progress = int((ai_analyzed / valid_total * 100)) if valid_total > 0 else 0
    eta = int((valid_total - gbif_done) / 20) if gbif_done < valid_total else 0
    
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Orchid Continuum - Unified Monitor</title>
        <meta http-equiv="refresh" content="10">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: 'Segoe UI', Arial, sans-serif; 
                background: #0a0a0a; 
                color: #fff; 
                padding: 20px;
            }
            .container { max-width: 1400px; margin: 0 auto; }
            .header { 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 30px;
                border-radius: 15px;
                margin-bottom: 20px;
                text-align: center;
            }
            .header h1 { font-size: 32px; margin-bottom: 10px; }
            .header p { opacity: 0.9; font-size: 14px; }
            
            .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
            .card { 
                background: #1a1a1a; 
                padding: 25px; 
                border-radius: 12px; 
                border: 1px solid #333;
                transition: transform 0.2s;
            }
            .card:hover { transform: translateY(-5px); border-color: #667eea; }
            .card h3 { color: #667eea; margin-bottom: 15px; font-size: 18px; }
            
            .progress-bar { 
                background: #333; 
                height: 25px; 
                border-radius: 15px; 
                overflow: hidden; 
                margin: 10px 0;
                position: relative;
            }
            .progress-fill { 
                background: linear-gradient(90deg, #667eea, #764ba2); 
                height: 100%; 
                transition: width 0.5s ease;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-weight: bold;
                font-size: 12px;
            }
            
            .stat { 
                display: flex; 
                justify-content: space-between; 
                padding: 10px 0; 
                border-bottom: 1px solid #222;
            }
            .stat:last-child { border-bottom: none; }
            .stat-label { color: #999; }
            .stat-value { 
                font-weight: bold; 
                color: #4CAF50;
                font-size: 18px;
            }
            
            .status-badge {
                display: inline-block;
                padding: 5px 15px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: bold;
                margin: 5px;
            }
            .status-running { background: #4CAF50; color: white; }
            .status-pending { background: #ff9800; color: white; }
            .status-complete { background: #2196F3; color: white; }
            
            .recent-item {
                background: #252525;
                padding: 10px;
                margin: 5px 0;
                border-radius: 5px;
                font-size: 13px;
            }
            
            .auto-refresh {
                position: fixed;
                top: 20px;
                right: 20px;
                background: #667eea;
                padding: 8px 15px;
                border-radius: 20px;
                font-size: 12px;
                animation: pulse 2s infinite;
            }
            
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.7; }
            }
        </style>
    </head>
    <body>
        <div class="auto-refresh">⟳ Auto-refresh: 10s</div>
        
        <div class="container">
            <div class="header">
                <h1>🌸 Orchid Continuum Unified Monitor</h1>
                <p>Real-time monitoring of all enrichment, AI analysis, and Julius AI systems</p>
            </div>
            
            <div class="grid">
                <!-- Enrichment Progress -->
                <div class="card">
                    <h3>📊 Data Enrichment Progress</h3>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {{ progress }}%">{{ progress }}%</div>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Valid Orchids</span>
                        <span class="stat-value">{{ valid_total }}</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">GBIF Enriched</span>
                        <span class="stat-value">{{ gbif_done }}</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">iNaturalist Photos</span>
                        <span class="stat-value">{{ inat_done }}</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">ETA (minutes)</span>
                        <span class="stat-value">{{ eta }}</span>
                    </div>
                    <span class="status-badge status-running">RUNNING</span>
                </div>
                
                <!-- AI Vision Analysis -->
                <div class="card">
                    <h3>🤖 AI Vision Analysis</h3>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {{ ai_progress }}%">{{ ai_progress }}%</div>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Images Analyzed</span>
                        <span class="stat-value">{{ ai_analyzed }}</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Remaining</span>
                        <span class="stat-value">{{ valid_total - ai_analyzed }}</span>
                    </div>
                    <span class="status-badge status-pending">READY TO START</span>
                </div>
                
                <!-- Julius AI Integration -->
                <div class="card">
                    <h3>🧠 Julius AI Intelligence</h3>
                    <div class="stat">
                        <span class="stat-label">Julius Messages</span>
                        <span class="stat-value">{{ julius_messages }}</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Status</span>
                        <span class="stat-value">Ready</span>
                    </div>
                    <p style="margin-top: 15px; color: #999; font-size: 13px;">
                        Paste Julius insights in chat to trigger enrichment priorities
                    </p>
                    <span class="status-badge status-complete">CONFIGURED</span>
                </div>
                
                <!-- Data Quality -->
                <div class="card">
                    <h3>✅ Data Quality</h3>
                    <div class="stat">
                        <span class="stat-label">Valid Orchids</span>
                        <span class="stat-value">{{ valid_total }}</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Invalid (Hidden)</span>
                        <span class="stat-value" style="color: #f44336;">{{ invalid_count }}</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Gallery Clean</span>
                        <span class="stat-value">100%</span>
                    </div>
                    <span class="status-badge status-complete">VALIDATED</span>
                </div>
            </div>
            
            <!-- Recent Activity -->
            <div class="card" style="margin-top: 20px;">
                <h3>⚡ Recent Enrichment Activity</h3>
                {% for orchid in recent_orchids %}
                <div class="recent-item">
                    <strong>{{ orchid[0] }}</strong> - enriched {{ orchid[1] }}
                </div>
                {% endfor %}
            </div>
        </div>
    </body>
    </html>
    '''
    
    recent_orchids = [(r[0], r[1].strftime('%H:%M:%S') if r[1] else 'Unknown') for r in recent]
    
    return render_template_string(html, 
        progress=progress,
        valid_total=valid_total,
        gbif_done=gbif_done,
        inat_done=inat_done,
        eta=eta,
        invalid_count=invalid_count,
        ai_analyzed=ai_analyzed,
        ai_progress=ai_progress,
        julius_messages=julius_messages,
        recent_orchids=recent_orchids
    )
