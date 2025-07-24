"""
Cache manager for YouTube MCP server.

Adapted from existing cache_manager.py with async support and MCP-specific enhancements.
"""

import json
import os
import random
import asyncio
from typing import Dict, Any, Optional
import time
from pathlib import Path
import threading
import logging
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Manages caching of YouTube data with TTL and async support.
    
    Adapted from existing cache_manager.py with async enhancements.
    """
    
    def __init__(self, cache_dir: str = "cache", ttl_seconds: int = 3600):
        """
        Initialize cache manager.
        
        Args:
            cache_dir: Directory to store cache files
            ttl_seconds: Time-to-live in seconds for cached items
        """
        self.cache_dir = Path(cache_dir)
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.access_times: Dict[str, float] = {}
        self.lock = asyncio.Lock()
        
        # Create cache directory if it doesn't exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing cache
        self._load_cache_sync()
    
    def _load_cache_sync(self) -> None:
        """Load cached data from disk (synchronous)."""
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    with open(cache_file) as f:
                        data = json.load(f)
                        if self._is_valid_cache_data(data):
                            cache_key = cache_file.stem
                            self.cache[cache_key] = data['data']
                            self.access_times[cache_key] = data['timestamp']
                except Exception as e:
                    logger.error(f"Error loading cache file {cache_file}: {e}")
        except Exception as e:
            logger.error(f"Error loading cache directory: {e}")
    
    def _is_valid_cache_data(self, data: Dict[str, Any]) -> bool:
        """Check if cached data is valid and not expired."""
        return (isinstance(data, dict) and 
                'timestamp' in data and 
                'data' in data and 
                time.time() - data['timestamp'] <= self.ttl_seconds)
    
    async def get(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Get data from cache if available and not expired.
        
        Args:
            cache_key: Cache key
            
        Returns:
            Cached data or None if not found/expired
        """
        async with self.lock:
            if cache_key in self.cache:
                if time.time() - self.access_times[cache_key] <= self.ttl_seconds:
                    self.access_times[cache_key] = time.time()  # Update access time
                    return self.cache[cache_key]
                else:
                    # Remove expired data
                    await self._remove_expired_item(cache_key)
            return None
    
    async def set(self, cache_key: str, data: Any, ttl: Optional[int] = None) -> None:
        """
        Store data in cache.
        
        Args:
            cache_key: Cache key
            data: Data to cache
            ttl: Override TTL for this item
        """
        async with self.lock:
            now = time.time()
            
            # Store in memory
            self.cache[cache_key] = data
            self.access_times[cache_key] = now
            
            # Store on disk
            cache_file = self.cache_dir / f"{cache_key}.json"
            cache_data = {
                'timestamp': now,
                'data': data,
                'ttl': ttl or self.ttl_seconds
            }
            
            # Write to file asynchronously
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._write_cache_file, cache_file, cache_data)
    
    def _write_cache_file(self, cache_file: Path, cache_data: Dict[str, Any]) -> None:
        """Write cache data to file (synchronous)."""
        try:
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, default=str)
        except Exception as e:
            logger.error(f"Error writing cache file {cache_file}: {e}")
    
    async def _remove_expired_item(self, cache_key: str) -> None:
        """Remove expired item from cache."""
        if cache_key in self.cache:
            del self.cache[cache_key]
        if cache_key in self.access_times:
            del self.access_times[cache_key]
        
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, cache_file.unlink)
    
    async def clear_expired(self) -> None:
        """Remove expired items from cache."""
        async with self.lock:
            now = time.time()
            expired = [
                key for key, access_time in self.access_times.items()
                if now - access_time > self.ttl_seconds
            ]
            
            for cache_key in expired:
                await self._remove_expired_item(cache_key)
    
    async def clear_all(self) -> None:
        """Clear all cached data."""
        async with self.lock:
            self.cache.clear()
            self.access_times.clear()
            
            # Remove files asynchronously
            loop = asyncio.get_event_loop()
            for cache_file in self.cache_dir.glob("*.json"):
                await loop.run_in_executor(None, cache_file.unlink)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            'total_items': len(self.cache),
            'cache_dir': str(self.cache_dir),
            'ttl_seconds': self.ttl_seconds,
            'memory_usage_mb': self._estimate_memory_usage() / (1024 * 1024)
        }
    
    def _estimate_memory_usage(self) -> int:
        """Estimate memory usage in bytes."""
        try:
            return len(json.dumps(self.cache, default=str).encode('utf-8'))
        except Exception:
            return 0


class RateLimiter:
    """
    Token bucket rate limiter for API requests with async support.
    
    Adapted from existing rate limiter with async enhancements.
    """
    
    def __init__(self, tokens_per_second: float = 1.0, bucket_size: int = 10):
        """
        Initialize rate limiter.
        
        Args:
            tokens_per_second: Rate of token replenishment
            bucket_size: Maximum number of tokens
        """
        self.tokens_per_second = tokens_per_second
        self.bucket_size = bucket_size
        self.tokens = bucket_size
        self.last_update = time.time()
        self.lock = asyncio.Lock()
    
    async def acquire(self, tokens: int = 1) -> None:
        """
        Acquire tokens, waiting if necessary.
        
        Args:
            tokens: Number of tokens to acquire
        """
        async with self.lock:
            await self._wait_for_tokens(tokens)
            self.tokens -= tokens
    
    async def _wait_for_tokens(self, tokens: int) -> None:
        """Wait for tokens to be available."""
        while True:
            now = time.time()
            time_passed = now - self.last_update
            self.tokens = min(
                self.bucket_size,
                self.tokens + time_passed * self.tokens_per_second
            )
            self.last_update = now
            
            if self.tokens >= tokens:
                break
            
            wait_time = (tokens - self.tokens) / self.tokens_per_second
            await asyncio.sleep(wait_time)
    
    def get_tokens_available(self) -> float:
        """Get current number of tokens available."""
        now = time.time()
        time_passed = now - self.last_update
        return min(
            self.bucket_size,
            self.tokens + time_passed * self.tokens_per_second
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics."""
        return {
            'tokens_per_second': self.tokens_per_second,
            'bucket_size': self.bucket_size,
            'current_tokens': self.get_tokens_available(),
            'last_update': self.last_update
        }


class RetryManager:
    """
    Manages retries with exponential backoff and async support.
    
    Adapted from existing retry manager with async enhancements.
    """
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, 
                 max_delay: float = 60.0, exponential_base: float = 2.0, jitter: float = 0.1):
        """
        Initialize retry manager.
        
        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            exponential_base: Base for exponential backoff
            jitter: Random jitter factor (0-1)
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
    
    async def execute_with_retry(self, func, *args, **kwargs):
        """
        Execute function with retry logic.
        
        Args:
            func: Async function to execute
            *args: Arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Function result
            
        Raises:
            Last exception if all retries failed
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    # Run sync function in executor
                    loop = asyncio.get_event_loop()
                    return await loop.run_in_executor(None, func, *args, **kwargs)
                    
            except Exception as e:
                last_exception = e
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                
                if attempt < self.max_retries:
                    delay = self.calculate_delay(attempt, e)
                    logger.info(f"Retrying in {delay:.2f} seconds...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All {self.max_retries + 1} attempts failed")
                    break
        
        if last_exception:
            raise last_exception
    
    def calculate_delay(self, attempt: int, error: Optional[Exception] = None) -> float:
        """
        Calculate delay for current retry attempt.
        
        Args:
            attempt: Current retry attempt number (0-based)
            error: Exception that caused the retry
            
        Returns:
            Delay in seconds
        """
        # Adjust delay based on error type
        if error is not None:
            if isinstance(error, Exception) and "quota" in str(error).lower():
                # Longer delay for quota errors
                multiplier = 4
            elif isinstance(error, Exception) and any(term in str(error).lower() 
                                                     for term in ["rate", "limit", "throttle"]):
                # Medium delay for rate limiting
                multiplier = 3
            else:
                # Standard delay for other errors
                multiplier = self.exponential_base
        else:
            multiplier = self.exponential_base

        delay = min(
            self.max_delay,
            self.base_delay * (multiplier ** attempt)
        )
        
        # Add jitter
        jitter_amount = delay * self.jitter
        final_delay = delay + (random.random() * 2 - 1) * jitter_amount
        
        logger.debug(f"Calculated retry delay: {final_delay:.2f}s for attempt {attempt}")
        return max(0, final_delay)  # Ensure non-negative delay
    
    def get_stats(self) -> Dict[str, Any]:
        """Get retry manager statistics."""
        return {
            'max_retries': self.max_retries,
            'base_delay': self.base_delay,
            'max_delay': self.max_delay,
            'exponential_base': self.exponential_base,
            'jitter': self.jitter
        }


class ErrorHandler:
    """
    Centralized error handling for the MCP server.
    """
    
    def __init__(self, logger_name: str = __name__):
        """
        Initialize error handler.
        
        Args:
            logger_name: Name for the logger
        """
        self.logger = logging.getLogger(logger_name)
        self.error_counts: Dict[str, int] = {}
        self.last_errors: Dict[str, str] = {}
    
    def handle_error(self, error: Exception, context: str = "unknown") -> Dict[str, Any]:
        """
        Handle and log an error, returning a standardized error response.
        
        Args:
            error: Exception to handle
            context: Context where the error occurred
            
        Returns:
            Standardized error response dictionary
        """
        error_type = type(error).__name__
        error_message = str(error)
        
        # Update statistics
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        self.last_errors[error_type] = error_message
        
        # Log the error
        self.logger.error(f"Error in {context}: {error_type}: {error_message}")
        
        # Log additional details for specific error types
        if "quota" in error_message.lower():
            self.logger.warning("YouTube API quota may be exhausted")
        elif "rate" in error_message.lower() or "limit" in error_message.lower():
            self.logger.warning("Rate limiting detected")
        elif "network" in error_message.lower() or "connection" in error_message.lower():
            self.logger.warning("Network connectivity issue detected")
        
        # Return standardized error response
        from datetime import datetime
        return {
            "success": False,
            "error": error_message,
            "error_type": error_type,
            "context": context,
            "timestamp": datetime.utcnow().isoformat(),
            "retry_suggested": error_type in ["ConnectionError", "TimeoutError", "HTTPError"]
        }
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics."""
        return {
            'error_counts': self.error_counts.copy(),
            'last_errors': self.last_errors.copy(),
            'total_errors': sum(self.error_counts.values())
        }
    
    def reset_stats(self) -> None:
        """Reset error statistics."""
        self.error_counts.clear()
        self.last_errors.clear()


# Async context managers for resource management
@asynccontextmanager
async def managed_cache(cache_dir: str = "cache", ttl_seconds: int = 3600):
    """Async context manager for cache."""
    cache = CacheManager(cache_dir, ttl_seconds)
    try:
        yield cache
    finally:
        await cache.clear_expired()


@asynccontextmanager
async def managed_rate_limiter(tokens_per_second: float = 1.0, bucket_size: int = 10):
    """Async context manager for rate limiter."""
    limiter = RateLimiter(tokens_per_second, bucket_size)
    try:
        yield limiter
    finally:
        # Clean up if needed
        pass