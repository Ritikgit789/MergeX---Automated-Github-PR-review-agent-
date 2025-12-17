"""Retry handler with exponential backoff for quota-limited APIs."""
import asyncio
import logging
from typing import Callable, TypeVar, Any
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


async def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    *args,
    **kwargs
) -> Any:
    """
    Retry async function with exponential backoff.
    
    Args:
        func: Async function to call
        max_retries: Maximum number of retries
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        *args: Function arguments
        **kwargs: Function keyword arguments
        
    Returns:
        Function result
        
    Raises:
        Exception: If all retries fail
    """
    delay = initial_delay
    last_error = None
    
    for attempt in range(max_retries + 1):
        try:
            logger.debug(f"Attempt {attempt + 1}/{max_retries + 1} for {func.__name__}")
            return await func(*args, **kwargs)
            
        except Exception as e:
            error_str = str(e).lower()
            
            # Check if it's a quota/rate limit error
            is_quota_error = any([
                "quota" in error_str,
                "rate_limit" in error_str,
                "429" in error_str,
                "resource_exhausted" in error_str,
                "too_many_requests" in error_str
            ])
            
            last_error = e
            
            # Only retry on quota errors, not on other errors
            if not is_quota_error:
                logger.error(f"Non-quota error in {func.__name__}: {str(e)}")
                raise
            
            if attempt < max_retries:
                logger.warning(
                    f"Quota exceeded in {func.__name__}. "
                    f"Retrying in {delay:.1f}s (attempt {attempt + 1}/{max_retries})..."
                )
                await asyncio.sleep(delay)
                
                # Exponential backoff with jitter
                delay = min(delay * 2, max_delay)
            else:
                logger.error(f"All {max_retries + 1} retry attempts failed for {func.__name__}")
                raise
    
    raise last_error


def retry_on_quota(
    max_retries: int = 3,
    initial_delay: float = 2.0,
    max_delay: float = 60.0
):
    """
    Decorator for async functions that should retry on quota errors.
    
    Args:
        max_retries: Maximum number of retries
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await retry_with_backoff(
                lambda: func(*args, **kwargs),
                max_retries=max_retries,
                initial_delay=initial_delay,
                max_delay=max_delay
            )
        return wrapper
    return decorator
