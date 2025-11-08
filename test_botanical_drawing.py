"""
Test Script: Botanical Drawing Generation
Demonstrates how the AI creates labeled botanical illustrations
"""

import os
import logging
from vision_ai_botanist import BotanistVisionAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_single_specimen_with_drawing():
    """
    Test botanical analysis + drawing generation on a single specimen
    """
    print("\n" + "="*80)
    print("🎨 BOTANICAL DRAWING SYSTEM TEST")
    print("Testing: AI generates labeled scientific illustrations from photos")
    print("="*80 + "\n")
    
    # Initialize with drawings ENABLED
    botanist = BotanistVisionAI(enable_drawings=True)
    
    # Test URL (example - replace with actual GBIF image)
    test_url = "https://inaturalist-open-data.s3.amazonaws.com/photos/1/square.jpg"
    
    print(f"📸 Analyzing specimen: {test_url}")
    print("⏳ This will:")
    print("   1. Analyze the orchid using GPT-4o Vision")
    print("   2. Generate a scientific line drawing using DALL-E")
    print("   3. Add anatomical labels with arrows")
    print("   4. Store both unlabeled and labeled versions\n")
    
    # Perform analysis with drawing generation
    result = botanist.analyze_specimen_blind(
        image_url=test_url,
        generate_drawing=True
    )
    
    if result:
        print("\n✅ ANALYSIS COMPLETE!\n")
        print(f"🔬 Identification: {result.get('ai_genus')} {result.get('ai_species')}")
        print(f"📊 Confidence: {result.get('ai_confidence', 0):.2f}")
        print(f"💰 Cost: ${result.get('analysis_cost', 0):.4f}")
        
        if result.get('botanical_drawing_url'):
            print("\n🎨 BOTANICAL DRAWINGS GENERATED:")
            print(f"   Unlabeled drawing: {len(result['botanical_drawing_url'])} bytes (base64)")
            print(f"   Labeled drawing: {len(result['labeled_drawing_url'])} bytes (base64)")
            print(f"   Label count: {len(result.get('drawing_labels', {}))}")
            print("\n💡 Drawings can be displayed in the monitoring dashboard!")
        else:
            print("\n⚠️  No drawing generated (DALL-E call may have failed)")
        
        return result
    else:
        print("\n❌ Analysis failed")
        return None


def test_batch_without_drawings():
    """
    Test batch analysis WITHOUT drawings (faster, cheaper)
    """
    print("\n" + "="*80)
    print("⚡ FAST BATCH ANALYSIS TEST (No Drawings)")
    print("Testing: Process multiple specimens with Vision AI only")
    print("="*80 + "\n")
    
    # Initialize with drawings DISABLED (default)
    botanist = BotanistVisionAI(enable_drawings=False)
    botanist.setup_results_table()
    
    print("📊 Processing 5 specimens WITHOUT botanical drawings")
    print("   (This is faster and cheaper for large-scale analysis)\n")
    
    results = botanist.batch_analyze_specimens(limit=5, enable_drawings=False)
    
    print("\n✅ BATCH ANALYSIS COMPLETE!")
    print(f"   Processed: {results['total_processed']}")
    print(f"   Successful: {results['successful_analysis']}")
    print(f"   Perfect IDs: {results['correct_identifications']}")
    print(f"   Cost: ${results['estimated_cost']:.2f}")
    
    return results


if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║     DIGITAL BOTANIST - BOTANICAL ILLUSTRATION SYSTEM        ║
    ║                                                              ║
    ║  Like botany students who must:                             ║
    ║  1. Observe the specimen carefully                          ║
    ║  2. Draw it (forces attention to detail)                    ║
    ║  3. Label all anatomical parts (proves understanding)       ║
    ║                                                              ║
    ║  The AI does the same to prove it understands structures!   ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    choice = input("\nChoose test mode:\n1. Single specimen WITH botanical drawing (slower, visual proof)\n2. Batch analysis WITHOUT drawings (faster, bulk processing)\n\nChoice (1 or 2): ")
    
    if choice == "1":
        test_single_specimen_with_drawing()
    else:
        test_batch_without_drawings()
    
    print("\n" + "="*80)
    print("🌺 View results at: http://localhost:5000/botanist/monitor")
    print("="*80 + "\n")
