#!/usr/bin/env python3
"""
METADATA ENRICHMENT ACTIVATION SCRIPT
Run Phase 1, 2, and 3 enrichment to populate all 28 fields
"""

import os
import sys
import logging
from datetime import datetime

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import OrchidRecord
from sqlalchemy import func, and_, or_

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def enrich_phase3_gbif_data(limit=100):
    """
    PHASE 3: Enrich taxonomic data from GBIF
    Populates: taxonomic_status, taxonomic_authority, continent, country
    """
    logger.info("=" * 80)
    logger.info("PHASE 3: GBIF Taxonomic Data Enrichment")
    logger.info("=" * 80)
    
    try:
        from external_databases.gbif_integration import GBIFIntegrator
        gbif = GBIFIntegrator()
        logger.info("✅ GBIF Integrator loaded")
        
        # Find orchids missing Phase 3 data
        orchids_to_enrich = OrchidRecord.query.filter(
            and_(
                OrchidRecord.genus != None,
                OrchidRecord.species != None,
                or_(
                    OrchidRecord.taxonomic_status == None,
                    OrchidRecord.continent == None
                )
            )
        ).limit(limit).all()
        
        logger.info(f"📊 Found {len(orchids_to_enrich)} orchids needing GBIF enrichment")
        
        enriched_count = 0
        for orchid in orchids_to_enrich:
            try:
                scientific_name = f"{orchid.genus} {orchid.species}" if orchid.species else orchid.genus
                logger.info(f"🔍 Enriching: {scientific_name} (ID: {orchid.id})")
                
                # Search for species in GBIF
                search_results = gbif.search_species(scientific_name, limit=1)
                
                if search_results and search_results.get('results'):
                    species_data = search_results['results'][0]
                    species_key = species_data.get('key')
                    
                    # Get detailed taxonomy
                    if species_key:
                        taxonomy = gbif.get_taxonomy(species_key)
                        
                        # Update Phase 3 fields from taxonomy
                        if taxonomy:
                            orchid.taxonomic_status = taxonomy.get('taxonomic_status', '').lower() if taxonomy.get('taxonomic_status') else None
                            orchid.taxonomic_authority = taxonomy.get('author')
                        
                        # Get occurrence data for geographic info
                        occurrences = gbif.get_occurrences(scientific_name=scientific_name, limit=1)
                        if occurrences and occurrences.get('results'):
                            first_occurrence = occurrences['results'][0]
                            orchid.continent = first_occurrence.get('continent')
                            orchid.country = first_occurrence.get('country')
                    
                    db.session.commit()
                    enriched_count += 1
                    logger.info(f"   ✅ Enriched with: {orchid.taxonomic_status or 'N/A'}, {orchid.continent or 'N/A'}")
                else:
                    logger.info(f"   ⚠️ No GBIF data found")
                    
            except Exception as e:
                logger.error(f"   ❌ Error enriching {scientific_name}: {e}")
                db.session.rollback()
        
        logger.info(f"\n✅ PHASE 3 COMPLETE: Enriched {enriched_count}/{len(orchids_to_enrich)} orchids")
        return enriched_count
        
    except Exception as e:
        logger.error(f"❌ Phase 3 failed: {e}")
        return 0

def enrich_phase1_phase2_ai_vision(limit=50):
    """
    PHASE 1 & 2: AI Vision Analysis
    Phase 1 (8 fields): flower_color, bloom_stage, inflorescence_type, inflorescence_position, 
                       bloombot_category, widget_visibility, is_hybrid, image_caption
    Phase 2 (13 fields): leaf_shape, pseudobulb_presence, pseudobulb_form, labellum_type, etc.
    """
    logger.info("\n" + "=" * 80)
    logger.info("PHASE 1 & 2: AI Vision Analysis")
    logger.info("=" * 80)
    
    try:
        import openai
        
        if not os.environ.get('OPENAI_API_KEY'):
            logger.error("❌ OPENAI_API_KEY not found!")
            return 0
        
        openai_client = openai.OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        logger.info("✅ OpenAI client initialized")
        
        # Find orchids with images but missing Phase 1/2 data
        orchids_to_analyze = OrchidRecord.query.filter(
            and_(
                OrchidRecord.google_drive_id != None,  # Has image
                or_(
                    OrchidRecord.flower_color == None,
                    OrchidRecord.bloom_stage == None,
                    OrchidRecord.leaf_shape == None
                )
            )
        ).limit(limit).all()
        
        logger.info(f"📊 Found {len(orchids_to_analyze)} orchids needing AI vision analysis")
        
        analyzed_count = 0
        for orchid in orchids_to_analyze:
            try:
                scientific_name = f"{orchid.genus} {orchid.species}" if orchid.species and orchid.genus else orchid.display_name
                logger.info(f"🔍 Analyzing: {scientific_name} (ID: {orchid.id})")
                
                # Construct image URL
                if orchid.google_drive_id:
                    image_url = f"https://drive.google.com/uc?export=view&id={orchid.google_drive_id}"
                else:
                    logger.info(f"   ⚠️ No image available")
                    continue
                
                # AI Vision Analysis Prompt
                prompt = f"""Analyze this orchid image for {scientific_name} and extract the following metadata:

PHASE 1 - Visual Analysis (8 fields):
1. flower_color: Primary color(s) of the flower (e.g., "pink", "white with purple spots")
2. bloom_stage: Current blooming stage (bud/opening/full_bloom/fading/seed_pod)
3. inflorescence_type: Type of flower arrangement (single/spike/raceme/panicle/umbel)
4. inflorescence_position: Position of flowers (terminal/lateral/basal)
5. bloombot_category: Flower type category (cattleya_type/phalaenopsis_type/oncidium_type/dendrobium_type/other)
6. is_hybrid: Is this a hybrid? (true/false)
7. image_caption: Brief descriptive caption (1 sentence)

PHASE 2 - Morphological Analysis (13 fields):
8. leaf_shape: Leaf shape (oval/lance/linear/strap/terete)
9. pseudobulb_presence: Are pseudobulbs visible? (true/false)
10. pseudobulb_form: If present, what form? (ovoid/cylindrical/conical/flattened/absent)
11. labellum_type: Lip/labellum type (simple/lobed/fringed/pouch/column)
12. flower_resupination: Are flowers twisted/resupinate? (true/false)
13. tissue_succulence: Leaf tissue type (thin/medium/thick_succulent)
14. growth_rate: Apparent growth habit (slow/moderate/fast)

Respond ONLY with valid JSON. Use null for uncertain values.
Format: {{"flower_color": "value", "bloom_stage": "value", ...}}"""

                try:
                    response = openai_client.chat.completions.create(
                        model="gpt-4o-mini",  # Cost-effective for Phase 1
                        messages=[
                            {"role": "system", "content": "You are an expert orchid botanist analyzing orchid images. Respond only with valid JSON."},
                            {"role": "user", "content": [
                                {"type": "text", "text": prompt},
                                {"type": "image_url", "image_url": {"url": image_url}}
                            ]}
                        ],
                        max_tokens=500,
                        temperature=0.3
                    )
                    
                    ai_response = response.choices[0].message.content
                    
                    # Parse JSON response
                    import json
                    try:
                        # Extract JSON from response (handles markdown code blocks)
                        if '```json' in ai_response:
                            ai_response = ai_response.split('```json')[1].split('```')[0].strip()
                        elif '```' in ai_response:
                            ai_response = ai_response.split('```')[1].split('```')[0].strip()
                        
                        metadata = json.loads(ai_response)
                        
                        # Update Phase 1 fields
                        if metadata.get('flower_color'):
                            orchid.flower_color = metadata['flower_color']
                        if metadata.get('bloom_stage'):
                            orchid.bloom_stage = metadata['bloom_stage']
                        if metadata.get('inflorescence_type'):
                            orchid.inflorescence_type = metadata['inflorescence_type']
                        if metadata.get('inflorescence_position'):
                            orchid.inflorescence_position = metadata['inflorescence_position']
                        if metadata.get('bloombot_category'):
                            orchid.bloombot_category = metadata['bloombot_category']
                        if metadata.get('is_hybrid') is not None:
                            orchid.is_hybrid = metadata['is_hybrid']
                        if metadata.get('image_caption'):
                            orchid.image_caption = metadata['image_caption']
                        
                        # Update Phase 2 fields
                        if metadata.get('leaf_shape'):
                            orchid.leaf_shape = metadata['leaf_shape']
                        if metadata.get('pseudobulb_presence') is not None:
                            orchid.pseudobulb_presence = metadata['pseudobulb_presence']
                        if metadata.get('pseudobulb_form'):
                            orchid.pseudobulb_form = metadata['pseudobulb_form']
                        if metadata.get('labellum_type'):
                            orchid.labellum_type = metadata['labellum_type']
                        if metadata.get('flower_resupination') is not None:
                            orchid.flower_resupination = metadata['flower_resupination']
                        if metadata.get('tissue_succulence'):
                            orchid.tissue_succulence = metadata['tissue_succulence']
                        if metadata.get('growth_rate'):
                            orchid.growth_rate = metadata['growth_rate']
                        
                        db.session.commit()
                        analyzed_count += 1
                        logger.info(f"   ✅ Analyzed: {metadata.get('flower_color', 'N/A')}, {metadata.get('bloom_stage', 'N/A')}")
                        
                    except json.JSONDecodeError as je:
                        logger.error(f"   ❌ JSON parse error: {je}")
                        logger.debug(f"   Response was: {ai_response[:200]}")
                        
                except Exception as api_error:
                    logger.error(f"   ❌ OpenAI API error: {api_error}")
                    
            except Exception as e:
                logger.error(f"   ❌ Error analyzing {scientific_name}: {e}")
                db.session.rollback()
        
        logger.info(f"\n✅ PHASE 1 & 2 COMPLETE: Analyzed {analyzed_count}/{len(orchids_to_analyze)} orchids")
        return analyzed_count
        
    except Exception as e:
        logger.error(f"❌ Phase 1 & 2 failed: {e}")
        return 0

def show_enrichment_stats():
    """Show current enrichment statistics"""
    logger.info("\n" + "=" * 80)
    logger.info("ENRICHMENT STATISTICS")
    logger.info("=" * 80)
    
    with app.app_context():
        total_orchids = OrchidRecord.query.count()
        
        # Phase 1 stats
        has_flower_color = OrchidRecord.query.filter(OrchidRecord.flower_color != None).count()
        has_bloom_stage = OrchidRecord.query.filter(OrchidRecord.bloom_stage != None).count()
        
        # Phase 2 stats
        has_leaf_shape = OrchidRecord.query.filter(OrchidRecord.leaf_shape != None).count()
        has_pseudobulb = OrchidRecord.query.filter(OrchidRecord.pseudobulb_presence != None).count()
        
        # Phase 3 stats
        has_taxonomic = OrchidRecord.query.filter(OrchidRecord.taxonomic_status != None).count()
        has_continent = OrchidRecord.query.filter(OrchidRecord.continent != None).count()
        
        logger.info(f"Total Orchids: {total_orchids}")
        logger.info(f"\nPHASE 1 Coverage:")
        logger.info(f"  Flower Color: {has_flower_color} ({has_flower_color/total_orchids*100:.1f}%)")
        logger.info(f"  Bloom Stage: {has_bloom_stage} ({has_bloom_stage/total_orchids*100:.1f}%)")
        logger.info(f"\nPHASE 2 Coverage:")
        logger.info(f"  Leaf Shape: {has_leaf_shape} ({has_leaf_shape/total_orchids*100:.1f}%)")
        logger.info(f"  Pseudobulb: {has_pseudobulb} ({has_pseudobulb/total_orchids*100:.1f}%)")
        logger.info(f"\nPHASE 3 Coverage:")
        logger.info(f"  Taxonomic Status: {has_taxonomic} ({has_taxonomic/total_orchids*100:.1f}%)")
        logger.info(f"  Continent: {has_continent} ({has_continent/total_orchids*100:.1f}%)")

def main():
    """Main enrichment orchestrator"""
    logger.info("\n" + "=" * 80)
    logger.info("🌺 ORCHID METADATA ENRICHMENT SYSTEM - ACTIVATING")
    logger.info("=" * 80)
    logger.info(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    with app.app_context():
        # Show before stats
        show_enrichment_stats()
        
        # Run Phase 3 (GBIF) - Free API, run more
        logger.info("\n🚀 Starting Phase 3 (GBIF Taxonomic Data)...")
        phase3_count = enrich_phase3_gbif_data(limit=200)
        
        # Run Phase 1 & 2 (AI Vision) - Costs money, run fewer
        logger.info("\n🚀 Starting Phase 1 & 2 (AI Vision Analysis)...")
        phase12_count = enrich_phase1_phase2_ai_vision(limit=25)
        
        # Show after stats
        show_enrichment_stats()
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ ENRICHMENT COMPLETE!")
        logger.info("=" * 80)
        logger.info(f"Phase 3 (GBIF): {phase3_count} orchids enriched")
        logger.info(f"Phase 1 & 2 (AI): {phase12_count} orchids analyzed")
        logger.info(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("\n💡 View results at: /admin/field-completion")
        logger.info("=" * 80)

if __name__ == "__main__":
    main()
