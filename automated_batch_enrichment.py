"""
AUTOMATED BATCH ENRICHMENT SYSTEM
Continuously enriches orchids until all are complete
"""

import os
import time
import logging
from flask import Blueprint, jsonify, render_template_string
from app import db, csrf
from models import OrchidRecord
from sqlalchemy import and_, or_
from admin_system import admin_required
from external_databases.gbif_integration import GBIFIntegrator
import openai
import json

logger = logging.getLogger(__name__)

auto_enrich_bp = Blueprint('auto_enrich', __name__)

class AutomatedEnrichmentRunner:
    """Automated enrichment that runs until completion"""
    
    def __init__(self):
        self.running = False
        self.stats = {
            'gbif_enriched': 0,
            'ai_analyzed': 0,
            'total_processed': 0,
            'errors': 0,
            'status': 'idle'
        }
    
    def get_remaining_counts(self):
        """Get count of orchids still needing enrichment"""
        gbif_remaining = OrchidRecord.query.filter(
            and_(
                OrchidRecord.genus != None,
                OrchidRecord.species != None,
                or_(
                    OrchidRecord.taxonomic_status == None,
                    OrchidRecord.continent == None
                )
            )
        ).count()
        
        ai_remaining = OrchidRecord.query.filter(
            and_(
                OrchidRecord.google_drive_id != None,
                or_(
                    OrchidRecord.flower_color == None,
                    OrchidRecord.bloom_stage == None,
                    OrchidRecord.leaf_shape == None
                )
            )
        ).count()
        
        return {'gbif': gbif_remaining, 'ai': ai_remaining}
    
    def enrich_batch_gbif(self, batch_size=10):
        """Enrich a batch with GBIF data"""
        try:
            gbif = GBIFIntegrator()
            
            orchids = OrchidRecord.query.filter(
                and_(
                    OrchidRecord.genus != None,
                    OrchidRecord.species != None,
                    or_(
                        OrchidRecord.taxonomic_status == None,
                        OrchidRecord.continent == None
                    )
                )
            ).limit(batch_size).all()
            
            if not orchids:
                return 0
            
            enriched = 0
            for orchid in orchids:
                try:
                    scientific_name = f"{orchid.genus} {orchid.species}" if orchid.species else orchid.genus
                    
                    search_results = gbif.search_species(scientific_name, limit=1)
                    if search_results and search_results.get('results'):
                        species_key = search_results['results'][0].get('key')
                        
                        if species_key:
                            taxonomy = gbif.get_taxonomy(species_key)
                            if taxonomy:
                                orchid.taxonomic_status = taxonomy.get('taxonomic_status', '').lower() if taxonomy.get('taxonomic_status') else None
                                orchid.taxonomic_authority = taxonomy.get('author')
                            
                            occurrences = gbif.get_occurrences(scientific_name=scientific_name, limit=1)
                            if occurrences and occurrences.get('results'):
                                first_occurrence = occurrences['results'][0]
                                orchid.continent = first_occurrence.get('continent')
                                orchid.country = first_occurrence.get('country')
                            
                            db.session.commit()
                            enriched += 1
                            logger.info(f"✅ GBIF enriched: {scientific_name}")
                except Exception as e:
                    logger.error(f"Error enriching {orchid.id}: {e}")
                    db.session.rollback()
                    self.stats['errors'] += 1
            
            return enriched
            
        except Exception as e:
            logger.error(f"GBIF batch failed: {e}")
            return 0
    
    def enrich_batch_ai(self, batch_size=5):
        """Enrich a batch with AI vision"""
        try:
            if not os.environ.get('OPENAI_API_KEY'):
                logger.error("OPENAI_API_KEY not configured")
                return 0
            
            openai_client = openai.OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
            
            orchids = OrchidRecord.query.filter(
                and_(
                    OrchidRecord.google_drive_id != None,
                    or_(
                        OrchidRecord.flower_color == None,
                        OrchidRecord.bloom_stage == None,
                        OrchidRecord.leaf_shape == None
                    )
                )
            ).limit(batch_size).all()
            
            if not orchids:
                return 0
            
            analyzed = 0
            for orchid in orchids:
                try:
                    scientific_name = f"{orchid.genus} {orchid.species}" if orchid.species and orchid.genus else orchid.display_name
                    image_url = f"https://drive.google.com/uc?export=view&id={orchid.google_drive_id}"
                    
                    prompt = f"""Analyze this orchid image for {scientific_name}. Extract metadata as JSON:
{{
  "flower_color": "primary color(s)",
  "bloom_stage": "bud/opening/full_bloom/fading/seed_pod",
  "inflorescence_type": "single/spike/raceme/panicle",
  "leaf_shape": "oval/lance/linear/strap",
  "pseudobulb_presence": true/false,
  "labellum_type": "simple/lobed/fringed/pouch"
}}"""

                    response = openai_client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "You are an expert orchid botanist. Respond only with valid JSON."},
                            {"role": "user", "content": [
                                {"type": "text", "text": prompt},
                                {"type": "image_url", "image_url": {"url": image_url}}
                            ]}
                        ],
                        max_tokens=300,
                        temperature=0.3
                    )
                    
                    ai_response = response.choices[0].message.content
                    
                    # Parse JSON
                    if '```json' in ai_response:
                        ai_response = ai_response.split('```json')[1].split('```')[0].strip()
                    elif '```' in ai_response:
                        ai_response = ai_response.split('```')[1].split('```')[0].strip()
                    
                    metadata = json.loads(ai_response)
                    
                    # Update fields
                    if metadata.get('flower_color'):
                        orchid.flower_color = metadata['flower_color']
                    if metadata.get('bloom_stage'):
                        orchid.bloom_stage = metadata['bloom_stage']
                    if metadata.get('inflorescence_type'):
                        orchid.inflorescence_type = metadata['inflorescence_type']
                    if metadata.get('leaf_shape'):
                        orchid.leaf_shape = metadata['leaf_shape']
                    if metadata.get('pseudobulb_presence') is not None:
                        orchid.pseudobulb_presence = metadata['pseudobulb_presence']
                    if metadata.get('labellum_type'):
                        orchid.labellum_type = metadata['labellum_type']
                    
                    db.session.commit()
                    analyzed += 1
                    logger.info(f"✅ AI analyzed: {scientific_name}")
                    
                except Exception as e:
                    logger.error(f"Error analyzing {orchid.id}: {e}")
                    db.session.rollback()
                    self.stats['errors'] += 1
            
            return analyzed
            
        except Exception as e:
            logger.error(f"AI batch failed: {e}")
            return 0
    
    def run_full_enrichment(self, app_instance, enable_ai=True):
        """Run enrichment until complete - MUST be called with Flask app instance"""
        with app_instance.app_context():
            self.running = True
            self.stats = {
                'gbif_enriched': 0,
                'ai_analyzed': 0,
                'total_processed': 0,
                'errors': 0,
                'status': 'running'
            }
            
            logger.info("🚀 Starting automated batch enrichment...")
            
            # Phase 1: GBIF enrichment (FREE - run to completion)
            logger.info("📊 Phase 3: GBIF Taxonomic Enrichment")
            while self.running:
                remaining = self.get_remaining_counts()
                if remaining['gbif'] == 0:
                    logger.info("✅ GBIF enrichment complete!")
                    break
                
                enriched = self.enrich_batch_gbif(batch_size=10)
                self.stats['gbif_enriched'] += enriched
                self.stats['total_processed'] += enriched
                
                logger.info(f"   Batch complete: {enriched} enriched, {remaining['gbif']} remaining")
                time.sleep(2)  # Rate limiting
            
            # Phase 2: AI Vision (COSTS MONEY - run with limit)
            if enable_ai:
                logger.info("🤖 Phase 1 & 2: AI Vision Analysis")
                ai_budget_limit = 100  # Process max 100 orchids ($1 cost)
                
                while self.running and self.stats['ai_analyzed'] < ai_budget_limit:
                    remaining = self.get_remaining_counts()
                    if remaining['ai'] == 0:
                        logger.info("✅ AI analysis complete!")
                        break
                    
                    analyzed = self.enrich_batch_ai(batch_size=5)
                    self.stats['ai_analyzed'] += analyzed
                    self.stats['total_processed'] += analyzed
                    
                    logger.info(f"   Batch complete: {analyzed} analyzed, {remaining['ai']} remaining")
                    time.sleep(3)  # Rate limiting for API
            
            self.stats['status'] = 'complete'
            self.running = False
            
            logger.info(f"✅ Automated enrichment complete!")
            logger.info(f"   GBIF enriched: {self.stats['gbif_enriched']}")
            logger.info(f"   AI analyzed: {self.stats['ai_analyzed']}")
            logger.info(f"   Errors: {self.stats['errors']}")
            
            return self.stats

# Global instance
enrichment_runner = AutomatedEnrichmentRunner()

@auto_enrich_bp.route('/admin/auto-enrich')
@admin_required
def auto_enrich_page():
    """Automated enrichment control panel"""
    template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Automated Enrichment - Orchid Continuum</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <script src="https://unpkg.com/feather-icons"></script>
    </head>
    <body class="bg-dark text-white">
        <div class="container mt-5">
            <h1><i data-feather="zap"></i> Automated Batch Enrichment</h1>
            <p class="lead">Automatically enrich ALL orchids until completion</p>
            
            <div class="alert alert-info">
                <strong>How it works:</strong> Click "Start Full Enrichment" and the system will continuously process 
                batches until all orchids are enriched. GBIF is FREE (runs to completion), AI vision has a $1 budget limit (100 orchids).
            </div>
            
            <div class="row mt-4">
                <div class="col-md-6">
                    <div class="card bg-secondary">
                        <div class="card-body">
                            <h5>Enrichment Status</h5>
                            <div id="status" class="mb-3">
                                <p>Status: <span id="run-status" class="badge bg-secondary">Idle</span></p>
                                <p>GBIF Enriched: <span id="gbif-count">0</span></p>
                                <p>AI Analyzed: <span id="ai-count">0</span></p>
                                <p>Errors: <span id="error-count">0</span></p>
                            </div>
                            
                            <button id="start-btn" class="btn btn-success w-100 mb-2" onclick="startEnrichment()">
                                Start Full Enrichment
                            </button>
                            <button id="stop-btn" class="btn btn-danger w-100" onclick="stopEnrichment()" disabled>
                                Stop Enrichment
                            </button>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-6">
                    <div class="card bg-secondary">
                        <div class="card-body">
                            <h5>Remaining Orchids</h5>
                            <div id="remaining">
                                <p>GBIF Needed: <span id="gbif-remaining">-</span></p>
                                <p>AI Needed: <span id="ai-remaining">-</span></p>
                            </div>
                            
                            <button class="btn btn-info w-100" onclick="checkRemaining()">
                                Check Remaining
                            </button>
                            
                            <div class="mt-3">
                                <a href="/admin/field-completion" class="btn btn-outline-light w-100">
                                    View Progress Dashboard
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="mt-4">
                <a href="/admin" class="btn btn-secondary">← Back to Admin</a>
            </div>
        </div>
        
        <script>
            feather.replace();
            let pollInterval = null;
            
            async function startEnrichment() {
                document.getElementById('start-btn').disabled = true;
                document.getElementById('stop-btn').disabled = false;
                document.getElementById('run-status').textContent = 'Starting...';
                document.getElementById('run-status').className = 'badge bg-warning';
                
                try {
                    const response = await fetch('/admin/auto-enrich/api/start', {method: 'POST'});
                    const data = await response.json();
                    
                    if (data.success) {
                        document.getElementById('run-status').textContent = 'Running';
                        document.getElementById('run-status').className = 'badge bg-success';
                        
                        // Start polling for status
                        pollInterval = setInterval(pollStatus, 3000);
                    }
                } catch (e) {
                    alert('Error: ' + e.message);
                    document.getElementById('start-btn').disabled = false;
                    document.getElementById('stop-btn').disabled = true;
                }
            }
            
            async function stopEnrichment() {
                try {
                    await fetch('/admin/auto-enrich/api/stop', {method: 'POST'});
                    clearInterval(pollInterval);
                    document.getElementById('start-btn').disabled = false;
                    document.getElementById('stop-btn').disabled = true;
                    document.getElementById('run-status').textContent = 'Stopped';
                    document.getElementById('run-status').className = 'badge bg-danger';
                } catch (e) {
                    alert('Error: ' + e.message);
                }
            }
            
            async function pollStatus() {
                try {
                    const response = await fetch('/admin/auto-enrich/api/status');
                    const data = await response.json();
                    
                    document.getElementById('gbif-count').textContent = data.gbif_enriched;
                    document.getElementById('ai-count').textContent = data.ai_analyzed;
                    document.getElementById('error-count').textContent = data.errors;
                    
                    if (data.status === 'complete') {
                        clearInterval(pollInterval);
                        document.getElementById('start-btn').disabled = false;
                        document.getElementById('stop-btn').disabled = true;
                        document.getElementById('run-status').textContent = 'Complete';
                        document.getElementById('run-status').className = 'badge bg-primary';
                        alert('Enrichment complete! Check the Field Completion Dashboard for results.');
                    }
                } catch (e) {
                    console.error('Poll error:', e);
                }
            }
            
            async function checkRemaining() {
                try {
                    const response = await fetch('/admin/auto-enrich/api/remaining');
                    const data = await response.json();
                    
                    document.getElementById('gbif-remaining').textContent = data.gbif;
                    document.getElementById('ai-remaining').textContent = data.ai;
                } catch (e) {
                    alert('Error: ' + e.message);
                }
            }
            
            // Check remaining on load
            checkRemaining();
        </script>
    </body>
    </html>
    """
    return render_template_string(template)

@auto_enrich_bp.route('/admin/auto-enrich/api/start', methods=['POST'])
@csrf.exempt
@admin_required
def start_auto_enrichment():
    """Start automated enrichment in background"""
    try:
        if enrichment_runner.running:
            return jsonify({'success': False, 'error': 'Enrichment already running'}), 400
        
        # Start enrichment in background thread with app context
        import threading
        from flask import current_app
        app_instance = current_app._get_current_object()
        thread = threading.Thread(target=enrichment_runner.run_full_enrichment, args=(app_instance, True))
        thread.daemon = True
        thread.start()
        
        return jsonify({'success': True, 'message': 'Enrichment started'})
        
    except Exception as e:
        logger.error(f"Failed to start enrichment: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@auto_enrich_bp.route('/admin/auto-enrich/api/stop', methods=['POST'])
@csrf.exempt
@admin_required
def stop_auto_enrichment():
    """Stop automated enrichment"""
    enrichment_runner.running = False
    return jsonify({'success': True, 'message': 'Enrichment stopped'})

@auto_enrich_bp.route('/admin/auto-enrich/api/status')
@admin_required
def get_enrichment_status():
    """Get current enrichment status"""
    return jsonify(enrichment_runner.stats)

@auto_enrich_bp.route('/admin/auto-enrich/api/remaining')
@admin_required
def get_remaining_counts():
    """Get counts of remaining orchids"""
    counts = enrichment_runner.get_remaining_counts()
    return jsonify(counts)

logger.info("🤖 Automated Batch Enrichment system initialized")
