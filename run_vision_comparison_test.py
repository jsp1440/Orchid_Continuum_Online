"""
Vision AI Comparison Test
Compare GPT-4o, Hugging Face, and other vision models on real orchid specimens
"""

import os
import sys
from datetime import datetime
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from multi_ai_vision_analyzer import MultiAIVisionAnalyzer
from app import app, db
from models import OrchidImage

def run_vision_comparison_test(num_images=3):
    """Test multiple AI vision providers on real GBIF orchid images"""
    
    analyzer = MultiAIVisionAnalyzer()
    
    print("\n" + "=" * 80)
    print("MULTI-AI VISION COMPARISON TEST")
    print("Testing GPT-4o vs Hugging Face vs Gemini on real orchid specimens")
    print("=" * 80 + "\n")
    
    # Standard botanical analysis prompt
    botanical_prompt = """Analyze this orchid specimen image. Provide:
    
1. **Identification**: Genus and species if recognizable
2. **Flower Structure**: Describe sepals, petals, labellum (lip), column
3. **Botanical Features**: Note any distinctive characteristics using proper terminology
4. **Growth Habit**: Epiphyte, terrestrial, lithophyte
5. **Condition**: Specimen quality and visible structures
    
Use proper botanical Latin terminology where applicable."""
    
    all_results = []
    
    with app.app_context():
        # Get sample images with local paths
        test_images = db.session.query(OrchidImage).filter(
            OrchidImage.local_path.isnot(None)
        ).limit(num_images).all()
        
        if not test_images:
            print("❌ No test images found in database with local paths")
            return
        
        print(f"📊 Testing {len(test_images)} orchid specimens\n")
        
        for idx, image in enumerate(test_images, 1):
            if not os.path.exists(image.local_path):
                print(f"⚠️  Skipping {image.scientific_name} - file not found")
                continue
            
            print(f"\n{'='*80}")
            print(f"TEST {idx}/{len(test_images)}: {image.scientific_name}")
            print(f"Image: {os.path.basename(image.local_path)}")
            print(f"{'='*80}\n")
            
            # Run comparison across all providers
            results = analyzer.compare_all_providers(
                image_path=image.local_path,
                prompt=botanical_prompt
            )
            
            # Display results
            for provider_key, result in results.items():
                print(f"\n--- {result.provider} ({result.model}) ---")
                
                if result.success:
                    print(f"✓ Success")
                    print(f"  Processing time: {result.processing_time:.2f}s")
                    print(f"  Cost estimate: ${result.cost_estimate:.4f}")
                    print(f"  Botanical terms found: {len(result.botanical_terms_found)}")
                    if result.botanical_terms_found:
                        print(f"  Terms: {', '.join(result.botanical_terms_found[:5])}")
                    print(f"\n  Analysis (first 300 chars):")
                    print(f"  {result.analysis[:300]}...")
                else:
                    print(f"✗ Failed: {result.error}")
            
            # Store results
            all_results.append({
                "image_id": image.id,
                "scientific_name": image.scientific_name,
                "file_path": image.local_path,
                "results": {
                    k: {
                        "provider": v.provider,
                        "model": v.model,
                        "success": v.success,
                        "analysis": v.analysis if v.success else None,
                        "processing_time": v.processing_time,
                        "cost": v.cost_estimate,
                        "botanical_terms": v.botanical_terms_found,
                        "error": v.error
                    }
                    for k, v in results.items()
                }
            })
            
            print("\n" + "-" * 80)
    
    # Generate final report
    print("\n\n" + "=" * 80)
    print("FINAL COMPARISON SUMMARY")
    print("=" * 80 + "\n")
    
    # Calculate aggregated stats
    total_tests = len(all_results)
    provider_stats = {}
    
    for test_result in all_results:
        for provider_key, result_data in test_result["results"].items():
            if provider_key not in provider_stats:
                provider_stats[provider_key] = {
                    "provider": result_data["provider"],
                    "model": result_data["model"],
                    "successes": 0,
                    "failures": 0,
                    "total_time": 0.0,
                    "total_cost": 0.0,
                    "avg_botanical_terms": 0.0
                }
            
            stats = provider_stats[provider_key]
            
            if result_data["success"]:
                stats["successes"] += 1
                stats["total_time"] += result_data["processing_time"]
                stats["total_cost"] += result_data["cost"]
                stats["avg_botanical_terms"] += len(result_data["botanical_terms"])
            else:
                stats["failures"] += 1
    
    # Display summary table
    print(f"{'Provider':<20} {'Model':<20} {'Success Rate':<15} {'Avg Time':<12} {'Total Cost':<12} {'Avg Terms'}")
    print("-" * 100)
    
    for provider_key, stats in provider_stats.items():
        success_rate = f"{stats['successes']}/{total_tests}"
        avg_time = stats["total_time"] / stats["successes"] if stats["successes"] > 0 else 0
        avg_terms = stats["avg_botanical_terms"] / stats["successes"] if stats["successes"] > 0 else 0
        
        print(
            f"{stats['provider']:<20} "
            f"{stats['model']:<20} "
            f"{success_rate:<15} "
            f"{avg_time:<12.2f} "
            f"${stats['total_cost']:<11.4f} "
            f"{avg_terms:.1f}"
        )
    
    print("\n" + "=" * 80)
    
    # Save detailed results to JSON
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"vision_comparison_results_{timestamp}.json"
    
    with open(results_file, "w") as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: {results_file}")
    
    # Recommendations
    print("\n" + "=" * 80)
    print("💡 RECOMMENDATIONS")
    print("=" * 80 + "\n")
    
    # Find best provider by different metrics
    if provider_stats:
        # Best by cost (free)
        free_providers = [k for k, v in provider_stats.items() if v["total_cost"] == 0 and v["successes"] > 0]
        if free_providers:
            print(f"💰 Best for Cost: {provider_stats[free_providers[0]]['provider']} - FREE!")
        
        # Best by speed
        fastest = min(provider_stats.items(), 
                     key=lambda x: x[1]["total_time"] / x[1]["successes"] if x[1]["successes"] > 0 else float('inf'))
        avg_speed = fastest[1]["total_time"] / fastest[1]["successes"] if fastest[1]["successes"] > 0 else 0
        print(f"⚡ Fastest: {fastest[1]['provider']} - {avg_speed:.2f}s average")
        
        # Best by botanical terminology
        most_terms = max(provider_stats.items(),
                        key=lambda x: x[1]["avg_botanical_terms"] / x[1]["successes"] if x[1]["successes"] > 0 else 0)
        avg_terms_count = most_terms[1]["avg_botanical_terms"] / most_terms[1]["successes"] if most_terms[1]["successes"] > 0 else 0
        print(f"🌿 Best Botanical Vocabulary: {most_terms[1]['provider']} - {avg_terms_count:.1f} terms average")
    
    print("\n" + "=" * 80 + "\n")
    
    return all_results


if __name__ == "__main__":
    # Run with 3 test images
    results = run_vision_comparison_test(num_images=3)
    
    if results:
        print("✅ Vision comparison test completed successfully!")
    else:
        print("❌ Test failed or no results generated")
