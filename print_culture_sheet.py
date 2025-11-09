#!/usr/bin/env python3
"""
Print Culture Sheet Generator
Renders customizable, print-optimized culture sheets with artwork options
"""
from culture_sheet_generator import CultureSheetGenerator
from flask import Flask, render_template
from datetime import datetime
from typing import Dict, Optional

class PrintCultureSheetGenerator:
    """
    Generates print-ready culture sheets in multiple formats:
    - Single-page (8.5x11)
    - Double-sided cards (index card size)
    - Booklet format
    
    Supports customization:
    - Artwork styles (etching, watercolor, none)
    - Data sections (toggle on/off)
    - Color schemes
    """
    
    def __init__(self):
        self.culture_gen = CultureSheetGenerator()
    
    def generate_single_page(
        self,
        taxonomy_id: int,
        latitude: float,
        longitude: float,
        city: Optional[str] = None,
        country: Optional[str] = None,
        artwork_style: str = "etching",  # "etching", "watercolor", "none"
        artwork_url: Optional[str] = None,
        sections: Optional[list] = None  # Which sections to include
    ) -> Dict:
        """
        Generate single-page print culture sheet
        
        Args:
            taxonomy_id: Species taxonomy ID
            latitude: Grower's location latitude
            longitude: Grower's location longitude
            city: Optional city name
            country: Optional country name
            artwork_style: Style of artwork to include
            artwork_url: Optional custom artwork URL
            sections: List of sections to include (default: all)
        
        Returns:
            Template context dictionary
        """
        # Generate culture sheet data
        culture_sheet = self.culture_gen.generate_culture_sheet(
            taxonomy_id=taxonomy_id,
            latitude=latitude,
            longitude=longitude,
            city=city,
            country=country
        )
        
        # Default sections if not specified
        if sections is None:
            sections = ['temperature', 'light', 'water', 'humidity', 'potting', 'fertilizer']
        
        # Prepare template context
        context = {
            # Format settings
            'format': 'single-page',
            'artwork_style': artwork_style,
            'artwork_url': artwork_url,
            
            # Species information
            'species_name': culture_sheet['metadata']['species'],
            'genus': culture_sheet['metadata']['genus'],
            'family': 'Orchidaceae',  # All orchids
            'native_origin': self._format_native_origin(culture_sheet),
            
            # Climate data
            'climate_data': culture_sheet['metadata'].get('climate'),
            'monthly_comparison': culture_sheet['metadata'].get('monthly_comparison'),
            'location_name': f"{city}, {country}" if city and country else "Your Location",
            
            # Culture sections (only include if in sections list)
            'temperature': culture_sheet.get('temperature') if 'temperature' in sections else None,
            'light': culture_sheet.get('light') if 'light' in sections else None,
            'water': culture_sheet.get('water') if 'water' in sections else None,
            'humidity': culture_sheet.get('humidity') if 'humidity' in sections else None,
            'potting': culture_sheet.get('potting') if 'potting' in sections else None,
            'fertilizer': culture_sheet.get('fertilizer') if 'fertilizer' in sections else None,
            
            # Metadata
            'generated_date': datetime.now().strftime('%B %d, %Y'),
            'data_sources': culture_sheet['metadata']['data_sources']
        }
        
        return context
    
    def _format_native_origin(self, culture_sheet: Dict) -> Optional[str]:
        """Format native origin string from culture sheet data"""
        # TODO: Extract from Baker origin data when available
        return None


def main():
    """Test the print culture sheet generator"""
    from flask import Flask
    
    app = Flask(__name__)
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    
    @app.route('/print/culture-sheet/<int:taxonomy_id>')
    def print_culture_sheet(taxonomy_id):
        """
        Test route for print culture sheet
        Example: http://localhost:5000/print/culture-sheet/7905
        """
        generator = PrintCultureSheetGenerator()
        
        # Generate context
        context = generator.generate_single_page(
            taxonomy_id=taxonomy_id,
            latitude=34.0522,
            longitude=-118.2437,
            city='Los Angeles',
            country='USA',
            artwork_style='etching',
            artwork_url='https://via.placeholder.com/150x200?text=Orchid'  # Placeholder
        )
        
        # Render template (type: ignore needed for Flask's render_template)
        return render_template('culture_sheets/single_page.html', **context)  # type: ignore
    
    print("=" * 70)
    print("🖨️  PRINT CULTURE SHEET TEST SERVER")
    print("=" * 70)
    print()
    print("Test URL: http://localhost:5000/print/culture-sheet/7905")
    print()
    print("Press Ctrl+C to stop")
    print()
    
    app.run(debug=True, port=5000)


if __name__ == '__main__':
    main()
