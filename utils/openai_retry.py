"""
OpenAI API Retry Wrapper with Rate Limiting
Fixes Render 429 errors per Julius's diagnostic report
"""
import time
import random
import logging
from functools import wraps
from typing import Optional

logger = logging.getLogger(__name__)

class RateLimiter:
    """Token bucket rate limiter - 1 request per second"""
    def __init__(self, max_rps=1):
        self.max_rps = max_rps
        self.last_request_time = 0
        
    def acquire(self):
        """Wait if necessary to respect rate limit"""
        now = time.time()
        time_since_last = now - self.last_request_time
        min_interval = 1.0 / self.max_rps
        
        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()

# Global rate limiter
_rate_limiter = RateLimiter(max_rps=1)

def openai_retry(max_retries=5, base_delay=0.25):
    """
    Decorator for OpenAI API calls with exponential backoff + jitter
    
    Handles:
    - 429 Too Many Requests
    - 500+ Server errors
    - Timeout errors
    - Respects Retry-After header
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Apply rate limiting
            _rate_limiter.acquire()
            
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                    
                except Exception as e:
                    last_exception = e
                    error_str = str(e)
                    
                    # Check if retryable
                    if '429' in error_str or 'Too Many Requests' in error_str:
                        # Rate limited - check for Retry-After header
                        retry_after = getattr(e, 'retry_after', None)
                        if retry_after:
                            wait_time = float(retry_after)
                        else:
                            # Exponential backoff with jitter
                            wait_time = base_delay * (2 ** attempt) + random.uniform(0, 0.1)
                        
                        logger.warning(
                            f"OpenAI 429 error (attempt {attempt + 1}/{max_retries}). "
                            f"Waiting {wait_time:.2f}s..."
                        )
                        time.sleep(wait_time)
                        
                    elif '500' in error_str or '502' in error_str or '503' in error_str:
                        # Server error - retry with backoff
                        wait_time = base_delay * (2 ** attempt)
                        logger.warning(
                            f"OpenAI server error (attempt {attempt + 1}/{max_retries}). "
                            f"Waiting {wait_time:.2f}s..."
                        )
                        time.sleep(wait_time)
                        
                    elif 'timeout' in error_str.lower():
                        # Timeout - retry
                        wait_time = base_delay * (2 ** attempt)
                        logger.warning(
                            f"OpenAI timeout (attempt {attempt + 1}/{max_retries}). "
                            f"Waiting {wait_time:.2f}s..."
                        )
                        time.sleep(wait_time)
                        
                    else:
                        # Non-retryable error
                        logger.error(f"Non-retryable OpenAI error: {error_str}")
                        raise
            
            # All retries exhausted
            logger.error(f"OpenAI API failed after {max_retries} attempts")
            raise last_exception
        
        return wrapper
    return decorator


def get_openai_with_retry():
    """
    Get OpenAI client with retry logic already applied
    
    Usage:
        from utils.openai_retry import get_openai_with_retry
        
        client = get_openai_with_retry()
        response = client.chat.completions.create(...)  # Auto-retries on failure
    """
    import os
    from openai import OpenAI
    
    client = OpenAI(
        api_key=os.environ.get('OPENAI_API_KEY'),
        timeout=60.0,  # Per Julius's spec
        max_retries=0  # We handle retries ourselves
    )
    
    # Wrap the create method with retry logic
    original_create = client.chat.completions.create
    client.chat.completions.create = openai_retry()(original_create)
    
    return client
