"""
Orchid Data Enrichment System
Populates missing cultural information, blooming seasons, habitat details, and growing requirements
PRIORITY: Real phenotypic trait data from GBIF/EOL authoritative sources
FALLBACK: AI generation for missing data
"""

import os
import logging
from typing import Dict, List, Optional
from datetime import datetime
from flask import Blueprint, jsonify, request, render_template
from flask_login import login_required
from app import db
from models import OrchidRecord
from sqlalchemy import func
import openai
import folium
from folium.plugins import MarkerCluster
import json

# Import admin authentication
from admin_system import admin_required

logger = logging.getLogger(__name__)

orchid_enrichment = Blueprint('orchid_enrichment', __name__, url_prefix='/admin/enrichment')

class OrchidDataEnricher:
    """
    Enriches orchid records with comprehensive cultural and botanical information
    PRIORITY: Uses authoritative GBIF and EOL databases for real phenotypic traits
    FALLBACK: AI generation only when authoritative data is unavailable
    """
    
    def __init__(self):
        # Initialize external database integrators
        try:
            from external_databases.gbif_integration import GBIFIntegrator
            self.gbif = GBIFIntegrator()
            logger.info("✅ GBIF integration initialized")
        except Exception as e:
            logger.warning(f"GBIF integration not available: {e}")
            self.gbif = None
        
        try:
            from eol_integration import EOLIntegrator
            self.eol = EOLIntegrator()
            logger.info("✅ EOL integration initialized")
        except Exception as e:
            logger.warning(f"EOL integration not available: {e}")
            self.eol = None
        
        # AI fallback
        self.openai_client = None
        if os.environ.get('OPENAI_API_KEY'):
            self.openai_client = openai.OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
            logger.info("✅ OpenAI client initialized for fallback enrichment")
    
    def generate_comprehensive_orchid_data(self, genus: str, species: str, existing_data: Dict = None) -> Dict:
        """
        Generate comprehensive orchid information using AI
        """
        if not self.openai_client:
            return {"error": "OpenAI not configured"}
        
        scientific_name = f"{genus} {species}" if species else genus
        
        prompt = f"""You are a world-renowned orchid botanist and horticulturist. Provide comprehensive, accurate information about {scientific_name}.

Generate a structured response with the following information:

1. NATIVE HABITAT & ORIGIN:
   - Geographic origin (countries/regions)
   - Specific habitat type (cloud forest, rainforest, etc.)
   - Elevation range
   - Natural growing conditions

2. BLOOMING SEASON:
   - Primary blooming months
   - Bloom duration
   - Flowering frequency per year
   - Seasonal triggers

3. CULTURAL REQUIREMENTS:
   - Light: (low/medium/bright/very bright, exact lux if known)
   - Temperature: Day and night ranges in °C and °F
   - Humidity: Percentage range
   - Air circulation needs

4. WATERING & FERTILIZING:
   - Watering frequency and method
   - Substrate preferences (bark, moss, etc.)
   - Fertilizer type and schedule
   - Seasonal adjustments

5. GROWTH CHARACTERISTICS:
   - Growth habit (epiphytic/terrestrial/lithophytic)
   - Pseudobulb presence/absence
   - Leaf characteristics
   - Root system type
   - Mature plant size

6. SPECIAL CARE NOTES:
   - Beginner/intermediate/advanced difficulty
   - Common problems and solutions
   - Propagation methods
   - Resting period requirements
   - Fragrance information if applicable

Provide factual, species-specific information. If certain details are variable or unknown, indicate this clearly.
Format your response as valid JSON with keys: native_habitat, origin_countries, elevation_range, bloom_season, bloom_months, bloom_duration, light_requirements, light_intensity, temperature_day, temperature_night, temperature_range, humidity_range, air_circulation, watering_frequency, watering_method, substrate_preference, fertilizer_schedule, growth_habit, pseudobulb, leaf_form, root_type, mature_size, care_difficulty, special_notes, fragrance."""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert orchidologist with deep knowledge of orchid cultivation, taxonomy, and ecology. Provide accurate, detailed information formatted as JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for more factual responses
                max_tokens=1500
            )
            
            ai_response = response.choices[0].message.content
            
            # Try to parse JSON response
            import json
            try:
                # Extract JSON from response (may be wrapped in markdown code blocks)
                if "```json" in ai_response:
                    ai_response = ai_response.split("```json")[1].split("```")[0].strip()
                elif "```" in ai_response:
                    ai_response = ai_response.split("```")[1].split("```")[0].strip()
                
                enriched_data = json.loads(ai_response)
                enriched_data['ai_generated'] = True
                enriched_data['ai_timestamp'] = datetime.now().isoformat()
                return enriched_data
                
            except json.JSONDecodeError:
                # Fallback: parse text response
                logger.warning(f"Could not parse JSON for {scientific_name}, using text response")
                return {
                    "raw_ai_response": ai_response,
                    "ai_generated": True,
                    "parsing_failed": True
                }
                
        except Exception as e:
            logger.error(f"Error enriching {scientific_name}: {str(e)}")
            return {"error": str(e)}
    
    def get_gbif_phenotypic_traits(self, genus: str, species: str) -> Dict:
        """
        Pull real phenotypic trait data from GBIF including distribution, habitat, elevation
        PRIORITY: Use authoritative occurrence data before AI
        """
        if not self.gbif:
            return {}
        
        scientific_name = f"{genus} {species}" if species else genus
        logger.info(f"📊 Fetching GBIF phenotypic traits for {scientific_name}")
        
        try:
            # Get occurrence data with geographic information
            occurrences = self.gbif.get_occurrences(scientific_name=scientific_name, limit=100, with_images=False)
            
            if not occurrences or 'results' not in occurrences:
                return {}
            
            traits = {
                'data_source': 'GBIF',
                'data_timestamp': datetime.now().isoformat(),
                'occurrence_count': len(occurrences['results']),
                'countries': [],
                'elevations': [],
                'coordinates': [],
                'habitats': []
            }
            
            # Extract phenotypic data from occurrences
            for occ in occurrences['results']:
                # Geographic distribution
                if occ.get('country'):
                    traits['countries'].append(occ['country'])
                
                # Elevation data
                if occ.get('elevation'):
                    traits['elevations'].append(occ['elevation'])
                
                # Coordinates for mapping
                if occ.get('decimalLatitude') and occ.get('decimalLongitude'):
                    traits['coordinates'].append({
                        'lat': occ['decimalLatitude'],
                        'lon': occ['decimalLongitude'],
                        'location': occ.get('locality', 'Unknown')
                    })
                
                # Habitat information
                if occ.get('habitat'):
                    traits['habitats'].append(occ['habitat'])
            
            # Aggregate data
            if traits['countries']:
                unique_countries = list(set(traits['countries']))
                traits['origin_countries'] = ', '.join(unique_countries[:10])  # Top 10
            
            if traits['elevations']:
                traits['elevation_min'] = min(traits['elevations'])
                traits['elevation_max'] = max(traits['elevations'])
                traits['elevation_range'] = f"{traits['elevation_min']}-{traits['elevation_max']}m"
            
            logger.info(f"✅ Found {len(traits['coordinates'])} GBIF occurrence points for {scientific_name}")
            return traits
            
        except Exception as e:
            logger.error(f"❌ GBIF trait extraction failed: {e}")
            return {}
    
    def get_eol_phenotypic_traits(self, genus: str, species: str) -> Dict:
        """
        Pull real phenotypic trait data from EOL TraitBank
        PRIORITY: Use authoritative trait data before AI
        """
        if not self.eol:
            return {}
        
        scientific_name = f"{genus} {species}" if species else genus
        logger.info(f"📊 Fetching EOL phenotypic traits for {scientific_name}")
        
        try:
            # Search EOL for the species
            eol_result = self.eol.search_eol_species(scientific_name)
            
            if not eol_result:
                return {}
            
            # Get detailed page data including traits
            page_id = eol_result.get('id')
            eol_data = self.eol.get_eol_page_data(page_id)
            
            if not eol_data:
                return {}
            
            # Extract trait data
            traits = self.eol.extract_trait_data(eol_data)
            traits['data_source'] = 'EOL'
            traits['data_timestamp'] = datetime.now().isoformat()
            
            logger.info(f"✅ Found EOL traits for {scientific_name}")
            return traits
            
        except Exception as e:
            logger.error(f"❌ EOL trait extraction failed: {e}")
            return {}
    
    def create_distribution_map(self, orchid_id: int, coordinates: List[Dict]) -> str:
        """
        Create an interactive distribution map using Folium
        Returns HTML string for embedding
        """
        if not coordinates:
            return None
        
        try:
            # Calculate center point
            avg_lat = sum(c['lat'] for c in coordinates) / len(coordinates)
            avg_lon = sum(c['lon'] for c in coordinates) / len(coordinates)
            
            # Create map
            m = folium.Map(
                location=[avg_lat, avg_lon],
                zoom_start=4,
                tiles='OpenStreetMap'
            )
            
            # Add marker cluster for better performance
            marker_cluster = MarkerCluster().add_to(m)
            
            # Add markers
            for coord in coordinates:
                folium.Marker(
                    location=[coord['lat'], coord['lon']],
                    popup=coord.get('location', 'Occurrence'),
                    icon=folium.Icon(color='purple', icon='leaf', prefix='fa')
                ).add_to(marker_cluster)
            
            # Save map HTML
            map_html = m._repr_html_()
            
            # Store map in database
            orchid = OrchidRecord.query.get(orchid_id)
            if orchid:
                orchid.distribution_map_html = map_html
                db.session.commit()
            
            logger.info(f"✅ Created distribution map with {len(coordinates)} points")
            return map_html
            
        except Exception as e:
            logger.error(f"❌ Map creation failed: {e}")
            return None

    def enrich_orchid_record(self, orchid_id: int, force_refresh: bool = False) -> Dict:
        """
        Enrich a single orchid record with comprehensive data
        PRIORITY ORDER: 1) GBIF phenotypic traits, 2) EOL trait data, 3) AI fallback
        """
        orchid = OrchidRecord.query.get(orchid_id)
        if not orchid:
            return {"error": "Orchid not found"}
        
        # Check if already enriched (unless force refresh)
        if not force_refresh and orchid.cultural_notes and len(orchid.cultural_notes) > 100:
            return {"status": "already_enriched", "orchid_id": orchid_id}
        
        genus = orchid.genus or "Unknown"
        species = orchid.species or ""
        
        # PRIORITY 1: Pull real phenotypic trait data from GBIF
        gbif_traits = self.get_gbif_phenotypic_traits(genus, species)
        
        # PRIORITY 2: Pull trait data from EOL
        eol_traits = self.get_eol_phenotypic_traits(genus, species)
        
        # Combine authoritative data
        enriched_data = {}
        
        # Merge GBIF data (distribution, habitat, elevation)
        if gbif_traits:
            enriched_data.update(gbif_traits)
            logger.info(f"📊 Using GBIF data for {genus} {species}")
        
        # Merge EOL data (traits, descriptions)
        if eol_traits:
            enriched_data.update(eol_traits)
            logger.info(f"📊 Using EOL data for {genus} {species}")
        
        # PRIORITY 3: AI fallback for missing data only
        if not enriched_data or len(enriched_data) < 5:
            logger.info(f"🤖 Falling back to AI for {genus} {species} - insufficient authoritative data")
            ai_data = self.generate_comprehensive_orchid_data(genus, species)
            # Only use AI data for fields not already populated
            for key, value in ai_data.items():
                if key not in enriched_data or not enriched_data[key]:
                    enriched_data[key] = value
            enriched_data['data_source'] = 'AI_fallback'
        else:
            enriched_data['data_source'] = f"GBIF+EOL ({len(enriched_data)} fields)"
        
        if "error" in enriched_data:
            return enriched_data
        
        # Create distribution map from GBIF coordinates
        if enriched_data.get('coordinates'):
            map_html = self.create_distribution_map(orchid_id, enriched_data['coordinates'])
            if map_html:
                logger.info(f"🗺️ Created distribution map for {genus} {species}")
        
        # Update orchid record with enriched data
        try:
            # Habitat & Origin (GBIF priority)
            if enriched_data.get('native_habitat'):
                orchid.native_habitat = enriched_data['native_habitat']
            if enriched_data.get('origin_countries'):
                orchid.region = enriched_data['origin_countries']
            if enriched_data.get('elevation_range'):
                if not orchid.native_habitat or 'elevation' not in orchid.native_habitat.lower():
                    orchid.native_habitat = f"{orchid.native_habitat or ''} Elevation: {enriched_data['elevation_range']}".strip()
            
            # Blooming
            if enriched_data.get('bloom_season'):
                orchid.bloom_time = enriched_data['bloom_season']
            if enriched_data.get('bloom_months'):
                orchid.bloom_season_indicator = enriched_data['bloom_months']
            
            # Light & Temperature
            if enriched_data.get('light_requirements'):
                orchid.light_requirements = enriched_data['light_requirements']
            if enriched_data.get('temperature_range'):
                orchid.temperature_range = enriched_data['temperature_range']
            
            # Water & Culture
            if enriched_data.get('watering_frequency'):
                orchid.water_requirements = f"{enriched_data['watering_frequency']}. {enriched_data.get('watering_method', '')}"
            if enriched_data.get('fertilizer_schedule'):
                orchid.fertilizer_needs = enriched_data['fertilizer_schedule']
            
            # Growth characteristics
            if enriched_data.get('growth_habit'):
                orchid.growth_habit = enriched_data['growth_habit']
            if enriched_data.get('leaf_form'):
                orchid.leaf_form = enriched_data['leaf_form']
            if enriched_data.get('pseudobulb'):
                orchid.pseudobulb_presence = enriched_data['pseudobulb'] in ['Yes', 'Present', True, 'yes', 'true']
            
            # Consolidated cultural notes
            cultural_notes_parts = []
            
            if enriched_data.get('care_difficulty'):
                cultural_notes_parts.append(f"**Care Level:** {enriched_data['care_difficulty']}")
            
            if enriched_data.get('special_notes'):
                cultural_notes_parts.append(f"**Special Care:** {enriched_data['special_notes']}")
            
            if enriched_data.get('substrate_preference'):
                cultural_notes_parts.append(f"**Potting:** {enriched_data['substrate_preference']}")
            
            if enriched_data.get('humidity_range'):
                cultural_notes_parts.append(f"**Humidity:** {enriched_data['humidity_range']}")
            
            if enriched_data.get('air_circulation'):
                cultural_notes_parts.append(f"**Air Flow:** {enriched_data['air_circulation']}")
            
            if enriched_data.get('fragrance'):
                cultural_notes_parts.append(f"**Fragrance:** {enriched_data['fragrance']}")
            
            orchid.cultural_notes = "\n\n".join(cultural_notes_parts)
            
            # Climate preference
            if enriched_data.get('temperature_range'):
                temp_range = enriched_data['temperature_range'].lower()
                if 'cool' in temp_range or '10' in temp_range or '50' in temp_range:
                    orchid.climate_preference = 'cool'
                elif 'warm' in temp_range or '27' in temp_range or '80' in temp_range:
                    orchid.climate_preference = 'warm'
                else:
                    orchid.climate_preference = 'intermediate'
            
            db.session.commit()
            
            return {
                "status": "success",
                "orchid_id": orchid_id,
                "genus": genus,
                "species": species,
                "fields_updated": len([k for k, v in enriched_data.items() if v]),
                "enriched_data": enriched_data
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating orchid {orchid_id}: {str(e)}")
            return {"error": str(e), "orchid_id": orchid_id}
    
    def batch_enrich_orchids(self, limit: int = 50, genus_filter: str = None, missing_data_only: bool = True) -> Dict:
        """
        Enrich multiple orchid records in batch
        """
        query = OrchidRecord.query
        
        # Filter for records missing cultural data
        if missing_data_only:
            query = query.filter(
                (OrchidRecord.cultural_notes == None) | 
                (OrchidRecord.native_habitat == None) |
                (OrchidRecord.bloom_time == None) |
                (OrchidRecord.light_requirements == None)
            )
        
        # Filter by genus if specified
        if genus_filter:
            query = query.filter(OrchidRecord.genus == genus_filter)
        
        orchids_to_enrich = query.limit(limit).all()
        
        results = {
            "total_processed": 0,
            "successful": 0,
            "failed": 0,
            "already_enriched": 0,
            "details": []
        }
        
        for orchid in orchids_to_enrich:
            result = self.enrich_orchid_record(orchid.id, force_refresh=False)
            results["total_processed"] += 1
            
            if result.get("status") == "success":
                results["successful"] += 1
            elif result.get("status") == "already_enriched":
                results["already_enriched"] += 1
            else:
                results["failed"] += 1
            
            results["details"].append(result)
        
        return results

# Initialize enricher
enricher = OrchidDataEnricher()

# API Routes

@orchid_enrichment.route('/dashboard')
@admin_required
def enrichment_dashboard():
    """Admin dashboard for orchid data enrichment"""
    # Get statistics
    stats = db.session.query(
        func.count(OrchidRecord.id).label('total'),
        func.count(OrchidRecord.native_habitat).label('has_habitat'),
        func.count(OrchidRecord.bloom_time).label('has_bloom'),
        func.count(OrchidRecord.light_requirements).label('has_light'),
        func.count(OrchidRecord.cultural_notes).label('has_culture')
    ).first()
    
    # Get genus breakdown
    genus_stats = db.session.query(
        OrchidRecord.genus,
        func.count(OrchidRecord.id).label('count')
    ).filter(OrchidRecord.genus != None).group_by(OrchidRecord.genus).order_by(func.count(OrchidRecord.id).desc()).limit(20).all()
    
    return render_template('admin/enrichment_dashboard.html',
                         stats=stats,
                         genus_stats=genus_stats)

@orchid_enrichment.route('/api/enrich-single/<int:orchid_id>', methods=['POST'])
@admin_required
def api_enrich_single(orchid_id):
    """Enrich a single orchid record"""
    force_refresh = request.args.get('force', 'false').lower() == 'true'
    result = enricher.enrich_orchid_record(orchid_id, force_refresh=force_refresh)
    return jsonify(result)

@orchid_enrichment.route('/api/enrich-batch', methods=['POST'])
@admin_required
def api_enrich_batch():
    """Batch enrich orchid records"""
    data = request.get_json() or {}
    limit = data.get('limit', 50)
    genus_filter = data.get('genus')
    missing_only = data.get('missing_only', True)
    
    results = enricher.batch_enrich_orchids(limit=limit, genus_filter=genus_filter, missing_data_only=missing_only)
    return jsonify(results)

@orchid_enrichment.route('/api/stats')
@admin_required
def api_enrichment_stats():
    """Get enrichment statistics"""
    stats = db.session.query(
        func.count(OrchidRecord.id).label('total_orchids'),
        func.count(OrchidRecord.native_habitat).label('has_habitat'),
        func.count(OrchidRecord.bloom_time).label('has_bloom_time'),
        func.count(OrchidRecord.light_requirements).label('has_light'),
        func.count(OrchidRecord.temperature_range).label('has_temperature'),
        func.count(OrchidRecord.water_requirements).label('has_water'),
        func.count(OrchidRecord.cultural_notes).label('has_cultural_notes')
    ).first()
    
    return jsonify({
        'total_orchids': stats.total_orchids,
        'coverage': {
            'native_habitat': {'count': stats.has_habitat, 'percentage': round((stats.has_habitat / stats.total_orchids * 100), 1)},
            'bloom_time': {'count': stats.has_bloom_time, 'percentage': round((stats.has_bloom_time / stats.total_orchids * 100), 1)},
            'light_requirements': {'count': stats.has_light, 'percentage': round((stats.has_light / stats.total_orchids * 100), 1)},
            'temperature_range': {'count': stats.has_temperature, 'percentage': round((stats.has_temperature / stats.total_orchids * 100), 1)},
            'water_requirements': {'count': stats.has_water, 'percentage': round((stats.has_water / stats.total_orchids * 100), 1)},
            'cultural_notes': {'count': stats.has_cultural_notes, 'percentage': round((stats.has_cultural_notes / stats.total_orchids * 100), 1)}
        }
    })

logger.info("🌺 Orchid Data Enrichment System initialized")
