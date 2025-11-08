"""
ADMIN QUICK ENRICHMENT BUTTON
Simple one-click enrichment for 10 orchids at a time
"""

import os
from flask import Blueprint, jsonify, render_template_string
from flask_login import login_required
from app import db, csrf
from models import OrchidRecord
from sqlalchemy import and_, or_
from admin_system import admin_required
import logging

logger = logging.getLogger(__name__)

quick_enrich_bp = Blueprint('quick_enrich', __name__)

@quick_enrich_bp.route('/admin/quick-enrich')
@admin_required
def quick_enrich_page():
    """Admin page for quick enrichment"""
    template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Quick Enrichment - Orchid Continuum</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <script src="https://unpkg.com/feather-icons"></script>
    </head>
    <body class="bg-dark text-white">
        <div class="container mt-5">
            <h1><i data-feather="zap"></i> Quick Metadata Enrichment</h1>
            <p class="lead">Enrich orchids with Phase 1, 2, and 3 metadata in small batches</p>
            
            <div class="row mt-4">
                <div class="col-md-4">
                    <div class="card bg-secondary">
                        <div class="card-body">
                            <h5>Phase 3: GBIF Taxonomic Data</h5>
                            <p class="small">FREE - Taxonomic status, authority, continent</p>
                            <button class="btn btn-primary w-100" onclick="enrichGBIF()">
                                Enrich 10 Orchids (GBIF)
                            </button>
                            <div id="gbif-status" class="mt-2"></div>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-4">
                    <div class="card bg-secondary">
                        <div class="card-body">
                            <h5>Phase 1 & 2: AI Vision</h5>
                            <p class="small">$0.01/orchid - Flower color, leaf shape, etc.</p>
                            <button class="btn btn-success w-100" onclick="enrichAI()">
                                Analyze 5 Orchids (AI)
                            </button>
                            <div id="ai-status" class="mt-2"></div>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-4">
                    <div class="card bg-secondary">
                        <div class="card-body">
                            <h5>View Results</h5>
                            <p class="small">Check enrichment progress</p>
                            <a href="/admin/field-completion" class="btn btn-info w-100">
                                Field Completion Dashboard
                            </a>
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
            
            async function enrichGBIF() {
                document.getElementById('gbif-status').innerHTML = '<span class="text-warning">Processing...</span>';
                try {
                    const response = await fetch('/admin/quick-enrich/api/gbif', {method: 'POST'});
                    const data = await response.json();
                    if (data.success) {
                        document.getElementById('gbif-status').innerHTML = 
                            `<span class="text-success">✅ Enriched ${data.enriched} orchids!</span>`;
                    } else {
                        document.getElementById('gbif-status').innerHTML = 
                            `<span class="text-danger">❌ ${data.error}</span>`;
                    }
                } catch (e) {
                    document.getElementById('gbif-status').innerHTML = 
                        `<span class="text-danger">❌ Error: ${e.message}</span>`;
                }
            }
            
            async function enrichAI() {
                document.getElementById('ai-status').innerHTML = '<span class="text-warning">Processing...</span>';
                try {
                    const response = await fetch('/admin/quick-enrich/api/ai-vision', {method: 'POST'});
                    const data = await response.json();
                    if (data.success) {
                        document.getElementById('ai-status').innerHTML = 
                            `<span class="text-success">✅ Analyzed ${data.analyzed} orchids!</span>`;
                    } else {
                        document.getElementById('ai-status').innerHTML = 
                            `<span class="text-danger">❌ ${data.error}</span>`;
                    }
                } catch (e) {
                    document.getElementById('ai-status').innerHTML = 
                        `<span class="text-danger">❌ Error: ${e.message}</span>`;
                }
            }
        </script>
    </body>
    </html>
    """
    return render_template_string(template)

@quick_enrich_bp.route('/admin/quick-enrich/api/gbif', methods=['POST'])
@csrf.exempt
@admin_required
def enrich_gbif():
    """Enrich 10 orchids with GBIF data"""
    try:
        from external_databases.gbif_integration import GBIFIntegrator
        
        gbif = GBIFIntegrator()
        
        # Find orchids needing GBIF enrichment
        orchids = OrchidRecord.query.filter(
            and_(
                OrchidRecord.genus != None,
                OrchidRecord.species != None,
                or_(
                    OrchidRecord.taxonomic_status == None,
                    OrchidRecord.continent == None
                )
            )
        ).limit(10).all()
        
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
            except Exception as e:
                logger.error(f"Error enriching orchid {orchid.id}: {e}")
                db.session.rollback()
        
        return jsonify({'success': True, 'enriched': enriched, 'total': len(orchids)})
        
    except Exception as e:
        logger.error(f"GBIF enrichment failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@quick_enrich_bp.route('/admin/quick-enrich/api/ai-vision', methods=['POST'])
@csrf.exempt
@admin_required
def enrich_ai_vision():
    """Analyze 5 orchids with AI vision"""
    try:
        import openai
        import json
        
        if not os.environ.get('OPENAI_API_KEY'):
            return jsonify({'success': False, 'error': 'OPENAI_API_KEY not configured'}), 400
        
        openai_client = openai.OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        
        # Find orchids with images needing AI analysis
        orchids = OrchidRecord.query.filter(
            and_(
                OrchidRecord.google_drive_id != None,
                or_(
                    OrchidRecord.flower_color == None,
                    OrchidRecord.bloom_stage == None,
                    OrchidRecord.leaf_shape == None
                )
            )
        ).limit(5).all()
        
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
                
            except Exception as e:
                logger.error(f"Error analyzing orchid {orchid.id}: {e}")
                db.session.rollback()
        
        return jsonify({'success': True, 'analyzed': analyzed, 'total': len(orchids)})
        
    except Exception as e:
        logger.error(f"AI vision enrichment failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

logger.info("⚡ Quick Enrichment system initialized")
