"""
POWO (Plants of the World Online) Integration
Kew Gardens' authoritative plant taxonomy database

Provides:
- Accepted scientific names
- Synonyms and taxonomic authorities
- Geographic distribution (native/introduced)
- Conservation status (IUCN)
- Botanical descriptions
"""

import logging
import requests
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class POWOIntegrator:
    """Interface to Plants of the World Online (Kew Gardens) API"""
    
    def __init__(self):
        self.base_url = "https://powo.science.kew.org/api/1"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Orchid-Continuum/1.0 (Educational Research)',
            'Accept': 'application/json'
        })
        
        # Cache for taxonomy lookups
        self._species_cache = {}
        self._search_cache = {}
    
    def search_orchid(self, name: str, limit: int = 10) -> List[Dict]:
        """
        Search POWO for orchid species
        
        Args:
            name: Scientific name or partial name
            limit: Maximum results to return
            
        Returns:
            List of matching taxa
        """
        cache_key = f"{name}_{limit}"
        if cache_key in self._search_cache:
            logger.debug(f"Cache hit for POWO search: {name}")
            return self._search_cache[cache_key]
        
        try:
            # Search within Orchidaceae family
            search_url = f"{self.base_url}/search"
            
            params = {
                'q': f"{name} family:Orchidaceae",
                'filters': 'accepted,species',
                'limit': limit
            }
            
            response = self.session.get(search_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                results = self._parse_search_results(data)
                self._search_cache[cache_key] = results
                logger.info(f"✅ POWO search for '{name}' returned {len(results)} results")
                return results
            else:
                logger.warning(f"POWO search failed with status {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"POWO search error for '{name}': {e}")
            return []
    
    def get_taxon_details(self, powo_id: str) -> Optional[Dict]:
        """
        Get detailed taxonomic information by POWO ID
        
        Args:
            powo_id: POWO taxon identifier
            
        Returns:
            Dictionary with detailed taxon information
        """
        if powo_id in self._species_cache:
            return self._species_cache[powo_id]
        
        try:
            lookup_url = f"{self.base_url}/taxon/urn:lsid:ipni.org:names:{powo_id}"
            
            response = self.session.get(lookup_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                details = self._parse_taxon_details(data)
                self._species_cache[powo_id] = details
                logger.info(f"✅ Retrieved POWO details for ID {powo_id}")
                return details
            else:
                logger.warning(f"POWO lookup failed for ID {powo_id}: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"POWO lookup error for ID {powo_id}: {e}")
            return None
    
    def get_accepted_name(self, scientific_name: str) -> Optional[Dict]:
        """
        Get accepted name and synonyms for an orchid
        
        Args:
            scientific_name: Scientific name to validate
            
        Returns:
            Dictionary with accepted name, synonyms, and authority
        """
        try:
            search_results = self.search_orchid(scientific_name, limit=5)
            
            if not search_results:
                logger.debug(f"No POWO results for '{scientific_name}'")
                return None
            
            # Find exact or best match
            best_match = None
            for result in search_results:
                if result.get('name', '').lower() == scientific_name.lower():
                    best_match = result
                    break
            
            if not best_match:
                best_match = search_results[0]  # Use first result
            
            # Get detailed information
            if best_match.get('fqId'):
                details = self.get_taxon_details(best_match['fqId'])
                if details:
                    return {
                        'accepted_name': details.get('name'),
                        'author': details.get('author'),
                        'synonyms': details.get('synonyms', []),
                        'distribution': details.get('distribution', {}),
                        'conservation_status': details.get('conservation_status'),
                        'powo_id': best_match.get('fqId'),
                        'family': details.get('family'),
                        'genus': details.get('genus')
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting accepted name for '{scientific_name}': {e}")
            return None
    
    def get_distribution(self, scientific_name: str) -> Optional[Dict]:
        """
        Get geographic distribution for an orchid species
        
        Args:
            scientific_name: Scientific name
            
        Returns:
            Dictionary with native and introduced ranges
        """
        try:
            accepted = self.get_accepted_name(scientific_name)
            
            if accepted and accepted.get('distribution'):
                distribution = accepted['distribution']
                
                return {
                    'native': distribution.get('native', []),
                    'introduced': distribution.get('introduced', []),
                    'extinct': distribution.get('extinct', []),
                    'tdwg_codes': distribution.get('tdwg_codes', [])
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting distribution for '{scientific_name}': {e}")
            return None
    
    def _parse_search_results(self, data: Dict) -> List[Dict]:
        """Parse POWO search results"""
        results = []
        
        for item in data.get('results', []):
            results.append({
                'fqId': item.get('fqId'),
                'name': item.get('name'),
                'author': item.get('author'),
                'rank': item.get('rank'),
                'family': item.get('family'),
                'genus': item.get('genus'),
                'species': item.get('species')
            })
        
        return results
    
    def _parse_taxon_details(self, data: Dict) -> Dict:
        """Parse detailed taxon information"""
        details = {
            'name': data.get('name'),
            'author': data.get('authors'),
            'family': data.get('family'),
            'genus': data.get('genus'),
            'rank': data.get('rank'),
            'taxonomic_status': data.get('taxonomicStatus'),
            'synonyms': [],
            'distribution': {},
            'images': [],
            'descriptions': []
        }
        
        # Parse synonyms
        if data.get('synonyms'):
            details['synonyms'] = [
                f"{syn.get('name')} {syn.get('author', '')}" 
                for syn in data.get('synonyms', [])
            ]
        
        # Parse distribution
        if data.get('distribution'):
            dist_data = data['distribution']
            details['distribution'] = {
                'native': dist_data.get('natives', []),
                'introduced': dist_data.get('introduced', []),
                'extinct': dist_data.get('extinct', []),
                'tdwg_codes': dist_data.get('tdwg', [])
            }
        
        # Parse images
        if data.get('images'):
            details['images'] = [
                {
                    'url': img.get('url'),
                    'caption': img.get('caption'),
                    'copyright': img.get('copyright')
                }
                for img in data.get('images', [])
            ]
        
        # Parse descriptions
        if data.get('descriptions'):
            details['descriptions'] = [
                desc.get('text') for desc in data.get('descriptions', [])
            ]
        
        # Conservation status
        if data.get('conservationStatus'):
            details['conservation_status'] = data['conservationStatus']
        
        return details


# Global instance
powo_integrator = POWOIntegrator()

logger.info("🌿 POWO (Kew Gardens) Integration initialized")
