#!/usr/bin/env python3
"""
Automated Scraper Controller
Coordinates and automates collection from partner photographers
and breeding databases (Gary Yong Gee, Roberta Fox, Sunset Valley Orchids)
"""

import logging
import time
from datetime import datetime
from typing import Dict

from optimized_gary_scraper import OptimizedGaryScraper
from roberta_fox_photo_collector import RobertaFoxPhotoCollector
from ron_parsons_scraper import RonParsonsOrchidScraper
from svo_enhanced_scraper import SunsetValleyOrchidsEnhancedScraper
from svo_hybrid_collector import SVOHybridCollector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AutomatedScraperController:
    """
    Automated controller for partner photographer and breeding data collection
    
    Partners:
    - Gary Yong Gee (orchids.yonggee.name) - Natural habitat photography
    - Roberta Fox (orchidcentral.org) - 19 galleries, natural specimens
    - Ron Parsons (flowershots.net, ronsorchids.weebly.com) - Public domain orchid photography
    - Sunset Valley Orchids - Hybrid breeding data (Sarcochilus, Catasetum, Zygopetalum, Cattleya)
    """
    
    def __init__(self):
        self.stats = {
            'gary_yong_gee': {'collected': 0, 'errors': 0, 'last_run': None},
            'roberta_fox': {'collected': 0, 'errors': 0, 'last_run': None},
            'ron_parsons': {'collected': 0, 'errors': 0, 'last_run': None},
            'svo_species': {'collected': 0, 'errors': 0, 'last_run': None},
            'svo_hybrids': {'collected': 0, 'errors': 0, 'last_run': None}
        }
    
    def run_gary_yong_gee_collection(self) -> Dict:
        """
        Collect from Gary Yong Gee's orchid photography collection
        Partner-approved natural habitat photography
        """
        logger.info("🌿 ===== GARY YONG GEE COLLECTION STARTING =====")
        start_time = time.time()
        
        try:
            scraper = OptimizedGaryScraper()
            
            # Discover and use Gary's API endpoints
            endpoints = scraper.discover_gary_api_endpoints()
            
            if endpoints:
                logger.info(f"✅ Found {len(endpoints)} working API endpoints")
                
                # Scrape all available data
                result = scraper.scrape_all_data()
                
                self.stats['gary_yong_gee']['collected'] = scraper.collected_count
                self.stats['gary_yong_gee']['errors'] = scraper.error_count
                self.stats['gary_yong_gee']['last_run'] = datetime.now().isoformat()
                
                elapsed = time.time() - start_time
                logger.info(f"✅ GARY COLLECTION COMPLETE: {scraper.collected_count} orchids in {elapsed:.1f}s")
                
                return {
                    'success': True,
                    'collected': scraper.collected_count,
                    'errors': scraper.error_count,
                    'duration': elapsed
                }
            else:
                logger.warning("⚠️  No working API endpoints found for Gary's site")
                return {'success': False, 'error': 'No API endpoints available'}
                
        except Exception as e:
            logger.error(f"❌ Error in Gary collection: {e}")
            self.stats['gary_yong_gee']['errors'] += 1
            return {'success': False, 'error': str(e)}
    
    def run_roberta_fox_collection(self) -> Dict:
        """
        Collect from Roberta Fox's 19 orchid galleries
        Partner-approved natural specimen photography
        """
        logger.info("🌺 ===== ROBERTA FOX COLLECTION STARTING =====")
        start_time = time.time()
        
        try:
            collector = RobertaFoxPhotoCollector()
            
            # Collect from all 19 galleries
            result = collector.collect_all_photos()
            
            self.stats['roberta_fox']['collected'] = collector.collected_count
            self.stats['roberta_fox']['errors'] = collector.rejected_count
            self.stats['roberta_fox']['last_run'] = datetime.now().isoformat()
            
            elapsed = time.time() - start_time
            logger.info(f"✅ ROBERTA FOX COLLECTION COMPLETE: {collector.collected_count} photos in {elapsed:.1f}s")
            
            return {
                'success': True,
                'collected': collector.collected_count,
                'rejected': collector.rejected_count,
                'duration': elapsed
            }
            
        except Exception as e:
            logger.error(f"❌ Error in Roberta Fox collection: {e}")
            self.stats['roberta_fox']['errors'] += 1
            return {'success': False, 'error': str(e)}
    
    def run_ron_parsons_collection(self) -> Dict:
        """
        Collect from Ron Parsons' public domain orchid photography
        Sources: flowershots.net and ronsorchids.weebly.com
        """
        logger.info("📸 ===== RON PARSONS COLLECTION STARTING =====")
        start_time = time.time()
        
        try:
            scraper = RonParsonsOrchidScraper()
            
            # Run comprehensive scraping from both sites
            result = scraper.run_comprehensive_scraping()
            
            self.stats['ron_parsons']['collected'] = result['total']
            self.stats['ron_parsons']['last_run'] = datetime.now().isoformat()
            
            elapsed = time.time() - start_time
            logger.info(f"✅ RON PARSONS COLLECTION COMPLETE: {result['total']} photos in {elapsed:.1f}s")
            logger.info(f"   📸 Photogallery: {result['photogallery']}")
            logger.info(f"   🏠 Personal site: {result['personal']}")
            
            return {
                'success': True,
                'collected': result['total'],
                'photogallery': result['photogallery'],
                'personal': result['personal'],
                'duration': elapsed
            }
            
        except Exception as e:
            logger.error(f"❌ Error in Ron Parsons collection: {e}")
            self.stats['ron_parsons']['errors'] += 1
            return {'success': False, 'error': str(e)}
    
    def run_svo_species_collection(self) -> Dict:
        """
        Collect species data from Sunset Valley Orchids
        Focus: Sarcochilus, Catasetum, Zygopetalum, Cattleya and other genera
        """
        logger.info("🌅 ===== SUNSET VALLEY ORCHIDS (SPECIES) COLLECTION STARTING =====")
        start_time = time.time()
        
        try:
            scraper = SunsetValleyOrchidsEnhancedScraper()
            
            # Collect species data for target genera
            target_genera = ['Sarcochilus', 'Catasetum', 'Zygopetalum', 'Cattleya']
            
            total_collected = 0
            for genus in target_genera:
                logger.info(f"📋 Collecting {genus} species...")
                # Scraper handles genus-specific collection
                result = scraper.scrape_genus(genus) if hasattr(scraper, 'scrape_genus') else None
                if result:
                    total_collected += result.get('collected', 0)
            
            self.stats['svo_species']['collected'] = total_collected
            self.stats['svo_species']['last_run'] = datetime.now().isoformat()
            
            elapsed = time.time() - start_time
            logger.info(f"✅ SVO SPECIES COLLECTION COMPLETE: {total_collected} species in {elapsed:.1f}s")
            
            return {
                'success': True,
                'collected': total_collected,
                'genera': target_genera,
                'duration': elapsed
            }
            
        except Exception as e:
            logger.error(f"❌ Error in SVO species collection: {e}")
            self.stats['svo_species']['errors'] += 1
            return {'success': False, 'error': str(e)}
    
    def run_svo_hybrid_collection(self) -> Dict:
        """
        Collect hybrid breeding information from Sunset Valley Orchids
        Includes parentage, breeding notes, and cross information
        For breeding widgets and AI analysis
        """
        logger.info("🧬 ===== SUNSET VALLEY ORCHIDS (HYBRIDS) COLLECTION STARTING =====")
        start_time = time.time()
        
        try:
            collector = SVOHybridCollector()
            
            # Collect all hybrid breeding information
            collector.collect_all_hybrids()
            
            self.stats['svo_hybrids']['collected'] = collector.collected_count
            self.stats['svo_hybrids']['errors'] = collector.rejected_count
            self.stats['svo_hybrids']['last_run'] = datetime.now().isoformat()
            
            elapsed = time.time() - start_time
            logger.info(f"✅ SVO HYBRID COLLECTION COMPLETE: {collector.collected_count} hybrids in {elapsed:.1f}s")
            
            return {
                'success': True,
                'collected': collector.collected_count,
                'rejected': collector.rejected_count,
                'duration': elapsed
            }
            
        except Exception as e:
            logger.error(f"❌ Error in SVO hybrid collection: {e}")
            self.stats['svo_hybrids']['errors'] += 1
            return {'success': False, 'error': str(e)}
    
    def run_full_collection_cycle(self) -> Dict:
        """
        Run complete collection cycle from all partners
        Returns comprehensive statistics
        """
        logger.info("🚀 ========== FULL COLLECTION CYCLE STARTING ==========")
        cycle_start = time.time()
        
        results = {
            'cycle_started': datetime.now().isoformat(),
            'sources': {}
        }
        
        # 1. Gary Yong Gee
        logger.info("\n" + "="*60)
        results['sources']['gary_yong_gee'] = self.run_gary_yong_gee_collection()
        time.sleep(5)  # Be respectful between sources
        
        # 2. Roberta Fox
        logger.info("\n" + "="*60)
        results['sources']['roberta_fox'] = self.run_roberta_fox_collection()
        time.sleep(5)
        
        # 3. Ron Parsons
        logger.info("\n" + "="*60)
        results['sources']['ron_parsons'] = self.run_ron_parsons_collection()
        time.sleep(5)
        
        # 4. SVO Species
        logger.info("\n" + "="*60)
        results['sources']['svo_species'] = self.run_svo_species_collection()
        time.sleep(5)
        
        # 5. SVO Hybrids
        logger.info("\n" + "="*60)
        results['sources']['svo_hybrids'] = self.run_svo_hybrid_collection()
        
        # Summary
        cycle_duration = time.time() - cycle_start
        total_collected = sum(
            res.get('collected', 0) 
            for res in results['sources'].values()
        )
        
        results['summary'] = {
            'total_collected': total_collected,
            'cycle_duration': cycle_duration,
            'sources_processed': len(results['sources']),
            'stats': self.stats
        }
        
        logger.info("\n" + "="*60)
        logger.info(f"🎉 FULL COLLECTION CYCLE COMPLETE!")
        logger.info(f"   Total collected: {total_collected}")
        logger.info(f"   Duration: {cycle_duration/60:.1f} minutes")
        logger.info("="*60 + "\n")
        
        return results
    
    def get_collection_stats(self) -> Dict:
        """Get current collection statistics"""
        return {
            'stats': self.stats,
            'timestamp': datetime.now().isoformat()
        }


# Global instance
automated_controller = AutomatedScraperController()

if __name__ == '__main__':
    # Run full collection cycle
    results = automated_controller.run_full_collection_cycle()
    
    print("\n" + "="*60)
    print("COLLECTION RESULTS:")
    print("="*60)
    import json
    print(json.dumps(results, indent=2))
