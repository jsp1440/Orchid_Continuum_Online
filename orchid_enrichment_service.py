#!/usr/bin/env python3
"""
🤖 AI-Powered Orchid Enrichment Service
Validates orchid names and enriches records with EOL and GBIF data before display
"""

import logging
import json
import tempfile
import requests
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from models import OrchidRecord, db
from eol_integration import EOLIntegrator
from external_databases.gbif_integration import GBIFIntegrator
from rhs_integration import RHSOrchidDatabase, get_rhs_orchid_data, analyze_hybrid_parentage
from powo_integration import POWOIntegrator
from orchid_ai import analyze_orchid_image, extract_exif_metadata

logger = logging.getLogger(__name__)

class OrchidEnrichmentService:
    """
    Comprehensive orchid enrichment service that:
    1. Validates orchid names using AI (if image available)
    2. Fetches metadata from Encyclopedia of Life (EOL)
    3. Fetches biodiversity data from GBIF
    4. Caches results to avoid repeated API calls
    5. Presents enriched information for gallery display
    """
    
    def __init__(self):
        self.eol = EOLIntegrator()
        self.gbif = GBIFIntegrator()
        self.rhs = RHSOrchidDatabase()
        self.powo = POWOIntegrator()
        self.cache_duration_days = 30  # Cache enrichment for 30 days
        
    def should_enrich(self, orchid: OrchidRecord) -> bool:
        """Determine if orchid needs enrichment"""
        # Always enrich if never enriched before
        if not orchid.eol_page_id and not orchid.gbif_key:
            return True
        
        # Re-enrich if data is old
        if orchid.updated_at:
            age_days = (datetime.now() - orchid.updated_at).days
            if age_days > self.cache_duration_days:
                return True
        
        # Re-enrich if name was recently changed
        if orchid.species in ['species', 'hybrid', 'sp.', None]:
            return True
            
        return False
    
    def extract_image_metadata(self, orchid: OrchidRecord) -> Optional[Dict]:
        """
        Extract comprehensive metadata from image using EXIF and AI
        
        Returns:
            Dictionary with all extracted metadata
        """
        try:
            # Get image URL
            image_url = None
            if orchid.google_drive_id:
                image_url = f'https://lh3.googleusercontent.com/d/{orchid.google_drive_id}'
            elif orchid.image_url:
                image_url = orchid.image_url
            
            if not image_url:
                logger.debug(f"No image available for orchid {orchid.id}")
                return None
            
            # Download image to temp file for EXIF extraction
            logger.info(f"📸 Extracting metadata from image for orchid {orchid.id}")
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                response = requests.get(image_url, timeout=30)
                response.raise_for_status()
                tmp_file.write(response.content)
                tmp_path = tmp_file.name
            
            # Extract EXIF metadata (date, GPS, camera info)
            exif_data = extract_exif_metadata(tmp_path)
            
            # Use AI to analyze image (identification + visual metadata)
            ai_result = analyze_orchid_image(tmp_path)
            
            # Clean up temp file
            import os
            os.unlink(tmp_path)
            
            # Combine EXIF and AI metadata
            metadata = {
                'extraction_timestamp': datetime.now().isoformat(),
                'has_exif': bool(exif_data),
                'has_ai_analysis': bool(ai_result)
            }
            
            # EXIF metadata
            if exif_data:
                metadata['exif'] = {
                    'photo_date': exif_data.get('photo_date').isoformat() if exif_data.get('photo_date') else None,
                    'photo_datetime': exif_data.get('photo_datetime').isoformat() if exif_data.get('photo_datetime') else None,
                    'gps_latitude': exif_data.get('gps_latitude'),
                    'gps_longitude': exif_data.get('gps_longitude'),
                    'gps_altitude': exif_data.get('gps_altitude'),
                    'camera_make': exif_data.get('camera_make'),
                    'camera_model': exif_data.get('camera_model'),
                    'software': exif_data.get('software')
                }
            
            # AI analysis metadata
            if ai_result:
                metadata['ai'] = {
                    'genus': ai_result.get('genus'),
                    'species': ai_result.get('species'),
                    'scientific_name': ai_result.get('scientific_name'),
                    'suggested_name': ai_result.get('suggested_name'),
                    'description': ai_result.get('description'),
                    'confidence': ai_result.get('confidence'),
                    'is_flowering': ai_result.get('is_flowering'),
                    'flower_color': ai_result.get('flower_color'),
                    'estimated_season': ai_result.get('estimated_season'),
                    'habitat_type': ai_result.get('habitat_type'),
                    'cultivation_type': ai_result.get('cultivation_type')
                }
                
                # AI-derived GPS from visual analysis if EXIF doesn't have it
                if ai_result.get('photo_gps_coordinates') and not exif_data.get('gps_latitude'):
                    metadata['ai_gps'] = ai_result['photo_gps_coordinates']
            
            logger.info(f"✅ Metadata extracted for orchid {orchid.id}")
            return metadata
            
        except Exception as e:
            logger.error(f"Metadata extraction error for orchid {orchid.id}: {e}")
            return None
    
    def validate_name_with_ai(self, orchid: OrchidRecord) -> Tuple[bool, Optional[Dict]]:
        """
        Use AI to validate/identify orchid from image
        
        Returns:
            (needs_update, ai_data) tuple
        """
        try:
            # Get image URL
            image_url = None
            if orchid.google_drive_id:
                image_url = f'https://lh3.googleusercontent.com/d/{orchid.google_drive_id}'
            elif orchid.image_url:
                image_url = orchid.image_url
            
            if not image_url:
                logger.debug(f"No image available for orchid {orchid.id}")
                return False, None
            
            # Skip if already has good data
            if (orchid.genus and orchid.species and 
                orchid.species not in ['species', 'hybrid', 'sp.']):
                logger.debug(f"Orchid {orchid.id} already has good name data")
                return False, None
            
            # Use AI to analyze
            logger.info(f"🤖 AI validating name for orchid {orchid.id}")
            ai_result = analyze_orchid_image(image_url)
            
            if ai_result and ai_result.get('genus'):
                logger.info(f"✅ AI identified: {ai_result.get('genus')} {ai_result.get('species')}")
                return True, ai_result
            
            return False, None
            
        except Exception as e:
            logger.error(f"AI validation error for orchid {orchid.id}: {e}")
            return False, None
    
    def enrich_with_eol(self, orchid: OrchidRecord) -> bool:
        """Enrich orchid with EOL data"""
        try:
            if not orchid.scientific_name or not orchid.scientific_name.strip():
                logger.debug(f"No scientific name for orchid {orchid.id}, skipping EOL")
                return False
            
            logger.info(f"🌿 Enriching orchid {orchid.id} with EOL data")
            
            # Search EOL
            search_result = self.eol.search_eol_species(orchid.scientific_name)
            if not search_result:
                logger.debug(f"No EOL results for {orchid.scientific_name}")
                return False
            
            # Get detailed page data
            page_id = search_result.get('id')
            page_data = self.eol.get_eol_page_data(page_id)
            if not page_data:
                return False
            
            # Extract and update
            traits = self.eol.extract_trait_data(page_data)
            
            # Update orchid record
            orchid.eol_page_id = traits.get('eol_page_id')
            
            # Add EOL citation metadata
            current_traits = json.loads(orchid.eol_traits) if orchid.eol_traits else {}
            current_traits.update(traits)
            current_traits['eol_citation'] = {
                'source': 'Encyclopedia of Life (EOL)',
                'url': f"https://eol.org/pages/{page_id}",
                'accessed_date': datetime.now().isoformat(),
                'citation': f"Encyclopedia of Life. {orchid.scientific_name}. Retrieved {datetime.now().strftime('%B %d, %Y')}, from https://eol.org/pages/{page_id}"
            }
            orchid.eol_traits = json.dumps(current_traits)
            
            # Add common names if missing
            if not orchid.common_names and traits.get('common_names'):
                common_names_list = [cn['name'] for cn in traits['common_names'][:3]]
                orchid.common_names = ', '.join(common_names_list)
            
            # Enhance description
            if traits.get('descriptions') and len(traits['descriptions']) > 0:
                eol_desc = traits['descriptions'][0]['description']
                if eol_desc and len(eol_desc) > 50:
                    current_traits['eol_description'] = eol_desc[:800]
                    orchid.eol_traits = json.dumps(current_traits)
            
            logger.info(f"✅ EOL enrichment successful for {orchid.scientific_name}")
            return True
            
        except Exception as e:
            logger.error(f"EOL enrichment error for orchid {orchid.id}: {e}")
            return False
    
    def enrich_with_gbif(self, orchid: OrchidRecord) -> bool:
        """Enrich orchid with GBIF data"""
        try:
            if not orchid.scientific_name or not orchid.scientific_name.strip():
                logger.debug(f"No scientific name for orchid {orchid.id}, skipping GBIF")
                return False
            
            logger.info(f"🌍 Enriching orchid {orchid.id} with GBIF data")
            
            # Search GBIF
            search_result = self.gbif.search_species(orchid.scientific_name, limit=1)
            if not search_result or not search_result.get('results'):
                logger.debug(f"No GBIF results for {orchid.scientific_name}")
                return False
            
            # Get first result
            species_data = search_result['results'][0]
            species_key = species_data.get('key')
            
            if not species_key:
                return False
            
            # Get detailed taxonomy
            taxonomy = self.gbif.get_taxonomy(str(species_key))
            if taxonomy:
                orchid.gbif_key = str(species_key)
                orchid.gbif_taxonomy = json.dumps(taxonomy)
                
                # Add author if missing
                if not orchid.author and taxonomy.get('author'):
                    orchid.author = taxonomy['author']
            
            # Get conservation status (occurrence-based)
            conservation = self.gbif.get_conservation_status(str(species_key))
            if conservation:
                current_traits = json.loads(orchid.eol_traits) if orchid.eol_traits else {}
                current_traits['gbif_conservation'] = conservation
                orchid.eol_traits = json.dumps(current_traits)
            
            # Get occurrence data with locations
            occurrences = self.gbif.get_occurrences(
                scientific_name=orchid.scientific_name,
                limit=10,
                with_images=True
            )
            
            if occurrences:
                current_traits = json.loads(orchid.eol_traits) if orchid.eol_traits else {}
                current_traits['gbif_occurrences'] = {
                    'count': occurrences.get('count', 0),
                    'sample_locations': []
                }
                
                # Store sample locations
                for occ in occurrences.get('results', [])[:5]:
                    loc = occ.get('location', {})
                    if loc.get('country'):
                        current_traits['gbif_occurrences']['sample_locations'].append({
                            'country': loc.get('country'),
                            'locality': loc.get('locality'),
                            'latitude': loc.get('latitude'),
                            'longitude': loc.get('longitude')
                        })
                
                orchid.eol_traits = json.dumps(current_traits)
            
            logger.info(f"✅ GBIF enrichment successful for {orchid.scientific_name}")
            return True
            
        except Exception as e:
            logger.error(f"GBIF enrichment error for orchid {orchid.id}: {e}")
            return False
    
    def enrich_with_powo(self, orchid: OrchidRecord) -> bool:
        """Enrich orchid with POWO (Kew Gardens) authoritative taxonomy"""
        try:
            if not orchid.scientific_name or not orchid.scientific_name.strip():
                logger.debug(f"No scientific name for orchid {orchid.id}, skipping POWO")
                return False
            
            logger.info(f"🌿 Enriching orchid {orchid.id} with POWO data")
            
            # Get accepted name and taxonomy from Kew
            powo_data = self.powo.get_accepted_name(orchid.scientific_name)
            
            if powo_data:
                current_traits = json.loads(orchid.eol_traits) if orchid.eol_traits else {}
                current_traits['powo_data'] = {
                    'accepted_name': powo_data.get('accepted_name'),
                    'author': powo_data.get('author'),
                    'synonyms': powo_data.get('synonyms', []),
                    'powo_id': powo_data.get('powo_id'),
                    'family': powo_data.get('family'),
                    'conservation_status': powo_data.get('conservation_status')
                }
                
                # Add distribution data
                if powo_data.get('distribution'):
                    current_traits['powo_data']['distribution'] = powo_data['distribution']
                
                orchid.eol_traits = json.dumps(current_traits)
                
                # Update author if missing and POWO has it
                if not orchid.author and powo_data.get('author'):
                    orchid.author = powo_data['author']
                
                # Use POWO accepted name if different (authoritative source)
                if powo_data.get('accepted_name') and powo_data['accepted_name'] != orchid.scientific_name:
                    logger.info(f"POWO suggests accepted name: {powo_data['accepted_name']} vs {orchid.scientific_name}")
                    # Store as alternative, don't overwrite (respect user's data)
                
                logger.info(f"✅ POWO enrichment successful for {orchid.scientific_name}")
                return True
            
            logger.debug(f"No POWO data found for {orchid.scientific_name}")
            return False
            
        except Exception as e:
            logger.error(f"POWO enrichment error for orchid {orchid.id}: {e}")
            return False
    def full_enrichment(self, orchid: OrchidRecord, force_ai: bool = False, extract_metadata: bool = True) -> Dict[str, bool]:
        """
        Perform complete enrichment: Image metadata + AI validation + EOL + GBIF
        
        Args:
            orchid: OrchidRecord to enrich
            force_ai: Force AI name validation even if name exists
            extract_metadata: Extract EXIF and AI metadata from image
            
        Returns:
            Dictionary with enrichment results
        """
        results = {
            'metadata_extracted': False,
            'ai_validated': False,
            'ai_updated_name': False,
            'eol_enriched': False,
            'gbif_enriched': False,
            'powo_enriched': False,
            'rhs_enriched': False,
            'errors': []
        }
        
        try:
            # Step 0: Extract Image Metadata (EXIF + AI visual analysis)
            if extract_metadata:
                image_metadata = self.extract_image_metadata(orchid)
                if image_metadata:
                    # Store metadata in eol_traits JSON field
                    current_traits = json.loads(orchid.eol_traits) if orchid.eol_traits else {}
                    current_traits['image_metadata'] = image_metadata
                    orchid.eol_traits = json.dumps(current_traits)
                    
                    # Update database fields from EXIF
                    if image_metadata.get('exif'):
                        exif = image_metadata['exif']
                        if exif.get('photo_date') and not orchid.collection_date:
                            orchid.collection_date = datetime.fromisoformat(exif['photo_date']).date()
                        if exif.get('gps_latitude') and not orchid.latitude:
                            orchid.latitude = exif['gps_latitude']
                            orchid.longitude = exif['gps_longitude']
                    
                    # Update from AI if EXIF missing
                    if image_metadata.get('ai'):
                        ai = image_metadata['ai']
                        # Use AI identification if name is poor quality
                        if (orchid.species in ['species', 'hybrid', 'sp.', None]) and ai.get('genus'):
                            orchid.genus = ai['genus']
                            orchid.species = ai.get('species', 'sp.')
                            orchid.scientific_name = ai.get('scientific_name', f"{ai['genus']} sp.")
                            results['ai_updated_name'] = True
                    
                    results['metadata_extracted'] = True
                    logger.info(f"📸 Image metadata extracted for orchid {orchid.id}")
            
            # Step 1: AI Name Validation (if needed or forced)
            if force_ai or orchid.species in ['species', 'hybrid', 'sp.', None]:
                needs_update, ai_data = self.validate_name_with_ai(orchid)
                results['ai_validated'] = True
                
                if needs_update and ai_data:
                    # Update orchid with AI identification
                    if ai_data.get('genus'):
                        orchid.genus = ai_data['genus']
                    if ai_data.get('species'):
                        orchid.species = ai_data['species']
                    if ai_data.get('scientific_name'):
                        orchid.scientific_name = ai_data['scientific_name']
                    if ai_data.get('display_name'):
                        orchid.display_name = ai_data['display_name']
                    
                    results['ai_updated_name'] = True
                    logger.info(f"🤖 AI updated name for orchid {orchid.id}")
            
            # Step 2: EOL Enrichment
            if orchid.scientific_name and orchid.scientific_name.strip():
                eol_success = self.enrich_with_eol(orchid)
                results['eol_enriched'] = eol_success
            
            # Step 3: GBIF Enrichment
            if orchid.scientific_name and orchid.scientific_name.strip():
                gbif_success = self.enrich_with_gbif(orchid)
                results['gbif_enriched'] = gbif_success
            
            # Step 4: POWO Enrichment (Kew Gardens authoritative taxonomy)
            if orchid.scientific_name and orchid.scientific_name.strip():
                powo_success = self.enrich_with_powo(orchid)
                results['powo_enriched'] = powo_success
            
            # Step 5: RHS Enrichment (Hybrid parentage or species info)
            if orchid.scientific_name and orchid.scientific_name.strip():
                rhs_success = self.enrich_with_rhs(orchid)
                results['rhs_enriched'] = rhs_success
            
            # Update timestamp
            orchid.updated_at = datetime.now()
            
            # Commit all changes
            db.session.commit()
            
            logger.info(f"✅ Full enrichment completed for orchid {orchid.id}: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Full enrichment failed for orchid {orchid.id}: {e}")
            results['errors'].append(str(e))
            db.session.rollback()
            return results
    
    def get_enriched_metadata(self, orchid: OrchidRecord) -> Dict:
        """
        Get enriched metadata for display in gallery
        
        Returns formatted metadata dictionary
        """
        metadata = {
            'has_enrichment': False,
            'eol_description': None,
            'common_names': None,
            'conservation_status': None,
            'occurrence_count': None,
            'sample_locations': [],
            'powo_accepted_name': None,
            'powo_synonyms': [],
            'powo_distribution': None,
            'rhs_parentage': None,
            'rhs_species_info': None,
            'author': orchid.author
        }
        
        try:
            # Parse stored traits
            if orchid.eol_traits:
                traits = json.loads(orchid.eol_traits)
                metadata['has_enrichment'] = True
                
                # EOL description
                if traits.get('eol_description'):
                    metadata['eol_description'] = traits['eol_description']
                
                # Common names
                if traits.get('common_names'):
                    names = [cn['name'] for cn in traits['common_names'][:2]]
                    metadata['common_names'] = ', '.join(names)
                
                # GBIF conservation
                if traits.get('gbif_conservation'):
                    metadata['conservation_status'] = traits['gbif_conservation'].get('status_indicator')
                    metadata['occurrence_count'] = traits['gbif_conservation'].get('occurrence_count')
                
                # GBIF locations
                if traits.get('gbif_occurrences'):
                    metadata['sample_locations'] = traits['gbif_occurrences'].get('sample_locations', [])
                
                # POWO data (Kew Gardens authoritative taxonomy)
                if traits.get('powo_data'):
                    powo = traits['powo_data']
                    if powo.get('accepted_name'):
                        metadata['powo_accepted_name'] = powo['accepted_name']
                    if powo.get('synonyms'):
                        metadata['powo_synonyms'] = powo['synonyms']
                    if powo.get('distribution'):
                        metadata['powo_distribution'] = powo['distribution']
                
                # RHS data (hybrid parentage or species info)
                if traits.get('rhs_data'):
                    rhs = traits['rhs_data']
                    if rhs.get('type') == 'hybrid' and rhs.get('parentage'):
                        metadata['rhs_parentage'] = rhs['parentage']
                    elif rhs.get('type') == 'species' and rhs.get('species_info'):
                        metadata['rhs_species_info'] = rhs['species_info']
            
            # Fallback to common_names field
            if not metadata['common_names'] and orchid.common_names:
                metadata['common_names'] = orchid.common_names
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error getting enriched metadata for orchid {orchid.id}: {e}")
            return metadata


# Global instance
enrichment_service = OrchidEnrichmentService()


logger.info("🤖 Orchid Enrichment Service initialized with EOL, GBIF, POWO, and RHS integrations")
