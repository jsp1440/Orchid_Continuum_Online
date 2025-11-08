"""
Orchid Distribution Map Generator
Creates interactive world maps showing where orchids occur
"""

import folium
from folium import plugins
import json
import logging

logger = logging.getLogger(__name__)

def create_distribution_map(orchid):
    """
    Create an interactive world map showing orchid distribution
    
    Args:
        orchid: OrchidRecord object with distribution data
        
    Returns:
        HTML string with embedded map
    """
    try:
        # Start with a world view centered on equator
        distribution_map = folium.Map(
            location=[0, 0],
            zoom_start=2,
            tiles='OpenStreetMap',
            control_scale=True
        )
        
        # Track if we added any markers
        has_data = False
        
        # Add GBIF occurrence points if available
        if orchid.gbif_distribution and orchid.gbif_distribution != '{}':
            gbif_data = orchid.gbif_distribution if isinstance(orchid.gbif_distribution, dict) else json.loads(orchid.gbif_distribution)
            
            # Add occurrence coordinates
            if 'coordinates' in gbif_data and gbif_data['coordinates']:
                for coord in gbif_data['coordinates']:
                    if coord.get('lat') and coord.get('lon'):
                        folium.CircleMarker(
                            location=[coord['lat'], coord['lon']],
                            radius=6,
                            popup=f"""
                                <strong>{orchid.scientific_name or 'Unknown'}</strong><br>
                                Location: {coord.get('locality', 'Unknown')}<br>
                                Country: {coord.get('country', 'Unknown')}
                            """,
                            color='#ff6b6b',
                            fill=True,
                            fillColor='#ff6b6b',
                            fillOpacity=0.7
                        ).add_to(distribution_map)
                        has_data = True
                
                # Add country boundaries if available
                if 'countries' in gbif_data and gbif_data['countries']:
                    countries_text = ', '.join(gbif_data['countries'])
                    folium.Marker(
                        location=[0, 0],
                        popup=f"<strong>Known from:</strong> {countries_text}",
                        icon=folium.Icon(color='green', icon='info-sign')
                    ).add_to(distribution_map)
        
        # Add single coordinate point if available
        if orchid.decimal_latitude and orchid.decimal_longitude:
            folium.Marker(
                location=[float(orchid.decimal_latitude), float(orchid.decimal_longitude)],
                popup=f"""
                    <strong>{orchid.scientific_name or 'Unknown'}</strong><br>
                    Coordinates: {orchid.decimal_latitude}, {orchid.decimal_longitude}<br>
                    {f'Country: {orchid.country}' if orchid.country else ''}
                """,
                icon=folium.Icon(color='red', icon='leaf', prefix='fa')
            ).add_to(distribution_map)
            
            # Center map on this location
            distribution_map.location = [float(orchid.decimal_latitude), float(orchid.decimal_longitude)]
            distribution_map.zoom_start = 6
            has_data = True
        
        # Add fullscreen control
        plugins.Fullscreen(
            position='topright',
            title='Fullscreen',
            title_cancel='Exit fullscreen',
            force_separate_button=True
        ).add_to(distribution_map)
        
        # Add layer control if we have data
        if has_data:
            folium.LayerControl().add_to(distribution_map)
        
        # Return HTML
        return distribution_map._repr_html_()
        
    except Exception as e:
        logger.error(f"Error creating distribution map: {e}")
        return None


def get_distribution_summary(orchid):
    """
    Get a text summary of orchid distribution
    
    Args:
        orchid: OrchidRecord object
        
    Returns:
        dict with distribution summary
    """
    summary = {
        'has_distribution': False,
        'countries': [],
        'continent': None,
        'occurrence_count': 0,
        'coordinates_count': 0
    }
    
    try:
        # Parse GBIF distribution
        if orchid.gbif_distribution and orchid.gbif_distribution != '{}':
            gbif_data = orchid.gbif_distribution if isinstance(orchid.gbif_distribution, dict) else json.loads(orchid.gbif_distribution)
            
            if 'countries' in gbif_data:
                summary['countries'] = gbif_data['countries']
                summary['has_distribution'] = True
            
            if 'continent' in gbif_data:
                summary['continent'] = gbif_data['continent']
            
            if 'occurrence_count' in gbif_data:
                summary['occurrence_count'] = gbif_data['occurrence_count']
            
            if 'coordinates' in gbif_data:
                summary['coordinates_count'] = len(gbif_data['coordinates'])
        
        # Check for single coordinate
        if orchid.decimal_latitude and orchid.decimal_longitude:
            summary['has_distribution'] = True
            if orchid.country and orchid.country not in summary['countries']:
                summary['countries'].append(orchid.country)
        
    except Exception as e:
        logger.error(f"Error getting distribution summary: {e}")
    
    return summary
