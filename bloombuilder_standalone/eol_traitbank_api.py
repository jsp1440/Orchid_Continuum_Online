"""EOL TraitBank API Integration for Morphological Traits"""
import requests
import logging

logger = logging.getLogger(__name__)

class EOLTraitBankClient:
    """Client for Encyclopedia of Life TraitBank API"""
    
    BASE_URL = "https://eol.org/api"
    
    def get_species_traits(self, scientific_name):
        """Get morphological traits for a species from TraitBank"""
        try:
            # EOL Pages API
            search_url = f"{self.BASE_URL}/search/1.0.json"
            params = {'q': scientific_name, 'page': 1, 'exact': True}
            
            response = requests.get(search_url, params=params, timeout=10)
            if response.status_code != 200:
                logger.warning(f"EOL search failed for {scientific_name}")
                return None
            
            data = response.json()
            if not data.get('results'):
                return None
            
            page_id = data['results'][0]['id']
            
            # Get trait data
            traits_url = f"{self.BASE_URL}/pages/1.0/{page_id}.json"
            traits_params = {'images_per_page': 0, 'videos_per_page': 0, 'details': True}
            
            traits_response = requests.get(traits_url, params=traits_params, timeout=10)
            if traits_response.status_code != 200:
                return None
            
            traits_data = traits_response.json()
            
            # Parse morphological traits
            morphological_traits = self._parse_morphological_traits(traits_data)
            
            return {
                'species': scientific_name,
                'eol_page_id': page_id,
                'traits': morphological_traits
            }
            
        except Exception as e:
            logger.error(f"EOL TraitBank error for {scientific_name}: {str(e)}")
            return None
    
    def _parse_morphological_traits(self, eol_data):
        """Extract morphological traits from EOL data"""
        traits = []
        
        # EOL data_objects contain trait information
        data_objects = eol_data.get('dataObjects', [])
        
        for obj in data_objects:
            if obj.get('dataType') == 'http://purl.org/dc/dcmitype/Text':
                # Check for morphological descriptions
                description = obj.get('description', '')
                
                # Extract common morphological traits
                if 'spur' in description.lower():
                    traits.append({
                        'category': 'spur_length',
                        'description': description,
                        'source': 'EOL TraitBank'
                    })
                
                if 'labellum' in description.lower() or 'lip' in description.lower():
                    traits.append({
                        'category': 'labellum_shape',
                        'description': description,
                        'source': 'EOL TraitBank'
                    })
                
                if 'petal' in description.lower():
                    traits.append({
                        'category': 'petal_morphology',
                        'description': description,
                        'source': 'EOL TraitBank'
                    })
                
                if 'color' in description.lower():
                    traits.append({
                        'category': 'flower_color',
                        'description': description,
                        'source': 'EOL TraitBank'
                    })
        
        return traits

# Sample trait data for the 25 Orchid-Gami species
ORCHIDGAMI_TRAIT_DATA = {
    'Dendrophylax lindenii': {  # Ghost Orchid
        'traits': [
            {
                'category': 'spur_length',
                'values': ['very_long'],
                'description': 'Extremely long spur (12-15cm) adapted for giant sphinx moth',
                'pollinator': 'Giant sphinx moth (Cocytius antaeus)',
                'significance': 'Classic example of coevolution - only giant sphinx moth has tongue long enough'
            },
            {
                'category': 'flower_color',
                'values': ['white', 'pale_green'],
                'description': 'White/pale green petals visible at night',
                'pollinator': 'Nocturnal moths',
                'significance': 'Night-blooming adaptation for moth pollination'
            }
        ]
    },
    'Cypripedium acaule': {  # Pink Lady's Slipper
        'traits': [
            {
                'category': 'labellum_shape',
                'values': ['pouch', 'inflated'],
                'description': 'Deep inflated pouch traps bees temporarily',
                'pollinator': 'Bumblebees',
                'significance': 'Trap-pollination mechanism - bee must exit through specific path'
            },
            {
                'category': 'flower_color',
                'values': ['pink', 'magenta'],
                'description': 'Pink to magenta pouch with darker veining',
                'pollinator': 'Bees (attracted to pink UV patterns)',
                'significance': 'Nectar guides lead pollinators to exit route'
            }
        ]
    },
    'Platanthera ciliaris': {  # Orange Fringed Orchid
        'traits': [
            {
                'category': 'labellum_shape',
                'values': ['fringed', 'deeply_lobed'],
                'description': 'Deeply fringed labellum provides landing platform',
                'pollinator': 'Butterflies',
                'significance': 'Fringe increases visual target size for butterflies'
            },
            {
                'category': 'spur_length',
                'values': ['long'],
                'description': 'Long curved spur (2-3cm)',
                'pollinator': 'Long-tongued butterflies',
                'significance': 'Spur length matches butterfly proboscis length'
            },
            {
                'category': 'flower_color',
                'values': ['orange', 'flame_orange'],
                'description': 'Brilliant orange - rare color in orchids',
                'pollinator': 'Butterflies (attracted to orange)',
                'significance': 'Orange color highly visible to butterfly vision'
            }
        ]
    }
}

eol_client = EOLTraitBankClient()
