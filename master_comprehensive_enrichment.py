#!/usr/bin/env python3
"""
MASTER COMPREHENSIVE ORCHID ENRICHMENT SYSTEM
==============================================
Combines multiple data sources for complete orchid metadata:
1. AI Vision Analysis (GPT-4o-mini) - Extract metadata from photos (~$8.69 for 2,897 orchids)
2. GBIF Data - Occurrence, distribution, elevation, habitat (FREE)
3. EOL Trait Data - Phenotypic traits, descriptions (FREE)
4. Correlation Analysis - Find patterns across data sources

Cost: ~$9 total for complete enrichment of 2,897 orchids
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import tempfile
import requests
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import io

# Import existing services
from app import app, db
from models import OrchidRecord
from ai_orchid_identification import AIOrchidIdentifier
from external_databases.gbif_integration import GBIFIntegrator
from eol_integration import EOLIntegrator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MasterOrchidEnricher:
    """
    Comprehensive orchid enrichment system combining multiple authoritative sources
    """
    
    def __init__(self):
        # Initialize AI vision analyzer (GPT-4o-mini)
        self.ai_identifier = AIOrchidIdentifier()
        logger.info("✅ AI Vision Analyzer initialized (GPT-4o-mini)")
        
        # Initialize external databases
        try:
            self.gbif = GBIFIntegrator()
            logger.info("✅ GBIF integration initialized")
        except Exception as e:
            logger.warning(f"⚠️ GBIF not available: {e}")
            self.gbif = None
        
        try:
            self.eol = EOLIntegrator()
            logger.info("✅ EOL integration initialized")
        except Exception as e:
            logger.warning(f"⚠️ EOL not available: {e}")
            self.eol = None
        
        # Statistics tracking
        self.stats = {
            'total_processed': 0,
            'ai_vision_success': 0,
            'gbif_success': 0,
            'eol_success': 0,
            'exif_found': 0,
            'correlations_found': 0,
            'errors': 0
        }
    
    def download_image(self, url: str) -> Optional[str]:
        """Download and convert image to proper format"""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            img = Image.open(io.BytesIO(response.content))
            
            # Convert to RGB if needed
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background
            
            # Save as JPEG
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
            img.convert('RGB').save(temp_file.name, 'JPEG', quality=95)
            temp_file.close()
            
            return temp_file.name
        except Exception as e:
            logger.error(f"❌ Failed to download image: {e}")
            return None
    
    def extract_exif_metadata(self, image_path: str) -> Dict:
        """Extract EXIF metadata including GPS and timestamp"""
        try:
            img = Image.open(image_path)
            exif_data = img._getexif()
            
            if not exif_data:
                return {'has_exif': False}
            
            exif = {}
            for tag_id, value in exif_data.items():
                tag = TAGS.get(tag_id, tag_id)
                exif[tag] = value
            
            # Extract GPS coordinates
            gps_latitude = None
            gps_longitude = None
            
            if 'GPSInfo' in exif:
                gps_info = {}
                for key in exif['GPSInfo'].keys():
                    decode = GPSTAGS.get(key, key)
                    gps_info[decode] = exif['GPSInfo'][key]
                
                if 'GPSLatitude' in gps_info and 'GPSLongitude' in gps_info:
                    lat = gps_info['GPSLatitude']
                    lon = gps_info['GPSLongitude']
                    lat_ref = gps_info.get('GPSLatitudeRef', 'N')
                    lon_ref = gps_info.get('GPSLongitudeRef', 'E')
                    
                    gps_latitude = lat[0] + lat[1]/60 + lat[2]/3600
                    if lat_ref == 'S':
                        gps_latitude = -gps_latitude
                    
                    gps_longitude = lon[0] + lon[1]/60 + lon[2]/3600
                    if lon_ref == 'W':
                        gps_longitude = -gps_longitude
            
            timestamp = exif.get('DateTime') or exif.get('DateTimeOriginal')
            
            return {
                'has_exif': True,
                'timestamp': timestamp,
                'gps_latitude': gps_latitude,
                'gps_longitude': gps_longitude,
                'camera_model': exif.get('Model', 'Unknown')
            }
        except:
            return {'has_exif': False}
    
    def enrich_from_ai_vision(self, orchid: OrchidRecord) -> Optional[Dict]:
        """Extract metadata from orchid photo using AI vision"""
        if not orchid.image_url:
            logger.info(f"  ⏭️  No image URL for {orchid.genus} {orchid.species}")
            return None
        
        try:
            logger.info(f"  📥 Downloading image: {orchid.image_url[:80]}...")
            # Download image
            temp_image = self.download_image(orchid.image_url)
            if not temp_image:
                logger.warning(f"  ⚠️  Failed to download image for {orchid.genus} {orchid.species}")
                return None
            
            logger.info(f"  🤖 Running AI vision analysis...")
            
            # Extract EXIF metadata
            exif_metadata = self.extract_exif_metadata(temp_image)
            if exif_metadata.get('has_exif'):
                self.stats['exif_found'] += 1
            
            # AI vision analysis
            analysis = self.ai_identifier.identify_orchid_from_image(temp_image)
            
            # Clean up temp file
            os.unlink(temp_image)
            
            if analysis and 'error' not in analysis:
                self.stats['ai_vision_success'] += 1
                
                ai_data = analysis.get('ai_identification', {})
                metadata = ai_data.get('metadata_extraction', {})
                cultural = ai_data.get('cultural_requirements', {})
                habitat = ai_data.get('habitat_indicators', {})
                phase1 = ai_data.get('phase1_visual', {})
                phase2 = ai_data.get('phase2_morphology', {})
                
                return {
                    'source': 'AI Vision (GPT-4o-mini)',
                    'growth_habit': metadata.get('growth_habit', {}).get('value'),
                    'temperature': metadata.get('temperature', {}).get('value'),
                    'light': metadata.get('light', {}).get('value'),
                    'humidity': metadata.get('humidity', {}).get('value'),
                    'bloom_season': metadata.get('bloom_season', {}).get('value'),
                    'difficulty': metadata.get('difficulty', {}).get('value'),
                    'watering': cultural.get('watering', {}).get('value'),
                    'fertilizer': cultural.get('fertilizer', {}).get('value'),
                    'potting_medium': cultural.get('potting_medium', {}).get('value'),
                    'native_climate': habitat.get('native_climate', {}).get('value'),
                    'elevation': habitat.get('elevation_preference', {}).get('value'),
                    'confidence': ai_data.get('confidence_score', 0),
                    'exif_metadata': exif_metadata,
                    # Phase 1: Enhanced Visual Analysis
                    'flower_color': phase1.get('flower_color', {}).get('value'),
                    'bloom_stage': phase1.get('bloom_stage', {}).get('value'),
                    'inflorescence_type': phase1.get('inflorescence_type', {}).get('value'),
                    'inflorescence_position': phase1.get('inflorescence_position', {}).get('value'),
                    'image_caption': phase1.get('image_caption', {}).get('value'),
                    # Phase 2: Advanced Morphology Analysis
                    'leaf_shape': phase2.get('leaf_shape', {}).get('value'),
                    'pseudobulb_presence': phase2.get('pseudobulb_presence', {}).get('value'),
                    'pseudobulb_form': phase2.get('pseudobulb_form', {}).get('value'),
                    'labellum_type': phase2.get('labellum_type', {}).get('value'),
                    'flower_resupination': phase2.get('flower_resupination', {}).get('value'),
                    'keiki_formation': phase2.get('keiki_formation', {}).get('value'),
                    'rhizome_spread_type': phase2.get('rhizome_spread', {}).get('value'),
                    'leaf_venation': phase2.get('leaf_venation', {}).get('value'),
                    'tissue_succulence': phase2.get('tissue_succulence', {}).get('value'),
                    'growth_rate': phase2.get('growth_rate', {}).get('value'),
                    'flower_longevity_days': phase2.get('flower_longevity_days', {}).get('value'),
                    'dormant_leaf_drop': phase2.get('dormant_leaf_drop', {}).get('value'),
                    'growth_eye_activation': phase2.get('growth_eye_activation', {}).get('value')
                }
        except Exception as e:
            logger.error(f"❌ AI vision error for {orchid.genus} {orchid.species}: {e}")
        
        return None
    
    def map_countries_to_continent(self, countries: List[str]) -> Optional[str]:
        """
        Map GBIF countries to continents using comprehensive mapping.
        
        NOTE: Covers 280+ common GBIF country labels but may not be exhaustive for all
        territories/dependencies. Unmapped countries will result in null continent.
        For production use, consider ISO-3166 or UN M.49 region data.
        """
        continent_map = {
            'Africa': [
                'South Africa', 'Madagascar', 'Kenya', 'Tanzania', 'Ethiopia', 'Nigeria', 
                'Cameroon', 'Uganda', 'Rwanda', 'Zimbabwe', 'Mozambique', 'Malawi', 
                'Zambia', 'Botswana', 'Namibia', 'Angola', 'Democratic Republic of the Congo',
                'Congo', 'Republic of the Congo', 'Gabon', 'Ghana', 'Ivory Coast', 
                'Côte d\'Ivoire', 'Senegal', 'Morocco', 'Algeria', 'Tunisia', 'Egypt', 
                'Libya', 'Sudan', 'South Sudan', 'Somalia', 'Eritrea', 'Djibouti',
                'Mauritius', 'Seychelles', 'Comoros', 'Mauritania', 'Mali', 'Niger',
                'Chad', 'Central African Republic', 'Equatorial Guinea', 'Burkina Faso',
                'Benin', 'Togo', 'Liberia', 'Sierra Leone', 'Guinea', 'Guinea-Bissau',
                'Gambia', 'Cape Verde', 'São Tomé and Príncipe', 'Burundi', 'Lesotho',
                'Eswatini', 'Swaziland', 'Réunion', 'Mayotte', 'Western Sahara',
                'Saint Helena', 'Ascension', 'Tristan da Cunha'
            ],
            'Asia': [
                'China', 'India', 'Thailand', 'Malaysia', 'Indonesia', 'Philippines', 
                'Vietnam', 'Japan', 'Myanmar', 'Burma', 'Laos', 'Cambodia', 'Nepal', 
                'Bhutan', 'Sri Lanka', 'Bangladesh', 'Taiwan', 'South Korea', 'North Korea',
                'Korea', 'Singapore', 'Brunei', 'East Timor', 'Timor-Leste', 'Mongolia', 
                'Pakistan', 'Afghanistan', 'Iran', 'Iraq', 'Saudi Arabia', 'Yemen', 'Oman', 
                'United Arab Emirates', 'UAE', 'Qatar', 'Bahrain', 'Kuwait', 'Jordan',
                'Lebanon', 'Syria', 'Israel', 'Palestine', 'Turkey', 'Georgia', 'Armenia',
                'Azerbaijan', 'Kazakhstan', 'Uzbekistan', 'Turkmenistan', 'Kyrgyzstan',
                'Tajikistan', 'Maldives', 'Hong Kong', 'Macao', 'Macau'
            ],
            'South America': [
                'Brazil', 'Colombia', 'Ecuador', 'Peru', 'Venezuela', 'Bolivia', 
                'Guyana', 'Suriname', 'French Guiana', 'Argentina', 'Chile', 'Paraguay',
                'Uruguay', 'Trinidad and Tobago', 'Falkland Islands', 'South Georgia'
            ],
            'North America': [
                'Mexico', 'United States', 'USA', 'U.S.A.', 'Canada', 'Guatemala', 
                'Honduras', 'Costa Rica', 'Panama', 'Nicaragua', 'El Salvador', 'Belize', 
                'Jamaica', 'Cuba', 'Haiti', 'Dominican Republic', 'Puerto Rico', 'Bahamas', 
                'Barbados', 'Grenada', 'Saint Lucia', 'Dominica', 'Saint Vincent', 
                'Saint Kitts and Nevis', 'Antigua and Barbuda', 'Trinidad', 'Tobago',
                'Martinique', 'Guadeloupe', 'Aruba', 'Curaçao', 'Bonaire',
                'Virgin Islands', 'Cayman Islands', 'Turks and Caicos', 'Bermuda',
                'Saint Barthélemy', 'Saint Martin', 'Sint Maarten', 'Saint Pierre and Miquelon',
                'Montserrat', 'Anguilla', 'Greenland'
            ],
            'Europe': [
                'United Kingdom', 'UK', 'Great Britain', 'England', 'Scotland', 'Wales',
                'France', 'Germany', 'Spain', 'Italy', 'Greece', 'Portugal', 'Netherlands', 
                'Belgium', 'Switzerland', 'Austria', 'Poland', 'Czech Republic', 'Czechia',
                'Slovakia', 'Hungary', 'Romania', 'Bulgaria', 'Croatia', 'Serbia', 
                'Slovenia', 'Denmark', 'Sweden', 'Norway', 'Finland', 'Iceland', 'Ireland',
                'Russia', 'Russian Federation', 'Ukraine', 'Belarus', 'Estonia', 'Latvia', 
                'Lithuania', 'Moldova', 'Albania', 'North Macedonia', 'Macedonia', 
                'Montenegro', 'Bosnia', 'Herzegovina', 'Luxembourg', 'Liechtenstein',
                'Monaco', 'Andorra', 'San Marino', 'Vatican', 'Malta', 'Cyprus',
                'Isle of Man', 'Guernsey', 'Jersey', 'Faroe Islands', 'Svalbard', 'Jan Mayen'
            ],
            'Oceania': [
                'Australia', 'New Zealand', 'Papua New Guinea', 'Fiji', 'New Caledonia',
                'Solomon Islands', 'Vanuatu', 'Samoa', 'Tonga', 'Micronesia', 'Palau',
                'Marshall Islands', 'Kiribati', 'Nauru', 'Tuvalu', 'Cook Islands',
                'French Polynesia', 'Tahiti', 'Guam', 'Northern Mariana Islands',
                'American Samoa', 'Wallis and Futuna', 'Niue', 'Tokelau', 'Norfolk Island',
                'Christmas Island', 'Cocos Islands', 'Pitcairn'
            ]
        }
        
        continent_counts = {}
        for continent, country_list in continent_map.items():
            # Case-insensitive substring matching
            count = sum(1 for country in countries if any(c.lower() in country.lower() for c in country_list))
            if count > 0:
                continent_counts[continent] = count
        
        if continent_counts:
            return max(continent_counts, key=continent_counts.get)
        
        # Log unmapped countries for future improvement
        if countries:
            logger.warning(f"⚠️ No continent mapping found for countries: {', '.join(countries[:5])}")
        return None
    
    def enrich_from_gbif(self, orchid: OrchidRecord) -> Optional[Dict]:
        """Get occurrence and habitat data from GBIF (Phase 3: includes taxonomic status)"""
        if not self.gbif:
            return None
        
        try:
            scientific_name = f"{orchid.genus} {orchid.species}"
            gbif_data = self.gbif.search_species(scientific_name)
            
            if gbif_data and gbif_data.get('results'):
                self.stats['gbif_success'] += 1
                result = gbif_data['results'][0]
                
                # Phase 3: Get taxonomic information
                species_key = result.get('key')
                taxonomic_status = result.get('taxonomicStatus', 'UNKNOWN')  # accepted, synonym, doubtful
                taxonomic_authority = result.get('authorship') or result.get('author')
                
                # Get occurrence data for distribution (correct method name)
                occurrences = self.gbif.get_occurrences(scientific_name=scientific_name, limit=100)
                
                # Extract geographic distribution
                countries = set()
                elevations = []
                latitudes = []
                longitudes = []
                
                if occurrences and occurrences.get('results'):
                    for occ in occurrences['results']:
                        if occ.get('country'):
                            countries.add(occ['country'])
                        if occ.get('elevation'):
                            elevations.append(occ['elevation'])
                        if occ.get('decimalLatitude') and occ.get('decimalLongitude'):
                            latitudes.append(occ['decimalLatitude'])
                            longitudes.append(occ['decimalLongitude'])
                
                # Phase 3: Derive continent from countries
                continent = self.map_countries_to_continent(list(countries)) if countries else None
                
                return {
                    'source': 'GBIF Occurrence Database',
                    'taxon_key': result.get('key'),
                    'kingdom': result.get('kingdom'),
                    'family': result.get('family'),
                    'native_countries': list(countries),
                    'elevation_range': f"{min(elevations)}-{max(elevations)}m" if elevations else None,
                    'avg_elevation': sum(elevations) // len(elevations) if elevations else None,
                    'distribution_coords': list(zip(latitudes, longitudes)),
                    'occurrence_count': len(occurrences.get('results', [])),
                    'habitat_type': result.get('habitat'),
                    # Phase 3 fields
                    'taxonomic_status': taxonomic_status.lower() if taxonomic_status else None,
                    'taxonomic_authority': taxonomic_authority,
                    'continent': continent
                }
        except Exception as e:
            logger.error(f"❌ GBIF error for {orchid.genus} {orchid.species}: {e}")
        
        return None
    
    def enrich_from_eol(self, orchid: OrchidRecord) -> Optional[Dict]:
        """Get trait data from Encyclopedia of Life"""
        if not self.eol:
            return None
        
        try:
            scientific_name = f"{orchid.genus} {orchid.species}"
            eol_data = self.eol.search_eol_species(scientific_name)
            
            if eol_data:
                self.stats['eol_success'] += 1
                
                traits = eol_data.get('traits', [])
                trait_dict = {}
                
                for trait in traits:
                    trait_name = trait.get('trait')
                    trait_value = trait.get('value')
                    if trait_name and trait_value:
                        trait_dict[trait_name] = trait_value
                
                return {
                    'source': 'Encyclopedia of Life TraitBank',
                    'description': eol_data.get('description'),
                    'traits': trait_dict,
                    'phenotypes': eol_data.get('phenotypes', []),
                    'conservation_status': trait_dict.get('conservation status'),
                    'life_span': trait_dict.get('life span'),
                    'growth_form': trait_dict.get('growth form')
                }
        except Exception as e:
            logger.error(f"❌ EOL error for {orchid.genus} {orchid.species}: {e}")
        
        return None
    
    def analyze_correlations(self, enrichment_data: Dict) -> Dict:
        """Analyze correlations between different data sources"""
        correlations = {}
        
        ai = enrichment_data.get('ai_vision') or {}
        gbif = enrichment_data.get('gbif') or {}
        eol = enrichment_data.get('eol') or {}
        
        # Correlation: AI temperature vs GBIF elevation
        if ai.get('temperature') and gbif.get('avg_elevation'):
            temp_map = {'cool': 'high', 'intermediate': 'mid', 'warm': 'low'}
            ai_temp = temp_map.get(ai['temperature'], 'unknown')
            
            elevation = gbif['avg_elevation']
            if elevation > 1500:
                gbif_temp = 'high'
            elif elevation > 500:
                gbif_temp = 'mid'
            else:
                gbif_temp = 'low'
            
            if ai_temp == gbif_temp:
                correlations['temperature_elevation'] = {
                    'match': True,
                    'ai_temp': ai['temperature'],
                    'gbif_elevation': elevation,
                    'confidence': 'high'
                }
        
        # Correlation: AI growth habit vs EOL growth form
        if ai.get('growth_habit') and eol.get('traits', {}).get('growth form'):
            correlations['growth_habit'] = {
                'ai': ai['growth_habit'],
                'eol': eol['traits']['growth form'],
                'match': ai['growth_habit'].lower() in eol['traits']['growth form'].lower()
            }
        
        # Correlation: AI native climate vs GBIF distribution
        if ai.get('native_climate') and gbif.get('native_countries'):
            tropical_countries = ['Brazil', 'Colombia', 'Ecuador', 'Madagascar', 'Thailand', 'Malaysia']
            is_tropical_region = any(c in gbif['native_countries'] for c in tropical_countries)
            
            correlations['climate_distribution'] = {
                'ai_climate': ai['native_climate'],
                'gbif_tropical': is_tropical_region,
                'match': (ai['native_climate'] == 'tropical') == is_tropical_region
            }
        
        if correlations:
            self.stats['correlations_found'] += 1
        
        return correlations
    
    def enrich_orchid(self, orchid: OrchidRecord) -> Dict:
        """Comprehensively enrich a single orchid from all sources"""
        logger.info(f"🌺 Enriching: {orchid.genus} {orchid.species}")
        
        enrichment = {
            'orchid_id': orchid.id,
            'genus': orchid.genus,
            'species': orchid.species,
            'ai_vision': None,
            'gbif': None,
            'eol': None,
            'correlations': {},
            'enrichment_timestamp': datetime.now().isoformat()
        }
        
        # 1. AI Vision Analysis (if image available)
        if orchid.image_url:
            enrichment['ai_vision'] = self.enrich_from_ai_vision(orchid)
        
        # 2. GBIF Data
        enrichment['gbif'] = self.enrich_from_gbif(orchid)
        
        # 3. EOL Data
        enrichment['eol'] = self.enrich_from_eol(orchid)
        
        # 4. Analyze Correlations
        enrichment['correlations'] = self.analyze_correlations(enrichment)
        
        self.stats['total_processed'] += 1
        
        return enrichment
    
    def enrich_single_orchid(self, orchid: OrchidRecord) -> Dict:
        """
        Enrich a single orchid and save to database
        Returns enrichment data with 'enriched' flag
        """
        enrichment = self.enrich_orchid(orchid)
        
        # Apply enrichment to database
        was_enriched = False
        
        try:
            fields_updated = []
            
            # Apply AI vision data (using CORRECT field names from models.py)
            if enrichment['ai_vision']:
                ai_data = enrichment['ai_vision']
                
                if ai_data.get('growth_habit') and not orchid.growth_habit:
                    orchid.growth_habit = ai_data['growth_habit']
                    fields_updated.append('growth_habit')
                
                if ai_data.get('temperature') and not orchid.climate_preference:
                    # Map temperature to climate_preference field
                    orchid.climate_preference = ai_data['temperature']
                    fields_updated.append('climate_preference')
                
                if ai_data.get('light') and not orchid.light_requirements:
                    orchid.light_requirements = ai_data['light']
                    fields_updated.append('light_requirements')
                
                if ai_data.get('humidity') and not orchid.water_requirements:
                    # Map humidity to water_requirements field
                    orchid.water_requirements = f"Humidity: {ai_data['humidity']}"
                    fields_updated.append('water_requirements')
                
                if ai_data.get('bloom_season') and not orchid.bloom_time:
                    # Map bloom_season to bloom_time field
                    orchid.bloom_time = ai_data['bloom_season']
                    fields_updated.append('bloom_time')
                
                # Phase 1: Enhanced Visual Analysis Fields
                if ai_data.get('flower_color') and not orchid.flower_color:
                    orchid.flower_color = ai_data['flower_color']
                    fields_updated.append('flower_color')
                
                if ai_data.get('bloom_stage') and not orchid.bloom_stage:
                    orchid.bloom_stage = ai_data['bloom_stage']
                    fields_updated.append('bloom_stage')
                
                if ai_data.get('inflorescence_type') and not orchid.inflorescence_type:
                    orchid.inflorescence_type = ai_data['inflorescence_type']
                    fields_updated.append('inflorescence_type')
                
                if ai_data.get('inflorescence_position') and not orchid.inflorescence_position:
                    orchid.inflorescence_position = ai_data['inflorescence_position']
                    fields_updated.append('inflorescence_position')
                
                if ai_data.get('image_caption') and not orchid.image_caption:
                    orchid.image_caption = ai_data['image_caption']
                    fields_updated.append('image_caption')
                
                # Detect hybrid from species name (× symbol)
                if orchid.species and '×' in orchid.species and not orchid.is_hybrid:
                    orchid.is_hybrid = True
                    fields_updated.append('is_hybrid')
                
                # Set widget visibility (default True for all orchids)
                if orchid.widget_visibility is None:
                    orchid.widget_visibility = True
                    fields_updated.append('widget_visibility')
                
                # Phase 2: Advanced Morphology Analysis Fields
                if ai_data.get('leaf_shape') and not orchid.leaf_shape:
                    orchid.leaf_shape = ai_data['leaf_shape']
                    fields_updated.append('leaf_shape')
                
                # Update pseudobulb_presence if AI provides a definitive answer
                pseudobulb_val = ai_data.get('pseudobulb_presence')
                if pseudobulb_val is not None:
                    orchid.pseudobulb_presence = pseudobulb_val
                    fields_updated.append('pseudobulb_presence')
                
                if ai_data.get('pseudobulb_form') and not orchid.pseudobulb_form:
                    orchid.pseudobulb_form = ai_data['pseudobulb_form']
                    fields_updated.append('pseudobulb_form')
                
                if ai_data.get('labellum_type') and not orchid.labellum_type:
                    orchid.labellum_type = ai_data['labellum_type']
                    fields_updated.append('labellum_type')
                
                if ai_data.get('flower_resupination') is not None and orchid.flower_resupination is None:
                    orchid.flower_resupination = ai_data['flower_resupination']
                    fields_updated.append('flower_resupination')
                
                if ai_data.get('keiki_formation') and not orchid.keiki_formation:
                    orchid.keiki_formation = ai_data['keiki_formation']
                    fields_updated.append('keiki_formation')
                
                if ai_data.get('rhizome_spread_type') and not orchid.rhizome_spread_type:
                    orchid.rhizome_spread_type = ai_data['rhizome_spread_type']
                    fields_updated.append('rhizome_spread_type')
                
                if ai_data.get('leaf_venation') and not orchid.leaf_venation:
                    orchid.leaf_venation = ai_data['leaf_venation']
                    fields_updated.append('leaf_venation')
                
                if ai_data.get('tissue_succulence') and not orchid.tissue_succulence:
                    orchid.tissue_succulence = ai_data['tissue_succulence']
                    fields_updated.append('tissue_succulence')
                
                if ai_data.get('growth_rate') and not orchid.growth_rate:
                    orchid.growth_rate = ai_data['growth_rate']
                    fields_updated.append('growth_rate')
                
                if ai_data.get('flower_longevity_days') and not orchid.flower_longevity_days:
                    orchid.flower_longevity_days = ai_data['flower_longevity_days']
                    fields_updated.append('flower_longevity_days')
                
                if ai_data.get('dormant_leaf_drop') is not None and orchid.dormant_leaf_drop is None:
                    orchid.dormant_leaf_drop = ai_data['dormant_leaf_drop']
                    fields_updated.append('dormant_leaf_drop')
                
                if ai_data.get('growth_eye_activation') and not orchid.growth_eye_activation:
                    orchid.growth_eye_activation = ai_data['growth_eye_activation']
                    fields_updated.append('growth_eye_activation')
            
            # Apply GBIF data
            if enrichment['gbif']:
                gbif_data = enrichment['gbif']
                
                if gbif_data.get('native_countries') and not orchid.region:
                    # Map native_countries to region field
                    orchid.region = ', '.join(gbif_data['native_countries'][:5])  # Top 5 countries
                    fields_updated.append('region')
                
                if gbif_data.get('elevation_range') and not orchid.native_habitat:
                    # Map elevation to native_habitat field  
                    orchid.native_habitat = f"Elevation: {gbif_data['elevation_range']}"
                    fields_updated.append('native_habitat')
                
                # Phase 3: GBIF External API Fields
                if gbif_data.get('taxonomic_status') and not orchid.taxonomic_status:
                    orchid.taxonomic_status = gbif_data['taxonomic_status']
                    fields_updated.append('taxonomic_status')
                
                if gbif_data.get('taxonomic_authority') and not orchid.taxonomic_authority:
                    orchid.taxonomic_authority = gbif_data['taxonomic_authority']
                    fields_updated.append('taxonomic_authority')
                
                if gbif_data.get('continent') and not orchid.continent:
                    orchid.continent = gbif_data['continent']
                    fields_updated.append('continent')
            
            # Apply EOL data
            if enrichment['eol']:
                eol_data = enrichment['eol']
                
                if eol_data.get('description') and not orchid.ai_description:
                    # Map description to ai_description field
                    orchid.ai_description = eol_data['description'][:500]  # Truncate to 500 chars
                    fields_updated.append('ai_description')
            
            if fields_updated:
                was_enriched = True
                db.session.add(orchid)  # Explicitly add to session
                db.session.commit()
                logger.info(f"  💾 Database updated: {', '.join(fields_updated)}")
        
        except Exception as e:
            logger.error(f"❌ Failed to save enrichment: {e}")
            db.session.rollback()
        
        enrichment['enriched'] = was_enriched
        return enrichment
    
    def enrich_database_batch(self, limit: int = None, skip_existing: bool = True):
        """Enrich multiple orchids in batch"""
        with app.app_context():
            # Get orchids with images
            query = OrchidRecord.query.filter(
                OrchidRecord.image_url.isnot(None),
                OrchidRecord.image_url != ''
            )
            
            if limit:
                query = query.limit(limit)
            
            orchids = query.all()
            total = len(orchids)
            
            logger.info(f"🚀 Starting comprehensive enrichment of {total} orchids")
            logger.info(f"💰 Estimated cost: ${total * 0.003:.2f} (AI vision only, GBIF/EOL are free)")
            
            results = []
            
            for idx, orchid in enumerate(orchids, 1):
                logger.info(f"\n{'='*60}")
                logger.info(f"📊 Progress: {idx}/{total}")
                
                try:
                    enrichment_data = self.enrich_orchid(orchid)
                    results.append(enrichment_data)
                    
                    # Log what we found
                    if enrichment_data['ai_vision']:
                        logger.info(f"  ✅ AI Vision: {enrichment_data['ai_vision']['confidence']}% confidence")
                    if enrichment_data['gbif']:
                        logger.info(f"  ✅ GBIF: {enrichment_data['gbif']['occurrence_count']} occurrences")
                    if enrichment_data['eol']:
                        logger.info(f"  ✅ EOL: {len(enrichment_data['eol'].get('traits', {}))} traits")
                    if enrichment_data['correlations']:
                        logger.info(f"  ✅ Correlations: {len(enrichment_data['correlations'])} found")
                
                except Exception as e:
                    logger.error(f"❌ Error enriching orchid {orchid.id}: {e}")
                    self.stats['errors'] += 1
            
            # Save results
            output_file = f"comprehensive_enrichment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            # Print summary
            logger.info(f"\n{'='*60}")
            logger.info(f"🎉 ENRICHMENT COMPLETE")
            logger.info(f"📁 Results saved to: {output_file}")
            logger.info(f"\n📊 STATISTICS:")
            logger.info(f"  Total processed: {self.stats['total_processed']}")
            logger.info(f"  AI Vision success: {self.stats['ai_vision_success']}")
            logger.info(f"  GBIF success: {self.stats['gbif_success']}")
            logger.info(f"  EOL success: {self.stats['eol_success']}")
            logger.info(f"  EXIF metadata found: {self.stats['exif_found']}")
            logger.info(f"  Correlations discovered: {self.stats['correlations_found']}")
            logger.info(f"  Errors: {self.stats['errors']}")
            
            # Calculate actual cost
            actual_cost = self.stats['ai_vision_success'] * 0.003
            logger.info(f"\n💰 ACTUAL COST: ${actual_cost:.2f}")
            
            return results

if __name__ == "__main__":
    enricher = MasterOrchidEnricher()
    
    # Run enrichment on entire database (or specify limit for testing)
    # enricher.enrich_database_batch(limit=10)  # Test with 10 orchids first
    enricher.enrich_database_batch()  # Full database enrichment
