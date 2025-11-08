#!/usr/bin/env python3
"""
Test enrichment on a single orchid to verify GBIF and EOL integration
"""
import sys
sys.path.insert(0, '.')

from app import app, db
from models import OrchidRecord
from batch_gbif_eol_enrichment import BatchOrchidEnrichment
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_enrichment():
    """Test enrichment on a sample orchid (hybrids are OK - natural hybrids are important!)"""
    with app.app_context():
        # Test with a known real species: Cattleya aurea (ID 6176)
        orchid = db.session.query(OrchidRecord).filter_by(id=6176).first()
        
        # Fallback: find any orchid with genus and species
        if not orchid:
            orchid = db.session.query(OrchidRecord).filter(
                OrchidRecord.genus.isnot(None),
                OrchidRecord.species.isnot(None)
            ).first()
        
        if not orchid:
            logger.error("No orchid found with genus and species")
            return
        
        logger.info(f"\n{'='*80}")
        logger.info(f"Testing enrichment on: {orchid.genus} {orchid.species} (ID: {orchid.id})")
        logger.info(f"{'='*80}\n")
        
        # Create enrichment system (no AI vision for this test)
        enrichment = BatchOrchidEnrichment(enable_ai_vision=False)
        
        # Record before state
        logger.info("BEFORE ENRICHMENT:")
        logger.info(f"  eol_page_id: {orchid.eol_page_id}")
        logger.info(f"  latitude: {orchid.latitude if hasattr(orchid, 'latitude') else 'N/A'}")
        logger.info(f"  longitude: {orchid.longitude if hasattr(orchid, 'longitude') else 'N/A'}")
        
        # Run enrichment
        success = enrichment.enrich_orchid(orchid)
        
        if success:
            logger.info("\n" + "="*80)
            logger.info("AFTER ENRICHMENT:")
            logger.info(f"  eol_page_id: {orchid.eol_page_id}")
            logger.info(f"  latitude: {getattr(orchid, 'latitude', 'N/A')}")
            logger.info(f"  longitude: {getattr(orchid, 'longitude', 'N/A')}")
            logger.info(f"  elevation_m: {getattr(orchid, 'elevation_m', 'N/A')}")
            logger.info(f"  eol_descriptions: {getattr(orchid, 'eol_descriptions', 'N/A')}")
            logger.info(f"  gbif_last_synced_at: {getattr(orchid, 'gbif_last_synced_at', 'N/A')}")
            logger.info(f"  eol_last_synced_at: {getattr(orchid, 'eol_last_synced_at', 'N/A')}")
            logger.info(f"  gbif_occurrence_key: {getattr(orchid, 'gbif_occurrence_key', 'N/A')}")
            logger.info(f"  institution_code: {getattr(orchid, 'institution_code', 'N/A')}")
            logger.info(f"  catalog_number: {getattr(orchid, 'catalog_number', 'N/A')}")
            logger.info("="*80)
            logger.info("\n✅ ENRICHMENT TEST SUCCESSFUL!")
        else:
            logger.error("\n❌ ENRICHMENT TEST FAILED!")
        
        return success

if __name__ == '__main__':
    test_enrichment()
