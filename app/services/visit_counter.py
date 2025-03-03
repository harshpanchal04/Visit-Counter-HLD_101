from typing import Dict, List, Any
import asyncio
from datetime import datetime
from ..core.redis_manager import RedisManager
import time


data: Dict[str, int] = {}

class CacheEntry:
    def __init__(self, value: int):
        self.value = value
        self.timestamp = time.time()

    def is_valid(self, ttl: int = 5) -> bool:
        """Check if cache entry is still valid"""
        return time.time() - self.timestamp < ttl

app_cache: Dict[str, CacheEntry] = {}


class VisitCounterService:
    def __init__(self):
        """Initialize the visit counter service with Redis manager"""
        self.redis_manager = RedisManager()
        self.cache_ttl = 5

    async def increment_visit(self, page_id: str) -> None:
        """
        Increment visit count for a page
        
        Args:
            page_id: Unique identifier for the page
        """
        # TODO: Implement visit count increment

        redis_key = f"visit:{page_id}"
        new_count = await self.redis_manager.increment(redis_key)
        
        # Update the cache with the new value
        app_cache[redis_key] = CacheEntry(new_count)

        pass

    async def get_visit_count(self, page_id: str) -> int:
        """
        Get current visit count for a page
        
        Args:
            page_id: Unique identifier for the page
            
        Returns:
            Current visit count
        """
        # TODO: Implement getting visit count
        # count = await self.redis_manager.get(f"visit:{page_id}")
        # return count
    
        redis_key = f"visit:{page_id}"
        
        # Check if we have a valid cache entry
        if redis_key in app_cache and app_cache[redis_key].is_valid(self.cache_ttl):
            return app_cache[redis_key].value, "in_memory"
        
        # Cache miss or expired, get from Redis
        count = await self.redis_manager.get(redis_key)
        
        # Update cache with new value from Redis
        app_cache[redis_key] = CacheEntry(count)
        
        return count, "redis"


        # return 0
