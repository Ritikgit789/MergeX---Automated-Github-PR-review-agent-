"""Rate limiter for Gemini API calls to prevent quota exhaustion."""
import asyncio
import time
import logging
from typing import Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class GeminiRateLimiter:
    """
    Rate limiter for Gemini API to prevent quota exhaustion.
    
    Free tier limits:
    - 60 requests per minute
    - 1 million tokens per day
    - This limiter helps stay well below these limits
    """
    
    def __init__(
        self,
        requests_per_minute: int = 30,  # Conservative: 50% of limit
        daily_request_limit: int = 100  # Daily soft limit
    ):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_minute: Max requests per minute (default: 30)
            daily_request_limit: Max requests per day (default: 100)
        """
        self.requests_per_minute = requests_per_minute
        self.daily_request_limit = daily_request_limit
        self.min_interval = 60.0 / requests_per_minute  # Seconds between requests
        
        # Tracking
        self.last_request_time: Optional[float] = None
        self.daily_requests = 0
        self.daily_reset_time = datetime.now() + timedelta(days=1)
        self.request_times = []  # For sliding window rate limiting
    
    async def acquire(self):
        """
        Acquire permission to make an API call.
        Will sleep if necessary to respect rate limits.
        """
        now = time.time()
        
        # Reset daily counter if needed
        if datetime.now() >= self.daily_reset_time:
            self.daily_requests = 0
            self.daily_reset_time = datetime.now() + timedelta(days=1)
            logger.info("Daily request counter reset")
        
        # Check daily limit
        if self.daily_requests >= self.daily_request_limit:
            logger.warning(
                f"Daily request limit ({self.daily_request_limit}) reached. "
                f"Resetting at {self.daily_reset_time.strftime('%H:%M:%S')}"
            )
            # Sleep until daily reset
            sleep_time = (self.daily_reset_time - datetime.now()).total_seconds()
            if sleep_time > 0:
                logger.info(f"Sleeping for {sleep_time:.0f}s until daily reset...")
                await asyncio.sleep(sleep_time)
                self.daily_requests = 0
        
        # Enforce per-minute rate limit
        if self.last_request_time is not None:
            elapsed = now - self.last_request_time
            if elapsed < self.min_interval:
                sleep_time = self.min_interval - elapsed
                await asyncio.sleep(sleep_time)
        
        self.last_request_time = time.time()
        self.daily_requests += 1
        
        logger.debug(
            f"Rate limited API call approved. "
            f"Daily: {self.daily_requests}/{self.daily_request_limit}"
        )
    
    def get_status(self) -> dict:
        """Get current rate limiter status."""
        return {
            "daily_requests": self.daily_requests,
            "daily_limit": self.daily_request_limit,
            "daily_reset": self.daily_reset_time.isoformat(),
            "requests_per_minute": self.requests_per_minute,
            "time_until_daily_reset": (
                self.daily_reset_time - datetime.now()
            ).total_seconds()
        }


# Global rate limiter instance
_rate_limiter: Optional[GeminiRateLimiter] = None


def get_rate_limiter() -> GeminiRateLimiter:
    """Get or create global rate limiter."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = GeminiRateLimiter(requests_per_minute=30, daily_request_limit=100)
    return _rate_limiter
