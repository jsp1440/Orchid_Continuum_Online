"""
Culture Sheet Database Models
Structured storage for Baker's methodology and AOS culture data
"""
from app import db
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime


class BakerCultureSheet(db.Model):
    """
    Charles & Margaret Baker's orchid culture sheets
    Source: https://orchidculture.com/COD/FREE/
    """
    __tablename__ = 'baker_culture_sheets'
    
    id = Column(Integer, primary_key=True)
    taxonomy_id = Column(Integer, ForeignKey('orchid_taxonomy.id'), nullable=False, index=True)
    
    # Basic Info
    genus = Column(String(100), nullable=False, index=True)
    species = Column(String(100))
    scientific_name = Column(String(255), nullable=False, index=True)
    common_name = Column(String(255))
    
    # Geographic Origin
    origin_country = Column(String(100))
    origin_region = Column(Text)
    native_elevation_min = Column(Integer)  # meters
    native_elevation_max = Column(Integer)  # meters
    climate_zone = Column(String(100))  # tropical, subtropical, temperate
    
    # Temperature Requirements (Fahrenheit)
    temp_summer_day_min = Column(Integer)
    temp_summer_day_max = Column(Integer)
    temp_summer_night_min = Column(Integer)
    temp_summer_night_max = Column(Integer)
    temp_winter_day_min = Column(Integer)
    temp_winter_day_max = Column(Integer)
    temp_winter_night_min = Column(Integer)
    temp_winter_night_max = Column(Integer)
    
    # Light Requirements
    light_level = Column(String(50))  # low, medium, high, very high
    light_description = Column(Text)
    light_footcandles_min = Column(Integer)
    light_footcandles_max = Column(Integer)
    
    # Water Requirements
    water_frequency = Column(String(100))
    water_description = Column(Text)
    drought_tolerance = Column(Boolean)
    
    # Humidity Requirements
    humidity_min = Column(Integer)  # percentage
    humidity_max = Column(Integer)  # percentage
    humidity_description = Column(Text)
    
    # Growing Media
    potting_media = Column(Text)
    mounting_recommended = Column(Boolean)
    
    # Fertilizer
    fertilizer_recommendation = Column(Text)
    fertilizer_frequency = Column(String(100))
    
    # Flowering
    flowering_season = Column(String(100))
    flowering_trigger = Column(Text)
    fragrance = Column(Boolean)
    fragrance_description = Column(Text)
    
    # Growth Habit
    growth_habit = Column(String(50))  # sympodial, monopodial
    growth_rate = Column(String(50))  # slow, moderate, fast
    
    # Special Requirements
    rest_period_required = Column(Boolean)
    rest_period_description = Column(Text)
    special_notes = Column(Text)
    
    # Metadata
    raw_data = Column(JSON)  # Store original scraped data
    source_url = Column(Text)
    scraped_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    data_quality_score = Column(Float)  # 0-100 based on completeness
    
    # Relationship
    taxonomy = relationship("OrchidTaxonomy", backref="baker_culture")
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'scientific_name': self.scientific_name,
            'common_name': self.common_name,
            'origin': {
                'country': self.origin_country,
                'region': self.origin_region,
                'elevation': f"{self.native_elevation_min}-{self.native_elevation_max}m" if self.native_elevation_min else None,
                'climate_zone': self.climate_zone
            },
            'temperature': {
                'summer': {
                    'day': f"{self.temp_summer_day_min}-{self.temp_summer_day_max}°F" if self.temp_summer_day_min else None,
                    'night': f"{self.temp_summer_night_min}-{self.temp_summer_night_max}°F" if self.temp_summer_night_min else None
                },
                'winter': {
                    'day': f"{self.temp_winter_day_min}-{self.temp_winter_day_max}°F" if self.temp_winter_day_min else None,
                    'night': f"{self.temp_winter_night_min}-{self.temp_winter_night_max}°F" if self.temp_winter_night_min else None
                }
            },
            'light': {
                'level': self.light_level,
                'footcandles': f"{self.light_footcandles_min}-{self.light_footcandles_max}" if self.light_footcandles_min else None,
                'description': self.light_description
            },
            'water': {
                'frequency': self.water_frequency,
                'description': self.water_description,
                'drought_tolerant': self.drought_tolerance
            },
            'humidity': {
                'range': f"{self.humidity_min}-{self.humidity_max}%" if self.humidity_min else None,
                'description': self.humidity_description
            },
            'potting': {
                'media': self.potting_media,
                'mounting_recommended': self.mounting_recommended
            },
            'flowering': {
                'season': self.flowering_season,
                'trigger': self.flowering_trigger,
                'fragrant': self.fragrance,
                'fragrance_description': self.fragrance_description
            },
            'special_care': {
                'rest_period': self.rest_period_required,
                'rest_description': self.rest_period_description,
                'notes': self.special_notes
            },
            'metadata': {
                'source': 'Charles & Margaret Baker',
                'source_url': self.source_url,
                'quality_score': self.data_quality_score,
                'updated': self.updated_at.isoformat() if self.updated_at else None
            }
        }


class AOSCultureSheet(db.Model):
    """
    American Orchid Society culture sheets
    Source: https://www.aos.org/orchid-care/care-sheets
    """
    __tablename__ = 'aos_culture_sheets'
    
    id = Column(Integer, primary_key=True)
    taxonomy_id = Column(Integer, ForeignKey('orchid_taxonomy.id'), index=True)
    
    # Basic Info (AOS sheets are typically genus-level)
    genus = Column(String(100), nullable=False, index=True, unique=True)
    common_names = Column(Text)  # comma-separated list
    
    # Light Requirements
    light_requirements = Column(Text)
    light_level = Column(String(50))  # shade, low, medium, bright, very bright
    
    # Temperature Requirements
    temperature_requirements = Column(Text)
    temp_category = Column(String(50))  # cool, intermediate, warm
    temp_day_min = Column(Integer)
    temp_day_max = Column(Integer)
    temp_night_min = Column(Integer)
    temp_night_max = Column(Integer)
    
    # Water Requirements
    water_requirements = Column(Text)
    watering_frequency = Column(String(100))
    
    # Humidity Requirements
    humidity_requirements = Column(Text)
    humidity_percentage = Column(String(50))
    
    # Fertilizer Requirements
    fertilizer_requirements = Column(Text)
    fertilizer_schedule = Column(String(100))
    
    # Potting Requirements
    potting_requirements = Column(Text)
    repotting_frequency = Column(String(100))
    preferred_media = Column(Text)
    
    # Special Notes
    special_notes = Column(Text)
    common_problems = Column(Text)
    
    # Metadata
    source_url = Column(Text)
    raw_data = Column(JSON)
    scraped_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    taxonomy = relationship("OrchidTaxonomy", backref="aos_culture", foreign_keys=[taxonomy_id])
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'genus': self.genus,
            'common_names': self.common_names.split(',') if self.common_names else [],
            'light': {
                'requirements': self.light_requirements,
                'level': self.light_level
            },
            'temperature': {
                'requirements': self.temperature_requirements,
                'category': self.temp_category,
                'day_range': f"{self.temp_day_min}-{self.temp_day_max}°F" if self.temp_day_min else None,
                'night_range': f"{self.temp_night_min}-{self.temp_night_max}°F" if self.temp_night_min else None
            },
            'water': {
                'requirements': self.water_requirements,
                'frequency': self.watering_frequency
            },
            'humidity': {
                'requirements': self.humidity_requirements,
                'percentage': self.humidity_percentage
            },
            'fertilizer': {
                'requirements': self.fertilizer_requirements,
                'schedule': self.fertilizer_schedule
            },
            'potting': {
                'requirements': self.potting_requirements,
                'repotting_frequency': self.repotting_frequency,
                'media': self.preferred_media
            },
            'special_care': {
                'notes': self.special_notes,
                'common_problems': self.common_problems
            },
            'metadata': {
                'source': 'American Orchid Society',
                'source_url': self.source_url,
                'updated': self.updated_at.isoformat() if self.updated_at else None
            }
        }


class CultureSheetCache(db.Model):
    """
    Cache for generated location-specific culture sheets
    Stores the combined Baker + AOS + Weather analysis
    """
    __tablename__ = 'culture_sheet_cache'
    
    id = Column(Integer, primary_key=True)
    taxonomy_id = Column(Integer, ForeignKey('orchid_taxonomy.id'), nullable=False, index=True)
    
    # Location Info
    location_lat = Column(Float, nullable=False)
    location_lon = Column(Float, nullable=False)
    location_city = Column(String(255))
    location_country = Column(String(100))
    usda_zone = Column(String(10))
    
    # Generated Culture Sheet (JSON)
    culture_sheet_data = Column(JSON, nullable=False)
    
    # Sources Used
    baker_data_used = Column(Boolean, default=False)
    aos_data_used = Column(Boolean, default=False)
    weather_data_used = Column(Boolean, default=False)
    
    # Cache Management
    generated_at = Column(DateTime, default=datetime.utcnow, index=True)
    expires_at = Column(DateTime)  # Refresh after 30 days
    access_count = Column(Integer, default=0)
    last_accessed = Column(DateTime)
    
    # Relationship
    taxonomy = relationship("OrchidTaxonomy", backref="cached_culture_sheets")
    
    def is_expired(self):
        """Check if cache has expired"""
        if not self.expires_at:
            return True
        return datetime.utcnow() > self.expires_at
    
    def record_access(self):
        """Record cache hit"""
        self.access_count += 1
        self.last_accessed = datetime.utcnow()
        db.session.commit()
