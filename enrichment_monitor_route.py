from flask import render_template_string
from app import app, db
from models import OrchidRecord
from sqlalchemy import func
import psycopg2
import os

@app.route('/enrichment-monitor')
def enrichment_monitor():
    """Real-time enrichment monitoring dashboard"""
    
    # Get enrichment stats
    conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
    cursor = conn.cursor()
    
    # Count valid orchids and enrichment progress
    cursor.execute("""
        SELECT 
            COUNT(*) FILTER (WHERE validation_status = 'approved') as valid_total,
            COUNT(*) FILTER (WHERE validation_status = 'approved' AND gbif_species_key IS NOT NULL) as gbif_done,
            COUNT(*) FILTER (WHERE validation_status = 'approved' AND inaturalist_observation_id IS NOT NULL) as inat_done,
            COUNT(*) FILTER (WHERE validation_status = 'invalid_taxonomy') as invalid_count
        FROM orchid_record
    """)
    
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    
    valid_total = result[0] if result else 4673
    gbif_done = result[1] if result else 0
    inat_done = result[2] if result else 0
    invalid_count = result[3] if result else 1155
    
    # Calculate progress
    progress = int((gbif_done / valid_total * 100)) if valid_total > 0 else 0
    current = gbif_done
    
    # Estimate ETA (rough calculation)
    remaining = valid_total - current
    eta = int(remaining / 20) if remaining > 0 else 0  # ~20 orchids/minute
    
    status = "🚀 Enrichment Running..." if current < valid_total else "✅ Enrichment Complete!"
    
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Orchid Enrichment Monitor</title>
        <meta http-equiv="refresh" content="10">
        <style>
            body { font-family: Arial; padding: 20px; background: #1a1a1a; color: #fff; }
            .stats { background: #2a2a2a; padding: 20px; border-radius: 10px; margin: 10px 0; }
            .progress-bar { background: #333; height: 30px; border-radius: 5px; overflow: hidden; }
            .progress-fill { background: #4CAF50; height: 100%; transition: width 0.3s; }
            .status { font-size: 24px; margin: 20px 0; }
            .metrics { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }
            .metric { background: #333; padding: 15px; border-radius: 5px; text-align: center; }
            .metric-value { font-size: 32px; font-weight: bold; color: #4CAF50; }
            .metric-label { color: #999; margin-top: 5px; }
        </style>
    </head>
    <body>
        <h1>🚀 Orchid Enrichment Monitor</h1>
        <p style="color: #999;">Auto-refreshes every 10 seconds - no action needed!</p>
        
        <div class="status">{{ status }}</div>
        
        <div class="stats">
            <h3>Progress</h3>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {{ progress }}%"></div>
            </div>
            <p>{{ current }}/{{ total }} orchids enriched ({{ progress }}%)</p>
        </div>
        
        <div class="metrics">
            <div class="metric">
                <div class="metric-value">{{ gbif }}</div>
                <div class="metric-label">GBIF Enriched</div>
            </div>
            <div class="metric">
                <div class="metric-value">{{ inat }}</div>
                <div class="metric-label">iNaturalist Enriched</div>
            </div>
            <div class="metric">
                <div class="metric-value">{{ eta }}</div>
                <div class="metric-label">ETA (minutes)</div>
            </div>
        </div>
        
        <div class="stats">
            <h3>📊 Summary</h3>
            <p>✅ Valid orchids being enriched: {{ total }}</p>
            <p>❌ Invalid orchids marked & skipped: {{ invalid }}</p>
            <p>⏱️ <strong>Running automatically in background!</strong></p>
            <p style="color: #4CAF50;">You can close this tab - enrichment continues running</p>
        </div>
    </body>
    </html>
    '''
    
    return render_template_string(html, 
        status=status,
        progress=progress,
        current=current,
        total=valid_total,
        gbif=gbif_done,
        inat=inat_done,
        eta=eta,
        invalid=invalid_count
    )
