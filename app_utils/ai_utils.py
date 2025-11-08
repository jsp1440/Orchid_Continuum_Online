"""
AI Utility Functions with Retry Logic and Graceful Degradation

Provides:
- Exponential backoff retry for transient failures
- Rate limit (429) handling
- Quota exhaustion (insufficient_quota) handling
- Never crashes the process on AI errors
"""
import time
import random
import logging
from typing import Callable, Any, Dict
from app_utils.settings import ORCHID_AI_ENABLED

logger = logging.getLogger(__name__)

def backoff_retry(request_fn: Callable, max_retries=5, base=0.5, cap=8.0):
    """
    Retry a function with exponential backoff.
    
    Args:
        request_fn: Function to execute (should make the API call)
        max_retries: Maximum number of retry attempts (default: 5)
        base: Base delay in seconds (default: 0.5)
        cap: Maximum delay cap in seconds (default: 8.0)
    
    Returns:
        Result from request_fn if successful
    
    Raises:
        RuntimeError: If all retries are exhausted
    """
    last_error = None
    
    for attempt in range(max_retries):
        try:
            return request_fn()
        except Exception as e:
            last_error = e
            error_msg = str(e).lower()
            
            # Check for retryable errors
            if any(keyword in error_msg for keyword in [
                "429",
                "too many requests",
                "rate limit",
                "insufficient_quota",
                "quota exceeded",
                "timeout",
                "connection",
                "temporary"
            ]):
                # Calculate exponential backoff with jitter
                delay = min(cap, base * (2 ** attempt)) + random.uniform(0, 0.2)
                
                logger.warning(
                    f"Retryable error (attempt {attempt + 1}/{max_retries}): {e}. "
                    f"Retrying in {delay:.2f}s..."
                )
                
                time.sleep(delay)
                continue
            else:
                # Non-retryable error - raise immediately
                logger.error(f"Non-retryable error: {e}")
                raise
    
    # All retries exhausted
    logger.error(f"OpenAI call failed after {max_retries} retries: {last_error}")
    raise RuntimeError(f"OpenAI call failed after {max_retries} retries: {last_error}")


def safe_ai_call(fn: Callable, *args, **kwargs) -> Dict[str, Any]:
    """
    Safely execute an AI function with automatic error handling and graceful degradation.
    
    Args:
        fn: The AI function to call (e.g., client.chat.completions.create)
        *args: Positional arguments for fn
        **kwargs: Keyword arguments for fn
    
    Returns:
        dict: AI response if successful, or error dict with graceful degradation
    
    Example:
        >>> from openai import OpenAI
        >>> client = OpenAI(api_key=OPENAI_API_KEY)
        >>> result = safe_ai_call(
        ...     client.chat.completions.create,
        ...     model="gpt-4",
        ...     messages=[{"role": "user", "content": "Hello"}]
        ... )
    """
    # Check AI kill-switch
    if not ORCHID_AI_ENABLED:
        logger.info("AI call blocked - ORCHID_AI_ENABLED=false")
        return {
            "status": "disabled",
            "reason": "AI temporarily paused for quota management",
            "message": "AI features are currently disabled. Please contact support to enable."
        }
    
    # Execute with retry logic
    try:
        result = backoff_retry(lambda: fn(*args, **kwargs))
        return {
            "status": "success",
            "result": result
        }
    except Exception as e:
        logger.error(f"AI call failed after retries: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "AI service temporarily unavailable. Please try again later."
        }


def get_ai_status() -> Dict[str, Any]:
    """
    Get current AI system status.
    
    Returns:
        dict: Status information including enabled state and message
    """
    from app.settings import OPENAI_API_KEY
    
    if not ORCHID_AI_ENABLED:
        return {
            "enabled": False,
            "status": "paused",
            "message": "AI features temporarily disabled for quota management"
        }
    
    if not OPENAI_API_KEY:
        return {
            "enabled": False,
            "status": "error",
            "message": "AI enabled but API key not configured"
        }
    
    return {
        "enabled": True,
        "status": "active",
        "message": "AI features fully operational"
    }
