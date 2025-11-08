"""
Quick Test Script for All AI Integrations
Verifies that all API keys are working correctly
"""

import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_api_keys():
    """Test that all API keys are present"""
    keys_to_check = {
        "OpenAI": "OPENAI_API_KEY",
        "Hugging Face": "HHUGGINGFACE_API_KEY",
        "Replicate": "REPLICATE_API_KEY",
        "Together AI": "Together_ai_user_key",
        "Google Gemini": "GOOGLE_API_KEY"
    }
    
    logger.info("=" * 80)
    logger.info("TESTING API KEY AVAILABILITY")
    logger.info("=" * 80)
    
    available = []
    missing = []
    
    for service, key_name in keys_to_check.items():
        key_value = os.environ.get(key_name)
        if key_value:
            logger.info(f"✓ {service}: Key found ({key_name})")
            available.append(service)
        else:
            logger.warning(f"✗ {service}: Key missing ({key_name})")
            missing.append(service)
    
    logger.info("")
    logger.info(f"Available services: {len(available)}/{len(keys_to_check)}")
    logger.info(f"Services ready: {', '.join(available)}")
    
    if missing:
        logger.warning(f"Missing services: {', '.join(missing)}")
    
    return available, missing


def test_huggingface():
    """Test Hugging Face API connection"""
    try:
        from huggingface_hub import InferenceClient
        
        hf_key = os.environ.get("HHUGGINGFACE_API_KEY")
        if not hf_key:
            logger.error("✗ Hugging Face: No API key found")
            return False
        
        client = InferenceClient(token=hf_key)
        logger.info("✓ Hugging Face: Client initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"✗ Hugging Face: Failed to initialize - {str(e)}")
        return False


def test_replicate():
    """Test Replicate API connection"""
    try:
        import replicate
        
        replicate_key = os.environ.get("REPLICATE_API_KEY")
        if not replicate_key:
            logger.error("✗ Replicate: No API key found")
            return False
        
        os.environ["REPLICATE_API_TOKEN"] = replicate_key
        logger.info("✓ Replicate: Client initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"✗ Replicate: Failed to initialize - {str(e)}")
        return False


def test_together_ai():
    """Test Together AI API connection"""
    try:
        import requests
        
        together_key = os.environ.get("Together_ai_user_key")
        if not together_key:
            logger.error("✗ Together AI: No API key found")
            return False
        
        # Quick API health check
        headers = {"Authorization": f"Bearer {together_key}"}
        response = requests.get(
            "https://api.together.xyz/v1/models",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info("✓ Together AI: API connection successful")
            models = response.json()
            logger.info(f"  Available models: {len(models)}")
            return True
        else:
            logger.error(f"✗ Together AI: API returned status {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"✗ Together AI: Connection failed - {str(e)}")
        return False


def test_openai():
    """Test OpenAI API connection"""
    try:
        import openai
        
        openai_key = os.environ.get("OPENAI_API_KEY")
        if not openai_key:
            logger.error("✗ OpenAI: No API key found")
            return False
        
        openai.api_key = openai_key
        logger.info("✓ OpenAI: Client initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"✗ OpenAI: Failed to initialize - {str(e)}")
        return False


def run_all_tests():
    """Run all integration tests"""
    logger.info("\n" + "=" * 80)
    logger.info("AI INTEGRATION TEST SUITE")
    logger.info("=" * 80 + "\n")
    
    # Test 1: Check API keys
    available, missing = test_api_keys()
    
    logger.info("\n" + "=" * 80)
    logger.info("TESTING API CONNECTIONS")
    logger.info("=" * 80 + "\n")
    
    results = {}
    
    # Test 2: Test individual services
    if "Hugging Face" in available:
        results["Hugging Face"] = test_huggingface()
    
    if "Replicate" in available:
        results["Replicate"] = test_replicate()
    
    if "Together AI" in available:
        results["Together AI"] = test_together_ai()
    
    if "OpenAI" in available:
        results["OpenAI"] = test_openai()
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    logger.info(f"\nPassed: {passed}/{total} tests")
    
    for service, status in results.items():
        status_icon = "✓" if status else "✗"
        logger.info(f"{status_icon} {service}")
    
    logger.info("\n" + "=" * 80)
    
    if passed == total:
        logger.info("🎉 ALL TESTS PASSED! Ready to compare AI providers.")
    else:
        logger.warning("⚠️  Some services failed. Check the logs above for details.")
    
    logger.info("=" * 80 + "\n")
    
    return results


if __name__ == "__main__":
    run_all_tests()
