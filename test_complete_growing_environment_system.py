#!/usr/bin/env python3
"""
Complete End-to-End Test of Growing Environment System
Demonstrates the revolutionary new feature
"""
from growing_environment_manager import GrowingEnvironmentManager
from environmental_delta_analyzer import EnvironmentalDeltaAnalyzer
from substrate_recommendation_engine import SubstrateRecommendationEngine
import json

def main():
    print("=" * 80)
    print("🌺 COMPLETE GROWING ENVIRONMENT SYSTEM TEST")
    print("=" * 80)
    print()
    
    # Step 1: Create a growing environment
    print("STEP 1: Creating user's growing environment")
    print("-" * 80)
    
    env_manager = GrowingEnvironmentManager()
    
    # User has a warm greenhouse
    my_greenhouse = env_manager.create_from_template(
        template_name='warm_greenhouse',
        custom_name='My Warm Greenhouse'
    )
    
    print(f"✅ Created: {my_greenhouse['name']}")
    print(f"   Temperature: {my_greenhouse['temperature']['avg']}°F (range: {my_greenhouse['temperature']['min']}-{my_greenhouse['temperature']['max']})")
    print(f"   Humidity: {my_greenhouse['humidity']['avg']}% (range: {my_greenhouse['humidity']['min']}-{my_greenhouse['humidity']['max']})")
    print(f"   Light: {my_greenhouse['light_level']}")
    print()
    
    # Step 2: Define species requirements (from Baker/AOS/Microclimate)
    print("STEP 2: Species requirements (from Microclimate Analysis + Baker + AOS)")
    print("-" * 80)
    
    # Example: Cool-growing species (Masdevallia)
    cool_species = {
        'name': 'Masdevallia veitchiana',
        'temperature': {'min': 50, 'max': 65, 'category': 'cool'},
        'humidity': 80,
        'light': 'medium'
    }
    
    # Example: Warm-growing species (Phalaenopsis)
    warm_species = {
        'name': 'Phalaenopsis amabilis',
        'temperature': {'min': 65, 'max': 85, 'category': 'warm'},
        'humidity': 60,
        'light': 'bright'
    }
    
    print(f"Cool Species: {cool_species['name']}")
    print(f"  Temp: {cool_species['temperature']['min']}-{cool_species['temperature']['max']}°F")
    print(f"  Humidity: {cool_species['humidity']}%")
    print(f"  Light: {cool_species['light']}")
    print()
    
    print(f"Warm Species: {warm_species['name']}")
    print(f"  Temp: {warm_species['temperature']['min']}-{warm_species['temperature']['max']}°F")
    print(f"  Humidity: {warm_species['humidity']}%")
    print(f"  Light: {warm_species['light']}")
    print()
    
    # Step 3: Delta Analysis for Cool Species (mismatch expected)
    print("STEP 3: Delta Analysis - Cool Species in Warm Greenhouse")
    print("-" * 80)
    
    delta_analyzer = EnvironmentalDeltaAnalyzer()
    
    cool_analysis = delta_analyzer.generate_comprehensive_analysis(
        species_data=cool_species,
        growing_environment=my_greenhouse
    )
    
    print(f"Compatibility Score: {cool_analysis['compatibility_score']}/100 ({cool_analysis['compatibility_rating'].upper()})")
    print(f"Summary: {cool_analysis['summary']}")
    print()
    print("Temperature Delta:")
    for rec in cool_analysis['temperature_delta']['recommendations']:
        print(f"  {rec}")
    print()
    print("Humidity Delta:")
    for rec in cool_analysis['humidity_delta']['recommendations']:
        print(f"  {rec}")
    print()
    
    # Step 4: Delta Analysis for Warm Species (good match)
    print("STEP 4: Delta Analysis - Warm Species in Warm Greenhouse")
    print("-" * 80)
    
    warm_analysis = delta_analyzer.generate_comprehensive_analysis(
        species_data=warm_species,
        growing_environment=my_greenhouse
    )
    
    print(f"Compatibility Score: {warm_analysis['compatibility_score']}/100 ({warm_analysis['compatibility_rating'].upper()})")
    print(f"Summary: {warm_analysis['summary']}")
    print()
    print("Temperature Delta:")
    for rec in warm_analysis['temperature_delta']['recommendations']:
        print(f"  {rec}")
    print()
    
    # Step 5: Substrate Recommendations with Environmental Adjustments
    print("STEP 5: Substrate Recommendations with Environmental Adjustments")
    print("-" * 80)
    
    substrate_engine = SubstrateRecommendationEngine()
    
    # Mock microclimate data for warm species
    microclimate_warm = {
        'status': 'success',
        'patterns': {
            'elevation': {'available': True, 'mean_meters': 500},
            'coordinates': {'available': True, 'centroid': {'lat': 5.0, 'lon': -75.0}}
        }
    }
    
    substrate_recs = substrate_engine.recommend_substrate(
        microclimate_data=microclimate_warm,
        grower_conditions={'climate': 'tropical'}
    )
    
    # Adjust for actual environment
    adjustments = delta_analyzer.adjust_substrate_for_conditions(
        base_substrate_recs=substrate_recs,
        environmental_deltas={
            'temperature': warm_analysis['temperature_delta'],
            'humidity': warm_analysis['humidity_delta'],
            'light': warm_analysis['light_delta']
        }
    )
    
    print(f"Primary Recommendation: {substrate_recs['primary_recommendation']['substrate']}")
    print(f"DIY Recipe: {substrate_recs['diy_recipe']['name']}")
    print(f"  {json.dumps(substrate_recs['diy_recipe']['ingredients'], indent=2)}")
    print()
    print(f"Environmental Adjustments: {adjustments['summary']}")
    if adjustments['environmental_adjustments']:
        for adj in adjustments['environmental_adjustments']:
            print(f"  - {adj['reason']}: {adj['suggestion']}")
    print()
    
    # Step 6: Complete Use Case Summary
    print("STEP 6: Complete Use Case Summary")
    print("=" * 80)
    print()
    print("📊 YOUR GREENHOUSE CONDITIONS:")
    print(f"   Temperature: {my_greenhouse['temperature']['avg']}°F")
    print(f"   Humidity: {my_greenhouse['humidity']['avg']}%")
    print(f"   Light: {my_greenhouse['light_level']}")
    print()
    print("✅ RECOMMENDED SPECIES (Good Match):")
    print(f"   {warm_species['name']}")
    print(f"   Compatibility: {warm_analysis['compatibility_score']}/100")
    print(f"   Use: {substrate_recs['diy_recipe']['name']}")
    print()
    print("⚠️  CHALLENGING SPECIES (Requires Modifications):")
    print(f"   {cool_species['name']}")
    print(f"   Compatibility: {cool_analysis['compatibility_score']}/100")
    print(f"   Key Issue: Too warm (needs cooling to 50-65°F)")
    print()
    
    print("=" * 80)
    print("✅ GROWING ENVIRONMENT SYSTEM TEST COMPLETE!")
    print("=" * 80)


if __name__ == '__main__':
    main()
