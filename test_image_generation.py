"""
Test Image Generation Across All Providers
Compare DALL-E 3, FLUX (Replicate), and Together AI for botanical illustrations
"""

import os
from datetime import datetime
import json

from multi_ai_image_generator import MultiAIImageGenerator


def test_botanical_illustration_generation():
    """Test all image generation providers on botanical illustration prompts"""
    
    print("\n" + "=" * 80)
    print("MULTI-AI IMAGE GENERATION COMPARISON TEST")
    print("Botanical Illustration Challenge")
    print("=" * 80 + "\n")
    
    generator = MultiAIImageGenerator()
    
    # Test species
    test_species = [
        ("Paphiopedilum rothschildianum", "lady slipper orchid with distinctive pouch-shaped labellum and striped petals"),
        ("Cattleya labiata", "large purple orchid with ruffled labellum and showy petals"),
        ("Phalaenopsis amabilis", "white moth orchid with graceful arching stems and round flowers")
    ]
    
    # Test styles
    styles = ["scientific", "artistic"]
    
    all_results = {}
    
    for species_name, description in test_species[:1]:  # Start with just 1 species
        print(f"\n{'='*80}")
        print(f"TESTING SPECIES: {species_name}")
        print(f"Description: {description}")
        print(f"{'='*80}\n")
        
        base_prompt = f"A detailed botanical illustration of {species_name}, {description}"
        
        for style in styles:
            print(f"\n--- STYLE: {style.upper()} ---\n")
            
            results = generator.compare_all_generators(base_prompt, style=style)
            
            # Display results
            for provider_key, result in results.items():
                print(f"{result.provider} ({result.model}):")
                
                if result.success:
                    print(f"  ✓ SUCCESS")
                    print(f"  Time: {result.processing_time:.2f}s")
                    print(f"  Cost: ${result.cost_estimate:.4f}")
                    print(f"  Image URL: {result.image_url[:80]}...")
                else:
                    print(f"  ✗ FAILED: {result.error}")
                
                print()
            
            # Store results
            test_key = f"{species_name}_{style}"
            all_results[test_key] = results
            
            print("-" * 80)
    
    # Summary
    print("\n\n" + "=" * 80)
    print("GENERATION SUMMARY")
    print("=" * 80 + "\n")
    
    # Aggregate stats
    provider_stats = {}
    
    for test_key, results in all_results.items():
        for provider_key, result in results.items():
            if provider_key not in provider_stats:
                provider_stats[provider_key] = {
                    "provider": result.provider,
                    "model": result.model,
                    "successes": 0,
                    "failures": 0,
                    "total_time": 0,
                    "total_cost": 0
                }
            
            stats = provider_stats[provider_key]
            if result.success:
                stats["successes"] += 1
                stats["total_time"] += result.processing_time
                stats["total_cost"] += result.cost_estimate
            else:
                stats["failures"] += 1
    
    # Display table
    total_tests = sum(stats["successes"] + stats["failures"] for stats in provider_stats.values()) // len(provider_stats) if provider_stats else 0
    
    print(f"{'Provider':<20} {'Model':<20} {'Success':<10} {'Avg Time':<12} {'Total Cost'}")
    print("-" * 75)
    
    for key, stats in provider_stats.items():
        success_count = f"{stats['successes']}/{stats['successes'] + stats['failures']}"
        avg_time = stats["total_time"] / stats["successes"] if stats["successes"] > 0 else 0
        
        print(
            f"{stats['provider']:<20} "
            f"{stats['model']:<20} "
            f"{success_count:<10} "
            f"{avg_time:<12.2f} "
            f"${stats['total_cost']:.4f}"
        )
    
    print("\n" + "=" * 80)
    
    # Recommendations
    print("\n💡 RECOMMENDATIONS:\n")
    
    # Find best options
    free_providers = [k for k, v in provider_stats.items() if v["total_cost"] == 0 and v["successes"] > 0]
    if free_providers:
        free_key = free_providers[0]
        print(f"💰 FREE OPTION: {provider_stats[free_key]['provider']} - No cost!")
    
    cheapest = min(provider_stats.items(), key=lambda x: x[1]["total_cost"]) if provider_stats else None
    if cheapest:
        print(f"💵 Cheapest: {cheapest[1]['provider']} - ${cheapest[1]['total_cost']:.4f} total")
    
    fastest = min(provider_stats.items(), 
                 key=lambda x: x[1]["total_time"]/x[1]["successes"] if x[1]["successes"] > 0 else 999) if provider_stats else None
    if fastest and fastest[1]["successes"] > 0:
        avg_speed = fastest[1]["total_time"] / fastest[1]["successes"]
        print(f"⚡ Fastest: {fastest[1]['provider']} - {avg_speed:.2f}s average")
    
    print("\n" + "=" * 80 + "\n")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"image_gen_test_results_{timestamp}.json"
    
    # Convert to serializable format
    serializable_results = {}
    for test_key, results in all_results.items():
        serializable_results[test_key] = {}
        for provider_key, result in results.items():
            serializable_results[test_key][provider_key] = {
                "provider": result.provider,
                "model": result.model,
                "success": result.success,
                "image_url": result.image_url if result.success else None,
                "processing_time": result.processing_time,
                "cost": result.cost_estimate,
                "error": result.error
            }
    
    with open(report_file, "w") as f:
        json.dump(serializable_results, f, indent=2)
    
    print(f"💾 Results saved to: {report_file}\n")
    
    return all_results


if __name__ == "__main__":
    results = test_botanical_illustration_generation()
    
    if results:
        print("✅ Image generation test completed!")
        print("\n📸 Check the JSON file for image URLs to view the generated illustrations")
    else:
        print("❌ No results generated")
