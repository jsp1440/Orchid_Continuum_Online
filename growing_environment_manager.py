#!/usr/bin/env python3
"""
Growing Environment Profile Manager
Allows users to define their actual growing conditions for personalized recommendations
"""
import os
import psycopg2
import json
from typing import Dict, List, Optional
from datetime import datetime

DATABASE_URL = os.environ.get('DATABASE_URL')

class GrowingEnvironmentManager:
    """
    Manages user growing environment profiles
    """
    
    # Standard environment templates
    ENVIRONMENT_TEMPLATES = {
        'cool_greenhouse': {
            'name': 'Cool Greenhouse',
            'location_type': 'greenhouse',
            'temperature_avg': 65.0,
            'temperature_min': 55.0,
            'temperature_max': 75.0,
            'humidity_avg': 70,
            'humidity_min': 60,
            'humidity_max': 80,
            'light_level': 'bright',
            'light_hours_per_day': 12.0,
            'air_circulation': 'good'
        },
        'warm_greenhouse': {
            'name': 'Warm Greenhouse',
            'location_type': 'greenhouse',
            'temperature_avg': 75.0,
            'temperature_min': 65.0,
            'temperature_max': 85.0,
            'humidity_avg': 65,
            'humidity_min': 55,
            'humidity_max': 75,
            'light_level': 'bright',
            'light_hours_per_day': 14.0,
            'air_circulation': 'excellent'
        },
        'shaded_patio': {
            'name': 'Shaded Patio',
            'location_type': 'outdoor',
            'temperature_avg': 70.0,
            'temperature_min': 60.0,
            'temperature_max': 80.0,
            'humidity_avg': 50,
            'humidity_min': 40,
            'humidity_max': 60,
            'light_level': 'medium',
            'light_hours_per_day': 8.0,
            'air_circulation': 'excellent',
            'seasonal_variation': True
        },
        'bright_window': {
            'name': 'Bright Window (South-facing)',
            'location_type': 'indoor',
            'temperature_avg': 72.0,
            'temperature_min': 68.0,
            'temperature_max': 78.0,
            'humidity_avg': 40,
            'humidity_min': 30,
            'humidity_max': 50,
            'light_level': 'bright',
            'light_hours_per_day': 10.0,
            'air_circulation': 'moderate'
        },
        'low_light_indoor': {
            'name': 'Low Light Indoor',
            'location_type': 'indoor',
            'temperature_avg': 70.0,
            'temperature_min': 65.0,
            'temperature_max': 75.0,
            'humidity_avg': 35,
            'humidity_min': 25,
            'humidity_max': 45,
            'light_level': 'low',
            'light_hours_per_day': 6.0,
            'air_circulation': 'poor'
        }
    }
    
    def __init__(self, connection=None):
        """
        Initialize manager with optional shared connection
        
        Args:
            connection: Optional psycopg2 connection to share
        """
        if connection:
            self.conn = connection
            self.owns_connection = False
        else:
            self.conn = psycopg2.connect(DATABASE_URL)
            self.owns_connection = True
        
        self.cur = self.conn.cursor()
    
    def create_environment(
        self,
        name: str,
        location_type: str,
        temperature_avg: float,
        humidity_avg: int,
        light_level: str,
        user_id: Optional[int] = None,
        **kwargs
    ) -> Dict:
        """
        Create a new growing environment profile
        
        Args:
            name: Descriptive name (e.g., "My Greenhouse")
            location_type: Type of growing area
            temperature_avg: Average temperature in Fahrenheit
            humidity_avg: Average humidity percentage
            light_level: Light level description
            user_id: Optional user ID (None for session-based)
            **kwargs: Additional optional parameters
        
        Returns:
            Created environment profile
        """
        self.cur.execute("""
            INSERT INTO user_growing_environments (
                user_id, name, location_type,
                temperature_avg, temperature_min, temperature_max,
                humidity_avg, humidity_min, humidity_max,
                light_level, light_hours_per_day, air_circulation,
                seasonal_variation, notes
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            user_id,
            name,
            location_type,
            temperature_avg,
            kwargs.get('temperature_min'),
            kwargs.get('temperature_max'),
            humidity_avg,
            kwargs.get('humidity_min'),
            kwargs.get('humidity_max'),
            light_level,
            kwargs.get('light_hours_per_day'),
            kwargs.get('air_circulation', 'moderate'),
            kwargs.get('seasonal_variation', False),
            kwargs.get('notes')
        ))
        
        env_id = self.cur.fetchone()[0]
        self.conn.commit()
        
        return self.get_environment(env_id)
    
    def create_from_template(
        self,
        template_name: str,
        custom_name: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> Dict:
        """
        Create environment from predefined template
        
        Args:
            template_name: Name of template to use
            custom_name: Optional custom name override
            user_id: Optional user ID
        
        Returns:
            Created environment profile
        """
        if template_name not in self.ENVIRONMENT_TEMPLATES:
            raise ValueError(f"Unknown template: {template_name}. Available: {list(self.ENVIRONMENT_TEMPLATES.keys())}")
        
        template = self.ENVIRONMENT_TEMPLATES[template_name].copy()
        if custom_name:
            template['name'] = custom_name
        
        return self.create_environment(user_id=user_id, **template)
    
    def get_environment(self, env_id: int) -> Optional[Dict]:
        """Get environment by ID"""
        self.cur.execute("""
            SELECT 
                id, user_id, name, location_type,
                temperature_avg, temperature_min, temperature_max,
                humidity_avg, humidity_min, humidity_max,
                light_level, light_hours_per_day, air_circulation,
                seasonal_variation, notes,
                created_at, updated_at, last_used
            FROM user_growing_environments
            WHERE id = %s
        """, (env_id,))
        
        row = self.cur.fetchone()
        if not row:
            return None
        
        return {
            'id': row[0],
            'user_id': row[1],
            'name': row[2],
            'location_type': row[3],
            'temperature': {
                'avg': float(row[4]) if row[4] else None,
                'min': float(row[5]) if row[5] else None,
                'max': float(row[6]) if row[6] else None
            },
            'humidity': {
                'avg': row[7],
                'min': row[8],
                'max': row[9]
            },
            'light_level': row[10],
            'light_hours_per_day': float(row[11]) if row[11] else None,
            'air_circulation': row[12],
            'seasonal_variation': row[13],
            'notes': row[14],
            'created_at': row[15],
            'updated_at': row[16],
            'last_used': row[17]
        }
    
    def list_environments(self, user_id: Optional[int] = None) -> List[Dict]:
        """List all environments for a user (or all if user_id is None)"""
        if user_id is not None:
            self.cur.execute("""
                SELECT id FROM user_growing_environments
                WHERE user_id = %s
                ORDER BY last_used DESC NULLS LAST, created_at DESC
            """, (user_id,))
        else:
            self.cur.execute("""
                SELECT id FROM user_growing_environments
                WHERE user_id IS NULL
                ORDER BY created_at DESC
                LIMIT 100
            """)
        
        env_ids = [row[0] for row in self.cur.fetchall()]
        return [self.get_environment(env_id) for env_id in env_ids]
    
    def update_environment(self, env_id: int, **updates) -> Dict:
        """Update environment parameters"""
        allowed_fields = [
            'name', 'location_type',
            'temperature_avg', 'temperature_min', 'temperature_max',
            'humidity_avg', 'humidity_min', 'humidity_max',
            'light_level', 'light_hours_per_day', 'air_circulation',
            'seasonal_variation', 'notes'
        ]
        
        update_parts = []
        values = []
        
        for field, value in updates.items():
            if field in allowed_fields:
                update_parts.append(f"{field} = %s")
                values.append(value)
        
        if not update_parts:
            return self.get_environment(env_id)
        
        update_parts.append("updated_at = NOW()")
        values.append(env_id)
        
        query = f"""
            UPDATE user_growing_environments
            SET {', '.join(update_parts)}
            WHERE id = %s
        """
        
        self.cur.execute(query, values)
        self.conn.commit()
        
        return self.get_environment(env_id)
    
    def delete_environment(self, env_id: int):
        """Delete an environment profile"""
        self.cur.execute("""
            DELETE FROM user_growing_environments
            WHERE id = %s
        """, (env_id,))
        self.conn.commit()
    
    def mark_used(self, env_id: int):
        """Mark environment as recently used"""
        self.cur.execute("""
            UPDATE user_growing_environments
            SET last_used = NOW()
            WHERE id = %s
        """, (env_id,))
        self.conn.commit()
    
    def add_measurement(
        self,
        env_id: int,
        temperature: Optional[float] = None,
        humidity: Optional[int] = None,
        light_reading: Optional[int] = None,
        source: str = 'manual',
        metadata: Optional[Dict] = None
    ):
        """
        Add environmental measurement (for sensor integration)
        
        Args:
            env_id: Environment ID
            temperature: Temperature reading
            humidity: Humidity reading
            light_reading: Light reading (lux/fc)
            source: Data source
            metadata: Additional sensor metadata
        """
        self.cur.execute("""
            INSERT INTO environment_measurements (
                environment_id, temperature, humidity, light_reading, source, metadata
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            env_id, temperature, humidity, light_reading, source,
            json.dumps(metadata) if metadata else None
        ))
        self.conn.commit()
    
    def __del__(self):
        """Cleanup - only close connection if we own it"""
        if hasattr(self, 'cur'):
            self.cur.close()
        if hasattr(self, 'conn') and self.owns_connection:
            self.conn.close()


def main():
    """Test growing environment manager"""
    manager = GrowingEnvironmentManager()
    
    print("=" * 70)
    print("🌱 GROWING ENVIRONMENT MANAGER")
    print("=" * 70)
    print()
    
    # Create from template
    print("Creating greenhouse environment from template...")
    greenhouse = manager.create_from_template(
        template_name='warm_greenhouse',
        custom_name='My Warm Greenhouse'
    )
    print(f"✅ Created: {greenhouse['name']}")
    print(f"   Temperature: {greenhouse['temperature']['avg']}°F (range: {greenhouse['temperature']['min']}-{greenhouse['temperature']['max']})")
    print(f"   Humidity: {greenhouse['humidity']['avg']}% (range: {greenhouse['humidity']['min']}-{greenhouse['humidity']['max']})")
    print(f"   Light: {greenhouse['light_level']} ({greenhouse['light_hours_per_day']} hrs/day)")
    print()
    
    # Create custom environment
    print("Creating custom shaded patio environment...")
    patio = manager.create_environment(
        name='My Shaded Patio',
        location_type='outdoor',
        temperature_avg=68.0,
        temperature_min=55.0,
        temperature_max=80.0,
        humidity_avg=55,
        humidity_min=40,
        humidity_max=70,
        light_level='medium',
        light_hours_per_day=6.0,
        air_circulation='excellent',
        seasonal_variation=True,
        notes='Gets morning sun, shaded afternoon. Cooler in winter.'
    )
    print(f"✅ Created: {patio['name']}")
    print()
    
    # List environments
    print("Listing all environments:")
    environments = manager.list_environments()
    for env in environments:
        print(f"  - {env['name']} ({env['location_type']}): {env['temperature']['avg']}°F, {env['humidity']['avg']}% humidity")
    
    print()
    print("✅ Growing environment system working!")


if __name__ == '__main__':
    main()
