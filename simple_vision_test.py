"""
Simple Vision AI Comparison Test (Standalone)
Tests vision models without needing to load the full Flask app
"""

import os
import sys
from datetime import datetime
import json

from multi_ai_vision_analyzer import MultiAIVisionAnalyzer


def find_test_images():
    """Find some test orchid images in common locations"""
    test_paths = [
        "static/uploads",
        "uploads",
        "orchid_images",
        "gbif_images"
    ]
    
    image_files = []
    
    for test_dir in test_paths:
        if os.path.exists(test_dir):
            for file in os.listdir(test_dir)[:5]:  # Get first 5 files
                if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                    full_path = os.path.join(test_dir, file)
                    if os.path.getsize(full_path) > 0:  # Not empty
                        image_files.append(full_path)
    
    return image_files[:3]  # Return up to 3 test images


def run_simple_vision_test():
    """Simple test of vision AI providers"""
    
    print("\n" + "=" * 80)
    print("SIMPLE MULTI-AI VISION COMPARISON TEST")
    print("=" * 80 + "\n")
    
    # Initialize analyzer
    analyzer = MultiAIVisionAnalyzer()
    
    # Find test images
    print("🔍 Searching for test orchid images...")
    test_images = find_test_images()
    
    if not test_images:
        print("❌ No test images found. Please add some orchid images to:")
        print("   - static/uploads/")
        print("   - uploads/")
        print("   - gbif_images/")
        return None
    
    print(f"✓ Found {len(test_images)} test images\n")
    
    # Botanical analysis prompt
    botanical_prompt = """Analyze this orchid image. Identify:
1. Genus and species (if possible)
2. Flower parts: sepals, petals, labellum (lip), column
3. Distinctive botanical features using proper terminology
4. Growth habit (epiphyte, terrestrial, etc.)"""
    
    all_results = []
    
    for idx, image_path in enumerate(test_images, 1):
        image_name = os.path.basename(image_path)
        
        print(f"\n{'='*80}")
        print(f"TEST {idx}/{len(test_images)}: {image_name}")
        print(f"Path: {image_path}")
        print(f"Size: {os.path.getsize(image_path) / 1024:.1f} KB")
        print(f"{'='*80}\n")
        
        # Run comparison
        results = analyzer.compare_all_providers(image_path, botanical_prompt)
        
        # Display results
        for provider_key, result in results.items():
            print(f"\n--- {result.provider} ({result.model}) ---")
            
            if result.success:
                print(f"✓ SUCCESS")
                print(f"  Time: {result.processing_time:.2f}s")
                print(f"  Cost: ${result.cost_estimate:.4f}")
                print(f"  Botanical terms: {len(result.botanical_terms_found)}")
                if result.botanical_terms_found:
                    print(f"  Found: {', '.join(result.botanical_terms_found[:5])}")
                print(f"\n  Analysis preview (first 200 chars):")
                print(f"  {result.analysis[:200]}...\n")
            else:
                print(f"✗ FAILED: {result.error}\n")
        
        all_results.append({
            "image": image_name,
            "path": image_path,
            "results": results
        })
        
        print("-" * 80)
    
    # Summary report
    print("\n\n" + "=" * 80)
    print("COMPARISON SUMMARY")
    print("=" * 80 + "\n")
    
    # Aggregate stats by provider
    provider_stats = {}
    
    for test in all_results:
        for provider_key, result in test["results"].items():
            if provider_key not in provider_stats:
                provider_stats[provider_key] = {
                    "provider": result.provider,
                    "model": result.model,
                    "successes": 0,
                    "total_time": 0,
                    "total_cost": 0,
                    "total_terms": 0
                }
            
            stats = provider_stats[provider_key]
            if result.success:
                stats["successes"] += 1
                stats["total_time"] += result.processing_time
                stats["total_cost"] += result.cost_estimate
                stats["total_terms"] += len(result.botanical_terms_found)
    
    # Display table
    print(f"{'Provider':<20} {'Success Rate':<15} {'Avg Time (s)':<15} {'Total Cost':<15} {'Avg Terms'}")
    print("-" * 85)
    
    total_tests = len(all_results)
    for key, stats in provider_stats.items():
        success_rate = f"{stats['successes']}/{total_tests}"
        avg_time = stats["total_time"] / stats["successes"] if stats["successes"] > 0 else 0
        avg_terms = stats["total_terms"] / stats["successes"] if stats["successes"] > 0 else 0
        
        print(
            f"{stats['provider']:<20} "
            f"{success_rate:<15} "
            f"{avg_time:<15.2f} "
            f"${stats['total_cost']:<14.4f} "
            f"{avg_terms:.1f}"
        )
    
    print("\n" + "=" * 80)
    
    # Recommendations
    print("\n💡 RECOMMENDATIONS:\n")
    
    # Best free option
    free_options = [k for k, v in provider_stats.items() if v["total_cost"] == 0 and v["successes"] > 0]
    if free_options:
        free_provider = provider_stats[free_options[0]]
        print(f"💰 Best FREE option: {free_provider['provider']}")
    
    # Fastest
    if provider_stats:
        fastest_key = min(provider_stats.items(), 
                         key=lambda x: x[1]["total_time"]/x[1]["successes"] if x[1]["successes"] > 0 else 999)
        print(f"⚡ Fastest: {fastest_key[1]['provider']} ({fastest_key[1]['total_time']/fastest_key[1]['successes']:.2f}s avg)")
    
    print("\n" + "=" * 80 + "\n")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"vision_test_results_{timestamp}.json"
    
    # Convert results to serializable format
    serializable_results = []
    for test in all_results:
        test_data = {
            "image": test["image"],
            "path": test["path"],
            "results": {}
        }
        for k, v in test["results"].items():
            test_data["results"][k] = {
                "provider": v.provider,
                "model": v.model,
                "success": v.success,
                "analysis": v.analysis if v.success else None,
                "processing_time": v.processing_time,
                "cost": v.cost_estimate,
                "botanical_terms": v.botanical_terms_found,
                "error": v.error
            }
        serializable_results.append(test_data)
    
    with open(report_file, "w") as f:
        json.dump(serializable_results, f, indent=2)
    
    print(f"💾 Results saved to: {report_file}\n")
    
    return all_results


if __name__ == "__main__":
    results = run_simple_vision_test()
    
    if results:
        print("✅ Vision comparison test completed!")
    else:
        print("❌ No results generated")
