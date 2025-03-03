from typing import Dict, Tuple
import asyncio
import time
from datetime import datetime
from ..core.redis_manager import RedisManager
# In-memory cache
app_cache: Dict[str, "CacheEntry"] = {}
# Write buffer for batching operations
write_buffer: Dict[str, int] = {}

class CacheEntry:
    def __init__(self, value: int):
        self.value = value
        self.timestamp = time.time()

    def is_valid(self, ttl: int = 5) -> bool:
        """Check if cache entry is still valid"""
        return time.time() - self.timestamp < ttl




class VisitCounterService:
    def __init__(self):
        """Initialize the visit counter service with Redis manager"""
        self.redis_manager = RedisManager()
        self.cache_ttl = 5  # Cache entry TTL (seconds)
        self.flush_interval = 30  # Time interval to flush write buffer (seconds)
        self._flush_lock = asyncio.Lock()
        
        # Start background task to periodically flush buffer
        self._start_background_flush()

    def _start_background_flush(self):
        """Start the background task to periodically flush the buffer"""
        asyncio.create_task(self._periodic_flush())

    async def _periodic_flush(self):
        """Periodically flush the write buffer to Redis"""
        while True:
            await asyncio.sleep(self.flush_interval)
            await self._flush_buffer()

    async def _flush_buffer(self):
        """Flush the write buffer to Redis"""
        async with self._flush_lock:
            buffer_copy = dict(write_buffer)
            write_buffer.clear()
            
            for key, count in buffer_copy.items():
                if count > 0:
                    await self.redis_manager.increment(key, count)
    
    async def increment_visit(self, page_id: str) -> None:
        """
        Increment visit count for a page
        
        Args:
            page_id: Unique identifier for the page
        """
        
        redis_key = f"visit:{page_id}"
        
        # Add to write buffer instead of writing directly to Redis
        async with self._flush_lock:
            write_buffer[redis_key] = write_buffer.get(redis_key, 0) + 1
    
    async def get_visit_count(self, page_id: str) -> Tuple[int, str]:
        """
        Get current visit count for a page
        
        Args:
            page_id: Unique identifier for the page
        
        Returns:
            Tuple of (visit count, source of data)
        """
        
        redis_key = f"visit:{page_id}"
        
        # Check if we have a valid cache entry
        if redis_key in app_cache and app_cache[redis_key].is_valid(self.cache_ttl):
            pending_count = write_buffer.get(redis_key, 0)
            return app_cache[redis_key].value + pending_count, "in_memory"
        
        # Cache miss or expired, get from Redis
        pending_count = 0
        async with self._flush_lock:
            pending_count = write_buffer.pop(redis_key, 0)
            if pending_count > 0:
                await self.redis_manager.increment(redis_key, pending_count)
        
        count = await self.redis_manager.get(redis_key)
        
        # Update cache with new value from Redis
        app_cache[redis_key] = CacheEntry(count)



        return count, "redis"
