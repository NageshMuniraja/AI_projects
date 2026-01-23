"""
Cache manager using Redis
"""

from typing import Any, Optional
import json
import hashlib
import logging
from redis import asyncio as aioredis

from app.core.config import settings

logger = logging.getLogger(__name__)


class CacheManager:
    """Manage caching with Redis"""
    
    def __init__(self):
        """Initialize cache manager"""
        self.redis_client: Optional[aioredis.Redis] = None
        self._initialized = False
    
    async def _ensure_initialized(self):
        """Ensure Redis client is initialized"""
        if not self._initialized:
            try:
                self.redis_client = await aioredis.from_url(
                    settings.redis_url,
                    encoding="utf-8",
                    decode_responses=True
                )
                self._initialized = True
                logger.info("Redis client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Redis: {str(e)}")
                self.redis_client = None
    
    def generate_key(self, *args) -> str:
        """Generate cache key from arguments"""
        key_data = json.dumps(args, sort_keys=True)
        return hashlib.sha256(key_data.encode()).hexdigest()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        await self._ensure_initialized()
        
        if not self.redis_client:
            return None
        
        try:
            value = await self.redis_client.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            logger.error(f"Cache get error: {str(e)}")
        
        return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = None
    ) -> bool:
        """Set value in cache"""
        await self._ensure_initialized()
        
        if not self.redis_client:
            return False
        
        try:
            ttl = ttl or settings.REDIS_CACHE_TTL
            await self.redis_client.setex(
                key,
                ttl,
                json.dumps(value)
            )
            return True
        except Exception as e:
            logger.error(f"Cache set error: {str(e)}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        await self._ensure_initialized()
        
        if not self.redis_client:
            return False
        
        try:
            await self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {str(e)}")
            return False
    
    async def clear(self) -> bool:
        """Clear all cache"""
        await self._ensure_initialized()
        
        if not self.redis_client:
            return False
        
        try:
            await self.redis_client.flushdb()
            return True
        except Exception as e:
            logger.error(f"Cache clear error: {str(e)}")
            return False
