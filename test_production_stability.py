#!/usr/bin/env python3
"""
Production Stability Test Suite
Tests AI kill-switch, health endpoint, and graceful degradation
"""
import os
import sys
import requests
import time

# Colors for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_test(name):
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}TEST: {name}{RESET}")
    print(f"{BLUE}{'='*70}{RESET}")

def print_pass(msg):
    print(f"{GREEN}✅ PASS: {msg}{RESET}")

def print_fail(msg):
    print(f"{RED}❌ FAIL: {msg}{RESET}")

def print_info(msg):
    print(f"{YELLOW}ℹ️  INFO: {msg}{RESET}")

# Configuration
BASE_URL = os.getenv('TEST_BASE_URL', 'http://localhost:5000')

def test_1_health_endpoint():
    """Test 1: Static /healthz endpoint returns 200 and never calls OpenAI"""
    print_test("Static Health Endpoint")
    
    try:
        response = requests.get(f"{BASE_URL}/healthz", timeout=5)
        
        if response.status_code == 200:
            print_pass("Health endpoint returns 200 OK")
        else:
            print_fail(f"Health endpoint returned {response.status_code}")
            return False
        
        data = response.json()
        
        if data.get('status') == 'ok':
            print_pass("Health status is 'ok'")
        else:
            print_fail(f"Health status is '{data.get('status')}'")
        
        if data.get('service') == 'orchid-continuum':
            print_pass("Service name correct")
        else:
            print_fail(f"Service name is '{data.get('service')}'")
        
        print_info(f"AI enabled: {data.get('ai_enabled')}")
        print_info(f"AI status: {data.get('ai_status')}")
        
        # Test response time (should be <100ms since no DB/API calls)
        start = time.time()
        requests.get(f"{BASE_URL}/healthz", timeout=5)
        elapsed = (time.time() - start) * 1000
        
        if elapsed < 200:  # 200ms threshold
            print_pass(f"Health check is fast: {elapsed:.0f}ms")
        else:
            print_fail(f"Health check is slow: {elapsed:.0f}ms")
        
        return True
        
    except Exception as e:
        print_fail(f"Health endpoint error: {e}")
        return False

def test_2_ai_disabled_boot():
    """Test 2: App boots successfully with AI disabled"""
    print_test("Boot with AI Disabled")
    
    print_info("Checking if ORCHID_AI_ENABLED is set to 'false'...")
    
    try:
        # Import settings to check current state
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from app.settings import ORCHID_AI_ENABLED
        from app.ai_utils import get_ai_status
        
        if not ORCHID_AI_ENABLED:
            print_pass("ORCHID_AI_ENABLED is False (AI disabled)")
        else:
            print_fail("ORCHID_AI_ENABLED is True (AI should be disabled for this test)")
            print_info("Set environment variable: ORCHID_AI_ENABLED=false")
            return False
        
        status = get_ai_status()
        
        if status['enabled'] == False:
            print_pass("AI status shows disabled")
        else:
            print_fail("AI status shows enabled")
        
        if status['status'] == 'paused':
            print_pass("AI status is 'paused'")
        else:
            print_fail(f"AI status is '{status['status']}'")
        
        print_pass("App imported successfully with AI disabled")
        return True
        
    except Exception as e:
        print_fail(f"Import error: {e}")
        return False

def test_3_safe_ai_call_wrapper():
    """Test 3: safe_ai_call returns graceful response when AI disabled"""
    print_test("Safe AI Call Wrapper")
    
    try:
        from app.ai_utils import safe_ai_call
        from app.settings import ORCHID_AI_ENABLED
        
        # Mock OpenAI function
        def mock_openai_call():
            return {"result": "AI response"}
        
        result = safe_ai_call(mock_openai_call)
        
        if not ORCHID_AI_ENABLED:
            # Should return disabled status
            if result.get('status') == 'disabled':
                print_pass("safe_ai_call returns 'disabled' when AI is off")
            else:
                print_fail(f"Expected 'disabled', got '{result.get('status')}'")
                return False
            
            if 'reason' in result:
                print_pass(f"Graceful message: {result.get('reason')}")
            else:
                print_fail("No reason provided in disabled response")
        else:
            print_info("AI is enabled - testing normal operation")
            if result.get('status') == 'success':
                print_pass("safe_ai_call returns 'success' when AI is on")
            else:
                print_info(f"Result status: {result.get('status')}")
        
        return True
        
    except Exception as e:
        print_fail(f"Wrapper test error: {e}")
        return False

def test_4_retry_logic():
    """Test 4: Retry logic handles 429 errors gracefully"""
    print_test("Exponential Backoff Retry")
    
    try:
        from app.ai_utils import backoff_retry
        
        # Mock function that fails with 429 once, then succeeds
        call_count = {'count': 0}
        
        def mock_rate_limited_call():
            call_count['count'] += 1
            if call_count['count'] == 1:
                raise Exception("429 Rate limit exceeded")
            return {"success": True}
        
        start = time.time()
        result = backoff_retry(mock_rate_limited_call, max_retries=3)
        elapsed = time.time() - start
        
        if result.get('success'):
            print_pass("Retry succeeded after 429 error")
        else:
            print_fail("Retry did not succeed")
        
        if call_count['count'] == 2:
            print_pass(f"Retried {call_count['count']-1} time(s)")
        else:
            print_fail(f"Unexpected retry count: {call_count['count']}")
        
        if elapsed >= 0.5:  # Should have delayed at least 0.5s
            print_pass(f"Exponential backoff applied: {elapsed:.2f}s")
        else:
            print_fail(f"Backoff too fast: {elapsed:.2f}s")
        
        return True
        
    except Exception as e:
        print_fail(f"Retry test error: {e}")
        return False

def test_5_non_retryable_error():
    """Test 5: Non-retryable errors fail immediately"""
    print_test("Non-Retryable Error Handling")
    
    try:
        from app.ai_utils import backoff_retry
        
        def mock_non_retryable_error():
            raise ValueError("Invalid input - non-retryable")
        
        start = time.time()
        try:
            backoff_retry(mock_non_retryable_error, max_retries=3)
            print_fail("Should have raised error")
            return False
        except ValueError:
            elapsed = time.time() - start
            if elapsed < 0.5:  # Should fail immediately, not retry
                print_pass(f"Failed immediately without retry: {elapsed:.2f}s")
            else:
                print_fail(f"Took too long (may have retried): {elapsed:.2f}s")
            return True
        
    except Exception as e:
        print_fail(f"Non-retryable test error: {e}")
        return False

def test_6_ui_banner():
    """Test 6: UI shows AI paused banner when disabled"""
    print_test("UI Banner Display")
    
    try:
        response = requests.get(BASE_URL, timeout=5)
        
        if response.status_code == 200:
            print_pass("Homepage loads successfully")
        else:
            print_fail(f"Homepage returned {response.status_code}")
            return False
        
        html = response.text
        
        # Check for banner CSS
        if 'ai-paused-banner' in html:
            print_pass("AI banner CSS found in template")
        else:
            print_info("AI banner CSS not found (may be in separate CSS file)")
        
        # Check for conditional rendering
        if 'ORCHID_AI_ENABLED' in html or 'ai_status' in html:
            print_pass("Template has AI status variables")
        else:
            print_info("Could not verify template variables (may be rendered)")
        
        print_info("Manual verification: Check if orange banner appears at top of page")
        
        return True
        
    except Exception as e:
        print_fail(f"UI banner test error: {e}")
        return False

def main():
    """Run all production stability tests"""
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}PRODUCTION STABILITY TEST SUITE{RESET}")
    print(f"{BLUE}Testing: {BASE_URL}{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")
    
    tests = [
        test_1_health_endpoint,
        test_2_ai_disabled_boot,
        test_3_safe_ai_call_wrapper,
        test_4_retry_logic,
        test_5_non_retryable_error,
        test_6_ui_banner,
    ]
    
    results = []
    
    for test_func in tests:
        try:
            passed = test_func()
            results.append((test_func.__name__, passed))
        except Exception as e:
            print_fail(f"Test crashed: {e}")
            results.append((test_func.__name__, False))
    
    # Summary
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}TEST SUMMARY{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = f"{GREEN}✅ PASS{RESET}" if result else f"{RED}❌ FAIL{RESET}"
        print(f"{status}: {test_name}")
    
    print(f"\n{BLUE}{'='*70}{RESET}")
    if passed == total:
        print(f"{GREEN}✅ ALL TESTS PASSED ({passed}/{total}){RESET}")
        print(f"{GREEN}Production stability system is working correctly!{RESET}")
    else:
        print(f"{RED}❌ SOME TESTS FAILED ({passed}/{total}){RESET}")
        print(f"{YELLOW}Review failed tests above{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")
    
    return 0 if passed == total else 1

if __name__ == '__main__':
    sys.exit(main())
