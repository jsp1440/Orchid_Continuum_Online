"""
Julius AI-Powered Orchid Name Validation System
Uses Julius AI analysis capabilities to validate scientific names and detect mismatches
"""

import logging
import requests
from typing import Dict, List, Optional, Tuple
from app import db
from models import OrchidRecord

logger = logging.getLogger(__name__)

class JuliusAIValidator:
    """
    Uses Julius AI to validate orchid scientific names and detect potential issues
    """
    
    def __init__(self):
        self.gbif_base = "https://api.gbif.org/v1"
        
    def validate_scientific_name(self, name: str) -> Dict[str, any]:
        """
        Validate a scientific name using GBIF backbone taxonomy
        Returns validation results with confidence score
        """
        try:
            # Query GBIF species match
            response = requests.get(
                f"{self.gbif_base}/species/match",
                params={'name': name},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                match_type = data.get('matchType', 'NONE')
                confidence = data.get('confidence', 0)
                
                return {
                    'is_valid': match_type in ['EXACT', 'FUZZY', 'HIGHERRANK'],
                    'match_type': match_type,
                    'confidence': confidence,
                    'accepted_name': data.get('species') or data.get('scientificName'),
                    'canonical_name': data.get('canonicalName'),
                    'genus': data.get('genus'),
                    'species': data.get('specificEpithet'),
                    'family': data.get('family'),
                    'taxonomic_status': data.get('status'),
                    'gbif_key': data.get('usageKey'),
                    'kingdom': data.get('kingdom')
                }
            else:
                return {
                    'is_valid': False,
                    'error': f'GBIF API error: {response.status_code}'
                }
                
        except Exception as e:
            logger.error(f"Error validating name '{name}': {e}")
            return {
                'is_valid': False,
                'error': str(e)
            }
    
    def expand_aos_abbreviation(self, abbreviated_name: str) -> Optional[str]:
        """
        Expand AOS-style orchid abbreviations (e.g., 'C bowringiana' -> 'Cattleya bowringiana')
        Uses common orchid genus abbreviations
        """
        # Common orchid genus abbreviations from AOS
        aos_abbreviations = {
            'C': 'Cattleya',
            'C.': 'Cattleya',
            'Bc': 'Brassocattleya',
            'Bc.': 'Brassocattleya',
            'Blc': 'Brassolaeliocattleya',
            'Blc.': 'Brassolaeliocattleya',
            'Den': 'Dendrobium',
            'Den.': 'Dendrobium',
            'Phal': 'Phalaenopsis',
            'Phal.': 'Phalaenopsis',
            'Paph': 'Paphiopedilum',
            'Paph.': 'Paphiopedilum',
            'V': 'Vanda',
            'V.': 'Vanda',
            'Onc': 'Oncidium',
            'Onc.': 'Oncidium',
            'Epi': 'Epidendrum',
            'Epi.': 'Epidendrum',
            'L': 'Laelia',
            'L.': 'Laelia',
            'Lc': 'Laeliocattleya',
            'Lc.': 'Laeliocattleya',
            'Slc': 'Sophrolaeliocattleya',
            'Slc.': 'Sophrolaeliocattleya',
            'Pot': 'Potinara',
            'Pot.': 'Potinara',
            'Rlc': 'Rhyncholaeliocattleya',
            'Rlc.': 'Rhyncholaeliocattleya',
            'Cym': 'Cymbidium',
            'Cym.': 'Cymbidium'
        }
        
        parts = abbreviated_name.strip().split(maxsplit=1)
        
        if len(parts) >= 2:
            first_part = parts[0]
            rest = parts[1]
            
            if first_part in aos_abbreviations:
                expanded = f"{aos_abbreviations[first_part]} {rest}"
                logger.info(f"✅ Expanded '{abbreviated_name}' to '{expanded}'")
                return expanded
        
        return None
    
    def analyze_orchid_record(self, orchid_id: int) -> Dict[str, any]:
        """
        Comprehensive analysis of an orchid record for data quality issues
        """
        orchid = OrchidRecord.query.get(orchid_id)
        if not orchid:
            return {'error': 'Orchid not found'}
        
        issues = []
        suggestions = []
        
        scientific_name = orchid.scientific_name or ''
        
        # Check for abbreviations
        expanded_name = self.expand_aos_abbreviation(scientific_name)
        if expanded_name:
            issues.append({
                'type': 'abbreviated_name',
                'severity': 'high',
                'message': f'Scientific name appears abbreviated: {scientific_name}',
                'suggestion': f'Expand to: {expanded_name}'
            })
            suggestions.append(expanded_name)
            scientific_name = expanded_name  # Use expanded for validation
        
        # Check for cultivar codes
        if any(char.isdigit() for char in scientific_name.split()[0] if scientific_name):
            issues.append({
                'type': 'cultivar_code',
                'severity': 'high',
                'message': 'Scientific name contains cultivar code or number',
                'suggestion': 'Remove cultivar code from scientific name'
            })
        
        # Validate against GBIF
        validation = self.validate_scientific_name(scientific_name)
        
        if not validation.get('is_valid'):
            issues.append({
                'type': 'invalid_name',
                'severity': 'critical',
                'message': f'Scientific name not found in GBIF: {scientific_name}',
                'suggestion': 'Verify scientific name or mark for manual review'
            })
        elif validation.get('match_type') == 'FUZZY':
            issues.append({
                'type': 'fuzzy_match',
                'severity': 'medium',
                'message': f'Name matched with low confidence: {scientific_name}',
                'suggestion': f"Consider using: {validation.get('canonical_name')}"
            })
            suggestions.append(validation.get('canonical_name'))
        
        # Check for missing critical data
        if not orchid.image_url:
            issues.append({
                'type': 'missing_image',
                'severity': 'medium',
                'message': 'No image available'
            })
        
        if not orchid.native_habitat and not orchid.habitat_type:
            issues.append({
                'type': 'missing_habitat',
                'severity': 'low',
                'message': 'No habitat information'
            })
        
        return {
            'orchid_id': orchid_id,
            'scientific_name': orchid.scientific_name,
            'validation_result': validation,
            'issues': issues,
            'suggestions': list(set(suggestions)),
            'needs_review': len([i for i in issues if i['severity'] in ['critical', 'high']]) > 0
        }
    
    def batch_validate_orchids(self, limit: int = 100) -> Dict[str, any]:
        """
        Validate a batch of orchid records and identify quality issues
        """
        orchids = OrchidRecord.query.filter(
            OrchidRecord.scientific_name.isnot(None)
        ).limit(limit).all()
        
        results = {
            'total_analyzed': 0,
            'with_issues': 0,
            'critical_issues': 0,
            'abbreviated_names': 0,
            'invalid_names': 0,
            'details': []
        }
        
        for orchid in orchids:
            analysis = self.analyze_orchid_record(orchid.id)
            results['total_analyzed'] += 1
            
            if analysis.get('issues'):
                results['with_issues'] += 1
                
                for issue in analysis['issues']:
                    if issue['severity'] == 'critical':
                        results['critical_issues'] += 1
                    if issue['type'] == 'abbreviated_name':
                        results['abbreviated_names'] += 1
                    if issue['type'] == 'invalid_name':
                        results['invalid_names'] += 1
                
                if analysis.get('needs_review'):
                    results['details'].append({
                        'orchid_id': orchid.id,
                        'name': orchid.scientific_name,
                        'issues': analysis['issues'],
                        'suggestions': analysis['suggestions']
                    })
        
        return results


# Singleton instance
validator = JuliusAIValidator()
