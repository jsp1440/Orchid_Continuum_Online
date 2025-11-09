#!/usr/bin/env python3
"""
Advanced Culture Sheet Generator
Combines Baker methodology + AOS guidelines + Location-specific weather analysis
+ Microclimate Analysis + Substrate Recommendations
"""
import os
import psycopg2
import json
from datetime import datetime, timedelta
import requests
from typing import Dict, Optional, Any

# Import our revolutionary new systems
from microclimate_analyzer import MicroclimateAnalyzer
from substrate_recommendation_engine import SubstrateRecommendationEngine
from growing_environment_manager import GrowingEnvironmentManager
from environmental_delta_analyzer import EnvironmentalDeltaAnalyzer

DATABASE_URL = os.environ.get('DATABASE_URL')

class CultureSheetGenerator:
    """
    Generates location-specific culture sheets by combining:
    1. Baker's detailed species data
    2. AOS genus-level guidelines  
    3. Local weather/climate data
    4. Microclimate analysis (revolutionary image-based insights)
    5. Substrate recommendations (commercial + DIY + mounting)
    """
    
    def __init__(self, enable_microclimate=True, enable_substrate=True, enable_environment_delta=True):
        """
        Initialize culture sheet generator
        
        Args:
            enable_microclimate: Enable microclimate analysis (default True)
            enable_substrate: Enable substrate recommendations (default True)
            enable_environment_delta: Enable growing environment analysis (default True)
        """
        self.conn = psycopg2.connect(DATABASE_URL)
        self.cur = self.conn.cursor()
        
        # Feature flags
        self.enable_microclimate = enable_microclimate
        self.enable_substrate = enable_substrate
        self.enable_environment_delta = enable_environment_delta
        
        # Initialize analyzers with shared connection
        if self.enable_microclimate:
            self.microclimate_analyzer = MicroclimateAnalyzer(connection=self.conn)
        
        if self.enable_substrate:
            self.substrate_engine = SubstrateRecommendationEngine()
        
        if self.enable_environment_delta:
            self.environment_manager = GrowingEnvironmentManager(connection=self.conn)
            self.delta_analyzer = EnvironmentalDeltaAnalyzer()
    
    def generate_culture_sheet(
        self, 
        taxonomy_id: int, 
        latitude: float, 
        longitude: float,
        city: Optional[str] = None,
        country: Optional[str] = None,
        growing_environment_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive culture sheet for a species at a specific location
        
        Args:
            taxonomy_id: ID from orchid_taxonomy table
            latitude: Location latitude
            longitude: Location longitude
            city: Optional city name
            country: Optional country name
            growing_environment_id: Optional ID of user's growing environment for personalized analysis
        
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
        
        # Get monthly comparison (native habitat vs grower location)
        monthly_comparison = self._get_monthly_comparison(baker_data, latitude, longitude)
        
        # NEW: Get microclimate analysis (revolutionary image-based insights)
        microclimate_data = None
        if self.enable_microclimate:
            try:
                print("   🔬 Running microclimate analysis...")
                microclimate_data = self.microclimate_analyzer.analyze_species_images(taxonomy_id)
                print(f"   ✅ Microclimate analysis complete (status: {microclimate_data.get('status', 'unknown')})")
            except Exception as e:
                print(f"   ⚠️  Microclimate analysis failed: {e}")
                microclimate_data = {'status': 'error', 'error': str(e)}
        
        # NEW: Get substrate recommendations
        substrate_recs = None
        if self.enable_substrate:
            try:
                print("   🌱 Generating substrate recommendations...")
                substrate_recs = self.substrate_engine.recommend_substrate(
                    microclimate_data=microclimate_data,
                    grower_conditions={'climate': weather_data.get('climate_type')}
                )
                print("   ✅ Substrate recommendations generated")
            except Exception as e:
                print(f"   ⚠️  Substrate recommendation failed: {e}")
                substrate_recs = {'status': 'error', 'error': str(e)}
        
        # NEW: Get growing environment delta analysis (personalized recommendations)
        environment_analysis = None
        if self.enable_environment_delta and growing_environment_id:
            try:
                print(f"   🏠 Analyzing growing environment (ID: {growing_environment_id})...")
                
                # Load user's growing environment
                growing_env = self.environment_manager.get_environment(growing_environment_id)
                
                if growing_env:
                    # Mark as recently used
                    self.environment_manager.mark_used(growing_environment_id)
                    
                    # Build species requirements from available data
                    species_requirements = {}
                    
                    # Temperature from Baker or AOS
                    if baker_data and baker_data.get('temp_summer_day_min'):
                        species_requirements['temperature'] = {
                            'min': baker_data.get('temp_summer_night_min', 60),
                            'max': baker_data.get('temp_summer_day_max', 85),
                            'category': baker_data.get('climate_zone', 'intermediate')
                        }
                    elif aos_data and aos_data.get('temperature_requirements'):
                        temp_req = aos_data['temperature_requirements']
                        species_requirements['temperature'] = {
                            'min': temp_req.get('night_min', 60),
                            'max': temp_req.get('day_max', 85),
                            'category': temp_req.get('category', 'intermediate')
                        }
                    
                    # Humidity from Baker or AOS
                    if baker_data and baker_data.get('humidity_min'):
                        humidity_avg = (baker_data['humidity_min'] + baker_data.get('humidity_max', baker_data['humidity_min'])) / 2
                        species_requirements['humidity'] = int(humidity_avg)
                    elif aos_data and aos_data.get('humidity_requirements'):
                        species_requirements['humidity'] = aos_data['humidity_requirements'].get('target', 60)
                    
                    # Light from Baker or AOS
                    if baker_data and baker_data.get('light_level'):
                        species_requirements['light'] = baker_data['light_level']
                    elif aos_data and aos_data.get('light_requirements'):
                        species_requirements['light'] = aos_data['light_requirements'].get('level', 'medium')
                    
                    # Run delta analysis
                    environment_analysis = self.delta_analyzer.generate_comprehensive_analysis(
                        species_data=species_requirements,
                        growing_environment=growing_env
                    )
                    
                    # Adjust substrate recommendations based on environmental deltas
                    if substrate_recs and environment_analysis:
                        substrate_adjustments = self.delta_analyzer.adjust_substrate_for_conditions(
                            base_substrate_recs=substrate_recs,
                            environmental_deltas={
                                'temperature': environment_analysis['temperature_delta'],
                                'humidity': environment_analysis['humidity_delta'],
                                'light': environment_analysis['light_delta']
                            }
                        )
                        # Add adjustments to substrate recs
                        substrate_recs['environmental_adjustments'] = substrate_adjustments
                    
                    print(f"   ✅ Environment analysis complete (compatibility: {environment_analysis['compatibility_score']}/100)")
                else:
                    print(f"   ⚠️  Growing environment ID {growing_environment_id} not found")
                    
            except Exception as e:
                print(f"   ⚠️  Environment analysis failed: {e}")
                environment_analysis = {'status': 'error', 'error': str(e)}
        
        # Generate comparison and recommendations
        culture_sheet = self._merge_and_analyze(
            species_info=species_info,
            baker_data=baker_data,
            aos_data=aos_data,
            weather_data=weather_data,
            monthly_comparison=monthly_comparison,
            microclimate_data=microclimate_data,
            substrate_recs=substrate_recs,
            environment_analysis=environment_analysis,
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
        """
        Get local climate data using Open-Meteo API (free, no key required)
        Calculates USDA hardiness zone and seasonal temperature ranges
        """
        try:
            # Get 30 years of data for USDA zone calculation (1991-2020)
            # Plus recent 3 years for current climate patterns
            historical_url = "https://archive-api.open-meteo.com/v1/archive"
            
            # 30-year data for USDA zone
            zone_params = {
                "latitude": lat,
                "longitude": lon,
                "start_date": "1991-01-01",
                "end_date": "2020-12-31",
                "daily": "temperature_2m_min",
                "temperature_unit": "fahrenheit"
            }
            
            zone_response = requests.get(historical_url, params=zone_params, timeout=10)
            if not zone_response.ok:
                raise Exception(f"Open-Meteo API error: {zone_response.status_code}")
            zone_data = zone_response.json()
            if 'daily' not in zone_data:
                raise Exception("Unexpected API response structure")
            
            # Calculate USDA hardiness zone
            usda_zone = self._calculate_usda_zone(zone_data)
            
            # Recent 3 years for seasonal averages (more current patterns)
            from datetime import datetime, timedelta
            end_date = datetime.now() - timedelta(days=7)  # Open-Meteo has 2-7 day delay
            start_date = end_date - timedelta(days=1095)  # 3 years
            
            climate_params = {
                "latitude": lat,
                "longitude": lon,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,relative_humidity_2m_mean",
                "temperature_unit": "fahrenheit",
                "precipitation_unit": "mm"
            }
            
            climate_response = requests.get(historical_url, params=climate_params, timeout=10)
            if not climate_response.ok:
                raise Exception(f"Open-Meteo API error: {climate_response.status_code}")
            climate_data = climate_response.json()
            if 'daily' not in climate_data:
                raise Exception("Unexpected API response structure")
            
            # Calculate seasonal averages
            seasonal_data = self._calculate_seasonal_averages(climate_data)
            
            return {
                'usda_zone': usda_zone['zone'],
                'avg_extreme_min': usda_zone['avg_extreme_min'],
                'summer_high': seasonal_data['summer_high'],
                'summer_low': seasonal_data['summer_low'],
                'winter_high': seasonal_data['winter_high'],
                'winter_low': seasonal_data['winter_low'],
                'avg_humidity': seasonal_data['avg_humidity'],
                'annual_precipitation': seasonal_data['annual_precipitation'],
                'climate_type': self._classify_climate(usda_zone['zone'], seasonal_data)
            }
            
        except Exception as e:
            print(f"   ⚠️  Weather API error: {e}")
            # Return None values if API fails
            return {
                'usda_zone': None,
                'avg_extreme_min': None,
                'summer_high': None,
                'summer_low': None,
                'winter_high': None,
                'winter_low': None,
                'avg_humidity': None,
                'annual_precipitation': None,
                'climate_type': None
            }
    
    def _calculate_usda_zone(self, zone_data: Dict) -> Dict:
        """Calculate USDA hardiness zone from 30-year minimum temperature data"""
        try:
            import pandas as pd
            
            # Convert to DataFrame
            df = pd.DataFrame({
                'date': pd.to_datetime(zone_data['daily']['time']),
                'temp_min': zone_data['daily']['temperature_2m_min']
            })
            
            # Extract year and find annual extreme minimum
            df['year'] = df['date'].dt.year
            annual_min = df.groupby('year')['temp_min'].min()
            
            # Calculate average annual extreme minimum
            avg_extreme_min = annual_min.mean()
            
            # Map to USDA hardiness zone with explicit boundaries
            # Each zone is a 5°F range (e.g., 10a is 30-35°F)
            if avg_extreme_min < -55:
                zone = '1a'
            elif avg_extreme_min < -50:
                zone = '1b'
            elif avg_extreme_min < -45:
                zone = '2a'
            elif avg_extreme_min < -40:
                zone = '2b'
            elif avg_extreme_min < -35:
                zone = '3a'
            elif avg_extreme_min < -30:
                zone = '3b'
            elif avg_extreme_min < -25:
                zone = '4a'
            elif avg_extreme_min < -20:
                zone = '4b'
            elif avg_extreme_min < -15:
                zone = '5a'
            elif avg_extreme_min < -10:
                zone = '5b'
            elif avg_extreme_min < -5:
                zone = '6a'
            elif avg_extreme_min < 0:
                zone = '6b'
            elif avg_extreme_min < 5:
                zone = '7a'
            elif avg_extreme_min < 10:
                zone = '7b'
            elif avg_extreme_min < 15:
                zone = '8a'
            elif avg_extreme_min < 20:
                zone = '8b'
            elif avg_extreme_min < 25:
                zone = '9a'
            elif avg_extreme_min < 30:
                zone = '9b'
            elif avg_extreme_min < 35:
                zone = '10a'
            elif avg_extreme_min < 40:
                zone = '10b'
            elif avg_extreme_min < 45:
                zone = '11a'
            elif avg_extreme_min < 50:
                zone = '11b'
            elif avg_extreme_min < 55:
                zone = '12a'
            elif avg_extreme_min < 60:
                zone = '12b'
            elif avg_extreme_min < 65:
                zone = '13a'
            else:
                zone = '13b'
            
            return {
                'zone': zone,
                'avg_extreme_min': round(avg_extreme_min, 1)
            }
        except Exception as e:
            print(f"   ⚠️  USDA zone calculation error: {e}")
            return {'zone': None, 'avg_extreme_min': None}
    
    def _calculate_seasonal_averages(self, climate_data: Dict) -> Dict:
        """Calculate seasonal temperature/humidity/precipitation averages"""
        try:
            import pandas as pd
            
            df = pd.DataFrame({
                'date': pd.to_datetime(climate_data['daily']['time']),
                'temp_max': climate_data['daily']['temperature_2m_max'],
                'temp_min': climate_data['daily']['temperature_2m_min'],
                'precipitation': climate_data['daily']['precipitation_sum'],
                'humidity': climate_data['daily']['relative_humidity_2m_mean']
            })
            
            # Define seasons (Northern Hemisphere - adjust for location if needed)
            df['month'] = df['date'].dt.month
            df['season'] = df['month'].apply(lambda m: 
                'summer' if m in [6, 7, 8] else 
                'winter' if m in [12, 1, 2] else 
                'spring' if m in [3, 4, 5] else 'fall'
            )
            
            # Calculate seasonal averages
            summer = df[df['season'] == 'summer']
            winter = df[df['season'] == 'winter']
            
            return {
                'summer_high': round(summer['temp_max'].mean(), 1) if len(summer) > 0 else None,
                'summer_low': round(summer['temp_min'].mean(), 1) if len(summer) > 0 else None,
                'winter_high': round(winter['temp_max'].mean(), 1) if len(winter) > 0 else None,
                'winter_low': round(winter['temp_min'].mean(), 1) if len(winter) > 0 else None,
                'avg_humidity': round(df['humidity'].mean(), 0) if 'humidity' in df else None,
                'annual_precipitation': round(df['precipitation'].sum() / 3, 1)  # 3 years of data
            }
        except Exception as e:
            print(f"   ⚠️  Seasonal calculation error: {e}")
            return {
                'summer_high': None, 'summer_low': None,
                'winter_high': None, 'winter_low': None,
                'avg_humidity': None, 'annual_precipitation': None
            }
    
    def _classify_climate(self, usda_zone: str, seasonal_data: Dict) -> Optional[str]:
        """Classify climate type based on USDA zone and seasonal patterns"""
        if not usda_zone:
            return None
        
        zone_num = int(usda_zone[:-1])  # Extract number from zone like "9a"
        
        # Simple climate classification
        if zone_num <= 3:
            return "arctic/subarctic"
        elif zone_num <= 5:
            return "cold continental"
        elif zone_num <= 7:
            return "temperate"
        elif zone_num <= 9:
            return "subtropical"
        else:
            return "tropical/subtropical"
    
    def _get_monthly_weather(self, lat: float, lon: float) -> Optional[Dict]:
        """
        Get monthly average weather data for a location (Baker's methodology)
        Returns 12 months of temperature, precipitation, and humidity data
        """
        try:
            import pandas as pd
            from datetime import datetime, timedelta
            
            historical_url = "https://archive-api.open-meteo.com/v1/archive"
            
            # Get 3 years of recent data for monthly averages
            end_date = datetime.now() - timedelta(days=7)
            start_date = end_date - timedelta(days=1095)  # 3 years
            
            params = {
                "latitude": lat,
                "longitude": lon,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,relative_humidity_2m_mean",
                "temperature_unit": "fahrenheit",
                "precipitation_unit": "mm"
            }
            
            response = requests.get(historical_url, params=params, timeout=10)
            if not response.ok:
                raise Exception(f"Open-Meteo API error: {response.status_code}")
            data = response.json()
            if 'daily' not in data:
                raise Exception("Unexpected API response structure")
            
            # Convert to DataFrame
            df = pd.DataFrame({
                'date': pd.to_datetime(data['daily']['time']),
                'temp_max': data['daily']['temperature_2m_max'],
                'temp_min': data['daily']['temperature_2m_min'],
                'precipitation': data['daily']['precipitation_sum'],
                'humidity': data['daily']['relative_humidity_2m_mean']
            })
            
            # Extract month and calculate monthly averages
            df['month'] = df['date'].dt.month
            monthly = df.groupby('month').agg({
                'temp_max': 'mean',
                'temp_min': 'mean',
                'precipitation': 'sum',
                'humidity': 'mean'
            })
            
            # Convert to list of dicts for each month
            months = []
            month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            
            for i in range(1, 13):
                if i in monthly.index:
                    months.append({
                        'month': month_names[i-1],
                        'avg_high': round(monthly.loc[i, 'temp_max'], 1),
                        'avg_low': round(monthly.loc[i, 'temp_min'], 1),
                        'precipitation': round(monthly.loc[i, 'precipitation'] / 3, 1),  # 3 years
                        'humidity': round(monthly.loc[i, 'humidity'], 0)
                    })
            
            return {'months': months}
            
        except Exception as e:
            print(f"   ⚠️  Monthly weather error: {e}")
            return None
    
    def _get_monthly_comparison(self, baker_data: Optional[Dict], 
                                grower_lat: float, grower_lon: float) -> Optional[Dict]:
        """
        Compare monthly weather between orchid's native habitat and grower's location
        (Following Baker's methodology of showing monthly climate data)
        """
        # Get grower's monthly weather
        grower_monthly = self._get_monthly_weather(grower_lat, grower_lon)
        if not grower_monthly:
            return None
        
        # Get native habitat monthly weather (requires geocoding Baker origin data)
        native_monthly = None
        if baker_data and baker_data.get('origin'):
            # Future implementation: geocode Baker origin_country/origin_region to coordinates
            # Then call: native_monthly = self._get_monthly_weather(native_lat, native_lon)
            pass
        
        # Only mark as available if we have actual comparison data
        has_comparison = bool(grower_monthly and native_monthly)
        
        return {
            'grower_location': grower_monthly,
            'native_habitat': native_monthly,
            'comparison_available': has_comparison,
            'grower_only': bool(grower_monthly and not native_monthly),
            'note': 'Native habitat climate data requires geocoding Baker origin country/region to coordinates' if not has_comparison else None
        }
    
    def _merge_and_analyze(
        self, 
        species_info: Dict,
        baker_data: Optional[Dict],
        aos_data: Optional[Dict],
        weather_data: Dict,
        monthly_comparison: Optional[Dict],
        microclimate_data: Optional[Dict],
        substrate_recs: Optional[Dict],
        environment_analysis: Optional[Dict],
        location: Dict
    ) -> Dict:
        """Merge all data sources including microclimate analysis and substrate recommendations"""
        
        culture_sheet = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'species': species_info['scientific_name'],
                'genus': species_info['genus'],
                'location': location,
                'data_sources': {
                    'baker': bool(baker_data),
                    'aos': bool(aos_data),
                    'weather': bool(weather_data and weather_data.get('usda_zone'))
                },
                'climate': weather_data if weather_data.get('usda_zone') else None,
                'monthly_comparison': monthly_comparison
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
        
        # NEW: Microclimate Analysis (Revolutionary feature!)
        if microclimate_data:
            culture_sheet['microclimate_analysis'] = {
                'data': microclimate_data,
                'generated_at': datetime.now().isoformat(),
                'unique_feature': 'This data-driven analysis is unique to The Orchid Continuum'
            }
        
        # NEW: Substrate Recommendations
        if substrate_recs:
            culture_sheet['substrate_recommendations'] = {
                'data': substrate_recs,
                'generated_at': datetime.now().isoformat()
            }
        
        # NEW: Growing Environment Personalization
        if environment_analysis:
            # Convert datetime objects to strings for JSON serialization
            env_data = environment_analysis.copy()
            # The growing_environment_name should already be a string, but ensure all nested objects are serializable
            culture_sheet['environment_personalization'] = {
                'compatibility_score': env_data.get('compatibility_score'),
                'compatibility_rating': env_data.get('compatibility_rating'),
                'growing_environment_name': env_data.get('growing_environment_name'),
                'summary': env_data.get('summary'),
                'temperature_delta': env_data.get('temperature_delta'),
                'humidity_delta': env_data.get('humidity_delta'),
                'light_delta': env_data.get('light_delta'),
                'generated_at': datetime.now().isoformat(),
                'unique_feature': 'Personalized recommendations based on YOUR actual growing conditions'
            }
        
        # Generate location-specific recommendations
        recommendations = self._generate_recommendations(
            baker_data, aos_data, weather_data, location, 
            microclimate_data, substrate_recs
        )
        culture_sheet['recommendations'] = recommendations
        
        return culture_sheet
    
    def _generate_recommendations(
        self,
        baker_data: Optional[Dict],
        aos_data: Optional[Dict],
        weather_data: Dict,
        location: Dict,
        microclimate_data: Optional[Dict] = None,
        substrate_recs: Optional[Dict] = None
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
        
        # Sanitize culture_sheet for JSON serialization with cycle detection
        def sanitize_for_json(obj, seen=None):
            """Recursively convert non-JSON-serializable objects"""
            if seen is None:
                seen = set()
            
            # Check for circular reference using object id
            obj_id = id(obj)
            if obj_id in seen:
                return "<circular reference>"
            
            if isinstance(obj, dict):
                seen.add(obj_id)
                result = {k: sanitize_for_json(v, seen) for k, v in obj.items()}
                seen.remove(obj_id)
                return result
            elif isinstance(obj, list):
                seen.add(obj_id)
                result = [sanitize_for_json(item, seen) for item in obj]
                seen.remove(obj_id)
                return result
            elif isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, (int, float, str, bool, type(None))):
                return obj
            else:
                # Convert other types to string representation
                return str(obj)
        
        sanitized_culture_sheet = sanitize_for_json(culture_sheet)
        
        self.cur.execute("""
            INSERT INTO culture_sheet_cache (
                taxonomy_id, location_lat, location_lon,
                culture_sheet_data,
                baker_data_used, aos_data_used,
                generated_at, expires_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            taxonomy_id, lat, lon,
            json.dumps(sanitized_culture_sheet),
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
