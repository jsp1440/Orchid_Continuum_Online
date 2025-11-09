#!/usr/bin/env python3
"""
Advanced Culture Sheet Generator
Combines Baker methodology + AOS guidelines + Location-specific weather analysis
"""
import os
import psycopg2
import json
from datetime import datetime, timedelta
import requests
from typing import Dict, Optional, Any

DATABASE_URL = os.environ.get('DATABASE_URL')

class CultureSheetGenerator:
    """
    Generates location-specific culture sheets by combining:
    1. Baker's detailed species data
    2. AOS genus-level guidelines  
    3. Local weather/climate data
    4. Orchid Continuum database enrichment
    """
    
    def __init__(self):
        self.conn = psycopg2.connect(DATABASE_URL)
        self.cur = self.conn.cursor()
    
    def generate_culture_sheet(
        self, 
        taxonomy_id: int, 
        latitude: float, 
        longitude: float,
        city: str = None,
        country: str = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive culture sheet for a species at a specific location
        
        Args:
            taxonomy_id: ID from orchid_taxonomy table
            latitude: Location latitude
            longitude: Location longitude
            city: Optional city name
            country: Optional country name
        
        Returns:
            Dict containing complete culture sheet with recommendations
        """
        print(f"🌺 Generating culture sheet for taxonomy_id={taxonomy_id}")
        print(f"📍 Location: {latitude}, {longitude} ({city}, {country})")
        
        # Check cache first
        cached = self._get_from_cache(taxonomy_id, latitude, longitude)
        if cached:
            print("   ✅ Retrieved from cache")
            return cached
        
        # Get species info
        species_info = self._get_species_info(taxonomy_id)
        if not species_info:
            raise ValueError(f"Taxonomy ID {taxonomy_id} not found")
        
        print(f"   Species: {species_info['scientific_name']}")
        
        # Get Baker data (species-specific)
        baker_data = self._get_baker_data(taxonomy_id, species_info['scientific_name'])
        
        # Get AOS data (genus-level)
        aos_data = self._get_aos_data(species_info['genus'])
        
        # Get location weather data
        weather_data = self._get_weather_data(latitude, longitude)
        
        # Generate comparison and recommendations
        culture_sheet = self._merge_and_analyze(
            species_info=species_info,
            baker_data=baker_data,
            aos_data=aos_data,
            weather_data=weather_data,
            location={'lat': latitude, 'lon': longitude, 'city': city, 'country': country}
        )
        
        # Cache the result
        self._save_to_cache(taxonomy_id, latitude, longitude, culture_sheet, 
                           baker_used=bool(baker_data), aos_used=bool(aos_data))
        
        return culture_sheet
    
    def _get_from_cache(self, taxonomy_id: int, lat: float, lon: float) -> Optional[Dict]:
        """Check if culture sheet is cached"""
        self.cur.execute("""
            SELECT culture_sheet_data, generated_at, expires_at
            FROM culture_sheet_cache
            WHERE taxonomy_id = %s 
              AND ABS(location_lat - %s) < 0.5
              AND ABS(location_lon - %s) < 0.5
              AND (expires_at IS NULL OR expires_at > NOW())
            ORDER BY generated_at DESC
            LIMIT 1
        """, (taxonomy_id, lat, lon))
        
        result = self.cur.fetchone()
        if result:
            data, generated_at, expires_at = result
            # Update access count
            self.cur.execute("""
                UPDATE culture_sheet_cache
                SET access_count = access_count + 1,
                    last_accessed = NOW()
                WHERE taxonomy_id = %s
            """, (taxonomy_id,))
            self.conn.commit()
            return data
        
        return None
    
    def _get_species_info(self, taxonomy_id: int) -> Optional[Dict]:
        """Get basic species information"""
        self.cur.execute("""
            SELECT id, scientific_name, genus, species, family, subfamily
            FROM orchid_taxonomy
            WHERE id = %s
        """, (taxonomy_id,))
        
        result = self.cur.fetchone()
        if not result:
            return None
        
        return {
            'taxonomy_id': result[0],
            'scientific_name': result[1],
            'genus': result[2],
            'species': result[3],
            'family': result[4],
            'subfamily': result[5]
        }
    
    def _get_baker_data(self, taxonomy_id: int, scientific_name: str) -> Optional[Dict]:
        """Get Baker culture data"""
        # Try by taxonomy_id first
        self.cur.execute("""
            SELECT 
                scientific_name, climate_zone,
                temp_summer_day_min, temp_summer_day_max,
                temp_summer_night_min, temp_summer_night_max,
                temp_winter_day_min, temp_winter_day_max,
                temp_winter_night_min, temp_winter_night_max,
                light_level, light_footcandles_min, light_footcandles_max,
                water_frequency, water_description, drought_tolerance,
                humidity_min, humidity_max, humidity_description,
                potting_media, mounting_recommended,
                fertilizer_recommendation, fertilizer_frequency,
                flowering_season, flowering_trigger, fragrance,
                rest_period_required, rest_period_description,
                special_notes,
                native_elevation_min, native_elevation_max,
                origin_country, origin_region
            FROM baker_culture_sheets
            WHERE taxonomy_id = %s OR scientific_name = %s
            LIMIT 1
        """, (taxonomy_id, scientific_name))
        
        result = self.cur.fetchone()
        if not result:
            return None
        
        return {
            'scientific_name': result[0],
            'climate_zone': result[1],
            'temperature': {
                'summer_day': {'min': result[2], 'max': result[3]},
                'summer_night': {'min': result[4], 'max': result[5]},
                'winter_day': {'min': result[6], 'max': result[7]},
                'winter_night': {'min': result[8], 'max': result[9]}
            },
            'light': {
                'level': result[10],
                'footcandles': {'min': result[11], 'max': result[12]}
            },
            'water': {
                'frequency': result[13],
                'description': result[14],
                'drought_tolerant': result[15]
            },
            'humidity': {
                'min': result[16],
                'max': result[17],
                'description': result[18]
            },
            'potting': {
                'media': result[19],
                'mounting_recommended': result[20]
            },
            'fertilizer': {
                'recommendation': result[21],
                'frequency': result[22]
            },
            'flowering': {
                'season': result[23],
                'trigger': result[24],
                'fragrance': result[25]
            },
            'special_care': {
                'rest_period': result[26],
                'rest_description': result[27],
                'notes': result[28]
            },
            'origin': {
                'elevation_min': result[29],
                'elevation_max': result[30],
                'country': result[31],
                'region': result[32]
            }
        }
    
    def _get_aos_data(self, genus: str) -> Optional[Dict]:
        """Get AOS genus-level culture data"""
        self.cur.execute("""
            SELECT 
                light_requirements, light_level,
                temperature_requirements, temp_category,
                water_requirements,
                humidity_requirements,
                fertilizer_requirements,
                potting_requirements,
                special_notes
            FROM aos_culture_sheets
            WHERE genus = %s
        """, (genus,))
        
        result = self.cur.fetchone()
        if not result:
            return None
        
        return {
            'light': {
                'requirements': result[0],
                'level': result[1]
            },
            'temperature': {
                'requirements': result[2],
                'category': result[3]
            },
            'water': result[4],
            'humidity': result[5],
            'fertilizer': result[6],
            'potting': result[7],
            'special_notes': result[8]
        }
    
    def _get_weather_data(self, lat: float, lon: float) -> Dict:
        """Get local weather/climate data (simplified - use weather API in production)"""
        # Simplified weather data - in production, call weather API
        # For now, return placeholder structure
        return {
            'current_temp': None,
            'avg_summer_high': None,
            'avg_summer_low': None,
            'avg_winter_high': None,
            'avg_winter_low': None,
            'avg_humidity': None,
            'usda_zone': None,
            'climate_type': None
        }
    
    def _merge_and_analyze(
        self, 
        species_info: Dict,
        baker_data: Optional[Dict],
        aos_data: Optional[Dict],
        weather_data: Dict,
        location: Dict
    ) -> Dict:
        """Merge all data sources and generate recommendations"""
        
        culture_sheet = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'species': species_info['scientific_name'],
                'genus': species_info['genus'],
                'location': location,
                'data_sources': {
                    'baker': bool(baker_data),
                    'aos': bool(aos_data),
                    'weather': bool(weather_data and weather_data.get('current_temp'))
                }
            },
            'temperature': {},
            'light': {},
            'water': {},
            'humidity': {},
            'potting': {},
            'fertilizer': {},
            'flowering': {},
            'special_care': {},
            'recommendations': []
        }
        
        # Temperature recommendations
        if baker_data and baker_data.get('temperature'):
            temp = baker_data['temperature']
            culture_sheet['temperature'] = {
                'summer_day': f"{temp['summer_day']['min']}-{temp['summer_day']['max']}°F" if temp['summer_day']['min'] else None,
                'summer_night': f"{temp['summer_night']['min']}-{temp['summer_night']['max']}°F" if temp['summer_night']['min'] else None,
                'winter_day': f"{temp['winter_day']['min']}-{temp['winter_day']['max']}°F" if temp['winter_day']['min'] else None,
                'winter_night': f"{temp['winter_night']['min']}-{temp['winter_night']['max']}°F" if temp['winter_night']['min'] else None,
                'source': 'Baker'
            }
        elif aos_data and aos_data.get('temperature'):
            culture_sheet['temperature'] = {
                'category': aos_data['temperature']['category'],
                'requirements': aos_data['temperature']['requirements'],
                'source': 'AOS'
            }
        
        # Light recommendations
        if baker_data and baker_data.get('light'):
            light = baker_data['light']
            culture_sheet['light'] = {
                'level': light.get('level'),
                'footcandles': f"{light['footcandles']['min']}-{light['footcandles']['max']}" if light.get('footcandles', {}).get('min') else None,
                'source': 'Baker'
            }
        elif aos_data and aos_data.get('light'):
            culture_sheet['light'] = {
                'level': aos_data['light'].get('level'),
                'requirements': aos_data['light'].get('requirements'),
                'source': 'AOS'
            }
        
        # Water recommendations
        if baker_data and baker_data.get('water'):
            culture_sheet['water'] = baker_data['water']
            culture_sheet['water']['source'] = 'Baker'
        elif aos_data and aos_data.get('water'):
            culture_sheet['water'] = {'requirements': aos_data['water'], 'source': 'AOS'}
        
        # Humidity recommendations
        if baker_data and baker_data.get('humidity'):
            hum = baker_data['humidity']
            culture_sheet['humidity'] = {
                'range': f"{hum.get('min')}-{hum.get('max')}%" if hum.get('min') else None,
                'description': hum.get('description'),
                'source': 'Baker'
            }
        elif aos_data and aos_data.get('humidity'):
            culture_sheet['humidity'] = {'requirements': aos_data['humidity'], 'source': 'AOS'}
        
        # Potting recommendations  
        if baker_data and baker_data.get('potting'):
            culture_sheet['potting'] = baker_data['potting']
            culture_sheet['potting']['source'] = 'Baker'
        elif aos_data and aos_data.get('potting'):
            culture_sheet['potting'] = {'requirements': aos_data['potting'], 'source': 'AOS'}
        
        # Fertilizer recommendations
        if baker_data and baker_data.get('fertilizer'):
            culture_sheet['fertilizer'] = baker_data['fertilizer']
            culture_sheet['fertilizer']['source'] = 'Baker'
        elif aos_data and aos_data.get('fertilizer'):
            culture_sheet['fertilizer'] = {'requirements': aos_data['fertilizer'], 'source': 'AOS'}
        
        # Flowering info
        if baker_data and baker_data.get('flowering'):
            culture_sheet['flowering'] = baker_data['flowering']
            culture_sheet['flowering']['source'] = 'Baker'
        
        # Special care
        if baker_data and baker_data.get('special_care'):
            culture_sheet['special_care'] = baker_data['special_care']
            culture_sheet['special_care']['source'] = 'Baker'
        elif aos_data and aos_data.get('special_notes'):
            culture_sheet['special_care'] = {'notes': aos_data['special_notes'], 'source': 'AOS'}
        
        # Generate location-specific recommendations
        recommendations = self._generate_recommendations(baker_data, aos_data, weather_data, location)
        culture_sheet['recommendations'] = recommendations
        
        return culture_sheet
    
    def _generate_recommendations(
        self,
        baker_data: Optional[Dict],
        aos_data: Optional[Dict],
        weather_data: Dict,
        location: Dict
    ) -> list:
        """Generate location-specific growing recommendations"""
        recommendations = []
        
        # Basic recommendation based on data availability
        if baker_data and aos_data:
            recommendations.append({
                'priority': 'high',
                'category': 'data_quality',
                'message': 'Excellent! Both species-specific (Baker) and genus-level (AOS) data available for comprehensive guidance.'
            })
        elif baker_data:
            recommendations.append({
                'priority': 'medium',
                'category': 'data_quality',
                'message': 'Species-specific Baker data available. Consider supplementing with AOS genus guidelines.'
            })
        elif aos_data:
            recommendations.append({
                'priority': 'medium',
                'category': 'data_quality',
                'message': 'Genus-level AOS data available. Baker species-specific data not yet imported.'
            })
        
        # Add mounting recommendation if applicable
        if baker_data and baker_data.get('potting', {}).get('mounting_recommended'):
            recommendations.append({
                'priority': 'high',
                'category': 'potting',
                'message': 'This species performs best when mounted rather than potted.'
            })
        
        # Add rest period warning if applicable
        if baker_data and baker_data.get('special_care', {}).get('rest_period'):
            recommendations.append({
                'priority': 'high',
                'category': 'seasonal_care',
                'message': f"Rest period required: {baker_data['special_care'].get('rest_description', 'Reduce water and temperature during dormancy.')}"
            })
        
        return recommendations
    
    def _save_to_cache(
        self,
        taxonomy_id: int,
        lat: float,
        lon: float,
        culture_sheet: Dict,
        baker_used: bool = False,
        aos_used: bool = False
    ):
        """Save generated culture sheet to cache"""
        expires_at = datetime.now() + timedelta(days=30)
        
        self.cur.execute("""
            INSERT INTO culture_sheet_cache (
                taxonomy_id, location_lat, location_lon,
                culture_sheet_data,
                baker_data_used, aos_data_used,
                generated_at, expires_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            taxonomy_id, lat, lon,
            json.dumps(culture_sheet),
            baker_used, aos_used,
            datetime.now(), expires_at
        ))
        
        self.conn.commit()
    
    def __del__(self):
        """Cleanup database connection"""
        if hasattr(self, 'cur'):
            self.cur.close()
        if hasattr(self, 'conn'):
            self.conn.close()


def main():
    """Test culture sheet generation"""
    generator = CultureSheetGenerator()
    
    # Test with a species (using taxonomy_id=1 as example)
    print("Testing culture sheet generation...")
    print()
    
    culture_sheet = generator.generate_culture_sheet(
        taxonomy_id=1,
        latitude=34.0522,
        longitude=-118.2437,
        city="Los Angeles",
        country="USA"
    )
    
    print()
    print("="*70)
    print("📄 GENERATED CULTURE SHEET")
    print("="*70)
    print(json.dumps(culture_sheet, indent=2))


if __name__ == '__main__':
    main()
