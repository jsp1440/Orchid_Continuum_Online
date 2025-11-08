"""
Geographic Orchid Trait Comparison System

Compares visible and inherited traits of the same orchid species across different
geographic locations using GBIF, POWO, Baker climate data, and AI analysis.

ALL AI-generated inferences are clearly marked with disclaimers and source citations.
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json
import os
from openai import OpenAI

from models import OrchidRecord, db
from external_databases.gbif_integration import GBIFIntegrator
from powo_integration import POWOIntegrator
from location_based_culture_system import LocationBasedCultureSystem

logger = logging.getLogger(__name__)

class GeographicTraitComparison:
    """
    Compare orchid traits across geographic locations using authoritative data
    and AI analysis with clear disclaimers
    """
    
    def __init__(self):
        self.gbif = GBIFIntegrator()
        self.powo = POWOIntegrator()
        self.climate_system = LocationBasedCultureSystem()
        
        # Initialize OpenAI for trait analysis
        api_key = os.environ.get('OPENAI_API_KEY')
        self.openai_client = OpenAI(api_key=api_key) if api_key else None
    
    def get_geographic_variants(self, scientific_name: str) -> Dict:
        """
        Get all geographic variants of a species with their locations and traits
        
        Returns:
            Dictionary with geographic distribution and specimen data
        """
        try:
            logger.info(f"🌍 Getting geographic variants for {scientific_name}")
            
            # Get database records for this species
            db_specimens = OrchidRecord.query.filter(
                OrchidRecord.scientific_name.ilike(f"%{scientific_name}%")
            ).all()
            
            # Get GBIF occurrences for geographic distribution
            gbif_occurrences = self.gbif.get_occurrences(
                scientific_name=scientific_name,
                limit=100,
                with_images=True
            )
            
            # Get POWO distribution data for native ranges
            powo_distribution = self.powo.get_distribution(scientific_name)
            
            # Organize specimens by location
            locations = {}
            
            # Process database specimens
            for specimen in db_specimens:
                if specimen.decimal_latitude and specimen.decimal_longitude:
                    location_key = self._get_location_key(
                        specimen.decimal_latitude,
                        specimen.decimal_longitude,
                        specimen.country or specimen.region
                    )
                    
                    if location_key not in locations:
                        locations[location_key] = {
                            'location_name': specimen.country or specimen.region or 'Unknown',
                            'latitude': specimen.decimal_latitude,
                            'longitude': specimen.decimal_longitude,
                            'specimens': [],
                            'climate_data': None,
                            'data_sources': ['OrchidContinuum Database']
                        }
                    
                    locations[location_key]['specimens'].append({
                        'id': specimen.id,
                        'display_name': specimen.display_name,
                        'image_url': specimen.image_url,
                        'visible_traits': self._extract_visible_traits(specimen),
                        'photographer': specimen.photographer,
                        'event_date': specimen.event_date
                    })
            
            # Add GBIF occurrences
            if gbif_occurrences and gbif_occurrences.get('results'):
                for occ in gbif_occurrences['results']:
                    loc = occ.get('location', {})
                    if loc.get('latitude') and loc.get('longitude'):
                        location_key = self._get_location_key(
                            loc['latitude'],
                            loc['longitude'],
                            loc.get('country')
                        )
                        
                        if location_key not in locations:
                            locations[location_key] = {
                                'location_name': loc.get('country') or loc.get('locality') or 'Unknown',
                                'latitude': loc['latitude'],
                                'longitude': loc['longitude'],
                                'specimens': [],
                                'climate_data': None,
                                'data_sources': ['GBIF']
                            }
                        
                        if 'GBIF' not in locations[location_key]['data_sources']:
                            locations[location_key]['data_sources'].append('GBIF')
            
            # Get climate data for each location
            for location_key, location_data in locations.items():
                if location_data['latitude'] and location_data['longitude']:
                    climate = self.climate_system._analyze_location_climate({
                        'latitude': location_data['latitude'],
                        'longitude': location_data['longitude']
                    })
                    location_data['climate_data'] = climate
            
            return {
                'scientific_name': scientific_name,
                'total_locations': len(locations),
                'locations': locations,
                'powo_native_distribution': powo_distribution,
                'gbif_occurrence_count': gbif_occurrences.get('count', 0) if gbif_occurrences else 0,
                'data_sources': {
                    'database': len(db_specimens),
                    'gbif': gbif_occurrences.get('count', 0) if gbif_occurrences else 0,
                    'powo': 'Available' if powo_distribution else 'Not Available'
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting geographic variants: {e}")
            return {'error': str(e)}
    
    def compare_trait_variations(self, scientific_name: str) -> Dict:
        """
        Compare trait variations across geographic locations with AI analysis
        
        Returns:
            Comparison report with visible traits, climate correlations, and AI insights
            ALL AI inferences clearly marked with disclaimers
        """
        try:
            logger.info(f"🔬 Comparing trait variations for {scientific_name}")
            
            # Get geographic variants
            variants = self.get_geographic_variants(scientific_name)
            
            if 'error' in variants:
                return variants
            
            if variants['total_locations'] < 2:
                return {
                    'scientific_name': scientific_name,
                    'status': 'insufficient_data',
                    'message': 'Need at least 2 geographic locations for comparison',
                    'available_locations': variants['total_locations']
                }
            
            # Analyze trait correlations
            comparison = {
                'scientific_name': scientific_name,
                'comparison_date': datetime.now().isoformat(),
                'total_locations_analyzed': variants['total_locations'],
                'locations': {},
                'climate_correlations': self._analyze_climate_correlations(variants),
                'ai_trait_analysis': None,
                'data_citations': self._generate_citations(variants)
            }
            
            # Process each location
            for location_key, location_data in variants['locations'].items():
                comparison['locations'][location_key] = {
                    'location_name': location_data['location_name'],
                    'coordinates': {
                        'latitude': location_data['latitude'],
                        'longitude': location_data['longitude']
                    },
                    'specimen_count': len(location_data['specimens']),
                    'climate': location_data['climate_data'],
                    'observed_traits': self._aggregate_traits(location_data['specimens']),
                    'data_sources': location_data['data_sources']
                }
            
            # AI-powered trait analysis (with clear disclaimer)
            if self.openai_client and len(variants['locations']) >= 2:
                comparison['ai_trait_analysis'] = self._ai_analyze_trait_patterns(
                    scientific_name,
                    comparison['locations']
                )
            
            return comparison
            
        except Exception as e:
            logger.error(f"Error comparing trait variations: {e}")
            return {'error': str(e)}
    
    def _extract_visible_traits(self, specimen: OrchidRecord) -> Dict:
        """Extract visible traits from specimen data"""
        traits = {}
        
        # Parse enriched metadata
        if specimen.eol_traits:
            try:
                eol_data = json.loads(specimen.eol_traits)
                
                # Image metadata (EXIF + AI visual analysis)
                if eol_data.get('image_metadata'):
                    img_meta = eol_data['image_metadata']
                    traits['image_analysis'] = {
                        'camera': img_meta.get('camera_info'),
                        'capture_date': img_meta.get('date_time'),
                        'gps_location': img_meta.get('gps_location'),
                        'ai_visual_description': img_meta.get('ai_analysis', {}).get('visual_description')
                    }
                
                # POWO traits
                if eol_data.get('powo_data'):
                    powo = eol_data['powo_data']
                    traits['authoritative_taxonomy'] = {
                        'accepted_name': powo.get('accepted_name'),
                        'synonyms': powo.get('synonyms', []),
                        'source': 'Plants of the World Online (Kew Gardens)'
                    }
            except:
                pass
        
        # Basic observable traits
        traits['basic'] = {
            'growth_habit': specimen.growth_habit,
            'climate_preference': specimen.climate_preference,
            'bloom_time': specimen.bloom_time,
            'native_habitat': specimen.native_habitat
        }
        
        return traits
    
    def _aggregate_traits(self, specimens: List[Dict]) -> Dict:
        """Aggregate traits from multiple specimens in same location"""
        aggregated = {
            'specimen_count': len(specimens),
            'visible_traits': {},
            'data_quality': 'High' if len(specimens) >= 3 else 'Limited'
        }
        
        # Count trait occurrences
        growth_habits = []
        bloom_times = []
        
        for specimen in specimens:
            traits = specimen.get('visible_traits', {}).get('basic', {})
            if traits.get('growth_habit'):
                growth_habits.append(traits['growth_habit'])
            if traits.get('bloom_time'):
                bloom_times.append(traits['bloom_time'])
        
        if growth_habits:
            aggregated['visible_traits']['growth_habit'] = {
                'observed_values': list(set(growth_habits)),
                'sample_size': len(growth_habits)
            }
        
        if bloom_times:
            aggregated['visible_traits']['bloom_time'] = {
                'observed_values': list(set(bloom_times)),
                'sample_size': len(bloom_times)
            }
        
        return aggregated
    
    def _analyze_climate_correlations(self, variants: Dict) -> Dict:
        """Analyze correlations between climate and observed traits"""
        correlations = {
            'analysis_type': 'Statistical Correlation',
            'disclaimer': 'Correlations indicate potential relationships but do not prove causation. Environmental adaptation is complex and multifactorial.',
            'findings': []
        }
        
        locations = variants.get('locations', {})
        
        if len(locations) < 2:
            return correlations
        
        # Compare climate variables across locations
        temp_ranges = []
        humidity_levels = []
        location_names = []
        
        for location_key, location_data in locations.items():
            climate = location_data.get('climate_data', {})
            if climate:
                location_names.append(location_data['location_name'])
                
                if climate.get('temperature'):
                    temp_ranges.append(climate['temperature'].get('average'))
                
                if climate.get('humidity'):
                    humidity_levels.append(climate['humidity'])
        
        # Statistical observation (not AI inference)
        if temp_ranges and len(temp_ranges) >= 2:
            correlations['findings'].append({
                'variable': 'Temperature Range',
                'observation': f'Observed across {len(temp_ranges)} locations',
                'range': f'{min(temp_ranges)}°C to {max(temp_ranges)}°C',
                'variation': f'{max(temp_ranges) - min(temp_ranges)}°C difference',
                'interpretation': 'This species shows adaptation to varying temperature conditions' if max(temp_ranges) - min(temp_ranges) > 10 else 'This species appears in relatively similar temperature zones',
                'data_quality': 'Observational' if len(temp_ranges) < 5 else 'Good sample size'
            })
        
        return correlations
    
    def _ai_analyze_trait_patterns(self, scientific_name: str, locations: Dict) -> Dict:
        """
        AI-powered analysis of trait patterns with CLEAR DISCLAIMERS
        """
        if not self.openai_client:
            return None
        
        try:
            # Prepare location summary for AI
            location_summary = []
            for location_key, location_data in locations.items():
                location_summary.append({
                    'name': location_data['location_name'],
                    'coordinates': location_data['coordinates'],
                    'climate': location_data.get('climate'),
                    'observed_traits': location_data.get('observed_traits')
                })
            
            prompt = f"""As a botanical AI assistant, analyze the geographic variation in {scientific_name} across these locations:

{json.dumps(location_summary, indent=2)}

Provide analysis of:
1. Visible trait variations across locations
2. Potential environmental adaptations
3. Inherited vs. environmentally-influenced traits

IMPORTANT: Clearly distinguish between:
- Direct observations from the data
- Statistical correlations
- Hypothetical inferences that need further research

Format your response as structured JSON."""

            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a botanical research AI specializing in orchid trait analysis. Always distinguish between observed data, statistical correlations, and hypothetical inferences."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            ai_analysis = response.choices[0].message.content
            
            return {
                '⚠️ DISCLAIMER': '🤖 AI-GENERATED ANALYSIS - This analysis is generated by artificial intelligence and represents computational inferences, not peer-reviewed scientific conclusions. All statements should be verified with botanical experts and empirical research.',
                'analysis_type': 'AI-Powered Trait Pattern Recognition',
                'model': 'OpenAI GPT-4o',
                'generated_at': datetime.now().isoformat(),
                'confidence_level': 'Computational Inference - Requires Expert Verification',
                'analysis': ai_analysis,
                'data_sources_used': list(set([
                    source
                    for loc in locations.values()
                    for source in loc.get('data_sources', [])
                ])),
                'limitations': [
                    'AI analysis based on available data only',
                    'Does not replace field observations or laboratory analysis',
                    'Correlation does not imply causation',
                    'Sample size may be limited for statistical significance',
                    'Environmental factors are complex and multifactorial'
                ]
            }
            
        except Exception as e:
            logger.error(f"AI analysis error: {e}")
            return {
                'error': 'AI analysis unavailable',
                'reason': str(e)
            }
    
    def _get_location_key(self, lat: float, lng: float, country: str = None) -> str:
        """Generate location key for grouping nearby specimens"""
        # Round to ~11km precision (0.1 degree)
        lat_rounded = round(lat, 1)
        lng_rounded = round(lng, 1)
        return f"{country or 'Unknown'}_{lat_rounded}_{lng_rounded}"
    
    def _generate_citations(self, variants: Dict) -> List[Dict]:
        """Generate proper academic citations for all data sources"""
        citations = []
        
        # Database citation
        if variants['data_sources']['database'] > 0:
            citations.append({
                'source': 'The Orchid Continuum Database',
                'type': 'Database',
                'specimens': variants['data_sources']['database'],
                'accessed': datetime.now().strftime('%Y-%m-%d'),
                'citation': f"The Orchid Continuum. {variants['scientific_name']} specimen records. Retrieved {datetime.now().strftime('%B %d, %Y')}"
            })
        
        # GBIF citation
        if variants['data_sources']['gbif'] > 0:
            citations.append({
                'source': 'Global Biodiversity Information Facility (GBIF)',
                'type': 'Biodiversity Database',
                'occurrences': variants['data_sources']['gbif'],
                'accessed': datetime.now().strftime('%Y-%m-%d'),
                'url': 'https://www.gbif.org',
                'citation': f"GBIF.org. {variants['scientific_name']} occurrence data. Retrieved {datetime.now().strftime('%B %d, %Y')} from https://www.gbif.org"
            })
        
        # POWO citation
        if variants['data_sources']['powo'] == 'Available':
            citations.append({
                'source': 'Plants of the World Online (Kew Gardens)',
                'type': 'Taxonomic Authority',
                'accessed': datetime.now().strftime('%Y-%m-%d'),
                'url': 'https://powo.science.kew.org',
                'citation': f"Plants of the World Online. {variants['scientific_name']} taxonomic and distribution data. Royal Botanic Gardens, Kew. Retrieved {datetime.now().strftime('%B %d, %Y')}"
            })
        
        return citations


# Global instance
geographic_comparison = GeographicTraitComparison()

logger.info("🌍 Geographic Trait Comparison System initialized with AI disclaimers")
